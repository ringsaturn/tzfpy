#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
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


def load_downloads(path: Path) -> dict[str, int]:
    data: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            data[row["filename"]] = int(row["downloads_30d"])
    return data


def parse_filename(filename: str) -> tuple[str, str, str, str, str]:
    if filename.endswith(".whl"):
        base = filename[:-4]
        parts = base.split("-")
        python_tag = ""
        abi_tag = ""
        platform_tag = ""
        if len(parts) >= 5:
            python_tag = parts[-3]
            abi_tag = parts[-2]
            platform_tag = parts[-1]
        file_type = "whl"
        platform_family = classify_platform(platform_tag)
        return file_type, python_tag, abi_tag, platform_tag, platform_family

    if filename.endswith(".tar.gz"):
        return "sdist", "", "", "source", "source"

    if filename.endswith(".whl.metadata"):
        base = filename[: -len(".metadata")]
        file_type, python_tag, abi_tag, platform_tag, platform_family = parse_filename(base)
        return "whl_metadata", python_tag, abi_tag, platform_tag, platform_family

    return "other", "", "", "", "other"


def classify_platform(platform_tag: str) -> str:
    tag = platform_tag.lower()
    if not tag:
        return "unknown"
    if "win" in tag:
        return "windows"
    if "macosx" in tag:
        return "macos"
    if "manylinux" in tag or "linux" in tag or "musllinux" in tag:
        return "linux"
    if tag == "any":
        return "any"
    if tag == "source":
        return "source"
    return "other"


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Build one ranked cleanup list from current input CSV files."
    )
    parser.add_argument(
        "--pypi-files",
        default=str(root / "pypi_all_files.csv"),
        help="Path to full PyPI file list CSV.",
    )
    parser.add_argument(
        "--downloads-all",
        default=str(root / "script_job_5c3854808754dd3102806a757c45cf6f_0.csv"),
        help="Path to 30d all-installer download CSV.",
    )
    parser.add_argument(
        "--downloads-pip",
        default=str(root / "script_job_6a7f35f7e60dc30855f818b6187f836a_0.csv"),
        help="Path to 30d pip download CSV.",
    )
    parser.add_argument(
        "--downloads-uv",
        default=str(root / "script_job_b7dcfb358f517da711bbf729a784c521_0.csv"),
        help="Path to 30d uv download CSV.",
    )
    parser.add_argument(
        "--output",
        default=str(root / "cleanup_ranked_list.csv"),
        help="Output ranked list CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pypi_files_path = Path(args.pypi_files)
    downloads_all = load_downloads(Path(args.downloads_all))
    downloads_pip = load_downloads(Path(args.downloads_pip))
    downloads_uv = load_downloads(Path(args.downloads_uv))

    records: list[dict[str, object]] = []
    with pypi_files_path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            filename = row["filename"]
            version = row["version"]
            file_type, python_tag, abi_tag, platform_tag, platform_family = parse_filename(filename)

            d_all = downloads_all.get(filename, 0)
            d_pip = downloads_pip.get(filename, 0)
            d_uv = downloads_uv.get(filename, 0)
            d_other = d_all - d_pip - d_uv

            records.append(
                {
                    "version": version,
                    "filename": filename,
                    "file_type": file_type,
                    "packagetype": row.get("packagetype", ""),
                    "size_bytes": int(row.get("size_bytes") or 0),
                    "size_mb": f"{(int(row.get('size_bytes') or 0) / (1024 * 1024)):.3f}",
                    "platform_family": platform_family,
                    "platform_tag": platform_tag,
                    "python_tag": python_tag,
                    "abi_tag": abi_tag,
                    "yanked": row.get("yanked", ""),
                    "upload_time_iso_8601": row.get("upload_time_iso_8601", ""),
                    "downloads_all_30d": d_all,
                    "downloads_pip_30d": d_pip,
                    "downloads_uv_30d": d_uv,
                    "downloads_other_30d": d_other,
                }
            )

    records.sort(
        key=lambda r: (
            r["downloads_all_30d"],
            r["downloads_pip_30d"],
            r["downloads_uv_30d"],
            version_sort_key(str(r["version"])),
            str(r["filename"]),
        )
    )

    for idx, row in enumerate(records, start=1):
        row["rank_cleanup"] = idx

    output_path = Path(args.output)
    fieldnames = [
        "rank_cleanup",
        "version",
        "filename",
        "file_type",
        "packagetype",
        "size_bytes",
        "size_mb",
        "platform_family",
        "platform_tag",
        "python_tag",
        "abi_tag",
        "yanked",
        "upload_time_iso_8601",
        "downloads_all_30d",
        "downloads_pip_30d",
        "downloads_uv_30d",
        "downloads_other_30d",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print("Ranked list generated.")
    print(f"records={len(records)}")
    print(f"output={output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
