"""PDX-44: tests for GET /games — browse endpoint with background prefetch."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_games_returns_list(client):
    r = client.get("/games")
    assert r.status_code == 200
    ids = r.json()
    assert isinstance(ids, list)
    assert len(ids) > 0


def test_games_default_season_is_2011(client):
    r = client.get("/games")
    ids = r.json()
    assert all(g.startswith("2011_") for g in ids)


def test_games_season_param(client):
    r = client.get("/games", params={"season": 2011})
    assert r.status_code == 200
    ids = r.json()
    assert len(ids) > 200


def test_games_returns_sorted_list(client):
    r = client.get("/games", params={"season": 2011})
    ids = r.json()
    assert ids == sorted(ids)


def test_games_season_out_of_range_low(client):
    r = client.get("/games", params={"season": 1990})
    assert r.status_code == 422


def test_games_season_out_of_range_high(client):
    r = client.get("/games", params={"season": 2031})
    assert r.status_code == 422
