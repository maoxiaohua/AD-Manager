from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.scheduler import init_scheduler, shutdown_scheduler
from app.routers import (
    auth,
    dashboard,
    computers,
    users,
    groups,
    sync,
    import_export,
    settings as settings_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB and scheduler on startup, cleanup on shutdown."""
    init_db()
    init_scheduler()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Windows AD Domain Hostname Registration & Management System",
        lifespan=lifespan,
    )

    # CORS - allow frontend origin for intranet deployment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security warning for wildcard CORS
    if settings.CORS_ORIGINS == ["*"]:
        import logging
        _cors_logger = logging.getLogger("uvicorn")
        _cors_logger.warning(
            "SECURITY: CORS_ORIGINS is set to wildcard ['*']. "
            "For production, restrict to specific origins (e.g., ['http://localhost:3000'])."
        )

    # Register routers
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(computers.router)
    app.include_router(users.router)
    app.include_router(groups.router)
    app.include_router(sync.router)
    app.include_router(import_export.router)
    app.include_router(settings_router.router)

    return app


app = create_app()
