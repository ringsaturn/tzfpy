#!/usr/bin/env python3
"""Append a PEP 440 local version label to the crate version in Cargo.toml.

maturin takes the wheel version from Cargo.toml, so tagging the crate version
is how the full-precision variant becomes `X.Y.Z+full`. That label is also what
keeps the variant off PyPI by construction: PyPI rejects local versions.

The rewrite is meant to be transient -- restore Cargo.toml afterwards rather
than committing the tagged version.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

VERSION_PATTERN = re.compile(r'^version = "([^"+]+)"$', re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "label",
        help='Local version label to append, for example "full" for 2.0.0+full.',
    )
    parser.add_argument(
        "--manifest",
        default="Cargo.toml",
        help="Cargo manifest to rewrite in place.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = pathlib.Path(args.manifest)
    text = path.read_text(encoding="utf-8")

    matches = VERSION_PATTERN.findall(text)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one top-level version line in {path}, found {len(matches)}"
        )

    base_version = matches[0]
    tagged_version = f"{base_version}+{args.label}"
    path.write_text(
        VERSION_PATTERN.sub(f'version = "{tagged_version}"', text, count=1),
        encoding="utf-8",
    )
    print(f"{path}: {base_version} -> {tagged_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
