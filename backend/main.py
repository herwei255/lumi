"""
Lumi — FastAPI application entry point.

Run with:
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.webhooks import router as webhook_router
from db.init_db import init_db
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup — creates DB tables if they don't exist yet
    init_db()
    yield


app = FastAPI(
    title="Lumi",
    version="0.3.0",
    description="Personal assistant bot — Phase 3 (integrations)",
    lifespan=lifespan,
)

# Allow the Next.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/webhook")
app.include_router(auth_router, prefix="/auth")


@app.get("/")
async def root():
    return {"status": "running", "name": "lumi", "phase": 2}
