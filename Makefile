export PYTHONPATH := $(shell pwd)
export UV_PYTHON_PREFERENCE=only-system
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG=true

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
	uv lock --upgrade

all: lock sync
	make fmt
	make lint
	make test	

test: lint
	uv run pytest -v .
