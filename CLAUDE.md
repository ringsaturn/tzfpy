# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

tzfpy is a Python library for fast longitude/latitude to timezone name conversion, built as a Rust extension using PyO3. It's a Python binding for the Rust library `tzf-rs` and claims to be the fastest Python package for timezone lookups.

## Architecture

### Core Components

- **Rust Extension**: The main functionality is implemented in Rust (`src/lib.rs`) using the `tzf-rs` library
- **Python Bindings**: PyO3 is used to create Python bindings for the Rust functions
- **Lazy Static Finder**: Uses a lazy-initialized `DefaultFinder` from `tzf-rs` for timezone lookups
- **Type Stubs**: `tzfpy.pyi` provides type hints for the Python API

### Key Functions

- `get_tz(lng, lat)`: Returns the first timezone for coordinates
- `get_tzs(lng, lat)`: Returns all possible timezones for coordinates  
- `timezonenames()`: Returns all supported timezone names
- `data_version()`: Returns the tzdata version

### Build System

- Uses **maturin** as the build backend for Rust-Python integration
- **uv** for Python dependency management
- **Cargo** for Rust dependency management

## Development Commands

### Setup and Dependencies
```bash
uv sync --compile          # Sync and compile dependencies
uv lock                    # Lock dependencies
uv lock --upgrade          # Upgrade and lock dependencies
cargo update               # Update Rust dependencies
```

### Building
```bash
uv build                   # Build the Python package
make sync                  # Compile dependencies
```

### Code Quality
```bash
make fmt                   # Format code (ruff check --select I --fix + ruff format)
make lint                  # Lint code (ruff check + ruff format --check)
uv run ruff check .        # Run ruff linter
uv run ruff format .       # Format Python code
```

### Testing
```bash
make test                  # Run all tests (includes lint check)
uv run pytest -v .        # Run tests directly
make examples              # Run all example files
```

### Complete Workflow
```bash
make all                   # Run lock, sync, fmt, lint, and test
```

### Performance Testing
```bash
pytest --benchmark-warmup=on --benchmark-warmup-iterations=100 tests/test_bench.py
```

## Project Structure

- `src/lib.rs`: Main Rust implementation with PyO3 bindings
- `tzfpy.pyi`: Python type stubs
- `examples/`: Usage examples with different datetime libraries
- `tests/`: Test suite including benchmarks
- `Cargo.toml`: Rust dependencies and configuration
- `pyproject.toml`: Python project configuration and dependencies
- `Makefile`: Development workflow commands

## Development Notes

- The project uses lazy initialization for the timezone finder, so first calls may be slower
- Memory usage is approximately 40MB
- Supports Python 3.9+
- Built with PyO3 ABI3 for cross-version compatibility
- Uses simplified polygon data for performance (less accurate around borders)