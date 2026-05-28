"""Shared pytest fixtures for paradox-stats test suite."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="session")
def pbp():
    """Load 2011 season play-by-play data once for the entire test session."""
    from loader import load_season
    return load_season(2011)


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient with app lifespan active for the entire test session."""
    with TestClient(app) as c:
        yield c
