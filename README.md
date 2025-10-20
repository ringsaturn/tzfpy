# tzfpy

- [![PyPI](https://img.shields.io/pypi/v/tzfpy)](https://pypi.org/project/tzfpy/)
- [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tzfpy)](https://pypi.org/project/tzfpy/)
- ![PyPI - Downloads](https://img.shields.io/pypi/dd/tzfpy)
- [![Anaconda-Server Badge](https://anaconda.org/conda-forge/tzfpy/badges/version.svg)](https://anaconda.org/conda-forge/tzfpy)
- ![Conda Downloads](https://img.shields.io/conda/d/conda-forge/tzfpy)
- ![Conda Platform](https://img.shields.io/conda/p/conda-forge/tzfpy)

![](https://github.com/ringsaturn/tzf/blob/gh-pages/docs/tzf-social-media.png?raw=true)

> [!NOTE]
>
> 0. It's probably the fastest Python package to convert longitude/latitude to
>    timezone name.
> 1. This package use a simplified polygon data and not so accurate around
>    borders.
> 2. Rust use lazy init, so first calling will be a little slow.
> 3. Use about 40MB memory.
> 4. It's tested under Python 3.10+.
> 5. Try it online:
>    - <https://ringsaturn.github.io/tzf-web/>, powered by tzf-rs and
>      WebAssembly

## Usage

Please note that new timezone names may be added to tzfpy, which could be
incompatible with old version package like pytz or tzdata. As an option, tzfpy
supports install compatible version of those packages with extra params.

```bash
# Install just tzfpy
pip install tzfpy

# Install with pytz
pip install "tzfpy[pytz]"

# Install with tzdata. https://github.com/python/tzdata
pip install "tzfpy[tzdata]"

# Install via conda, see more in https://github.com/conda-forge/tzfpy-feedstock
conda install -c conda-forge tzfpy
```

```python
>>> from tzfpy import get_tz, get_tzs
>>> get_tz(116.3883, 39.9289)  # in (longitude, latitude) order.
'Asia/Shanghai'
>>> get_tzs(87.4160, 44.0400)  # in (longitude, latitude) order.
['Asia/Shanghai', 'Asia/Urumqi']
```

For data visualization, you can get timezone polygon GeoJSON data from tzfpy:

```python
from tzfpy import get_tz, get_tz_index_geojson, get_tz_polygon_geojson

lng = -74.0060
lat = 40.7128
tz = get_tz(lng, lat)
print(f"Timezone for ({lng}, {lat}): {tz}")

with open("tz_nyc_polygon.geojson", "w") as f:
    geojson_data = get_tz_polygon_geojson(tz)
    f.write(geojson_data)

with open("tz_nyc_index.geojson", "w") as f:
    geojson_data = get_tz_index_geojson(tz)
    f.write(geojson_data)
```

### Best practices

1. Always install tzfpy with `tzdata` extra: `pip install tzfpy[tzdata]`
2. Use Python's zoneinfo package(`import zoneinfo`, aka
   [`tzdata` in PyPI](https://pypi.org/project/tzdata/)) to handle timezone
   names, even if you are using arrow:

   [`examples/tzfpy_with_datetime.py`](examples/tzfpy_with_datetime.py):

   ```python
   from datetime import datetime, timezone
   from zoneinfo import ZoneInfo

   from tzfpy import get_tz

   tz = get_tz(139.7744, 35.6812)  # Tokyo

   now = datetime.now(timezone.utc)
   now = now.replace(tzinfo=ZoneInfo(tz))
   print(now)
   # 2025-04-29 01:33:56.325194+09:00
   ```

   [`examples/tzfpy_with_arrow.py`](examples/tzfpy_with_arrow.py):

   ```python
   from zoneinfo import ZoneInfo

   import arrow
   from tzfpy import get_tz

   tz = get_tz(139.7744, 35.6812)  # Tokyo

   arrow_now = arrow.now(ZoneInfo(tz))
   print(arrow_now.format("YYYY-MM-DD HH:mm:ss ZZZ"))
   # 2025-04-29 01:33:56.325194+09:00
   ```

   If you are using whenever, since whenever use tzdata internally, so it's
   compatible with tzfpy:

   [`examples/tzfpy_with_whenever.py`](examples/tzfpy_with_whenever.py):

   ```python
   from whenever import Instant
   from tzfpy import get_tz

   now = Instant.now()

   tz = get_tz(139.7744, 35.6812)  # Tokyo

   now = now.to_tz(tz)

   print(now)
   # 2025-04-29T10:33:28.427784+09:00[Asia/Tokyo]
   ```

## Performance

Benchmark runs under
[`v1.0.0`](https://github.com/ringsaturn/tzfpy/releases/tag/v1.0.0) on my
MacBook Pro with Apple M3 Max.

```bash
pytest --benchmark-warmup=on --benchmark-warmup-iterations=100 tests/test_bench.py
```

```
-------------------------------------------------------------- benchmark: 1 tests --------------------------------------------------------------
Name (time in ns)                 Min          Max        Mean      StdDev      Median         IQR    Outliers  OPS (Kops/s)  Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------------------------
test_tzfpy_random_cities     895.7926  11,420.8087  2,597.6093  1,331.8472  2,337.5032  1,587.5907  11611;1000      384.9694   33614          10
------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
Results (2.03s):
         1 passed
```

Or you can view more benchmark results on
[GitHub Action summary page](https://github.com/ringsaturn/tzfpy/actions/workflows/Test.yml).

More benchmarks compared with other packages can be found in
[ringsaturn/tz-benchmark](https://github.com/ringsaturn/tz-benchmark).

## Background

`tzfpy` was originally written in Go named [`tzf`][tzf] and use CGO compiled to
`.so` to be used by Python. Since `v0.11.0` it's rewritten in Rust built on PyO3
and [`tzf-rs`][tzf-rs], a tzf's Rust port.

I have written an article about the history of tzf, its Rust port, and its Rust
port's Python binding; you can view it
[here](https://blog.ringsaturn.me/en/posts/2023-01-31-history-of-tzf/).

[tzf]: https://github.com/ringsaturn/tzf
[tzf-rs]: https://github.com/ringsaturn/tzf-rs

## Compare with other packages

Please note that directly compare with other packages is not fair, because they
have different use cases and design goals, for example, the precise.

### [TimezoneFinder](https://github.com/jannikmi/timezonefinder)

I got lots of inspiration from it. Timezonefinder is a very good package and
it's mostly written in Python, so it's easy to use. And it's much
[more widely used](https://github.com/jannikmi/timezonefinder/network/dependents)
compared with tzfpy if you care about that.

However, it's slower than tzfpy, especially around the borders, and I have lots
of API requests from there. That's the reason I created tzf originally. And then
tzf-rs and tzfpy.

### [pytzwhere](https://github.com/pegler/pytzwhere)

I recommend to read timezonefinder's
[Comparison to pytzwhere](https://timezonefinder.readthedocs.io/en/latest/3_about.html#comparison-to-pytzwhere)
since it's very detailed.

## Contributing

Install:

- [Rust](https://www.rust-lang.org/tools/install)
- [Python](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/)

```console
Available commands:
  build    - Build the project using uv
  fmt      - Format the code using ruff
  lint     - Lint the code using ruff
  sync     - Sync and compile the project using uv
  lock     - Lock dependencies using uv
  upgrade  - Upgrade dependencies using uv
  all      - Run lock, sync, fmt, lint, and test
  test     - Run tests using pytest
```

```bash
make all
```

## LICENSE

This project is licensed under the [MIT license](./LICENSE) and
[Anti CSDN License](./LICENSE_ANTI_CSDN.md)[^anti_csdn]. The data is licensed
under the
[ODbL license](https://github.com/ringsaturn/tzf-rel/blob/main/LICENSE), same as
[`evansiroky/timezone-boundary-builder`](https://github.com/evansiroky/timezone-boundary-builder)

[^anti_csdn]: This license is to prevent the use of this project by CSDN, has no
    effect on other use cases.

<!-- ## Other info

[![](https://ringsaturn.github.io/pypi-downloads-chart/tzfpy/download-trends.svg)](https://ringsaturn.github.io/pypi-downloads-chart/tzfpy/index.html) -->
