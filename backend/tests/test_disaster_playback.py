import pytest
from backend.app.services.disaster_playback_service import disaster_playback_service


@pytest.mark.asyncio
async def test_historical_benchmark_seeding_and_playback(db_session):
    # 1. Seed benchmarks
    await disaster_playback_service.seed_historical_benchmarks(db_session)

    # 2. Get all incidents
    incidents = await disaster_playback_service.get_all_incidents(db_session)
    assert len(incidents) >= 4
    lhonak = next((i for i in incidents if "HIST-SIK-LHONAK-2023" == i.id), None)
    assert lhonak is not None
    assert lhonak.recorded_lead_time_hours >= 15.0

    # 3. Retrieve playback frames
    playback = await disaster_playback_service.get_playback_for_incident(db_session, lhonak.id)
    assert playback is not None
    assert playback.total_frames >= 5
    assert len(playback.playback_frames) == playback.total_frames

    # Check frame progression
    first_frame = playback.playback_frames[0]
    impact_frame = next((f for f in playback.playback_frames if f.step_offset_hours == 0), None)
    assert first_frame.step_offset_hours < 0
    assert impact_frame is not None
    assert impact_frame.simulated_risk_score > 90.0
