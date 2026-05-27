"""PDX-47: Integration tests — StatsMatrix cache behavior, temporal isolation, browse endpoint."""
import pytest
from fastapi.testclient import TestClient

from main import app

GAME_ID = "2011_01_NO_GB"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fresh_registry(client):
    """Clear registry before registry-sensitive tests."""
    app.state.registry.clear()
    yield app.state.registry


def test_stats_cache_cold_then_warm(client):
    r1 = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    r2 = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


def test_stats_registry_grows_after_first_request(client, fresh_registry):
    assert fresh_registry.size() == 0
    client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    assert fresh_registry.size() == 1


def test_stats_temporal_monotonic_pass_yards(client):
    r_early = client.get(f"/game/{GAME_ID}/stats", params={"tick": 900})
    r_late = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    assert r_early.status_code == 200
    assert r_late.status_code == 200
    yards_early = r_early.json()["team"]["home"]["pass_yards"]
    yards_late = r_late.json()["team"]["home"]["pass_yards"]
    assert yards_late >= yards_early


def test_stats_player_omitted_at_tick_zero(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 0})
    assert r.status_code == 200
    players = r.json()["players"]
    for side in ("home", "away"):
        assert players[side]["qb"] == [], f"{side} qb should be empty at tick=0"
        assert players[side]["rb"] == [], f"{side} rb should be empty at tick=0"
        assert players[side]["wr_te"] == [], f"{side} wr_te should be empty at tick=0"
        assert players[side]["k"] == [], f"{side} k should be empty at tick=0"


def test_browse_endpoint_returns_game_list(client):
    r = client.get("/games", params={"season": 2011})
    assert r.status_code == 200
    ids = r.json()
    assert isinstance(ids, list)
    assert len(ids) > 0
    assert GAME_ID in ids


def test_browse_season_out_of_range(client):
    r = client.get("/games", params={"season": 1990})
    assert r.status_code == 422


def test_stats_graceful_degradation_unknown_game(client):
    r = client.get("/game/9999_99_XX_YY/stats", params={"tick": 0})
    assert r.status_code == 404
