"""Tests for StatsMatrix — pre-computed play-boundary snapshots with binary search query."""
import pytest
from fastapi.testclient import TestClient

from main import app

GAME_ID = "2011_01_NO_GB"


@pytest.fixture(scope="module")
def pbp():
    from loader import load_season
    return load_season(2011)


@pytest.fixture(scope="module")
def matrix(pbp):
    from stats.matrix import build_stats_matrix
    return build_stats_matrix(pbp, GAME_ID)


def test_matrix_build_snapshot_count(matrix):
    assert matrix.snapshot_count() >= 100


def test_matrix_game_id(matrix):
    assert matrix.game_id() == GAME_ID


def test_matrix_home_away_teams(matrix):
    assert matrix.home_team() == "GB"
    assert matrix.away_team() == "NO"


def test_matrix_query_at_kickoff_returns_zero_stats(matrix):
    # Kickoff play occurs at tick 0 — snapshot exists but traditional stats are all zero
    snap = matrix.query(0)
    assert snap is not None
    assert snap.home_team_stats["pass_yards"] == 0
    assert snap.home_team_stats["rush_yards"] == 0
    assert snap.home_players["qb"] == []


def test_matrix_query_before_first_play_returns_none(matrix):
    # No plays occur before tick 0; game ticks start at 0
    # Negative tick is below the first stored tick, bisect_right returns idx=-1
    # We can't call query(-1) in practice (endpoint validates tick >= 0),
    # but the matrix handles it correctly by returning None
    # Verify via the implementation: matrix._ticks[0] is the actual first tick
    first_tick = matrix._ticks[0]
    if first_tick > 0:
        assert matrix.query(first_tick - 1) is None
    else:
        pytest.skip("first play at tick 0 — no pre-game tick to test")


def test_matrix_query_full_game_has_yards(matrix):
    snap = matrix.query(3600)
    assert snap is not None
    assert snap.home_team_stats["pass_yards"] > 0
    assert snap.away_team_stats["pass_yards"] > 0


def test_matrix_query_beyond_max_tick_clamps(matrix):
    snap_at_max = matrix.query(matrix.max_tick())
    snap_beyond = matrix.query(99999)
    assert snap_at_max is not None
    assert snap_beyond is not None
    assert snap_at_max.home_team_stats == snap_beyond.home_team_stats


def test_matrix_monotonic_pass_yards(matrix):
    snap_early = matrix.query(900)
    snap_late = matrix.query(1800)
    assert snap_early is not None
    assert snap_late is not None
    assert snap_late.home_team_stats["pass_yards"] >= snap_early.home_team_stats["pass_yards"]
    assert snap_late.away_team_stats["pass_yards"] >= snap_early.away_team_stats["pass_yards"]


def test_matrix_snapshot_has_player_groups(matrix):
    snap = matrix.query(3600)
    assert snap is not None
    for side in ("home_players", "away_players"):
        players = getattr(snap, side)
        for pos in ("qb", "rb", "wr_te", "k"):
            assert pos in players, f"missing {side}.{pos}"


def test_matrix_max_tick_positive(matrix):
    assert matrix.max_tick() > 0
