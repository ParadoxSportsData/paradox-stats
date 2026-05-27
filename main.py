"""paradox-stats: Temporally-gated NFL statistics service."""
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from loader import LazySeasonLoader
from routers.games import router as games_router
from routers.stats import router as stats_router
from stats.registry import StatsMatrixRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_EAGER_SEASON = 2011


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.loader = LazySeasonLoader()
    app.state.registry = StatsMatrixRegistry()
    pbp = app.state.loader.get_season(_EAGER_SEASON)
    logger.info(
        "main: startup complete — %d plays, %d games (season %d eager-loaded)",
        len(pbp),
        pbp["game_id"].nunique(),
        _EAGER_SEASON,
    )
    yield


app = FastAPI(title="paradox-stats", version="0.1.0", lifespan=lifespan)
app.include_router(games_router)
app.include_router(stats_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health(request: Request):
    return {
        "status": "ok",
        "service": "paradox-stats",
        "loaded_seasons": request.app.state.loader.loaded_seasons(),
        "cached_games": request.app.state.registry.size(),
    }


@app.get("/debug/games", response_model=List[str])
async def debug_games(request: Request):
    return request.app.state.loader.game_ids(_EAGER_SEASON)
