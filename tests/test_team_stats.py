"""Tests for stats/team.py — PDX-32."""
import pytest
import pandas as pd
from loader import load_season


@pytest.fixture(scope="module")
def pbp():
    return load_season(2011)


def test_zero_stats_at_tick_zero(pbp):
    from stats.team import aggregate_team_stats
    s = aggregate_team_stats(pbp, "2011_01_NO_GB", 0, "GB")
    assert s["pass_yards"] == 0
    assert s["rush_yards"] == 0
    assert s["attempts"] == 0


def test_positive_yards_at_end_of_game(pbp):
    from stats.team import aggregate_team_stats
    s = aggregate_team_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    assert s["pass_yards"] > 0
    assert s["rush_yards"] > 0


def test_temporal_monotonicity(pbp):
    from stats.team import aggregate_team_stats
    s900 = aggregate_team_stats(pbp, "2011_01_NO_GB", 900, "GB")
    s1800 = aggregate_team_stats(pbp, "2011_01_NO_GB", 1800, "GB")
    assert s900["pass_yards"] <= s1800["pass_yards"]
    assert s900["rush_yards"] <= s1800["rush_yards"]


def test_teamstats_has_all_fields(pbp):
    from stats.team import aggregate_team_stats, TEAM_STAT_FIELDS
    s = aggregate_team_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    missing = [f for f in TEAM_STAT_FIELDS if f not in s]
    assert missing == [], f"Missing fields: {missing}"


def test_numeric_types_are_python_native(pbp):
    from stats.team import aggregate_team_stats
    s = aggregate_team_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    for k, v in s.items():
        assert isinstance(v, (int, float)), f"{k}: expected int/float, got {type(v)}"


def test_turnovers_equals_ints_plus_fumbles(pbp):
    from stats.team import aggregate_team_stats
    s = aggregate_team_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    assert s["turnovers"] == s["interceptions"] + s["fumbles_lost"]


def test_sacks_allowed_is_offensive_sacks(pbp):
    from stats.team import aggregate_team_stats
    gb = aggregate_team_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    no = aggregate_team_stats(pbp, "2011_01_NO_GB", 3600, "NO")
    # GB's sacks_allowed = sacks where GB is posteam = NO's sacks (def)
    assert gb["sacks_allowed"] == no["sacks"]
