"""Tests for stats/players.py — PDX-33."""
import pytest
from loader import load_season


@pytest.fixture(scope="module")
def pbp():
    return load_season(2011)


def test_qb_list_nonempty_at_game_end(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    assert len(ps["qb"]) > 0


def test_qb_has_passer_rating_when_attempts_positive(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    for qb in ps["qb"]:
        if qb["attempts"] > 0:
            assert qb["passer_rating"] is not None
            assert isinstance(qb["passer_rating"], float)
            assert 0.0 <= qb["passer_rating"] <= 158.3


def test_all_positions_empty_at_tick_zero(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 0, "GB")
    assert ps["qb"] == []
    assert ps["rb"] == []
    assert ps["wr_te"] == []
    assert ps["k"] == []


def test_rb_list_nonempty_at_game_end(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    assert len(ps["rb"]) > 0
    for rb in ps["rb"]:
        assert rb["carries"] > 0 or rb["receptions"] > 0


def test_wr_te_list_nonempty_at_game_end(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    assert len(ps["wr_te"]) > 0
    for wr in ps["wr_te"]:
        assert wr["targets"] > 0


def test_all_numeric_fields_are_python_native(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    for group in ["qb", "rb", "wr_te", "k"]:
        for player in ps[group]:
            for k, v in player.items():
                if v is not None:
                    assert isinstance(v, (int, float, str)), (
                        f"{group}.{k}: expected int/float/str, got {type(v)}"
                    )


def test_rb_not_in_wr_te(pbp):
    from stats.players import aggregate_player_stats
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    rb_ids = {rb["player_id"] for rb in ps["rb"]}
    wr_ids = {w["player_id"] for w in ps["wr_te"]}
    overlap = rb_ids & wr_ids
    assert overlap == set(), f"Players appear in both RB and WR/TE: {overlap}"


def test_passer_rating_none_when_zero_attempts(pbp):
    from stats.players import aggregate_player_stats
    # Tick=0: no plays, so any QB built would have 0 attempts (but list is empty)
    # Instead verify via tick=3600 that no QB with 0 attempts slips through
    ps = aggregate_player_stats(pbp, "2011_01_NO_GB", 3600, "GB")
    for qb in ps["qb"]:
        if qb["attempts"] == 0:
            assert qb["passer_rating"] is None
