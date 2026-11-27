from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import api_router
from app.core.config import settings


def get_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "PRAVAAH: Predictive Risk Assessment and Vulnerability Analysis "
            "for Adaptive Assistance & Humanitarian Response. "
            "Phase 0 — Project Foundation and Development Environment."
        ),
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Configure CORS using environment-driven origin whitelist + Vercel deployment domains
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
        allow_origin_regex=r"^https?:\/\/.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Attach versioned API routes under /api (standard) and root fallback
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(api_router)

    @app.get(
        "/",
        tags=["root"],
        summary="API Root Identification",
        description="Provides API identification and documentation links.",
    )
    @app.get(
        "/api",
        tags=["root"],
        summary="API Root Identification",
        description="Provides API identification and documentation links.",
    )
    @app.get(
        "/api/",
        tags=["root"],
        summary="API Root Identification",
        description="Provides API identification and documentation links.",
    )
    def root():
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "message": "PRAVAAH API is operational. See documentation at /api/docs.",
            "docs_url": f"{settings.API_V1_STR}/docs",
            "health_url": f"{settings.API_V1_STR}/health",
        }

    return app


app = get_application()
