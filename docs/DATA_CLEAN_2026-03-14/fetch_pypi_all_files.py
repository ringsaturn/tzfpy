#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def version_sort_key(version: str) -> list[tuple[int, object]]:
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
    url = f"https://pypi.org/pypi/{urllib.parse.quote(package)}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"PyPI package not found: {package}") from exc
        raise RuntimeError(f"Failed to fetch PyPI metadata: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch PyPI metadata: {exc.reason}") from exc


def flatten_release_files(payload: dict) -> list[dict[str, str]]:
    releases = payload.get("releases") or {}
    records: list[dict[str, str]] = []

    for version in sorted(releases, key=version_sort_key):
        files = releases.get(version) or []
        for index, item in enumerate(files):
            digests = item.get("digests") or {}
            record = {
                "version": version,
                "filename": str(item.get("filename") or ""),
                "packagetype": str(item.get("packagetype") or ""),
                "python_version": str(item.get("python_version") or ""),
                "requires_python": str(item.get("requires_python") or ""),
                "yanked": str(bool(item.get("yanked"))).lower(),
                "yanked_reason": str(item.get("yanked_reason") or ""),
                "size_bytes": str(item.get("size") or ""),
                "upload_time_iso_8601": str(item.get("upload_time_iso_8601") or ""),
                "upload_time": str(item.get("upload_time") or ""),
                "md5_digest": str(item.get("md5_digest") or ""),
                "sha256_digest": str(digests.get("sha256") or ""),
                "blake2b_256_digest": str(digests.get("blake2b_256") or ""),
                "url": str(item.get("url") or ""),
                "comment_text": str(item.get("comment_text") or ""),
                "downloads_field": str(item.get("downloads") or ""),
                "has_sig": str(bool(item.get("has_sig"))).lower(),
                "release_file_index": str(index),
            }
            records.append(record)
    return records


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "version",
        "filename",
        "packagetype",
        "python_version",
        "requires_python",
        "yanked",
        "yanked_reason",
        "size_bytes",
        "upload_time_iso_8601",
        "upload_time",
        "md5_digest",
        "sha256_digest",
        "blake2b_256_digest",
        "url",
        "comment_text",
        "downloads_field",
        "has_sig",
        "release_file_index",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, str]]) -> tuple[int, int, int, int]:
    versions = {row["version"] for row in rows}
    wheel_count = sum(1 for row in rows if row["filename"].endswith(".whl"))
    sdist_count = sum(1 for row in rows if row["filename"].endswith(".tar.gz"))
    return len(versions), len(rows), wheel_count, sdist_count


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Fetch full file list of a PyPI package into CSV."
    )
    parser.add_argument(
        "--package",
        default="tzfpy",
        help="PyPI package name.",
    )
    parser.add_argument(
        "--output",
        default=str(script_dir / "pypi_all_files.csv"),
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = fetch_pypi_metadata(package=args.package)
    rows = flatten_release_files(payload)
    if not rows:
        raise RuntimeError(f"No release files found for package: {args.package}")

    output_path = Path(args.output)
    write_csv(output_path, rows)

    version_count, file_count, wheel_count, sdist_count = summarize(rows)
    print(f"package={args.package}")
    print(f"versions={version_count}")
    print(f"files={file_count}")
    print(f"wheels={wheel_count}")
    print(f"sdists={sdist_count}")
    print(f"output={output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
