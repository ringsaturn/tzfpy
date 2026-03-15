# Install via backup index

To reduce PyPI storage size([`ringsaturn/tzfpy#117`][issue_117]), many history
whls, some platform specific whls will no nolonger be uploaded to PyPI. Instead,
a backup index based on GitHub Release distribution assets is maintained at
[this][index_url].

[issue_117]: https://github.com/ringsaturn/tzfpy/issues/117
[index_url]: https://ringsaturn.github.io/tzfpy/simple/

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

## Development

Raw distribution metadata is stored in:
[docs/release_wheels.csv](docs/release_wheels.csv).

Update metadata and regenerate index (incremental mode):

```bash
uv run scripts/build_simple_index.py \
  --repository ringsaturn/tzfpy \
  --package tzfpy \
  --min-tag v0.6.0 \
  --csv docs/release_wheels.csv \
  --output site
```

Force a full rebuild:

```bash
uv run scripts/build_simple_index.py \
  --repository ringsaturn/tzfpy \
  --package tzfpy \
  --min-tag v0.6.0 \
  --csv docs/release_wheels.csv \
  --full-fetch \
  --output site
```
