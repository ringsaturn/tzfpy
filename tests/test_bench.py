import os
import random

from citiespy import all_cities
from pytest import mark

from tzfpy import get_tz

EXP_INDEX = os.getenv("_TZFPY_EXP_INDEX")
DATASET_SIZE = 4096
DATASET_SEED = 20260410

_ALL_CITIES = list(all_cities())
_RNG = random.Random(DATASET_SEED)
_FIXED_CITIES = _RNG.sample(_ALL_CITIES, min(DATASET_SIZE, len(_ALL_CITIES)))
_FIXED_POINTS = [(city.lng, city.lat) for city in _FIXED_CITIES]

# warmup lazy init
_ = get_tz(116.3883, 39.9289)
for lng, lat in _FIXED_POINTS[:64]:
    _ = get_tz(lng, lat)


def _test_tzfpy_fixed_dataset_batch():
    for lng, lat in _FIXED_POINTS:
        _ = get_tz(lng, lat)


@mark.benchmark
def test_tzfpy_fixed_cities(benchmark):
    benchmark.extra_info["exp_index"] = EXP_INDEX or "none"
    benchmark.extra_info["dataset_seed"] = DATASET_SEED
    benchmark.extra_info["dataset_size"] = len(_FIXED_POINTS)
    benchmark(_test_tzfpy_fixed_dataset_batch)
