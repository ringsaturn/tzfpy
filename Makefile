# export UV_PYTHON_PREFERENCE=only-system
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG=true
export UV_NO_SYNC=1

BENCHMARK_ARGS=--benchmark-warmup=on --benchmark-warmup-iterations=500 --benchmark-min-rounds=500 --benchmark-min-time=0.01

.PHONY: help build build-ext build-full fmt lint sync lock upgrade all test test-all bench measure-memory examples

help:
	@echo "Available commands:"
	@echo "  build            - Build the project using uv"
	@echo "  build-ext        - Rebuild and install local Rust extension into venv"
	@echo "  build-full       - Build the full-precision (+full) wheel into dist/"
	@echo "  fmt              - Format the code using ruff"
	@echo "  lint             - Lint the code using ruff"
	@echo "  sync             - Sync and compile the project using uv"
	@echo "  lock             - Lock dependencies using uv"
	@echo "  upgrade          - Upgrade dependencies using uv"
	@echo "  all              - Run lock, sync, fmt, lint, and test"
	@echo "  test             - Run non-benchmark tests"
	@echo "  test-all         - Run all tests including benchmark"
	@echo "  bench            - Compare index modes in a Markdown benchmark table"
	@echo "  measure-memory   - Measure memory usage for index modes and TimezoneFinder"

build:
	uv build

build-ext:
	uv run maturin develop --release

# Full-precision variant. Never published to PyPI: the `+full` local version is
# rejected there by design, and tzf-dist keeps full.tzb git-only because it is
# too large for crates.io. See README "Full-precision wheels".
#
# The Cargo.toml/Cargo.lock rewrite is transient and restored on any exit path.
build-full:
	@cp Cargo.toml .Cargo.toml.orig && cp Cargo.lock .Cargo.lock.orig && \
		trap 'mv .Cargo.toml.orig Cargo.toml; mv .Cargo.lock.orig Cargo.lock' EXIT INT TERM; \
		uv run --no-sync scripts/set_local_version.py full && \
		uv run --no-sync maturin build --release --no-default-features --features full --out dist

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
	make THIRDPARTY.yml NOTICE

all: lock sync
	make fmt
	make lint
	make test
	make measure-memory

measure-memory:
	@echo "Measuring memory usage with different index modes:"
	@echo ""
	@echo "Default index mode:"
	@uv run --with psutil scripts/measure_memory_tzfpy.py
	@echo ""
	@echo "Disable Y stripes mode:"
	@_TZFPY_DISABLE_Y_STRIPES=1 uv run --with psutil scripts/measure_memory_tzfpy.py
	@echo ""
	@echo "TimezoneFinder:"
	@uv run --with psutil --with timezonefinder scripts/measure_memory_timezonefinder.py

test: lint build-ext
	uv run pytest -v -m "not benchmark" .

test-all: lint build-ext
	uv run pytest -v .

bench: build-ext
	@uv run python scripts/benchmark_index_modes.py $(BENCHMARK_ARGS)

THIRDPARTY.yml: Cargo.lock Cargo.toml
	cargo-bundle-licenses --format yaml --output THIRDPARTY.yml

NOTICE: THIRDPARTY.yml scripts/build_notice.py
	python3 scripts/build_notice.py

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
