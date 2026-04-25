# export UV_PYTHON_PREFERENCE=only-system
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG=true

BENCHMARK_ARGS=--benchmark-warmup=on --benchmark-warmup-iterations=500 --benchmark-min-rounds=500 --benchmark-min-time=0.01

.PHONY: help build build-ext fmt lint sync lock upgrade all test test-all test-bench test-bench-index examples

help:
	@echo "Available commands:"
	@echo "  build            - Build the project using uv"
	@echo "  build-ext        - Rebuild and install local Rust extension into venv"
	@echo "  fmt              - Format the code using ruff"
	@echo "  lint             - Lint the code using ruff"
	@echo "  sync             - Sync and compile the project using uv"
	@echo "  lock             - Lock dependencies using uv"
	@echo "  upgrade          - Upgrade dependencies using uv"
	@echo "  all              - Run lock, sync, fmt, lint, and test"
	@echo "  test             - Run non-benchmark tests"
	@echo "  test-all         - Run all tests including benchmark"
	@echo "  test-bench       - Run benchmark test with current env"
	@echo "  test-bench-index - Run benchmark in default/disable-y-stripes modes"

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
	make measure-memory

measure-memory:
	@echo "Measuring memory usage with different index modes:"
	@echo ""
	@echo "Default index mode:"
	@uv run --with psutil --no-sync scripts/measure_memory_tzfpy.py
	@echo ""
	@echo "Disable Y stripes mode:"
	@_TZFPY_DISABLE_Y_STRIPES=1 uv run --with psutil --no-sync scripts/measure_memory_tzfpy.py
	@echo ""
	@echo "TimezoneFinder:"
	@uv run --with psutil --no-sync --with timezonefinder scripts/measure_memory_timezonefinder.py

test: lint build-ext
	uv run --no-sync pytest -v -m "not benchmark" .

test-all: lint build-ext
	uv run --no-sync pytest -v .

bench: build-ext
	@echo "Benchmark with _TZFPY_DISABLE_Y_STRIPES=1"
	@_TZFPY_DISABLE_Y_STRIPES=1 uv run --no-sync pytest -q -s tests/test_bench.py $(BENCHMARK_ARGS)
	@echo "Benchmark with default index mode"
	@uv run --no-sync pytest -q -s tests/test_bench.py $(BENCHMARK_ARGS)

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
