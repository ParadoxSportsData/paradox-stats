"""PDX-40: StatsMatrix — pre-computed play-boundary snapshots with binary search query."""
import bisect
import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from stats.players import aggregate_player_stats
from stats.team import TeamStats, aggregate_team_stats

logger = logging.getLogger(__name__)


@dataclass
class StatsSnapshot:
    tick: int
    home_team_stats: TeamStats
    away_team_stats: TeamStats
    home_players: dict
    away_players: dict


@dataclass
class StatsMatrix:
    _game_id: str = field(default="", repr=False)
    _home_team: str = field(default="", repr=False)
    _away_team: str = field(default="", repr=False)
    _ticks: list = field(default_factory=list, repr=False)
    _snapshots: list = field(default_factory=list, repr=False)

    def build(self, pbp: pd.DataFrame, game_id: str) -> None:
        game = pbp[pbp["game_id"] == game_id]
        if game.empty:
            raise ValueError(f"stats.matrix.StatsMatrix.build: game_id {game_id!r} not found in pbp")

        self._game_id = game_id
        self._home_team = str(game["home_team"].iloc[0])
        self._away_team = str(game["away_team"].iloc[0])

        play_ticks = sorted(game["game_clock_total_seconds"].dropna().unique().tolist())
        logger.info(
            "stats.matrix.StatsMatrix.build: building %d snapshots for %s",
            len(play_ticks),
            game_id,
        )

        for tick in play_ticks:
            snapshot = _build_snapshot(pbp, game_id, int(tick), self._home_team, self._away_team)
            self._ticks.append(int(tick))
            self._snapshots.append(snapshot)

    def query(self, tick: int) -> Optional[StatsSnapshot]:
        if not self._ticks:
            return None
        idx = bisect.bisect_right(self._ticks, tick) - 1
        if idx < 0:
            return None
        return self._snapshots[idx]

    def game_id(self) -> str:
        return self._game_id

    def snapshot_count(self) -> int:
        return len(self._snapshots)

    def max_tick(self) -> int:
        return self._ticks[-1] if self._ticks else 0

    def home_team(self) -> str:
        return self._home_team

    def away_team(self) -> str:
        return self._away_team


def _build_snapshot(
    pbp: pd.DataFrame,
    game_id: str,
    tick: int,
    home_team: str,
    away_team: str,
) -> StatsSnapshot:
    return StatsSnapshot(
        tick=tick,
        home_team_stats=aggregate_team_stats(pbp, game_id, tick, home_team),
        away_team_stats=aggregate_team_stats(pbp, game_id, tick, away_team),
        home_players=aggregate_player_stats(pbp, game_id, tick, home_team),
        away_players=aggregate_player_stats(pbp, game_id, tick, away_team),
    )


def build_stats_matrix(pbp: pd.DataFrame, game_id: str) -> StatsMatrix:
    """Factory: creates and builds a StatsMatrix for game_id."""
    matrix = StatsMatrix()
    matrix.build(pbp, game_id)
    return matrix
