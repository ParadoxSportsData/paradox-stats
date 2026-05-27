"""PDX-41: StatsMatrixRegistry — async LRU cache of StatsMatrix instances at game level."""
import asyncio
import logging
from collections import OrderedDict

import pandas as pd

from stats.matrix import StatsMatrix, build_stats_matrix

logger = logging.getLogger(__name__)


class StatsMatrixRegistry:
    def __init__(self, max_games: int = 100) -> None:
        self._cache: OrderedDict[str, StatsMatrix] = OrderedDict()
        self._max_games = max_games
        self._locks: dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()

    async def get_or_build(self, game_id: str, pbp: pd.DataFrame) -> StatsMatrix:
        if game_id in self._cache:
            self._cache.move_to_end(game_id)
            return self._cache[game_id]

        async with self._meta_lock:
            if game_id not in self._locks:
                self._locks[game_id] = asyncio.Lock()
        game_lock = self._locks[game_id]

        async with game_lock:
            if game_id in self._cache:
                self._cache.move_to_end(game_id)
                return self._cache[game_id]

            logger.info("stats.registry.StatsMatrixRegistry.get_or_build: building %s", game_id)
            loop = asyncio.get_event_loop()
            matrix = await loop.run_in_executor(None, build_stats_matrix, pbp, game_id)

            self._cache[game_id] = matrix
            if len(self._cache) > self._max_games:
                evicted, _ = self._cache.popitem(last=False)
                logger.info(
                    "stats.registry.StatsMatrixRegistry.get_or_build: evicted %s (LRU)",
                    evicted,
                )
            return matrix

    def size(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        self._cache.clear()

    def contains(self, game_id: str) -> bool:
        return game_id in self._cache
