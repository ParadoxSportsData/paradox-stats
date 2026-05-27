"""PDX-32: Temporally-gated team statistics aggregator."""
from typing import TypedDict

import pandas as pd


class TeamStats(TypedDict):
    pass_yards: int
    completions: int
    attempts: int
    pass_tds: int
    interceptions: int
    rush_yards: int
    carries: int
    rush_tds: int
    fumbles_lost: int
    turnovers: int
    sacks_allowed: int
    sacks: int
    first_downs: int
    third_down_attempts: int
    third_down_conversions: int
    epa: float


TEAM_STAT_FIELDS = list(TeamStats.__annotations__.keys())


def _isum(series: pd.Series) -> int:
    return int(series.fillna(0).sum())


def _fsum(series: pd.Series) -> float:
    return float(series.dropna().sum())


def aggregate_team_stats(
    pbp: pd.DataFrame, game_id: str, tick: int, team: str
) -> TeamStats:
    """Return cumulative TeamStats for all plays in game_id where elapsed <= tick."""
    gated = pbp[(pbp["game_id"] == game_id) & (pbp["game_clock_total_seconds"] <= tick)]
    off = gated[gated["posteam"] == team]
    def_plays = gated[gated["defteam"] == team]

    interceptions = _isum(off["interception"])
    fumbles_lost = _isum(off["fumble_lost"])

    return TeamStats(
        pass_yards=_isum(off["passing_yards"]),
        completions=_isum(off["complete_pass"]),
        attempts=_isum(off["pass_attempt"]),
        pass_tds=_isum(off["pass_touchdown"]),
        interceptions=interceptions,
        rush_yards=_isum(off["rushing_yards"]),
        carries=_isum(off["rush_attempt"]),
        rush_tds=_isum(off["rush_touchdown"]),
        fumbles_lost=fumbles_lost,
        turnovers=interceptions + fumbles_lost,
        sacks_allowed=_isum(off["sack"]),
        sacks=_isum(def_plays["sack"]),
        first_downs=_isum(off["first_down_rush"]) + _isum(off["first_down_pass"]),
        third_down_attempts=_isum(off["third_down_converted"]) + _isum(off["third_down_failed"]),
        third_down_conversions=_isum(off["third_down_converted"]),
        epa=_fsum(off["epa"]),
    )
