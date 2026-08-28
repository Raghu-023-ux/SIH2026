import pytest
from sqlalchemy import select
from backend.app.models.event import DisasterEvent
from backend.app.services.sitrep_service import sitrep_service


@pytest.mark.asyncio
async def test_situation_report_generation(client, db_session):
    # Seed event
    await client.post("/api/v1/simulation/scenario", json={"scenario": "heavy_rain", "seed": 42})

    events = list((await db_session.execute(select(DisasterEvent))).scalars().all())
    assert len(events) >= 1
    ev = events[0]

    sitrep = await sitrep_service.generate_sitrep(db_session, ev.id, reporting_officer="Duty Officer Sharma")
    assert sitrep is not None
    assert "SITREP-NER" in sitrep.report_number
    assert sitrep.reporting_officer == "Duty Officer Sharma"
    assert len(sitrep.executive_summary) > 20
    assert len(sitrep.sections) >= 5

    # Check key sections
    headings = [s.heading for s in sitrep.sections]
    assert any("Scientific Risk Assessment" in h for h in headings)
    assert any("Field Intelligence" in h for h in headings)
    assert any("Tactical Recommendations" in h for h in headings)
