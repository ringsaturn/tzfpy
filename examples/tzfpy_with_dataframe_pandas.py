import time

import citiespy
import numpy as np
import pandas as pd

import tzfpy

# lazy init
_ = tzfpy.get_tz(0, 0)


cities_as_dict = []
for city in citiespy.all_cities():
    cities_as_dict.append({"name": city.name, "lng": city.lng, "lat": city.lat})

df = pd.DataFrame(cities_as_dict)


start = time.perf_counter()
df["tz_from_tzfpy"] = df.apply(lambda x: tzfpy.get_tz(x.lng, x.lat), axis=1)
end = time.perf_counter()
print(f"[tzfpy_with_dataframe] Pandas apply Time taken: {end - start} seconds")

vec_tzfpy_get_tz = np.vectorize(tzfpy.get_tz)
start = time.perf_counter()
df["tz_from_tzfpy_vec"] = vec_tzfpy_get_tz(df.lng, df.lat)
end = time.perf_counter()
print(
    f"[tzfpy_with_dataframe] Pandas apply with NumPy vectorize Time taken: {end - start} seconds"
)

"""
[tzfpy_with_dataframe] Pandas apply Time taken: 0.8276746249757707 seconds
[tzfpy_with_dataframe] Pandas apply with NumPy vectorize Time taken: 0.348435917054303 seconds
"""
