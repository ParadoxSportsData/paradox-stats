"""Tests for GET /game/{game_id}/stats — PDX-34."""
import pytest
from fastapi.testclient import TestClient

from main import app

GAME_ID = "2011_01_NO_GB"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_stats_200_correct_shape(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    assert r.status_code == 200
    d = r.json()
    assert d["game_id"] == GAME_ID
    assert d["tick"] == 1800
    assert "home_team" in d
    assert "away_team" in d
    assert "team" in d
    assert "players" in d


def test_stats_home_team_gb(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    assert r.status_code == 200
    d = r.json()
    assert d["home_team"] == "GB"
    assert d["away_team"] == "NO"


def test_stats_team_has_home_and_away(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    d = r.json()
    team = d["team"]
    assert "home" in team
    assert "away" in team
    assert "pass_yards" in team["home"]
    assert "rush_yards" in team["away"]


def test_stats_players_has_home_and_away(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 1800})
    d = r.json()
    players = d["players"]
    assert "home" in players
    assert "away" in players
    for side in ("home", "away"):
        for pos in ("qb", "rb", "wr_te", "k"):
            assert pos in players[side], f"missing {side}.{pos}"


def test_stats_404_unknown_game(client):
    r = client.get("/game/9999_99_XX_YY/stats", params={"tick": 0})
    assert r.status_code == 404


def test_stats_400_negative_tick(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": -1})
    assert r.status_code == 400


def test_stats_tick_zero_yields_zero_team_stats(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 0})
    assert r.status_code == 200
    d = r.json()
    assert d["team"]["home"]["pass_yards"] == 0
    assert d["team"]["away"]["rush_yards"] == 0


def test_stats_full_game_has_positive_yards(client):
    r = client.get(f"/game/{GAME_ID}/stats", params={"tick": 3600})
    assert r.status_code == 200
    d = r.json()
    assert d["team"]["home"]["pass_yards"] > 0
    assert d["team"]["away"]["rush_yards"] >= 0
