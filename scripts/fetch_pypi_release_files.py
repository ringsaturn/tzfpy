#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


def fetch_release_metadata(package: str, version: str) -> dict:
    url = (
        f"https://pypi.org/pypi/{urllib.parse.quote(package)}/"
        f"{urllib.parse.quote(version)}/json"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(
                f"PyPI release not found for package={package}, version={version}"
            ) from exc
        raise RuntimeError(
            f"Failed to fetch release metadata: HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch release metadata: {exc.reason}") from exc


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download_files(package: str, version: str, output_dir: Path) -> list[Path]:
    payload = fetch_release_metadata(package=package, version=version)
    urls = payload.get("urls") or []
    if not urls:
        raise RuntimeError(
            f"No files found on PyPI for package={package}, version={version}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files: list[Path] = []

    for item in urls:
        file_url = str(item.get("url") or "").strip()
        filename = str(item.get("filename") or "").strip()
        expected_sha256 = str((item.get("digests") or {}).get("sha256") or "").strip()
        if not file_url or not filename:
            continue

        destination = output_dir / filename
        with urllib.request.urlopen(file_url, timeout=120) as response:
            data = response.read()
        destination.write_bytes(data)

        if expected_sha256:
            actual_sha256 = sha256sum(destination)
            if actual_sha256 != expected_sha256:
                raise RuntimeError(
                    f"Checksum mismatch for {filename}, expected {expected_sha256}, got {actual_sha256}"
                )

        downloaded_files.append(destination)

    if not downloaded_files:
        raise RuntimeError(
            f"No downloadable files found on PyPI for package={package}, version={version}"
        )
    return downloaded_files


def write_github_output(path: str, files: list[Path]) -> None:
    with open(path, "a", encoding="utf-8") as output:
        output.write(f"count={len(files)}\n")
        output.write("files<<EOF\n")
        for file_path in files:
            output.write(f"{file_path.as_posix()}\n")
        output.write("EOF\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download all files for a specific package version from PyPI."
    )
    parser.add_argument("--package", required=True, help="PyPI package name.")
    parser.add_argument("--version", required=True, help="Package version.")
    parser.add_argument("--output-dir", required=True, help="Download directory.")
    parser.add_argument(
        "--github-output",
        default="",
        help="Path to GitHub Actions output file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = download_files(
        package=args.package,
        version=args.version,
        output_dir=Path(args.output_dir),
    )

    print("Downloaded files:")
    for file_path in files:
        print(f"- {file_path.as_posix()}")

    if args.github_output:
        write_github_output(args.github_output, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
