import time

import citiespy
import polars as pl

import tzfpy

# lazy init
_ = tzfpy.get_tz(0, 0)


cities_as_dict = []
for city in citiespy.all_cities():
    cities_as_dict.append({"name": city.name, "lng": city.lng, "lat": city.lat})

df = pl.from_dicts(cities_as_dict)

start = time.perf_counter()
df = df.with_columns(
    pl.struct(["lng", "lat"])
    .map_elements(
        lambda cols: tzfpy.get_tz(cols["lng"], cols["lat"]), return_dtype=pl.Utf8
    )
    .alias("tz_from_tzfpy")
)
end = time.perf_counter()
print(f"[tzfpy_with_dataframe] Polars Time taken: {end - start} seconds")

"""
[tzfpy_with_dataframe] Polars Time taken: 0.34632241702638566 seconds
"""
