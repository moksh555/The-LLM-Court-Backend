# Backend/src/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI #type:ignore
from fastapi.middleware.cors import CORSMiddleware #type:ignore

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Put startup/shutdown logic here (DB connections, warm caches, etc).
    Keep it boring and predictable.
    """
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # CORS (adjust as needed)
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "https://www.llm-court.com",
                "https://llm-court.com"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Routes
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
