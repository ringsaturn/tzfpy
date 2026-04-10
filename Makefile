# export UV_PYTHON_PREFERENCE=only-system
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG=true

.PHONY: help build build-ext fmt lint sync lock upgrade all test test-all test-bench test-bench-index examples

help:
	@echo "Available commands:"
	@echo "  build    - Build the project using uv"
	@echo "  build-ext - Rebuild and install local Rust extension into venv"
	@echo "  fmt      - Format the code using ruff"
	@echo "  lint     - Lint the code using ruff"
	@echo "  sync     - Sync and compile the project using uv"
	@echo "  lock     - Lock dependencies using uv"
	@echo "  upgrade  - Upgrade dependencies using uv"
	@echo "  all      - Run lock, sync, fmt, lint, and test"
	@echo "  test     - Run non-benchmark tests"
	@echo "  test-all - Run all tests including benchmark"
	@echo "  test-bench - Run benchmark test with current env"
	@echo "  test-bench-index - Run benchmark in none/rtree/quadtree modes"

build:
	uv build

build-ext:
	uv run maturin develop --release

fmt:
	uv run ruff check --select I --fix .
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .

sync:
	uv sync --compile

lock:
	uv lock

upgrade:
	cargo update
	uv lock --upgrade
	make licences

all: lock sync
	make fmt
	make lint
	make test

test: lint build-ext
	uv run pytest -v -m "not benchmark" .

test-all: lint build-ext
	uv run pytest -v .

test-bench: build-ext
	uv run pytest -q -s tests/test_bench.py

test-bench-index: build-ext
	@echo "Benchmark with _TZFPY_EXP_INDEX unset"
	@uv run pytest -q -s tests/test_bench.py
	@echo "Benchmark with _TZFPY_EXP_INDEX=rtree"
	@_TZFPY_EXP_INDEX=rtree uv run pytest -q -s tests/test_bench.py
	@echo "Benchmark with _TZFPY_EXP_INDEX=quadtree"
	@_TZFPY_EXP_INDEX=quadtree uv run pytest -q -s tests/test_bench.py

licences:
	cargo-bundle-licenses --format yaml --output THIRDPARTY.yml

examples:
	@echo "Running examples:"
	@cd examples && for file in $$(find . -name "*.py" ! -name "*fastapi*" | sort); do \
		printf "%s: " "$$file"; uv run python "$$file"; \
	done

simple-index:
	uv run scripts/build_simple_index.py \
		--repository ringsaturn/tzfpy \
		--package tzfpy \
		--min-tag v0.6.0 \
		--csv docs/release_wheels.csv \
		--output site/
