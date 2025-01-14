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
> 4. It's tested under Python 3.9+.
> 5. Try it online:
>     - <https://tzfpy-reflex-teal-apple.reflex.run>, powered by tzfpy and Reflex
>     - <https://ringsaturn.github.io/tzf-web/>, powered by tzf-rs and WebAssembly

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

## Performance

Benchmark runs under
[`v0.16.0`](https://github.com/ringsaturn/tzfpy/releases/tag/v0.16.0) on my
MacBook Pro with Apple M3 Max.

```bash
pytest --benchmark-warmup=on --benchmark-warmup-iterations=100 tests/test_bench.py
```

```
----------------------------------------------------------- benchmark: 1 tests -----------------------------------------------------------
Name (time in ns)                 Min         Max        Mean    StdDev      Median       IQR   Outliers  OPS (Kops/s)  Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------------------
test_tzfpy_random_cities     699.9937  7,175.0022  1,562.1433  646.9249  1,441.6990  833.3940  13716;984      640.1461   41026          10
------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
Results (1.81s):
         1 passed
```

Or you can view more benchmark results on
[GitHub Action summary page](https://github.com/ringsaturn/tzfpy/actions/workflows/Test.yml).

## Background

`tzfpy` was originally written in Go named [`tzf`][tzf] and use CGO compiled to
`.so` to be used by Python. Since `v0.11.0` it's rewritten in Rust built on PyO3
and [`tzf-rs`][tzf-rs], a tzf's Rust port.

I have written an article about the history of tzf, its Rust port, and its Rust
port's Python binding; you can view it
[here](https://blog.ringsaturn.me/en/posts/2023-01-31-history-of-tzf/).

[tzf]: https://github.com/ringsaturn/tzf
[tzf-rs]: https://github.com/ringsaturn/tzf-rs

## Project status

`tzfpy` is still under development and it has been deployed into
[my current company](https://github.com/caiyunapp)'s production environment and
it works well under high concurrency for weather API and location related data
processed. So I think it's ready to be used in production with caution.

I haven't release the v1.0.0 yet and I will try my best to keep current API as
stable as possible(only 3 functions). I'm still working on performance
improvements on Rust side, which is a release blocker for both tzf-rs and tzfpy.

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

This project is licensed under the [MIT license](./LICENSE). The data is
licensed under the
[ODbL license](https://github.com/ringsaturn/tzf-rel/blob/main/LICENSE), same as
[`evansiroky/timezone-boundary-builder`](https://github.com/evansiroky/timezone-boundary-builder)
