# tzfpy [![PyPI](https://img.shields.io/pypi/v/tzfpy)](https://pypi.org/project/tzfpy/) [![](https://img.shields.io/pypi/wheel/tzfpy.svg)](https://pypi.org/project/tzfpy/)

![](https://github.com/ringsaturn/tzf/blob/gh-pages/docs/tzf-social-media.png?raw=true)

It's probably the fastest Python package to convert longitude/latitude to
timezone name.

> **NOTE**
>
> 1. This package use a simplified polygon data and not so accurate around
   > borders.
> 2. Rust use lazy init, so first calling will be a little slow.
> 3. Use about 40MB memory.

It's tested under Python 3.9+ but support 3.7+(noqa).

## Usage

Please note that new timezone names may be added to tzfpy, which could be
incompatible with old version package like pytz. As an option, tzfpy supports
install compatible version of those packages with extra params.

```bash
# Install just tzfpy
pip install tzfpy

# Install tzfpy with pytz
pip install "tzfpy[pytz]"
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
[`v0.15.0`](https://github.com/ringsaturn/tzfpy/releases/tag/v0.15.0) on my
MacBook Pro with 2.3 GHz 8-Core Intel Core i9.

```bash
pytest tests/test_bench.py
```

```
-------------------------------------------------- benchmark: 1 tests --------------------------------------------------
Name (time in us)               Min      Max    Mean  StdDev  Median     IQR  Outliers  OPS (Kops/s)  Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------
test_tzfpy_random_cities     1.4783  34.8846  3.6341  1.9382  3.2185  2.1708  4384;754      275.1715   20000          10
------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
Results (1.10s):
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

## LICENSE

This project is licensed under the [MIT license](./LICENSE). The data is
licensed under the
[ODbL license](https://github.com/ringsaturn/tzf-rel/blob/main/LICENSE), same as
[`evansiroky/timezone-boundary-builder`](https://github.com/evansiroky/timezone-boundary-builder)
