from citiespy import random_city
from pytest import mark

from tzfpy import get_tz

# warmup lazy init
_ = get_tz(116.3883, 39.9289)


def _test_tzfpy_random_stream():
    city = random_city()
    _ = get_tz(city.lng, city.lat)


@mark.benchmark
def test_tzfpy(benchmark):
    benchmark(_test_tzfpy_random_stream)
