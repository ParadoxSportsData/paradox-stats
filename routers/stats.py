"""PDX-34: GET /game/{game_id}/stats?tick=N — temporally-gated stats endpoint."""
from fastapi import APIRouter, HTTPException, Query, Request

from stats.players import aggregate_player_stats
from stats.team import aggregate_team_stats

router = APIRouter()


def _team_id(pbp_slice, col: str) -> str:
    return str(pbp_slice[col].iloc[0])


@router.get("/game/{game_id}/stats")
async def get_game_stats(game_id: str, request: Request, tick: int = Query(...)):
    if tick < 0:
        raise HTTPException(status_code=400, detail="tick must be >= 0")

    pbp = request.app.state.pbp
    game_plays = pbp[pbp["game_id"] == game_id]

    if game_plays.empty:
        raise HTTPException(status_code=404, detail=f"game_id {game_id!r} not found")

    home_team = _team_id(game_plays, "home_team")
    away_team = _team_id(game_plays, "away_team")

    home_team_stats = aggregate_team_stats(pbp, game_id, tick, home_team)
    away_team_stats = aggregate_team_stats(pbp, game_id, tick, away_team)

    home_players = aggregate_player_stats(pbp, game_id, tick, home_team)
    away_players = aggregate_player_stats(pbp, game_id, tick, away_team)

    return {
        "game_id": game_id,
        "tick": tick,
        "home_team": home_team,
        "away_team": away_team,
        "team": {
            "home": home_team_stats,
            "away": away_team_stats,
        },
        "players": {
            "home": home_players,
            "away": away_players,
        },
    }
