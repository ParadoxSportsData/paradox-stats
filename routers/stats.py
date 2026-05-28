"""PDX-34/PDX-45: GET /game/{game_id}/stats?tick=N — temporally-gated stats via StatsMatrixRegistry."""
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from stats.team import TEAM_STAT_FIELDS

router = APIRouter()
logger = logging.getLogger(__name__)

_SEASON_PREFIX_LEN = 4
_SEASON_YEAR_MIN = 1999
_SEASON_YEAR_MAX = 2030


def _parse_season_year(game_id: str) -> int:
    try:
        year = int(game_id[:_SEASON_PREFIX_LEN])
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail=f"game_id {game_id!r} not found")
    if not (_SEASON_YEAR_MIN <= year <= _SEASON_YEAR_MAX):
        raise HTTPException(status_code=404, detail=f"game_id {game_id!r} not found")
    return year


@router.get("/game/{game_id}/stats")
async def get_game_stats(game_id: str, request: Request, tick: int = Query(...)):
    if tick < 0:
        raise HTTPException(status_code=400, detail="tick must be >= 0")

    year = _parse_season_year(game_id)
    loader = request.app.state.loader
    registry = request.app.state.registry

    try:
        pbp = loader.get_season(year)
    except Exception as exc:
        logger.warning("stats.get_game_stats: upstream data unavailable for year %d: %s", year, exc)
        raise HTTPException(status_code=503, detail="upstream data service unavailable")

    if game_id not in pbp["game_id"].values:
        raise HTTPException(status_code=404, detail=f"game_id {game_id!r} not found")

    try:
        matrix = await registry.get_or_build(game_id, pbp)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    snap = matrix.query(tick)

    if snap is None:
        home_stats = {k: 0 for k in TEAM_STAT_FIELDS}
        away_stats = dict(home_stats)
        empty_players = {"qb": [], "rb": [], "wr_te": [], "k": []}
        home_players = empty_players
        away_players = empty_players
    else:
        home_stats = snap.home_team_stats
        away_stats = snap.away_team_stats
        home_players = snap.home_players
        away_players = snap.away_players

    return {
        "game_id": game_id,
        "tick": tick,
        "home_team": matrix.home_team(),
        "away_team": matrix.away_team(),
        "team": {
            "home": home_stats,
            "away": away_stats,
        },
        "players": {
            "home": home_players,
            "away": away_players,
        },
    }
