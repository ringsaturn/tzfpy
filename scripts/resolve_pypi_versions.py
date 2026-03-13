#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request

PRERELEASE_RE = re.compile(
    r"(?i)(?:^|[._-])(a|b|rc|alpha|beta|dev|pre|preview)\d*(?:$|[._-])"
)


def split_versions(raw: str) -> list[str]:
    return [item for item in re.split(r"[,\s]+", raw.strip()) if item]


def unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items


def all_yanked(files: list[dict]) -> bool:
    return bool(files) and all(bool(item.get("yanked")) for item in files)


def is_prerelease(version: str) -> bool:
    return bool(PRERELEASE_RE.search(version))


def sort_key(version: str) -> list[tuple[int, object]]:
    key: list[tuple[int, object]] = []
    for part in re.split(r"([0-9]+)", version):
        if not part:
            continue
        if part.isdigit():
            key.append((0, int(part)))
            continue
        key.append((1, part.lower()))
    return key


def fetch_pypi_metadata(package: str) -> dict:
    metadata_url = f"https://pypi.org/pypi/{urllib.parse.quote(package)}/json"
    try:
        with urllib.request.urlopen(metadata_url, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"PyPI package not found: {package}") from exc
        raise RuntimeError(f"Failed to fetch PyPI metadata: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch PyPI metadata: {exc.reason}") from exc


def resolve_versions(
    package: str, raw_versions: str, include_prerelease: bool
) -> list[str]:
    payload = fetch_pypi_metadata(package)
    releases = payload.get("releases") or {}
    if not releases:
        raise RuntimeError(f"No releases found on PyPI for package: {package}")

    available_releases: dict[str, list[dict]] = {}
    for version, files in releases.items():
        files = files or []
        if not files:
            continue
        if all_yanked(files):
            continue
        available_releases[version] = files

    if not available_releases:
        raise RuntimeError(
            f"No non-yanked releases with files found on PyPI for package: {package}"
        )

    if raw_versions.strip():
        requested_versions = unique_keep_order(split_versions(raw_versions))
        missing_versions = [
            version for version in requested_versions if version not in releases
        ]
        if missing_versions:
            missing = ", ".join(missing_versions)
            raise RuntimeError(
                f"Versions not found on PyPI for package {package}: {missing}"
            )

        invalid_versions: list[str] = []
        selected_versions: list[str] = []
        for version in requested_versions:
            files = releases.get(version) or []
            if not files:
                invalid_versions.append(f"{version} (no files)")
                continue
            if all_yanked(files):
                invalid_versions.append(f"{version} (all files yanked)")
                continue
            selected_versions.append(version)

        if invalid_versions:
            details = ", ".join(invalid_versions)
            raise RuntimeError(f"Requested versions are not syncable: {details}")
    else:
        selected_versions = sorted(available_releases.keys(), key=sort_key)
        if not include_prerelease:
            selected_versions = [
                version for version in selected_versions if not is_prerelease(version)
            ]

    if not selected_versions:
        raise RuntimeError("No versions selected for syncing.")

    return selected_versions


def write_github_output(path: str, versions: list[str]) -> None:
    versions_json = json.dumps(versions, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as file:
        file.write(f"count={len(versions)}\n")
        file.write(f"versions_json={versions_json}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve syncable versions from PyPI metadata."
    )
    parser.add_argument(
        "--package",
        required=True,
        help="PyPI package name.",
    )
    parser.add_argument(
        "--versions",
        default="",
        help="Version list separated by comma, space, or newline.",
    )
    parser.add_argument(
        "--include-prerelease",
        action="store_true",
        help="Include pre-release versions when --versions is empty.",
    )
    parser.add_argument(
        "--github-output",
        default="",
        help="Path to GitHub Actions output file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    versions = resolve_versions(
        package=args.package,
        raw_versions=args.versions,
        include_prerelease=args.include_prerelease,
    )

    print("Selected versions:")
    for version in versions:
        print(f"- {version}")

    if args.github_output:
        write_github_output(args.github_output, versions)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
