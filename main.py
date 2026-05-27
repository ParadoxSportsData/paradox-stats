"""paradox-stats: Temporally-gated NFL statistics service."""
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from loader import load_season
from routers.stats import router as stats_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pbp = load_season(2011)
    logger.info(
        "Startup complete: %d plays, %d games",
        len(app.state.pbp),
        app.state.pbp["game_id"].nunique(),
    )
    yield


app = FastAPI(title="paradox-stats", version="0.1.0", lifespan=lifespan)
app.include_router(stats_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "paradox-stats"}


@app.get("/debug/games", response_model=List[str])
async def debug_games(request: Request):
    return sorted(request.app.state.pbp["game_id"].unique().tolist())
