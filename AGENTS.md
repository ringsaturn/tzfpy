# Repository Guidelines

## Project Structure & Module Organization
- `src/lib.rs` contains the PyO3 extension module and the exported Python-callable functions.
- `tests/` holds runtime, compatibility, benchmark, and smoke tests (`test_basic.py`, `test_compatibility.py`, `test_bench.py`, `test_smock.py`).
- `examples/` contains integration samples for `datetime`, `arrow`, `pandas`, `polars`, `numpy`, and `fastapi`.
- `scripts/` includes release and index automation helpers.
- `docs/` and `site/` store release-index inputs and generated static index output.

## Build, Test, and Development Commands
- `make sync` installs and compiles dependencies with `uv`.
- `make fmt` runs import sorting and formatting via Ruff.
- `make lint` checks Ruff lint and formatting compliance.
- `make test` runs lint plus `pytest -v .`.
- `make all` runs lock, sync, format, lint, and test in sequence.
- `uv build` builds distribution artifacts.
- `make examples` runs example scripts except the FastAPI sample.

## Coding Style & Naming Conventions
- Python style follows Ruff defaults, 4-space indentation, and `snake_case` for functions and test names.
- Rust style uses `snake_case` for functions and `CamelCase` for types.
- Keep Python API names aligned across `src/lib.rs`, tests, and `tzfpy.pyi`.
- Prefer small focused functions and direct assertions in tests.

## Testing Guidelines
- Test framework: `pytest` with `pytest-benchmark` support.
- Name new tests as `tests/test_<feature>.py` and test functions as `test_<behavior>`.
- Add deterministic coordinate assertions to `test_basic.py` for API changes.
- Add ecosystem compatibility checks to `test_compatibility.py` when timezone handling logic changes.
- Run benchmark locally when performance-sensitive code changes:
  - `pytest --benchmark-warmup=on --benchmark-warmup-iterations=100 tests/test_bench.py`

## Commit & Pull Request Guidelines
- Commit subjects in this repository are short and imperative, for example `fix action`, `Add sdist to index`, `Bump ruff ... (#118)`.
- Keep the first line under 72 characters when practical.
- Pull requests should include: purpose summary, linked issue or context, and local verification commands with results.
- Include CI or wheel-impact notes when touching `src/`, `Cargo.toml`, or workflow files.
