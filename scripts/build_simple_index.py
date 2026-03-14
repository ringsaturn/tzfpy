#!/usr/bin/env python3
"""Build a PEP 503 simple index from GitHub Release distribution assets."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from datetime import datetime, timezone

CSV_FIELDNAMES = [
    "key",
    "release_tag",
    "release_published_at",
    "release_commit_at",
    "release_prerelease",
    "asset_id",
    "asset_name",
    "asset_url",
    "asset_updated_at",
    "asset_digest",
    "uploader_login",
]

SUPPORTED_DIST_SUFFIXES = (".whl", ".tar.gz")
RELEASE_TAG_PATTERN = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:(?:-?(?P<stage>alpha|beta|rc)[\.-]?(?P<stage_num>\d*)?)?)?$",
    re.IGNORECASE,
)
RELEASE_STAGE_RANK = {"alpha": 0, "beta": 1, "rc": 2, "": 3}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text == "None":
        return ""
    return text


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def is_supported_distribution_file(filename: str) -> bool:
    return filename.endswith(SUPPORTED_DIST_SUFFIXES)


def parse_release_tag_key(tag: str) -> tuple[int, int, int, int, int] | None:
    tag_text = clean_text(tag)
    if not tag_text:
        return None
    match = RELEASE_TAG_PATTERN.fullmatch(tag_text)
    if not match:
        return None

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    stage = clean_text(match.group("stage")).lower()
    stage_rank = RELEASE_STAGE_RANK.get(stage, -1)
    if stage_rank < 0:
        return None
    stage_num_text = clean_text(match.group("stage_num"))
    stage_num = int(stage_num_text) if stage_num_text else 0
    return (major, minor, patch, stage_rank, stage_num)


def is_release_tag_at_or_after(release_tag: str, min_release_tag: str) -> bool:
    release_key = parse_release_tag_key(release_tag)
    min_key = parse_release_tag_key(min_release_tag)
    if release_key is not None and min_key is not None:
        return release_key >= min_key
    return clean_text(release_tag) >= clean_text(min_release_tag)


@dataclass(frozen=True)
class WheelAsset:
    key: str
    release_tag: str
    release_published_at: str
    release_commit_at: str
    release_prerelease: bool
    asset_id: str
    name: str
    url: str
    updated_at: str
    digest: str
    uploader_login: str

    @property
    def url_with_hash(self) -> str:
        if self.digest.startswith("sha256:"):
            return f"{self.url}#sha256={self.digest.split(':', maxsplit=1)[1]}"
        return self.url

    def is_for_package(self, package_name: str) -> bool:
        dist_name = self.name.split("-", maxsplit=1)[0]
        return normalize_name(dist_name) == normalize_name(package_name)

    def matches_filters(
        self,
        package_name: str,
        min_release_tag: str | None = None,
        uploader_login: str | None = None,
    ) -> bool:
        if not self.is_for_package(package_name):
            return False
        if min_release_tag and not is_release_tag_at_or_after(
            self.release_tag, min_release_tag
        ):
            return False
        if uploader_login and self.uploader_login != uploader_login:
            return False
        return True

    def to_csv_row(self) -> dict[str, str]:
        return {
            "key": self.key,
            "release_tag": self.release_tag,
            "release_published_at": self.release_published_at,
            "release_commit_at": self.release_commit_at,
            "release_prerelease": "true" if self.release_prerelease else "false",
            "asset_id": self.asset_id,
            "asset_name": self.name,
            "asset_url": self.url,
            "asset_updated_at": self.updated_at,
            "asset_digest": self.digest,
            "uploader_login": self.uploader_login,
        }

    @staticmethod
    def from_csv_row(row: dict[str, str]) -> "WheelAsset":
        prerelease_text = clean_text(row.get("release_prerelease", "")).lower()
        release_prerelease = prerelease_text in {"1", "true", "yes"}
        return WheelAsset(
            key=clean_text(row.get("key", "")),
            release_tag=clean_text(row.get("release_tag", "")),
            release_published_at=clean_text(row.get("release_published_at", "")),
            release_commit_at=clean_text(row.get("release_commit_at", "")),
            release_prerelease=release_prerelease,
            asset_id=clean_text(row.get("asset_id", "")),
            name=clean_text(row.get("asset_name", "")),
            url=clean_text(row.get("asset_url", "")),
            updated_at=clean_text(row.get("asset_updated_at", "")),
            digest=clean_text(row.get("asset_digest", "")),
            uploader_login=clean_text(row.get("uploader_login", "")),
        )

    @staticmethod
    def from_release_asset(
        release: dict, asset: dict, release_commit_at: str = ""
    ) -> "WheelAsset":
        asset_id = clean_text(asset.get("id", ""))
        url = clean_text(asset.get("browser_download_url", ""))
        name = clean_text(asset.get("name", ""))
        key = asset_id or url or name

        uploader = asset.get("uploader", {})
        if isinstance(uploader, dict):
            uploader_login = clean_text(uploader.get("login", ""))
        else:
            uploader_login = ""

        return WheelAsset(
            key=key,
            release_tag=clean_text(release.get("tag_name", "")),
            release_published_at=clean_text(release.get("published_at", "")),
            release_commit_at=clean_text(release_commit_at),
            release_prerelease=bool(release.get("prerelease", False)),
            asset_id=asset_id,
            name=name,
            url=url,
            updated_at=clean_text(asset.get("updated_at", "")),
            digest=clean_text(asset.get("digest", "")),
            uploader_login=uploader_login,
        )


def _request_json(url: str, token: str | None) -> dict | list:
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {url}: {message}") from exc


def fetch_release_by_tag(repository: str, tag: str, token: str | None) -> dict:
    encoded_tag = urllib.parse.quote(tag, safe="")
    url = f"https://api.github.com/repos/{repository}/releases/tags/{encoded_tag}"
    payload = _request_json(url, token)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected GitHub API response for {url}: {payload!r}")
    return payload


def normalize_iso8601_utc(timestamp: str) -> str:
    text = clean_text(timestamp)
    if not text:
        return ""
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return clean_text(timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_local_tag_created_at(tag: str) -> str:
    return collect_local_tag_created_at({tag}).get(tag, "")


def collect_local_tag_created_at(tags: set[str]) -> dict[str, str]:
    if not tags:
        return {}

    command = [
        "git",
        "for-each-ref",
        "--format=%(refname:strip=2),%(creatordate:iso8601-strict)",
        "refs/tags",
    ]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {}

    mapped: dict[str, str] = {}
    for line in result.stdout.splitlines():
        row = clean_text(line)
        if not row:
            continue
        parts = row.split(",", maxsplit=1)
        if len(parts) != 2:
            continue
        tag, created_at = parts
        if tag not in tags:
            continue
        normalized = normalize_iso8601_utc(created_at)
        if normalized:
            mapped[tag] = normalized
    return mapped


def resolve_min_published_at(
    repository: str, tag: str, token: str | None
) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    local_tag_created_at = get_local_tag_created_at(tag)
    if local_tag_created_at:
        candidates.append(("local-tag", local_tag_created_at))

    release_lookup_error = ""
    try:
        min_release = fetch_release_by_tag(repository=repository, tag=tag, token=token)
        release_published_at = normalize_iso8601_utc(
            str(min_release.get("published_at", "")).strip()
        )
        if release_published_at:
            candidates.append(("release", release_published_at))
    except RuntimeError as exc:
        release_lookup_error = str(exc)

    if not candidates:
        suffix = (
            f", release lookup failed: {release_lookup_error}"
            if release_lookup_error
            else ""
        )
        raise RuntimeError(f"Unable to resolve min-tag boundary for {tag}{suffix}")

    source, min_published_at = min(candidates, key=lambda item: item[1])
    return min_published_at, source


def fetch_releases(
    repository: str,
    token: str | None,
    stop_before_or_at_published_at: str | None = None,
) -> list[dict]:
    releases: list[dict] = []
    page = 1

    while True:
        params = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = f"https://api.github.com/repos/{repository}/releases?{params}"
        payload = _request_json(url, token)

        if not payload:
            break
        if not isinstance(payload, list):
            raise RuntimeError(f"Unexpected GitHub API response for {url}: {payload!r}")

        releases.extend(payload)

        if stop_before_or_at_published_at:
            reached_boundary = False
            for release in payload:
                published_at = str(release.get("published_at", "")).strip()
                if published_at and published_at <= stop_before_or_at_published_at:
                    reached_boundary = True
                    break
            if reached_boundary:
                break

        page += 1

    return releases


def collect_wheels(
    releases: list[dict],
    package_name: str,
    min_release_tag: str | None = None,
    uploader_login: str | None = None,
    tag_commit_dates: dict[str, str] | None = None,
) -> dict[str, WheelAsset]:
    wheels: dict[str, WheelAsset] = {}
    normalized_tag_commit_dates = tag_commit_dates or {}

    for release in releases:
        if release.get("draft", False):
            continue
        release_tag = clean_text(release.get("tag_name", ""))
        release_commit_at = normalized_tag_commit_dates.get(release_tag, "")
        for asset in release.get("assets", []):
            wheel = WheelAsset.from_release_asset(
                release=release,
                asset=asset,
                release_commit_at=release_commit_at,
            )

            if not is_supported_distribution_file(wheel.name):
                continue
            if not wheel.url:
                continue
            if not wheel.matches_filters(
                package_name=package_name,
                min_release_tag=min_release_tag,
                uploader_login=uploader_login,
            ):
                continue
            wheels[wheel.key] = wheel

    return wheels


def render_html_page(title: str, body_lines: list[str]) -> str:
    body = "\n".join(body_lines)
    escaped_title = html.escape(title)
    return (
        "<!doctype html>\n"
        "<html>\n"
        "  <head>\n"
        '    <meta charset="utf-8" />\n'
        f"    <title>{escaped_title}</title>\n"
        "  </head>\n"
        "  <body>\n"
        f"{body}\n"
        "  </body>\n"
        "</html>\n"
    )


def sort_wheels(wheels: list[WheelAsset]) -> list[WheelAsset]:
    return sorted(
        wheels,
        key=lambda item: (
            item.release_commit_at or item.release_published_at,
            item.release_published_at,
            item.updated_at,
            item.name,
        ),
        reverse=True,
    )


def load_wheels_csv(csv_path: pathlib.Path) -> dict[str, WheelAsset]:
    if not csv_path.exists():
        return {}

    wheels: dict[str, WheelAsset] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wheel = WheelAsset.from_csv_row(dict(row))
            if not wheel.key:
                continue
            wheels[wheel.key] = wheel
    return wheels


def write_wheels_csv(csv_path: pathlib.Path, wheels: list[WheelAsset]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for wheel in sort_wheels(wheels):
            writer.writerow(wheel.to_csv_row())


def write_site(
    output_dir: pathlib.Path,
    package_name: str,
    wheels: list[WheelAsset],
    csv_name: str,
) -> None:
    normalized_package = normalize_name(package_name)
    simple_dir = output_dir / "simple"
    package_dir = simple_dir / normalized_package
    package_dir.mkdir(parents=True, exist_ok=True)

    sorted_wheels = sort_wheels(wheels)

    package_body: list[str] = []
    for wheel in sorted_wheels:
        href = html.escape(wheel.url_with_hash, quote=True)
        display_name = html.escape(wheel.name)
        package_body.append(f'    <a href="{href}">{display_name}</a><br />')

    if not package_body:
        package_body.append("    <p>No wheel assets found.</p>")

    package_index = render_html_page(
        title=f"Simple index for {package_name}",
        body_lines=package_body,
    )
    (package_dir / "index.html").write_text(package_index, encoding="utf-8")

    simple_index = render_html_page(
        title="Simple index",
        body_lines=[
            f'    <a href="{html.escape(normalized_package)}/">{html.escape(normalized_package)}</a>'
        ],
    )
    (simple_dir / "index.html").write_text(simple_index, encoding="utf-8")

    site_index = render_html_page(
        title="Package index",
        body_lines=[
            '    <a href="simple/">simple/</a><br />',
            f'    <a href="docs/{html.escape(csv_name)}">docs/{html.escape(csv_name)}</a>',
        ],
    )
    (output_dir / "index.html").write_text(site_index, encoding="utf-8")

    docs_dir = output_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    write_wheels_csv(docs_dir / csv_name, sorted_wheels)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        required=True,
        help="GitHub repository in owner/repo format, for example ringsaturn/tzfpy.",
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Package name used in distribution filenames, for example tzfpy.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for generated static files.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="GitHub token for higher API rate limit. Defaults to GITHUB_TOKEN env var.",
    )
    parser.add_argument(
        "--min-tag",
        default="",
        help=(
            "Only include distribution files from releases at or after this release "
            "tag version, for example v1.0.0."
        ),
    )
    parser.add_argument(
        "--uploader-login",
        default="",
        help="If set, only include distribution assets uploaded by this GitHub login.",
    )
    parser.add_argument(
        "--csv",
        default="",
        help="Optional CSV file path for raw distribution metadata cache.",
    )
    parser.add_argument(
        "--csv-name",
        default="release_wheels.csv",
        help="CSV filename written under <output>/docs/.",
    )
    parser.add_argument(
        "--full-fetch",
        action="store_true",
        help="Fetch all release pages instead of incremental fetch based on CSV cache.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = pathlib.Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = pathlib.Path(args.csv).resolve() if args.csv else None
    existing_wheels: dict[str, WheelAsset] = {}
    if csv_path:
        existing_wheels = load_wheels_csv(csv_path)

    min_release_tag = clean_text(args.min_tag) or None

    latest_cached_published_at = ""
    if existing_wheels:
        latest_cached_published_at = max(
            (
                wheel.release_published_at
                for wheel in existing_wheels.values()
                if wheel.release_published_at
            ),
            default="",
        )

    incremental_boundary = ""
    if not args.full_fetch and latest_cached_published_at:
        incremental_boundary = latest_cached_published_at

    releases = fetch_releases(
        repository=args.repository,
        token=args.token or None,
        stop_before_or_at_published_at=incremental_boundary or None,
    )

    release_tags = {
        clean_text(release.get("tag_name", ""))
        for release in releases
        if clean_text(release.get("tag_name", ""))
    }
    release_tags.update(
        wheel.release_tag for wheel in existing_wheels.values() if wheel.release_tag
    )
    tag_commit_dates = collect_local_tag_created_at(release_tags)

    fetched_wheels = collect_wheels(
        releases=releases,
        package_name=args.package,
        min_release_tag=min_release_tag,
        uploader_login=args.uploader_login or None,
        tag_commit_dates=tag_commit_dates,
    )

    merged_wheels: dict[str, WheelAsset] = {}
    for key, wheel in existing_wheels.items():
        release_commit_at = wheel.release_commit_at or tag_commit_dates.get(
            wheel.release_tag, ""
        )
        if release_commit_at == wheel.release_commit_at:
            merged_wheels[key] = wheel
            continue
        merged_wheels[key] = replace(wheel, release_commit_at=release_commit_at)

    merged_wheels.update(fetched_wheels)

    filtered_wheels = [
        wheel
        for wheel in merged_wheels.values()
        if wheel.matches_filters(
            package_name=args.package,
            min_release_tag=min_release_tag,
            uploader_login=args.uploader_login or None,
        )
    ]

    if csv_path:
        write_wheels_csv(csv_path, filtered_wheels)

    write_site(
        output_dir=output_dir,
        package_name=args.package,
        wheels=filtered_wheels,
        csv_name=args.csv_name,
    )

    print(f"Generated index for {args.package} in {output_dir}")
    print(f"Releases fetched this run: {len(releases)}")
    print(f"Cached assets loaded: {len(existing_wheels)}")
    print(f"New assets fetched this run: {len(fetched_wheels)}")
    if min_release_tag:
        print(f"Minimum release tag: {min_release_tag}")
    if args.uploader_login:
        print(f"Uploader filter: {args.uploader_login}")
    if incremental_boundary:
        print(f"Incremental boundary: {incremental_boundary}")
    print(f"Distribution files indexed: {len(filtered_wheels)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
