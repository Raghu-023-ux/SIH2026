from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.core.logging import logger
from backend.app.services.location_service import LocationService
from backend.app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed initial NER monitoring stations
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    try:
        await init_db()
        async with AsyncSessionLocal() as session:
            await LocationService.seed_initial_locations(session)
        logger.info("Application startup completed successfully.")
    except Exception as err:
        logger.error(f"Database initialization deferred on startup ({err}). Server continuing startup...")
    yield
    # Shutdown
    logger.info("Shutting down application...")



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "MVP Disaster Intelligence Engine for SIH26001: AI-Based Early Warning and "
        "Landslide Risk Monitoring System in the North Eastern Region (NER)."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."}
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint returning system status, database reachability, and service details.
    """
    from backend.app.core.database import check_database_health
    from backend.app.core.redis import redis_service
    db_health = await check_database_health()
    cache_health = await redis_service.check_health()
    return {
        "status": "healthy" if (db_health["reachable"] and cache_health["reachable"]) else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "application_mode": settings.DATA_MODE,
        "database": {
            "reachable": db_health["reachable"],
            "engine": db_health["engine"],
            "latency_ms": db_health["latency_ms"],
        },
        "cache": {
            "reachable": cache_health["reachable"],
            "backend": cache_health.get("backend", "in_memory"),
            "mode": cache_health.get("mode", "LOCAL_MEMORY"),
            "latency_ms": cache_health.get("latency_ms", 0.0),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Landslide risk calculation formulas represent a prototype analytical model."
    }


from backend.app.api.v1.endpoints.health_ready import router as health_ready_router

# Include Health Probes & Prometheus Metrics
app.include_router(health_ready_router, prefix="/health", tags=["Health & Readiness"])
app.include_router(health_ready_router, prefix="", tags=["Metrics"])

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)
