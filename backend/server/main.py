from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.schemas.responses import HealthResponse
from server.services.analysis import AnalysisService
from server.storage import ensure_directories


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="G-Catch Receipt Forensics API",
        description=(
            "Backend API for analyzing receipt authenticity using Error Level "
            "Analysis (ELA), typography & kerning forensics, and micro-alignment "
            "detection."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from server.routers.ela import router as ela_router
    from server.routers.typography import router as typography_router
    from server.routers.alignment import router as alignment_router
    from server.routers.pipeline import router as pipeline_router

    app.include_router(ela_router)
    app.include_router(typography_router)
    app.include_router(alignment_router)
    app.include_router(pipeline_router)

    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Health check",
    )
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get(
        "/api/v1/analyzers",
        tags=["health"],
        summary="List available analyzers",
    )
    async def list_analyzers():
        return AnalysisService.available_analyzers()

    return app


app = create_app()
