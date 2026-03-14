#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

IGNORED_INSTALLERS = {"browser", "unknown"}


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
    if not path.exists():
        return data
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            data[row["filename"]] = int(row["downloads_30d"])
    return data


def load_installer_downloads(path: Path) -> dict[str, dict[str, int]]:
    data: dict[str, dict[str, int]] = {}
    if not path.exists():
        return data

    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            filename = row["filename"]
            installer = row.get("installer", "") or "unknown"
            downloads = int(row["downloads_30d"])
            if filename not in data:
                data[filename] = {}
            data[filename][installer] = data[filename].get(installer, 0) + downloads
    return data


def aggregate_from_installer_downloads(
    downloads_by_installer: dict[str, dict[str, int]],
) -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    downloads_all: dict[str, int] = {}
    downloads_pip: dict[str, int] = {}
    downloads_uv: dict[str, int] = {}
    downloads_excluded_browser: dict[str, int] = {}
    downloads_excluded_unknown: dict[str, int] = {}

    for filename, installer_map in downloads_by_installer.items():
        filtered = {
            name: value
            for name, value in installer_map.items()
            if name.lower() not in IGNORED_INSTALLERS
        }
        downloads_all[filename] = sum(filtered.values())
        downloads_pip[filename] = filtered.get("pip", 0)
        downloads_uv[filename] = filtered.get("uv", 0)
        downloads_excluded_browser[filename] = sum(
            value for name, value in installer_map.items() if name.lower() == "browser"
        )
        downloads_excluded_unknown[filename] = sum(
            value for name, value in installer_map.items() if name.lower() == "unknown"
        )

    return (
        downloads_all,
        downloads_pip,
        downloads_uv,
        downloads_excluded_browser,
        downloads_excluded_unknown,
    )


def detect_installer_file(root: Path) -> Path | None:
    for path in sorted(root.glob("script_job_*.csv")):
        with path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames or []
        required = {"installer", "version", "filename", "downloads_30d"}
        if required.issubset(set(fieldnames)):
            return path
    return None


def installer_col_name(installer: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", installer.lower()).strip("_")
    if not normalized:
        normalized = "unknown"
    return f"downloads_installer_{normalized}_30d"


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
        help="Path to 30d all-installer download CSV, legacy fallback.",
    )
    parser.add_argument(
        "--downloads-pip",
        default=str(root / "script_job_6a7f35f7e60dc30855f818b6187f836a_0.csv"),
        help="Path to 30d pip download CSV, legacy fallback.",
    )
    parser.add_argument(
        "--downloads-uv",
        default=str(root / "script_job_b7dcfb358f517da711bbf729a784c521_0.csv"),
        help="Path to 30d uv download CSV, legacy fallback.",
    )
    parser.add_argument(
        "--output",
        default=str(root / "cleanup_ranked_list.csv"),
        help="Output ranked list CSV.",
    )
    parser.add_argument(
        "--downloads-installer-file",
        default="",
        help="Path to installer+file download CSV generated by installer_file_stats.sql.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pypi_files_path = Path(args.pypi_files)
    downloads_all: dict[str, int]
    downloads_pip: dict[str, int]
    downloads_uv: dict[str, int]
    downloads_excluded_browser: dict[str, int]
    downloads_excluded_unknown: dict[str, int]
    installer_file = (
        Path(args.downloads_installer_file)
        if args.downloads_installer_file
        else detect_installer_file(pypi_files_path.parent)
    )
    downloads_by_installer = (
        load_installer_downloads(installer_file) if installer_file else {}
    )

    if downloads_by_installer:
        (
            downloads_all,
            downloads_pip,
            downloads_uv,
            downloads_excluded_browser,
            downloads_excluded_unknown,
        ) = aggregate_from_installer_downloads(downloads_by_installer)
    else:
        downloads_all = load_downloads(Path(args.downloads_all))
        downloads_pip = load_downloads(Path(args.downloads_pip))
        downloads_uv = load_downloads(Path(args.downloads_uv))
        downloads_excluded_browser = {}
        downloads_excluded_unknown = {}

    installer_names: list[str] = sorted(
        {
            installer
            for installer_map in downloads_by_installer.values()
            for installer in installer_map
            if installer.lower() not in IGNORED_INSTALLERS
        }
    )
    installer_columns = [installer_col_name(installer) for installer in installer_names]
    installer_name_to_col = {
        installer: installer_col_name(installer) for installer in installer_names
    }

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
            excluded_browser = downloads_excluded_browser.get(filename, 0)
            excluded_unknown = downloads_excluded_unknown.get(filename, 0)
            installer_map = downloads_by_installer.get(filename, {})
            if installer_map:
                filtered_installer_map = {
                    name: value
                    for name, value in installer_map.items()
                    if name.lower() not in IGNORED_INSTALLERS
                }
                d_pip = filtered_installer_map.get("pip", d_pip)
                d_uv = filtered_installer_map.get("uv", d_uv)
                d_other = d_all - d_pip - d_uv
                if filtered_installer_map:
                    top_installer, top_installer_downloads = max(
                        filtered_installer_map.items(), key=lambda item: item[1]
                    )
                else:
                    top_installer = ""
                    top_installer_downloads = 0
            else:
                filtered_installer_map = {}
                top_installer = ""
                top_installer_downloads = 0

            record: dict[str, object] = {
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
                "downloads_excluded_browser_30d": excluded_browser,
                "downloads_excluded_unknown_30d": excluded_unknown,
                "downloads_top_installer": top_installer,
                "downloads_top_installer_30d": top_installer_downloads,
            }
            for installer, col in installer_name_to_col.items():
                record[col] = filtered_installer_map.get(installer, 0)
            records.append(record)

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
        "downloads_excluded_browser_30d",
        "downloads_excluded_unknown_30d",
        "downloads_top_installer",
        "downloads_top_installer_30d",
    ]
    fieldnames.extend(installer_columns)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print("Ranked list generated.")
    print(f"records={len(records)}")
    print(f"installer_file={installer_file.as_posix() if installer_file else ''}")
    print(f"installers={','.join(installer_names)}")
    print(f"output={output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
