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

lngs = df.lng.values
lats = df.lat.values

vec_tzfpy_get_tz = np.vectorize(tzfpy.get_tz)

start = time.perf_counter()
_ = vec_tzfpy_get_tz(lngs, lats)
end = time.perf_counter()
print(f"[tzfpy_with_dataframe] Numpy Time taken: {end - start} seconds")

"""
[tzfpy_with_dataframe] Numpy Time taken: 0.33512612502090633 seconds
"""
