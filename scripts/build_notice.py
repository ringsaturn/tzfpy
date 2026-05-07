#!/usr/bin/env python3
"""Build a compact NOTICE file from cargo-bundle-licenses YAML output."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


PACKAGE_RE = re.compile(r"^- package_name: (?P<value>.+)$")
FIELD_RE = re.compile(r"^  (?P<key>package_version|repository|license): (?P<value>.*)$")


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value


def normalize_project(package_name: str, repository: str | None) -> str:
    repo = normalize_repository(repository)
    if repo:
        return f"{package_name} ({repo})"
    return package_name


def normalize_repository(repository: str | None) -> str:
    if not repository:
        return ""

    parsed = urlparse(repository)
    if parsed.netloc and parsed.path:
        repo = f"{parsed.netloc}{parsed.path}"
    else:
        repo = repository

    return (
        repo.removeprefix("git+")
        .removeprefix("https://")
        .removeprefix("http://")
        .removesuffix(".git")
        .rstrip("/")
    )


def infer_author(repository: str | None) -> str:
    repo = normalize_repository(repository)
    parts = repo.split("/")
    if len(parts) >= 2 and parts[0] in {"github.com", "gitlab.com"}:
        return f"Author: {parts[1]}"
    return "Author: unknown"


def has_copyright_holder(value: str) -> bool:
    holder = re.sub(r"^Copyright\s*(?:\(c\))?\s*", "", value)
    holder = re.sub(r"^\d{4}(?:-\d{4})?\s*", "", holder).strip()
    return bool(holder)


def format_author(package: dict[str, object]) -> str:
    copyrights = package.get("copyrights")
    fallback_author = infer_author(package.get("repository"))
    if not copyrights:
        return fallback_author

    copyright_text = "; ".join(str(item) for item in copyrights)
    if any(has_copyright_holder(str(item)) for item in copyrights):
        return copyright_text
    return f"{copyright_text}; {fallback_author}"


def normalize_product_source(cargo_toml: Path) -> str:
    if tomllib is not None:
        package = tomllib.loads(cargo_toml.read_text(encoding="utf-8")).get(
            "package", {}
        )
        source = (
            package.get("repository") or package.get("homepage") or package.get("name")
        )
        if source:
            return clean_product_source(str(source))

    text = cargo_toml.read_text(encoding="utf-8")
    for key in ("repository", "homepage", "name"):
        match = re.search(rf'(?m)^{key}\s*=\s*"([^"]+)"', text)
        if match:
            return clean_product_source(match.group(1))
    return cargo_toml.parent.name


def clean_product_source(value: str) -> str:
    parsed = urlparse(value)
    if parsed.netloc and parsed.path:
        return f"{parsed.netloc}{parsed.path}".removesuffix(".git").rstrip("/")
    return value.removesuffix(".git").rstrip("/")


def parse_thirdparty(path: Path) -> list[dict[str, object]]:
    packages: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        package_match = PACKAGE_RE.match(line)
        if package_match:
            if current is not None:
                packages.append(current)
            current = {
                "package_name": clean_scalar(package_match.group("value")),
                "copyrights": [],
            }
            continue

        if current is None:
            continue

        field_match = FIELD_RE.match(line)
        if field_match:
            current[field_match.group("key")] = clean_scalar(field_match.group("value"))
            continue

        stripped = line.strip()
        if stripped.startswith("Copyright") and not is_copyright_template(stripped):
            copyright_text = " ".join(stripped.split()).rstrip(".")
            copyrights = current["copyrights"]
            if copyright_text not in copyrights:
                copyrights.append(copyright_text)

    if current is not None:
        packages.append(current)

    return packages


def is_copyright_template(value: str) -> bool:
    return any(
        token in value for token in ("{yyyy}", "[yyyy]", "name of copyright owner")
    )


# Packages whose declared license in THIRDPARTY.yml is incorrect and must be
# overridden here.  The value is the true SPDX expression for the *code*.
LICENSE_OVERRIDES: dict[str, str] = {
    # tzf-dist / tzf-rel ship Rust code under MIT; the bundled geodata is
    # ODbL-1.0.  cargo-bundle-licenses picks up the ODbL from the data files,
    # so we correct the code license here and append a separate data entry below.
    "tzf-dist": "MIT",
    "tzf-rel": "MIT",
}

# Packages that also distribute data under a separate license.
# Each entry maps package_name -> (data label, data SPDX expression).
DATA_LICENSE_ENTRIES: dict[str, tuple[str, str]] = {
    "tzf-dist": ("data", "ODbL-1.0"),
    "tzf-rel": ("data", "ODbL-1.0"),
}


def build_notice(product_source: str, packages: list[dict[str, object]]) -> str:
    lines = [
        "NOTICE",
        "",
        f"This product includes software developed by [{product_source}].",
        "-" * 72,
    ]

    for package in packages:
        package_name = str(package.get("package_name", "")).strip()
        if not package_name:
            continue

        project = normalize_project(package_name, package.get("repository"))
        license_name = LICENSE_OVERRIDES.get(
            package_name,
            str(package.get("license", "UNKNOWN")).strip() or "UNKNOWN",
        )
        author = format_author(package)

        lines.append("")
        lines.append(project)
        lines.append(f"License: {license_name}")
        lines.append(author)

        if package_name in DATA_LICENSE_ENTRIES:
            label, data_license = DATA_LICENSE_ENTRIES[package_name]
            lines.append("")
            lines.append(f"{project} ({label})")
            lines.append(f"License: {data_license}")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thirdparty", default="THIRDPARTY.yml")
    parser.add_argument("--cargo-toml", default="Cargo.toml")
    parser.add_argument("--output", default="NOTICE")
    args = parser.parse_args()

    thirdparty_path = Path(args.thirdparty)
    cargo_toml_path = Path(args.cargo_toml)
    output_path = Path(args.output)

    product_source = normalize_product_source(cargo_toml_path)
    packages = parse_thirdparty(thirdparty_path)
    output_path.write_text(build_notice(product_source, packages), encoding="utf-8")


if __name__ == "__main__":
    main()
