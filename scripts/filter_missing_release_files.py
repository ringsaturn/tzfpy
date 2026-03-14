#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_release_assets(repository: str, tag: str, token: str) -> set[str]:
    encoded_tag = urllib.parse.quote(tag, safe="")
    url = f"https://api.github.com/repos/{repository}/releases/tags/{encoded_tag}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(
                f"Release not found for repository={repository}, tag={tag}"
            ) from exc
        raise RuntimeError(f"Failed to fetch release info: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch release info: {exc.reason}") from exc

    assets = payload.get("assets") or []
    return {
        str(asset.get("name") or "").strip() for asset in assets if asset.get("name")
    }


def read_files_list(path: Path) -> list[Path]:
    files: list[Path] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        item = raw.strip()
        if not item:
            continue
        file_path = Path(item)
        if not file_path.exists():
            raise RuntimeError(f"File not found: {file_path.as_posix()}")
        files.append(file_path)
    if not files:
        raise RuntimeError("No files provided for filtering.")
    return files


def select_missing_files(
    files: list[Path], asset_names: set[str]
) -> tuple[list[Path], list[Path]]:
    missing: list[Path] = []
    existing: list[Path] = []
    for file_path in files:
        filename = file_path.name
        if filename in asset_names:
            existing.append(file_path)
            continue
        missing.append(file_path)
    return missing, existing


def write_github_output(path: str, missing_files: list[Path]) -> None:
    with open(path, "a", encoding="utf-8") as output:
        output.write(f"missing_count={len(missing_files)}\n")
        output.write("missing_files<<EOF\n")
        for file_path in missing_files:
            output.write(f"{file_path.as_posix()}\n")
        output.write("EOF\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter files that are missing in a GitHub release."
    )
    parser.add_argument("--repository", required=True, help="owner/repo")
    parser.add_argument("--tag", required=True, help="release tag")
    parser.add_argument(
        "--files-file", required=True, help="newline-separated file list"
    )
    parser.add_argument(
        "--github-output",
        default="",
        help="Path to GitHub Actions output file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GH_TOKEN is required.")

    files = read_files_list(Path(args.files_file))
    asset_names = fetch_release_assets(
        repository=args.repository,
        tag=args.tag,
        token=token,
    )
    missing, existing = select_missing_files(files=files, asset_names=asset_names)

    print(f"Existing files on release ({len(existing)}):")
    for file_path in existing:
        print(f"- skip {file_path.name}")

    print(f"Missing files to upload ({len(missing)}):")
    for file_path in missing:
        print(f"- upload {file_path.name}")

    if args.github_output:
        write_github_output(args.github_output, missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
