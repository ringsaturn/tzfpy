# wait until python binding for cities.json

# import json
# import random

# from tzfpy import get_tz


# cities = []
# with open("tests/cities.json") as f:
#     raw_cities = json.loads(f.read())
# for rawcity in raw_cities:
#     cities.append([float(rawcity["lng"]), float(rawcity["lat"])])


# def random_city():
#     index = random.randint(0, len(cities)-1)
#     return cities[index]

# def _test_tzfpy_random_city():
#     lng, lat = random_city()
#     _ = get_tz(lng, lat)


# def test_tzfpy_random_cities(benchmark):
#     benchmark(_test_tzfpy_random_city)

