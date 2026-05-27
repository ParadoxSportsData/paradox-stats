"""PDX-43: tests for health endpoint — LazySeasonLoader + StatsMatrixRegistry wire-up."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_200(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_has_loaded_seasons(client):
    r = client.get("/health")
    d = r.json()
    assert "loaded_seasons" in d
    assert isinstance(d["loaded_seasons"], list)


def test_health_has_cached_games(client):
    r = client.get("/health")
    d = r.json()
    assert "cached_games" in d
    assert isinstance(d["cached_games"], int)


def test_health_eager_season_loaded(client):
    r = client.get("/health")
    d = r.json()
    assert 2011 in d["loaded_seasons"]


def test_debug_games_returns_sorted_list(client):
    r = client.get("/debug/games")
    assert r.status_code == 200
    ids = r.json()
    assert len(ids) > 0
    assert all(g.startswith("2011_") for g in ids)
    assert ids == sorted(ids)
