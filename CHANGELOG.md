# Changelog

Release notes for `1.3.3` and earlier live in
[GitHub Releases](https://github.com/ringsaturn/tzfpy/releases).

## 2.1.0b2 (unreleased)

Second pre-release on the same routing as 2.1.0b1: lite wheels to TestPyPI
and GitHub Releases, `+full` wheels to GitHub Releases and tzfpy's own index.
Built on tzf-rs 2.1.1 and tzf-dist `0.0.2026-c-tzb2`: the same `2026c`
boundaries encoded at 64-point chunks, plus the tzf-rs in-place reader work
(open-time group validation, chunk block skipping, per-group latitude
stripes, endpoint-parity skip, targeted FUZZY probes). No API change; results
are identical.

The full-precision variant is the one that moves. tz-benchmark Python
harness, Apple M3 Max, CPython 3.14, medians per call:

| Candidate                     | random cities | edge cities | RSS delta |
| ----------------------------- | ------------: | ----------: | --------: |
| tzfpy 2.1.0b2 (lite)          |        625 ns |      875 ns |  39.0 MiB |
| tzfpy 2.1.0b2+full (2.1.0b1+full in parentheses) | 750 ns (917) | 1.21 µs (6.25) | 16.0 MiB (13.5) |
| timezonefinder 9.0.0          |       1.17 µs |     2.71 µs |  52.5 MiB |

Wheel sizes grow with the chunk change: lite 2.9 → 3.0 MB, full 10.8 →
11.8 MB (macOS arm64).

## 2.1.0b1 (unreleased)

A pre-release: the lite wheels go to
[TestPyPI](https://test.pypi.org/project/tzfpy/) and GitHub Releases, not
PyPI. The point of the tag is to put the experimental full-precision wheels
on tzfpy's own index.

### Added

- Experimental full-precision wheels, built from tzf-dist's unsimplified
  `full.tzb` (~14 MB) instead of the ~4 MB `lite.tzb`, via the new mutually
  exclusive `lite` (default) / `full` Cargo features. They carry a `+full` PEP
  440 local version and, being experimental, are published only to GitHub
  Releases and tzfpy's own index at
  `https://ringsaturn.github.io/tzfpy/full/simple/` — never to PyPI, which
  rejects local versions by design. The PyPI and conda-forge builds are
  unchanged. The full variant runs on tzf-rs's `EmbeddedFinder`, which queries
  the data in place: about 13.5 MB resident against lite's 40 MB, with
  `get_tz` ~1.8x and `get_tzs` ~14x slower per call. See README
  "Full-precision wheels" for the measurements and install instructions.

## 2.0.0

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
