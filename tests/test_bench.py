from citiespy import random_city

from tzfpy import get_tz

# warmup lazy init
_ = random_city()
_ = get_tz(116.3883, 39.9289)


def _test_tzfpy_random_city():
    city = random_city()
    _ = get_tz(city.lng, city.lat)


def test_tzfpy_random_cities(benchmark):
    benchmark(_test_tzfpy_random_city)
