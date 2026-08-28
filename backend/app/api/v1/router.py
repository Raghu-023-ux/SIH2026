from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    dashboard,
    locations,
    weather,
    risk,
    events,
    engine,
    simulation,
    ingestion,
    system,
    ai,
)

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard Intelligence"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather & Environment"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Intelligence"])
api_router.include_router(events.router, prefix="/events", tags=["Disaster Events"])
api_router.include_router(engine.router, prefix="/engine", tags=["Disaster Engine"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation & Scenarios"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Data Ingestion"])
api_router.include_router(system.router, prefix="/system", tags=["System & Providers"])
api_router.include_router(ai.router, prefix="/ai", tags=["Agentic AI Intelligence"])
