import os
import random

from citiespy import all_cities
from pytest import mark

from tzfpy import get_tz

# To make test data consistent across runs, use a fixed seed and a fixed dataset size.
EXP_INDEX = os.getenv("_TZFPY_EXP_INDEX")
DATASET_SEED = 20260410
DATASET_SIZE = 16384

_ALL_CITIES = list(all_cities())
_RNG = random.Random(DATASET_SEED)
_RANDOM_POINTS = [
    (city.lng, city.lat) for city in _RNG.choices(_ALL_CITIES, k=DATASET_SIZE)
]


class QueryStream:
    def __init__(self, points):
        self.points = points
        self.idx = 0

    def reset(self):
        self.idx = 0

    def __call__(self):
        lng, lat = self.points[self.idx]
        self.idx += 1
        if self.idx == len(self.points):
            self.idx = 0
        _ = get_tz(lng, lat)


_QUERY_STREAM = QueryStream(_RANDOM_POINTS)

# warmup lazy init
_ = get_tz(116.3883, 39.9289)


def _test_tzfpy_random_stream():
    _QUERY_STREAM()


@mark.benchmark
def test_tzfpy(benchmark):
    _QUERY_STREAM.reset()
    benchmark.extra_info["exp_index"] = EXP_INDEX or "none"
    benchmark.extra_info["dataset_seed"] = DATASET_SEED
    benchmark.extra_info["dataset_size"] = len(_RANDOM_POINTS)
    benchmark(_test_tzfpy_random_stream)
