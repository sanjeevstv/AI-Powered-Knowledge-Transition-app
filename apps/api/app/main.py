from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.config import get_settings
from app.db.session import engine, init_db
from app.routers import auth, chat, dashboard, documents, health, search, sessions
from app.services.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with Session(engine) as s:
        seed_if_empty(s)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="KT Platform API", version="0.1.0", lifespan=lifespan)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = "/api/v1"
    app.include_router(health.router, prefix=api)
    app.include_router(auth.router, prefix=api)
    app.include_router(sessions.router, prefix=api)
    app.include_router(documents.router, prefix=api)
    app.include_router(search.router, prefix=api)
    app.include_router(chat.router, prefix=api)
    app.include_router(dashboard.router, prefix=api)

    return app


app = create_app()
