# tzfpy

- [![PyPI](https://img.shields.io/pypi/v/tzfpy)](https://pypi.org/project/tzfpy/)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fringsaturn%2Ftzfpy.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fringsaturn%2Ftzfpy?ref=badge_shield)
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
> 1. This package uses simplified polygon data. The error around borders is
>    small and bounded: every simplified boundary stays within about 111 m of
>    the full-precision border. See [Accuracy](#accuracy) for measured numbers.
> 2. The finder is built on the first call, so that call takes 15 ms on the
>    machine used in [Performance](#performance); later calls take under 1 µs.
> 3. Uses about 40MB memory, down from about 72MB in 1.x. See
>    [Memory](#memory).
> 4. It's tested under Python 3.10+.
> 5. Try it online:
>    - <https://ringsaturn.github.io/tzf-web/>, powered by tzf-rs and
>      WebAssembly

## Changes in 2.0

tzfpy 2.0 upgrades the Rust core from [`tzf-rs`][tzf-rs] 1.x to
[2.0](https://github.com/ringsaturn/tzf-rs/blob/main/CHANGELOG.md), which
carries no protobuf dependency: the boundary data ships as the TZF embedded
binary format (`.tzb`).

The Python API is unchanged. The same six functions with the same names,
signatures and return types: `get_tz`, `get_tzs`, `timezonenames`,
`data_version`, `get_tz_polygon_geojson`, `get_tz_index_geojson`. Apart from
the four changes listed below, code written against 1.x runs unmodified.

Measured differences:

| Metric | 1.3.3 | 2.0.0 |
| --- | ---: | ---: |
| Memory after import + first query | ~72 MB | ~41 MB |
| Wheel size (macOS arm64) | 4.31 MB | 2.77 MB |
| Dataset | `2026c` | `2026c` |

### Breaking changes

1. `get_tzs()` results are sorted alphabetically. 1.x returned them in
   internal polygon order. `get_tz()` returns the first positive match and is
   the supported way to obtain a single name.
2. The `_TZFPY_DISABLE_Y_STRIPES` environment variable was removed. tzf-rs 2
   removed `FinderOptions`, and the YStripes index is always enabled. Setting
   the variable has no effect and raises no error.
3. `get_tz_polygon_geojson()` and `get_tz_index_geojson()` raise `ValueError`
   for a name the dataset does not carry. In 1.x the same input panicked,
   surfacing as `pyo3_runtime.PanicException`.
4. Exported GeoJSON no longer repeats the duplicated junction vertices that the
   protobuf expansion carried. Query results are identical; byte-for-byte
   comparisons of exported GeoJSON against 1.x output are not.

Unchanged: coordinate order is `(longitude, latitude)`, the dataset is `2026c`,
and a point lying exactly on a shared border belongs to both neighbouring
zones.

See the [tzf-rs v2
changelog](https://github.com/ringsaturn/tzf-rs/blob/main/CHANGELOG.md) for the
Rust-side detail.

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

`get_tz` returns one name, or `''` when no timezone covers the point. It is
answered from the pre-index when a tile covers the point and by exact
point-in-polygon otherwise. `get_tzs` is always polygon-exact and returns every
match, sorted alphabetically: overlapping timezones and points lying exactly on
a shared border yield more than one name.

Or you can try it via `uvx`:

```bash
uvx --with tzfpy python -c "from tzfpy import get_tz;tz = get_tz(116.3883,39.9289);print(tz)"
Asia/Shanghai
```

### Export to GeoJSON

For data visualization, you can get timezone polygon GeoJSON data from tzfpy.
`get_tz_polygon_geojson` returns the timezone's boundary polygons;
`get_tz_index_geojson` returns the bounding boxes of its pre-index tiles: the
area where `get_tz` answers from the fast path. Both return a serialized
GeoJSON `FeatureCollection`, and both raise `ValueError` for a name the
dataset does not carry:

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

Each call re-serializes the geometry, so the cost is proportional to the
timezone's polygon size.

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

## Accuracy

The Douglas-Peucker simplification uses an epsilon of 0.001 degrees, which
caps boundary displacement at roughly 111 m by construction. Measured against
the full-precision 2026c dataset with `tzf`'s `internal/cmd/borderchange`
(spherical model, certified via Lipschitz interval subdivision):

| Metric                                            |                        Result |
| ------------------------------------------------- | ----------------------------: |
| Certified maximum boundary displacement           | 111.7 m (+1.0 m tolerance)    |
| Boundary length displaced more than 100 m         | 0.41%                         |
| Boundary length displaced more than 500 m         | 0%                            |
| Total mis-assigned area                           | 16,962 km² (~0.003% of Earth) |
| Mis-assigned area within 100 m of the true border | 92.8%                         |

Only queries within about 111 m of a timezone border can differ from the
full-precision result, and most of that band is much narrower. See
[`BORDER_CHANGE.md`](https://github.com/ringsaturn/tzf/blob/main/BORDER_CHANGE.md)
in the `tzf` repository for the complete evaluation results.

## Performance

Benchmark run under `v2.0.0` on a MacBook Pro (Apple M3 Max, macOS 26.6.2,
CPython 3.10.18), via `make bench`, over random world cities, 500 rounds after
500 warmup iterations:

| Index mode | Median (µs) | Mean (µs) | Throughput (Kops/s) | Memory |
| --- | ---: | ---: | ---: | ---: |
| Default (pre-index + YStripes) | 0.6825 | 0.8990 | 1112.3 | ~40.4 MB |

Timings include the Python call overhead and the benchmark's own coordinate
generation; the Rust lookup itself measures ~260 ns for a random city on the
same machine. The 1.x median on the same machine was 0.636 µs, so query latency
is within run-to-run variation of 1.x. The measured reductions are in memory
and wheel size.

### Memory

Measured with `make measure-memory` on the same machine (RSS increase after
`import tzfpy` plus one query, CPython 3.10.18):

| Version | RSS delta (3 runs) | Whole process |
| --- | ---: | ---: |
| 1.3.3 | 71.6–73.6 MB | 89.7–96.4 MB |
| 2.0.0 | 39.8–42.3 MB | 57.8–60.3 MB |

Both rows were measured back to back on the same machine with the same script,
against the same `2026c` dataset.

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

Also, see [Project tzf][project-tzf] for more information.

[tzf]: https://github.com/ringsaturn/tzf
[tzf-rs]: https://github.com/ringsaturn/tzf-rs
[project-tzf]: https://project-tzf.ringsaturn.me/docs/getting-started/

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
  build            - Build the project using uv
  build-ext        - Rebuild and install local Rust extension into venv
  fmt              - Format the code using ruff
  lint             - Lint the code using ruff
  sync             - Sync and compile the project using uv
  lock             - Lock dependencies using uv
  upgrade          - Upgrade dependencies using uv
  all              - Run lock, sync, fmt, lint, and test
  test             - Run non-benchmark tests
  test-all         - Run all tests including benchmark
  bench            - Run the query benchmark and print a Markdown table
  measure-memory   - Measure memory usage of tzfpy and TimezoneFinder
```

```bash
make all
```

## LICENSE

This project is licensed under the [MIT license](./LICENSE). The data is
licensed under the
[ODbL license](https://github.com/ringsaturn/tzf-dist/blob/main/LICENSE_DATA), same as
[`evansiroky/timezone-boundary-builder`](https://github.com/evansiroky/timezone-boundary-builder)

<!-- ## Other info

[![](https://ringsaturn.github.io/pypi-downloads-chart/tzfpy/download-trends.svg)](https://ringsaturn.github.io/pypi-downloads-chart/tzfpy/index.html) -->


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fringsaturn%2Ftzfpy.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fringsaturn%2Ftzfpy?ref=badge_large)
