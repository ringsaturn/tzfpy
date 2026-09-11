# Changelog

Release notes for `1.3.3` and earlier live in
[GitHub Releases](https://github.com/ringsaturn/tzfpy/releases).

## 2.0.0 (unreleased)

Rust core upgraded from [`tzf-rs`](https://github.com/ringsaturn/tzf-rs) 1.3.7
to 2.0.0, which is protobuf-free: boundary data now ships as the TZF embedded
binary format (`.tzb`) from `tzf-dist` instead of protobuf artifacts. The
dataset itself is unchanged (`data_version() == "2026c"`).

The Python API is unchanged: the same six functions with the same names,
signatures and return types. Apart from the changes below, code written against
1.x runs unmodified.

### Breaking changes

- `get_tzs()` returns names sorted alphabetically; 1.x returned them in
  internal polygon order. `get_tz()` returns the first positive match.
- `_TZFPY_DISABLE_Y_STRIPES` was removed: tzf-rs 2 removed `FinderOptions` and
  the YStripes index is always enabled. Setting the variable has no effect and
  raises no error.
- `get_tz_polygon_geojson()` / `get_tz_index_geojson()` raise `ValueError` for
  an unknown timezone name instead of panicking with
  `pyo3_runtime.PanicException`.
- Exported GeoJSON no longer repeats the duplicated junction vertices the
  protobuf expansion carried. Query results are unaffected; byte-comparisons
  against 1.x exports are not.

### Improvements

Measured on a MacBook Pro (Apple M3 Max, macOS 26.6.2, CPython 3.10.18), same
machine and script for both versions:

| Metric | 1.3.3 | 2.0.0 |
| --- | ---: | ---: |
| RSS after import + one query | 71.6–73.6 MB | 39.8–42.3 MB |
| Wheel size (macOS arm64) | 4.31 MB | 2.77 MB |
| Query median (`make bench`) | 0.636 µs | 0.683 µs |

Query latency is within run-to-run variation of 1.3.3. The measured reductions
are in memory and download size.

### Internal

- `get_tz` is answered by the pre-index fast path first and falls back to exact
  point-in-polygon; `get_tzs` is always polygon-exact. This matches tzf-rs 2 and
  Go `tzf/v2` semantics, and matches the behavior of 1.3.3.
- `make bench` / `scripts/benchmark_index_modes.py` collapsed to the single
  remaining index mode.
- Added `py-cpuinfo` to the dev dependency group: `pytest-benchmark` 5.3 made it
  optional, but `--benchmark-json` (used by `make bench`) still requires it.
