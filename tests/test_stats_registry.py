"""Tests for StatsMatrixRegistry — async LRU cache at game level."""
import asyncio
from unittest.mock import patch

import pytest

from loader import load_season

GAME_A = "2011_01_NO_GB"
GAME_B = "2011_09_GB_SD"


@pytest.fixture(scope="module")
def pbp():
    return load_season(2011)


@pytest.fixture
def registry():
    from stats.registry import StatsMatrixRegistry
    r = StatsMatrixRegistry(max_games=2)
    yield r
    r.clear()


def test_registry_empty_on_construction(registry):
    assert registry.size() == 0


async def test_registry_grows_after_build(registry, pbp):
    await registry.get_or_build(GAME_A, pbp)
    assert registry.size() == 1
    assert registry.contains(GAME_A)


async def test_registry_cache_hit_returns_same_object(registry, pbp):
    m1 = await registry.get_or_build(GAME_A, pbp)
    m2 = await registry.get_or_build(GAME_A, pbp)
    assert m1 is m2


async def test_registry_lru_eviction(registry, pbp):
    await registry.get_or_build(GAME_A, pbp)
    await registry.get_or_build(GAME_B, pbp)
    assert registry.size() == 2
    # Adding a third game (max_games=2) should evict GAME_A (LRU)
    await registry.get_or_build("2011_14_OAK_GB", pbp)
    assert registry.size() == 2
    assert not registry.contains(GAME_A)
    assert registry.contains(GAME_B)
    assert registry.contains("2011_14_OAK_GB")


async def test_registry_clear_resets_size(registry, pbp):
    await registry.get_or_build(GAME_A, pbp)
    assert registry.size() == 1
    registry.clear()
    assert registry.size() == 0
    assert not registry.contains(GAME_A)


async def test_registry_concurrent_build_calls_once(pbp):
    """Two concurrent get_or_build calls for same cold game trigger exactly one build."""
    from stats.registry import StatsMatrixRegistry
    from stats.matrix import build_stats_matrix

    registry = StatsMatrixRegistry(max_games=10)
    build_calls = []

    original_build = build_stats_matrix

    def counting_build(pbp, game_id):
        build_calls.append(game_id)
        return original_build(pbp, game_id)

    with patch("stats.registry.build_stats_matrix", side_effect=counting_build):
        await asyncio.gather(
            registry.get_or_build(GAME_A, pbp),
            registry.get_or_build(GAME_A, pbp),
        )

    assert len(build_calls) == 1, f"Expected 1 build call, got {len(build_calls)}"
