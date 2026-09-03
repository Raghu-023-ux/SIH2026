import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.event import DisasterEvent
from backend.app.models.location import Location
from backend.app.models.risk import RiskAssessment
from backend.app.schemas.alerting import (
    CAPAlertFeedItem,
    CAPInfo,
    CAPArea,
    CAPParameter,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger


class CAPAlertService:
    """
    Common Alerting Protocol (CAP v1.2 / ITU X.1303 / OASIS) Standard Generator.
    Produces compliant XML and JSON feeds for national disaster aggregators (NDMA, IMD, SDMAs).
    """

    @staticmethod
    def _map_cap_urgency_severity(event_severity: str) -> Dict[str, str]:
        sev = event_severity.upper()
        if sev == "CRITICAL":
            return {
                "urgency": "Immediate",
                "severity": "Extreme",
                "certainty": "Observed",
                "responseType": "Evacuate",
            }
        elif sev == "HIGH":
            return {
                "urgency": "Expected",
                "severity": "Severe",
                "certainty": "Likely",
                "responseType": "Prepare",
            }
        elif sev == "MODERATE":
            return {
                "urgency": "Future",
                "severity": "Moderate",
                "certainty": "Possible",
                "responseType": "Monitor",
            }
        else:
            return {
                "urgency": "Past",
                "severity": "Minor",
                "certainty": "Unlikely",
                "responseType": "Monitor",
            }

    @staticmethod
    async def build_cap_item(session: AsyncSession, event: DisasterEvent) -> Optional[CAPAlertFeedItem]:
        loc_stmt = select(Location).where(Location.id == event.location_id)
        loc = (await session.execute(loc_stmt)).scalars().first()
        if not loc:
            return None

        # Fetch latest scientific assessment for parameters
        assess_stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.location_id == loc.id)
            .order_by(RiskAssessment.timestamp.desc())
        )
        assess = (await session.execute(assess_stmt)).scalars().first()

        cap_mapping = CAPAlertService._map_cap_urgency_severity(event.severity)
        expires_dt = event.updated_at + timedelta(hours=12)

        radius_km = 25.0 if event.severity == "CRITICAL" else 15.0
        area_circle = f"{loc.latitude:.4f},{loc.longitude:.4f} {radius_km:.1f}"

        parameters = [
            CAPParameter(valueName="disaster_risk_score", value=f"{event.risk_score:.1f}"),
            CAPParameter(valueName="hazard_type", value=event.event_type),
            CAPParameter(valueName="engine_confidence", value=f"{assess.confidence_score if assess else 0.82:.2f}"),
            CAPParameter(valueName="data_mode", value=settings.DATA_MODE),
            CAPParameter(valueName="state_authority", value=f"{loc.state} SDMA"),
        ]

        info_en = CAPInfo(
            language="en-IN",
            category="Geo",
            event="Landslide Early Warning",
            responseType=cap_mapping["responseType"],
            urgency=cap_mapping["urgency"],
            severity=cap_mapping["severity"],
            certainty=cap_mapping["certainty"],
            eventCode="EQ-LS-01",
            expires=expires_dt,
            headline=f"{cap_mapping['severity'].upper()} LANDSLIDE RISK: {loc.district}, {loc.state}",
            description=(
                f"The AI Disaster Intelligence Engine detected high landslide susceptibility "
                f"with elevated rainfall persistence and pore saturation around {loc.name}. {event.summary}"
            ),
            instruction=(
                "Move away from steep slopes and hillside cut-banks. Avoid blocked transit roads. "
                "Follow official guidance from district disaster management authorities."
            ),
            web="http://localhost:3000/public",
            contact=f"{loc.state} Disaster Control Room: 1070 / 112",
            parameter=parameters,
            area=[
                CAPArea(
                    areaDesc=f"{loc.name}, {loc.district}, {loc.state} ({radius_km:.0f}km Radius)",
                    circle=area_circle
                )
            ]
        )

        return CAPAlertFeedItem(
            identifier=f"IN-NER-CAP-{event.id}",
            sender="DISASTER_ENGINE@NER.NDMA.GOV.IN",
            sent=event.updated_at,
            status="Actual" if settings.DATA_MODE == "LIVE" else "Draft",
            msgType="Alert" if event.status in ["DETECTED", "ACTIVE"] else "Update",
            scope="Public",
            code=["IPAWS-CAP-1.2"],
            info=[info_en]
        )

    @staticmethod
    async def generate_cap_xml(session: AsyncSession, event_id: Optional[str] = None) -> str:
        """Generates valid OASIS CAP v1.2 XML string."""
        if event_id:
            stmt = select(DisasterEvent).where(DisasterEvent.id == event_id)
        else:
            stmt = (
                select(DisasterEvent)
                .where(
                    and_(
                        DisasterEvent.status != "RESOLVED",
                        DisasterEvent.severity.in_(["HIGH", "CRITICAL"])
                    )
                )
                .order_by(DisasterEvent.updated_at.desc())
            )
        events = list((await session.execute(stmt)).scalars().all())

        # Root XML element
        alert_elem = ET.Element("alert", xmlns="urn:oasis:names:tc:emergency:cap:1.2")

        if not events:
            # Empty heartbeat alert
            ET.SubElement(alert_elem, "identifier").text = f"IN-NER-HEARTBEAT-{int(datetime.now(timezone.utc).timestamp())}"
            ET.SubElement(alert_elem, "sender").text = "DISASTER_ENGINE@NER.NDMA.GOV.IN"
            ET.SubElement(alert_elem, "sent").text = datetime.now(timezone.utc).isoformat()
            ET.SubElement(alert_elem, "status").text = "Actual" if settings.DATA_MODE == "LIVE" else "Draft"
            ET.SubElement(alert_elem, "msgType").text = "Cancel"
            ET.SubElement(alert_elem, "scope").text = "Public"
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(alert_elem, encoding="unicode")

        # Build first active event as root alert
        ev = events[0]
        cap_item = await CAPAlertService.build_cap_item(session, ev)
        if not cap_item:
            return '<?xml version="1.0" encoding="UTF-8"?>\n<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2"/>'

        ET.SubElement(alert_elem, "identifier").text = cap_item.identifier
        ET.SubElement(alert_elem, "sender").text = cap_item.sender
        ET.SubElement(alert_elem, "sent").text = cap_item.sent.isoformat()
        ET.SubElement(alert_elem, "status").text = cap_item.status
        ET.SubElement(alert_elem, "msgType").text = cap_item.msgType
        ET.SubElement(alert_elem, "scope").text = cap_item.scope

        for info in cap_item.info:
            info_elem = ET.SubElement(alert_elem, "info")
            ET.SubElement(info_elem, "language").text = info.language
            ET.SubElement(info_elem, "category").text = info.category
            ET.SubElement(info_elem, "event").text = info.event
            ET.SubElement(info_elem, "responseType").text = info.responseType
            ET.SubElement(info_elem, "urgency").text = info.urgency
            ET.SubElement(info_elem, "severity").text = info.severity
            ET.SubElement(info_elem, "certainty").text = info.certainty
            ET.SubElement(info_elem, "eventCode").text = info.eventCode or "EQ-LS-01"
            ET.SubElement(info_elem, "expires").text = info.expires.isoformat()
            ET.SubElement(info_elem, "headline").text = info.headline
            ET.SubElement(info_elem, "description").text = info.description
            ET.SubElement(info_elem, "instruction").text = info.instruction
            if info.web:
                ET.SubElement(info_elem, "web").text = info.web
            if info.contact:
                ET.SubElement(info_elem, "contact").text = info.contact

            for param in info.parameter:
                param_elem = ET.SubElement(info_elem, "parameter")
                ET.SubElement(param_elem, "valueName").text = param.valueName
                ET.SubElement(param_elem, "value").text = param.value

            for area in info.area:
                area_elem = ET.SubElement(info_elem, "area")
                ET.SubElement(area_elem, "areaDesc").text = area.areaDesc
                if area.circle:
                    ET.SubElement(area_elem, "circle").text = area.circle

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(alert_elem, encoding="unicode")

    @staticmethod
    async def generate_cap_json(session: AsyncSession) -> List[CAPAlertFeedItem]:
        """Generates CAP v1.2 JSON feed."""
        stmt = (
            select(DisasterEvent)
            .where(
                and_(
                    DisasterEvent.status != "RESOLVED",
                    DisasterEvent.severity.in_(["HIGH", "CRITICAL"])
                )
            )
            .order_by(DisasterEvent.updated_at.desc())
        )
        events = list((await session.execute(stmt)).scalars().all())
        results: List[CAPAlertFeedItem] = []

        for ev in events:
            item = await CAPAlertService.build_cap_item(session, ev)
            if item:
                results.append(item)

        return results


cap_service = CAPAlertService()
