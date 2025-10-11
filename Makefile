# export UV_PYTHON_PREFERENCE=only-system
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG=true

.PHONY: help build fmt lint sync lock upgrade all test examples

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

build:
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
