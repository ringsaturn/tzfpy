# Install via backup index

## Usage

For a self-hosted index built from GitHub Release distribution assets:

```bash
# For pip
pip install tzfpy \
  --index-url https://ringsaturn.github.io/tzfpy/simple/ \
  --extra-index-url https://pypi.org/simple

# For uv
uv pip install tzfpy \
  --index-url https://ringsaturn.github.io/tzfpy/simple/ \
  --extra-index-url https://pypi.org/simple
```

If using uv, you can also configure the index in `pyproject.toml`:

```toml
# pyproject.toml
[[tool.uv.index]]
name = "tzfpy-mirror"
url = "https://ringsaturn.github.io/tzfpy/simple"
explicit = true

[tool.uv.sources]
tzfpy = { index = "tzfpy-mirror" }
```

Raw distribution metadata is stored in: [docs/release_wheels.csv](docs/release_wheels.csv).

## Development

Update metadata and regenerate index (incremental mode):

```bash
uv run scripts/build_simple_index.py \
  --repository ringsaturn/tzfpy \
  --package tzfpy \
  --min-tag v0.11.0 \
  --csv docs/release_wheels.csv \
  --output site
```

Force a full rebuild:

```bash
uv run scripts/build_simple_index.py \
  --repository ringsaturn/tzfpy \
  --package tzfpy \
  --min-tag v0.11.0 \
  --csv docs/release_wheels.csv \
  --full-fetch \
  --output site
```
