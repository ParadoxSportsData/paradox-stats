"""PDX-44: GET /games?season=N — game browse with background StatsMatrix prefetch."""
import asyncio
import logging

from fastapi import APIRouter, Query, Request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/games")
async def list_games(
    request: Request,
    season: int = Query(default=2011, ge=2000, le=2030),
) -> list[str]:
    loader = request.app.state.loader
    registry = request.app.state.registry

    game_ids = loader.game_ids(season)
    pbp = loader.get_season(season)

    asyncio.create_task(_prefetch_season(game_ids, pbp, registry))

    return game_ids


async def _prefetch_season(game_ids: list[str], pbp, registry) -> None:
    try:
        for game_id in game_ids:
            if not registry.contains(game_id):
                logger.info("routers.games._prefetch_season: warming cache for %s", game_id)
                await registry.get_or_build(game_id, pbp)
    except Exception:
        logger.warning("routers.games._prefetch_season: prefetch failed", exc_info=True)
