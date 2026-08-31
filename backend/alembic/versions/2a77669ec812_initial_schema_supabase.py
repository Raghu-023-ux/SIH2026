"""initial_schema_supabase

Revision ID: 2a77669ec812
Revises: 
Create Date: 2026-08-31 19:17:30.938578

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a77669ec812'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Locations Table
    op.create_table(
        'locations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('district', sa.String(length=128), nullable=False),
        sa.Column('state', sa.String(length=128), nullable=False),
        sa.Column('elevation', sa.Float(), nullable=False),
        sa.Column('slope_angle', sa.Float(), nullable=False),
        sa.Column('susceptibility_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_district'), 'locations', ['district'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    op.create_index(op.f('ix_locations_state'), 'locations', ['state'], unique=False)

    # 2. Disaster Events Table
    op.create_table(
        'disaster_events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('initial_risk', sa.Float(), nullable=False),
        sa.Column('peak_risk', sa.Float(), nullable=False),
        sa.Column('peak_severity', sa.String(length=32), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('trajectory', sa.String(length=32), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expected_start', sa.DateTime(), nullable=True),
        sa.Column('expected_peak', sa.DateTime(), nullable=True),
        sa.Column('affected_area', sa.String(length=256), nullable=True),
        sa.Column('summary', sa.String(length=1024), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disaster_events_event_type'), 'disaster_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_disaster_events_location_id'), 'disaster_events', ['location_id'], unique=False)
    op.create_index(op.f('ix_disaster_events_status'), 'disaster_events', ['status'], unique=False)
    op.create_index('idx_event_loc_status', 'disaster_events', ['location_id', 'status'], unique=False)
    op.create_index('idx_event_type_status', 'disaster_events', ['event_type', 'status'], unique=False)

    # 3. Weather Observations Table
    op.create_table(
        'weather_observations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('wind_direction', sa.Float(), nullable=True),
        sa.Column('rainfall_1h', sa.Float(), nullable=True),
        sa.Column('rainfall_6h', sa.Float(), nullable=True),
        sa.Column('rainfall_24h', sa.Float(), nullable=True),
        sa.Column('soil_moisture', sa.Float(), nullable=True),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('source_version', sa.String(length=32), nullable=False),
        sa.Column('retrieved_at', sa.DateTime(), nullable=False),
        sa.Column('freshness_status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_observations_location_id'), 'weather_observations', ['location_id'], unique=False)
    op.create_index(op.f('ix_weather_observations_source'), 'weather_observations', ['source'], unique=False)
    op.create_index(op.f('ix_weather_observations_timestamp'), 'weather_observations', ['timestamp'], unique=False)
    op.create_index('idx_weather_loc_time', 'weather_observations', ['location_id', 'timestamp'], unique=False)
    op.create_index('idx_weather_loc_source', 'weather_observations', ['location_id', 'source'], unique=False)

    # 4. Risk Assessments Table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('hazard_type', sa.String(length=64), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(length=512), nullable=False),
        sa.Column('factors', sa.JSON(), nullable=False),
        sa.Column('assessment_version', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessments_hazard_type'), 'risk_assessments', ['hazard_type'], unique=False)
    op.create_index(op.f('ix_risk_assessments_location_id'), 'risk_assessments', ['location_id'], unique=False)
    op.create_index(op.f('ix_risk_assessments_risk_level'), 'risk_assessments', ['risk_level'], unique=False)
    op.create_index(op.f('ix_risk_assessments_timestamp'), 'risk_assessments', ['timestamp'], unique=False)
    op.create_index('idx_risk_loc_time_hazard', 'risk_assessments', ['location_id', 'timestamp', 'hazard_type'], unique=False)

    # 5. Risk Assessment History Table
    op.create_table(
        'risk_assessment_history',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('trajectory', sa.String(length=32), nullable=False),
        sa.Column('factors_json', sa.JSON(), nullable=False),
        sa.Column('reasons_json', sa.JSON(), nullable=False),
        sa.Column('quality_json', sa.JSON(), nullable=True),
        sa.Column('engine_version', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessment_history_event_id'), 'risk_assessment_history', ['event_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_history_location_id'), 'risk_assessment_history', ['location_id'], unique=False)
    op.create_index(op.f('ix_risk_assessment_history_timestamp'), 'risk_assessment_history', ['timestamp'], unique=False)
    op.create_index('idx_hist_event_time', 'risk_assessment_history', ['event_id', 'timestamp'], unique=False)
    op.create_index('idx_hist_loc_time', 'risk_assessment_history', ['location_id', 'timestamp'], unique=False)

    # 6. Field Teams Table
    op.create_table(
        'field_teams',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('team_name', sa.String(length=128), nullable=False),
        sa.Column('callsign', sa.String(length=64), nullable=False),
        sa.Column('assigned_location_id', sa.String(length=64), nullable=True),
        sa.Column('assigned_event_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('contact_channel', sa.String(length=64), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_event_id'], ['disaster_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_field_teams_assigned_event_id'), 'field_teams', ['assigned_event_id'], unique=False)
    op.create_index(op.f('ix_field_teams_assigned_location_id'), 'field_teams', ['assigned_location_id'], unique=False)
    op.create_index(op.f('ix_field_teams_callsign'), 'field_teams', ['callsign'], unique=True)
    op.create_index(op.f('ix_field_teams_status'), 'field_teams', ['status'], unique=False)
    op.create_index(op.f('ix_field_teams_team_name'), 'field_teams', ['team_name'], unique=False)

    # 7. Field Reports Table
    op.create_table(
        'field_reports',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('team_id', sa.String(length=64), nullable=True),
        sa.Column('reported_by', sa.String(length=128), nullable=False),
        sa.Column('report_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location_accuracy', sa.Float(), nullable=True),
        sa.Column('location_source', sa.String(length=32), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('reviewed_by', sa.String(length=128), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['field_teams.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_field_reports_event_id'), 'field_reports', ['event_id'], unique=False)
    op.create_index(op.f('ix_field_reports_location_id'), 'field_reports', ['location_id'], unique=False)
    op.create_index(op.f('ix_field_reports_report_type'), 'field_reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_field_reports_severity'), 'field_reports', ['severity'], unique=False)
    op.create_index(op.f('ix_field_reports_status'), 'field_reports', ['status'], unique=False)
    op.create_index(op.f('ix_field_reports_team_id'), 'field_reports', ['team_id'], unique=False)
    op.create_index(op.f('ix_field_reports_timestamp'), 'field_reports', ['timestamp'], unique=False)
    op.create_index('idx_field_rep_event_status', 'field_reports', ['event_id', 'status'], unique=False)
    op.create_index('idx_field_rep_loc_time', 'field_reports', ['location_id', 'timestamp'], unique=False)

    # 8. Field Report Images Table
    op.create_table(
        'field_report_images',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('report_id', sa.String(length=64), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.Float(), nullable=False),
        sa.Column('uploaded_by', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['field_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_field_report_images_report_id'), 'field_report_images', ['report_id'], unique=False)

    # 9. Assistance Requests Table
    op.create_table(
        'assistance_requests',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('team_id', sa.String(length=64), nullable=False),
        sa.Column('request_type', sa.String(length=64), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('assigned_unit', sa.String(length=128), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['team_id'], ['field_teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assistance_requests_created_at'), 'assistance_requests', ['created_at'], unique=False)
    op.create_index(op.f('ix_assistance_requests_event_id'), 'assistance_requests', ['event_id'], unique=False)
    op.create_index(op.f('ix_assistance_requests_priority'), 'assistance_requests', ['priority'], unique=False)
    op.create_index(op.f('ix_assistance_requests_request_type'), 'assistance_requests', ['request_type'], unique=False)
    op.create_index(op.f('ix_assistance_requests_status'), 'assistance_requests', ['status'], unique=False)
    op.create_index(op.f('ix_assistance_requests_team_id'), 'assistance_requests', ['team_id'], unique=False)

    # 10. Operational Messages Table
    op.create_table(
        'operational_messages',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('sender_id', sa.String(length=128), nullable=False),
        sa.Column('recipient_team', sa.String(length=128), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operational_messages_created_at'), 'operational_messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_operational_messages_event_id'), 'operational_messages', ['event_id'], unique=False)
    op.create_index(op.f('ix_operational_messages_priority'), 'operational_messages', ['priority'], unique=False)
    op.create_index(op.f('ix_operational_messages_recipient_team'), 'operational_messages', ['recipient_team'], unique=False)

    # 11. Broadcasts Table
    op.create_table(
        'broadcasts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('sender_id', sa.String(length=128), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('target_type', sa.String(length=64), nullable=False),
        sa.Column('target_filter', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_broadcasts_created_at'), 'broadcasts', ['created_at'], unique=False)
    op.create_index(op.f('ix_broadcasts_event_id'), 'broadcasts', ['event_id'], unique=False)
    op.create_index(op.f('ix_broadcasts_priority'), 'broadcasts', ['priority'], unique=False)
    op.create_index(op.f('ix_broadcasts_target_type'), 'broadcasts', ['target_type'], unique=False)

    # 12. Notifications Table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('broadcast_id', sa.String(length=64), nullable=False),
        sa.Column('recipient_id', sa.String(length=128), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['broadcast_id'], ['broadcasts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_broadcast_id'), 'notifications', ['broadcast_id'], unique=False)
    op.create_index(op.f('ix_notifications_channel'), 'notifications', ['channel'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_id'), 'notifications', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_notifications_status'), 'notifications', ['status'], unique=False)

    # 13. Notification Dispatch Logs Table
    op.create_table(
        'notification_dispatch_logs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('recipient_group', sa.String(length=64), nullable=False),
        sa.Column('language', sa.String(length=16), nullable=False),
        sa.Column('payload_summary', sa.String(length=256), nullable=False),
        sa.Column('full_payload_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_dispatch_logs_channel'), 'notification_dispatch_logs', ['channel'], unique=False)
    op.create_index(op.f('ix_notification_dispatch_logs_created_at'), 'notification_dispatch_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_notification_dispatch_logs_event_id'), 'notification_dispatch_logs', ['event_id'], unique=False)
    op.create_index(op.f('ix_notification_dispatch_logs_location_id'), 'notification_dispatch_logs', ['location_id'], unique=False)
    op.create_index(op.f('ix_notification_dispatch_logs_status'), 'notification_dispatch_logs', ['status'], unique=False)

    # 14. Situation Reports Table
    op.create_table(
        'situation_reports',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('report_number', sa.String(length=64), nullable=False),
        sa.Column('incident_name', sa.String(length=128), nullable=False),
        sa.Column('reporting_officer', sa.String(length=128), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('full_sitrep_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_situation_reports_created_at'), 'situation_reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_situation_reports_event_id'), 'situation_reports', ['event_id'], unique=False)
    op.create_index(op.f('ix_situation_reports_location_id'), 'situation_reports', ['location_id'], unique=False)
    op.create_index(op.f('ix_situation_reports_report_number'), 'situation_reports', ['report_number'], unique=True)

    # 15. Safety Points Table
    op.create_table(
        'safety_points',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('point_type', sa.String(length=32), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('availability', sa.String(length=32), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False),
        sa.Column('contact_number', sa.String(length=64), nullable=True),
        sa.Column('is_simulated', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_safety_points_location_id'), 'safety_points', ['location_id'], unique=False)
    op.create_index(op.f('ix_safety_points_name'), 'safety_points', ['name'], unique=False)
    op.create_index(op.f('ix_safety_points_point_type'), 'safety_points', ['point_type'], unique=False)
    op.create_index('idx_safepoint_loc_type', 'safety_points', ['location_id', 'point_type'], unique=False)

    # 16. Public Users Table
    op.create_table(
        'public_users',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location_permission', sa.Boolean(), nullable=False),
        sa.Column('alert_enabled', sa.Boolean(), nullable=False),
        sa.Column('alert_radius_km', sa.Float(), nullable=False),
        sa.Column('preferred_language', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. Public Alert Acknowledgments Table
    op.create_table(
        'public_alert_acknowledgments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['disaster_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_public_alert_acknowledgments_event_id'), 'public_alert_acknowledgments', ['event_id'], unique=False)
    op.create_index(op.f('ix_public_alert_acknowledgments_location_id'), 'public_alert_acknowledgments', ['location_id'], unique=False)
    op.create_index(op.f('ix_public_alert_acknowledgments_timestamp'), 'public_alert_acknowledgments', ['timestamp'], unique=False)
    op.create_index(op.f('ix_public_alert_acknowledgments_user_id'), 'public_alert_acknowledgments', ['user_id'], unique=False)

    # 18. Historical Disaster Incidents Table
    op.create_table(
        'historical_disaster_incidents',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=True),
        sa.Column('state', sa.String(length=64), nullable=False),
        sa.Column('district', sa.String(length=64), nullable=False),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('incident_type', sa.String(length=64), nullable=False),
        sa.Column('actual_impact_summary', sa.Text(), nullable=False),
        sa.Column('casualties', sa.Integer(), nullable=False),
        sa.Column('infrastructure_loss', sa.String(length=256), nullable=True),
        sa.Column('recorded_lead_time_hours', sa.Float(), nullable=False),
        sa.Column('peak_rainfall_mm', sa.Float(), nullable=False),
        sa.Column('timeline_data_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historical_disaster_incidents_event_date'), 'historical_disaster_incidents', ['event_date'], unique=False)
    op.create_index(op.f('ix_historical_disaster_incidents_location_id'), 'historical_disaster_incidents', ['location_id'], unique=False)
    op.create_index(op.f('ix_historical_disaster_incidents_name'), 'historical_disaster_incidents', ['name'], unique=True)

    # 19. Model Evaluation Runs Table
    op.create_table(
        'model_evaluation_runs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('run_name', sa.String(length=128), nullable=False),
        sa.Column('dataset_name', sa.String(length=128), nullable=False),
        sa.Column('weights_json', sa.JSON(), nullable=False),
        sa.Column('precision', sa.Float(), nullable=False),
        sa.Column('recall', sa.Float(), nullable=False),
        sa.Column('f1_score', sa.Float(), nullable=False),
        sa.Column('roc_auc', sa.Float(), nullable=False),
        sa.Column('brier_score', sa.Float(), nullable=False),
        sa.Column('mean_lead_time_hours', sa.Float(), nullable=False),
        sa.Column('total_samples', sa.Integer(), nullable=False),
        sa.Column('true_positives', sa.Integer(), nullable=False),
        sa.Column('false_positives', sa.Integer(), nullable=False),
        sa.Column('false_negatives', sa.Integer(), nullable=False),
        sa.Column('true_negatives', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_evaluation_runs_created_at'), 'model_evaluation_runs', ['created_at'], unique=False)
    op.create_index(op.f('ix_model_evaluation_runs_run_name'), 'model_evaluation_runs', ['run_name'], unique=False)

    # 20. AI Audit Logs Table
    op.create_table(
        'ai_audit_logs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('agent_name', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=True),
        sa.Column('event_id', sa.String(length=64), nullable=True),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('data_mode', sa.String(length=32), nullable=False),
        sa.Column('tool_calls_count', sa.Integer(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_audit_logs_agent_name'), 'ai_audit_logs', ['agent_name'], unique=False)
    op.create_index(op.f('ix_ai_audit_logs_event_id'), 'ai_audit_logs', ['event_id'], unique=False)
    op.create_index(op.f('ix_ai_audit_logs_location_id'), 'ai_audit_logs', ['location_id'], unique=False)
    op.create_index(op.f('ix_ai_audit_logs_request_id'), 'ai_audit_logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_ai_audit_logs_timestamp'), 'ai_audit_logs', ['timestamp'], unique=False)

    # 21. Earth Observations Table
    op.create_table(
        'earth_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('location_id', sa.String(length=50), nullable=True),
        sa.Column('collection', sa.String(length=100), nullable=False),
        sa.Column('product_id', sa.String(length=150), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acquisition_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acquisition_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('instrument', sa.String(length=50), nullable=False),
        sa.Column('processing_level', sa.String(length=50), nullable=True),
        sa.Column('bbox_json', sa.JSON(), nullable=True),
        sa.Column('geometry_json', sa.JSON(), nullable=True),
        sa.Column('available_online', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_earth_observations_collection'), 'earth_observations', ['collection'], unique=False)
    op.create_index(op.f('ix_earth_observations_location_id'), 'earth_observations', ['location_id'], unique=False)
    op.create_index(op.f('ix_earth_observations_product_id'), 'earth_observations', ['product_id'], unique=True)
    op.create_index(op.f('ix_earth_observations_timestamp'), 'earth_observations', ['timestamp'], unique=False)
    op.create_index('ix_earth_obs_coll_time', 'earth_observations', ['collection', 'timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('earth_observations')
    op.drop_table('ai_audit_logs')
    op.drop_table('model_evaluation_runs')
    op.drop_table('historical_disaster_incidents')
    op.drop_table('public_alert_acknowledgments')
    op.drop_table('public_users')
    op.drop_table('safety_points')
    op.drop_table('situation_reports')
    op.drop_table('notification_dispatch_logs')
    op.drop_table('notifications')
    op.drop_table('broadcasts')
    op.drop_table('operational_messages')
    op.drop_table('assistance_requests')
    op.drop_table('field_report_images')
    op.drop_table('field_reports')
    op.drop_table('field_teams')
    op.drop_table('risk_assessment_history')
    op.drop_table('risk_assessments')
    op.drop_table('weather_observations')
    op.drop_table('disaster_events')
    op.drop_table('locations')
