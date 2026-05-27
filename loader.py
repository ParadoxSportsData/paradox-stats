"""PDX-31: Load nflfastR play-by-play data for a full season."""
import logging

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
        "Loaded %d plays for %d season (%d games)",
        len(df),
        year,
        df["game_id"].nunique(),
    )
    return df
