import pytest
from backend.app.agents.tools import agent_tools
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.services.field_service import field_service
from backend.app.schemas.field import FieldReportCreate


@pytest.mark.asyncio
async def test_ai_field_evidence_incorporation(client, db_session):
    # 1. Submit a ground report
    report_in = FieldReportCreate(
        location_id="NER-SIK-GANGTOK-01",
        reported_by="SDRF Unit Alpha",
        report_type="ROAD_BLOCKED",
        severity="CRITICAL",
        description="Massive mudflow blocking NH-10 near Gangtok bypass.",
        latitude=27.3389,
        longitude=88.6065
    )
    await field_service.submit_field_report(db_session, report_in)

    # 2. Test get_field_reports tool
    tools_res = await agent_tools.get_field_reports(db_session, location_id="NER-SIK-GANGTOK-01")
    assert tools_res["reports_count"] >= 1
    assert tools_res["reports"][0]["report_type"] == "ROAD_BLOCKED"

    # 3. Run AI Analyst via orchestrator
    ai_resp = await agent_orchestrator.execute(
        session=db_session,
        location_id="NER-SIK-GANGTOK-01",
        question="What are the current ground conditions and risk drivers?",
        agent_type="analyst"
    )

    # 4. Verify AI findings contain field observation evidence
    field_ev = next((e for e in ai_resp.evidence if e.evidence_type == "FIELD_GROUND_TRUTH"), None)
    assert field_ev is not None
    assert "observation" in field_ev.metric or "report" in field_ev.metric
    assert "sector observations" in ai_resp.answer.lower() or "rescue" in ai_resp.answer.lower()
