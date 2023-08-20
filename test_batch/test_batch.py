import numpy as np
import pandas as pd
import polars as pl
from citiespy import all_cities
from tzfpy import get_tz

ROUNDS = 5
ITER = 3

# warmup lazy init
_ = get_tz(116.3883, 39.9289)

# Prepare NumPy vectorized functions
vec_get_tz = np.vectorize(get_tz)

cities_as_dict = []
for city in all_cities():
    cities_as_dict.append(
        {
            "name": city.name,
            "lng": city.lng,
            "lat": city.lat,
        }
    )

pd_df = pd.DataFrame(cities_as_dict)
pl_df = pl.from_dicts(cities_as_dict)

lng_array = np.array(pd_df["lng"])
lat_array = np.array(pd_df["lat"])


def _test_pandas_batch():
    _ = pd_df.apply(lambda x: get_tz(x.lng, x.lat), axis=1)


def test_pandas_batch(benchmark):
    benchmark.pedantic(_test_pandas_batch, rounds=ROUNDS, iterations=ITER)


def _test_pandas_batch_numpy_vec():
    _ = vec_get_tz(pd_df.lng, pd_df.lat)


def test_pandas_batch_numpy_vec(benchmark):
    benchmark.pedantic(_test_pandas_batch_numpy_vec, rounds=ROUNDS, iterations=ITER)


def _test_pl_df_batch():
    _ = pl_df.with_columns(
        pl.struct(["lng", "lat"])
        .apply(lambda cols: get_tz(cols["lng"], cols["lat"]))
        .alias("tz_from_tzfpy")
    )


def test_pl_df_batch(benchmark):
    benchmark.pedantic(_test_pl_df_batch, rounds=ROUNDS, iterations=ITER)


def _test_pl_df_batch_numpy_vec():
    _ = vec_get_tz(pl_df["lng"], pl_df["lat"])


def test_pl_df_batch_numpy_vec(benchmark):
    benchmark.pedantic(_test_pl_df_batch_numpy_vec, rounds=ROUNDS, iterations=ITER)


def _test_np_vec():
    _ = vec_get_tz(lng_array, lat_array)


def test_np_vec(benchmark):
    benchmark.pedantic(_test_np_vec, rounds=ROUNDS, iterations=ITER)
