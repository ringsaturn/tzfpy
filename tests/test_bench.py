from citiespy import random_city
from tzfpy import get_tz

_ = random_city()


def _test_tzfpy_random_city():
    city = random_city()
    _ = get_tz(city.lng, city.lat)


def test_tzfpy_random_cities(benchmark):
    benchmark(_test_tzfpy_random_city)
