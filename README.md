# tzfpy [![PyPI](https://img.shields.io/pypi/v/tzfpy)](https://pypi.org/project/tzfpy/) [![](https://img.shields.io/pypi/wheel/tzfpy.svg)](https://pypi.org/project/tzfpy/)

It's probably the fastest Python package to convert longitude/latitude to timezone name.

NOTE:

1. This package use a simplified polygon data and not so accurate around borders.
2. Rust use lazzy init, so first calling will be a little slow.
3. Use about 40MB memory.

It's tested under Python 3.9+ but support 3.7+(noqa).

## Usage

```bash
pip install tzfpy
```

```python
>>> from tzfpy import get_tz, get_tzs
>>> get_tz(116.3883, 39.9289)
'Asia/Shanghai'
>>> get_tzs(87.4160, 44.0400)
['Asia/Shanghai', 'Asia/Urumqi']
```

## Background

`tzfpy` was originally written in Go named [`tzf`][tzf] and use CGO compiled to `.so` to be used by Python.
Since `v0.11.0` it's rewritten in Rust built on PyO3 and [`tzf-rs`][tzf-rs], a tzf's Rust port.

[tzf]: https://github.com/ringsaturn/tzf
[tzf-rs]: https://github.com/ringsaturn/tzf-rs
