"""Tests for LazySeasonLoader — on-demand season loading with LRU eviction."""
import pytest


@pytest.fixture
def loader():
    from loader import LazySeasonLoader
    return LazySeasonLoader(max_seasons=1)


def test_loader_empty_on_construction(loader):
    assert loader.loaded_seasons() == []


def test_loader_gets_season(loader):
    pbp = loader.get_season(2011)
    assert len(pbp) > 0
    assert loader.loaded_seasons() == [2011]


def test_loader_game_ids_returns_sorted_list(loader):
    ids = loader.game_ids(2011)
    assert len(ids) > 0
    assert all(g.startswith("2011_") for g in ids)
    assert ids == sorted(ids)


def test_loader_lru_eviction(loader):
    loader.get_season(2011)
    assert 2011 in loader.loaded_seasons()
    # max_seasons=1 — loading 2012 evicts 2011
    loader.get_season(2012)
    assert 2011 not in loader.loaded_seasons()
    assert 2012 in loader.loaded_seasons()


def test_loader_cache_hit_returns_same_object(loader):
    pbp1 = loader.get_season(2011)
    pbp2 = loader.get_season(2011)
    assert pbp1 is pbp2
