import pytest
import xml.etree.ElementTree as ET
from backend.app.services.cap_service import cap_service


@pytest.mark.asyncio
async def test_cap_xml_generation(client, db_session):
    # Seed event
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    xml_str = await cap_service.generate_cap_xml(db_session)
    assert xml_str.startswith("<?xml")
    assert "<alert" in xml_str
    assert "xmlns=\"urn:oasis:names:tc:emergency:cap:1.2\"" in xml_str

    # Parse XML to verify schema compliance
    root = ET.fromstring(xml_str)
    # Check namespace
    ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
    identifier = root.find("cap:identifier", ns)
    assert identifier is not None
    assert "IN-NER" in identifier.text

    status = root.find("cap:status", ns)
    assert status is not None

    info = root.find("cap:info", ns)
    assert info is not None
    headline = info.find("cap:headline", ns)
    assert headline is not None
    assert "LANDSLIDE" in headline.text


@pytest.mark.asyncio
async def test_cap_json_generation(client, db_session):
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    cap_items = await cap_service.generate_cap_json(db_session)
    assert len(cap_items) >= 1
    assert cap_items[0].identifier.startswith("IN-NER-CAP-")
    assert len(cap_items[0].info) >= 1
    assert cap_items[0].info[0].category == "Geo"
