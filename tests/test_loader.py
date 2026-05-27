"""Tests for loader.py — PDX-31."""
import pytest
import pandas as pd

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


def test_load_season_returns_dataframe():
    from loader import load_season
    df = load_season(2011)
    assert isinstance(df, pd.DataFrame)


def test_load_season_has_required_columns():
    from loader import load_season
    df = load_season(2011)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    assert missing == [], f"Missing columns: {missing}"


def test_load_season_contains_2011_no_gb():
    from loader import load_season
    df = load_season(2011)
    assert "2011_01_NO_GB" in df["game_id"].values, (
        "Expected game 2011_01_NO_GB not found in loaded data"
    )


def test_load_season_has_plays():
    from loader import load_season
    df = load_season(2011)
    assert len(df) > 10_000, f"Expected >10,000 plays, got {len(df)}"


def test_load_season_game_clock_total_seconds_is_numeric():
    from loader import load_season
    df = load_season(2011)
    assert pd.api.types.is_numeric_dtype(df["game_clock_total_seconds"]), (
        "game_clock_total_seconds must be numeric"
    )
