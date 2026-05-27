"""PDX-31/PDX-42: Load nflfastR play-by-play data — load_season() and LazySeasonLoader."""
import logging
from collections import OrderedDict

import nfl_data_py as nfl
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "game_id",
    "game_clock_total_seconds",
    "posteam",
    "defteam",
    "home_team",
    "away_team",
    "pass_attempt",
    "complete_pass",
    "pass_touchdown",
    "interception",
    "rushing_yards",
    "rush_attempt",
    "rush_touchdown",
    "fumble_lost",
    "sack",
    "epa",
    "passing_yards",
    "first_down_rush",
    "first_down_pass",
    "third_down_converted",
    "third_down_failed",
    "passer_player_id",
    "passer_player_name",
    "rusher_player_id",
    "rusher_player_name",
    "receiver_player_id",
    "receiver_player_name",
    "air_yards",
    "yards_after_catch",
    "kicker_player_id",
    "kicker_player_name",
    "field_goal_attempt",
    "field_goal_result",
    "kick_distance",
    "extra_point_attempt",
    "extra_point_result",
    "receiving_yards",
]

_SOURCE_COLUMNS = [c for c in REQUIRED_COLUMNS if c != "game_clock_total_seconds"] + [
    "game_seconds_remaining",
    "qtr",
]


def _derive_elapsed(df: pd.DataFrame) -> pd.Series:
    """Compute elapsed seconds from kickoff.

    Regulation (qtr 1-4): 3600 - game_seconds_remaining
    OT (qtr >= 5): 3600 + (qtr - 4) * 900 - game_seconds_remaining
    Rows with null qtr or game_seconds_remaining get 0.
    """
    gsr = df["game_seconds_remaining"].fillna(0)
    qtr = df["qtr"].fillna(1)
    reg_elapsed = 3600 - gsr
    ot_elapsed = 3600 + (qtr - 4) * 900 - gsr
    is_ot = qtr >= 5
    return reg_elapsed.where(~is_ot, ot_elapsed).clip(lower=0).round().astype("int32")


def load_season(year: int) -> pd.DataFrame:
    """Return play-by-play DataFrame for the given season with REQUIRED_COLUMNS."""
    raw = nfl.import_pbp_data(
        years=[year],
        columns=_SOURCE_COLUMNS,
        include_participation=False,
    )
    raw["game_clock_total_seconds"] = _derive_elapsed(raw)
    available = [c for c in REQUIRED_COLUMNS if c in raw.columns]
    df = raw[available].copy()
    logger.info(
        "loader.load_season: loaded %d plays for %d season (%d games)",
        len(df),
        year,
        df["game_id"].nunique(),
    )
    return df


class LazySeasonLoader:
    """Loads season pbp data on demand and caches with LRU eviction."""

    def __init__(self, max_seasons: int = 3) -> None:
        self._cache: OrderedDict[int, pd.DataFrame] = OrderedDict()
        self._max_seasons = max_seasons

    def get_season(self, year: int) -> pd.DataFrame:
        if year in self._cache:
            self._cache.move_to_end(year)
            return self._cache[year]

        pbp = load_season(year)
        self._cache[year] = pbp
        if len(self._cache) > self._max_seasons:
            evicted, _ = self._cache.popitem(last=False)
            logger.info("loader.LazySeasonLoader.get_season: evicted season %d", evicted)
        return pbp

    def game_ids(self, year: int) -> list[str]:
        pbp = self.get_season(year)
        return sorted(pbp["game_id"].unique().tolist())

    def loaded_seasons(self) -> list[int]:
        return list(self._cache.keys())
