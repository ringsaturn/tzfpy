export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG=true

PYTHON_LIB_DIR := $(shell uv run python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR') or sysconfig.get_config_var('LIBPL') or '')")
PYTHON_LIB_NAME := $(shell uv run python -c "import sysconfig, os; n = sysconfig.get_config_var('LDLIBRARY') or ''; n = os.path.splitext(n)[0]; print(n[3:] if n.startswith('lib') else n)")
RUSTFLAGS="-L native=$(PYTHON_LIB_DIR) -l dylib=$(PYTHON_LIB_NAME) -C link-arg=-Wl,-rpath,$(PYTHON_LIB_DIR)"

.PHONY: help build fmt lint sync lock upgrade all test examples stub_gen

help:
	@echo "Available commands:"
	@echo "  build    - Build the project using uv"
	@echo "  fmt      - Format the code using ruff"
	@echo "  lint     - Lint the code using ruff"
	@echo "  sync     - Sync and compile the project using uv"
	@echo "  lock     - Lock dependencies using uv"
	@echo "  upgrade  - Upgrade dependencies using uv"
	@echo "  all      - Run lock, sync, fmt, lint, and test"
	@echo "  test     - Run tests using pytest"

stub_gen:
	@RUSTFLAGS=$(RUSTFLAGS) cargo run --bin stub_gen
	make fmt

build: stub_gen
	uv build

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

test: lint
	uv run pytest -v .

licences:
	cargo-bundle-licenses --format yaml --output THIRDPARTY.yml

examples:
	@echo "Running examples:"
	@cd examples && for file in $$(find . -name "*.py" ! -name "*fastapi*" | sort); do \
		printf "%s: " "$$file"; uv run python "$$file"; \
	done
