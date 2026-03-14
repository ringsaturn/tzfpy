#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

MIRROR_COLUMNS = (
    "downloads_installer_nexus_30d",
    "downloads_installer_bandersnatch_30d",
    "downloads_installer_devpi_30d",
)

CLI_COLUMNS = (
    "downloads_installer_pip_30d",
    "downloads_installer_uv_30d",
    "downloads_installer_poetry_30d",
    "downloads_installer_requests_30d",
)


def version_sort_key(version: str) -> list[tuple[int, object]]:
    key: list[tuple[int, object]] = []
    for part in re.split(r"([0-9]+)", version):
        if not part:
            continue
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part.lower()))
    return key


def int_field(row: dict[str, str], name: str) -> int:
    raw = (row.get(name, "") or "").strip()
    if not raw:
        return 0
    return int(raw)


def float_field(row: dict[str, str], name: str) -> float:
    raw = (row.get(name, "") or "").strip()
    if not raw:
        return 0.0
    return float(raw)


def is_deletable(row: dict[str, str]) -> bool:
    mirror = sum(int_field(row, col) for col in MIRROR_COLUMNS)
    cli = sum(int_field(row, col) for col in CLI_COLUMNS)
    return mirror > 0 and cli == 0


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Generate deletable file lists from cleanup_ranked_list.csv."
    )
    parser.add_argument(
        "--input",
        default=str(root / "cleanup_ranked_list.csv"),
        help="Input cleanup ranked CSV.",
    )
    parser.add_argument(
        "--output-files",
        default=str(root / "deletable_files_by_version.csv"),
        help="Output file-level deletable CSV.",
    )
    parser.add_argument(
        "--output-summary",
        default=str(root / "deletable_versions_summary.csv"),
        help="Output version summary CSV.",
    )
    parser.add_argument(
        "--output-todo",
        default=str(root / "deletable_files_todo_by_version.md"),
        help="Output markdown TODO file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_files = Path(args.output_files)
    output_summary = Path(args.output_summary)
    output_todo = Path(args.output_todo)

    with input_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    deletable = [row for row in rows if is_deletable(row)]
    deletable.sort(
        key=lambda row: (
            version_sort_key(row["version"]),
            int_field(row, "rank_cleanup"),
        )
    )

    file_columns = [
        "version",
        "rank_cleanup",
        "filename",
        "size_bytes",
        "size_mb",
        "downloads_all_30d",
        "downloads_installer_nexus_30d",
        "downloads_installer_bandersnatch_30d",
        "downloads_installer_devpi_30d",
        "downloads_installer_browser_30d",
        "downloads_installer_unknown_30d",
        "downloads_installer_pip_30d",
        "downloads_installer_uv_30d",
        "downloads_installer_poetry_30d",
        "downloads_installer_requests_30d",
    ]

    output_files.parent.mkdir(parents=True, exist_ok=True)
    with output_files.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=file_columns)
        writer.writeheader()
        for row in deletable:
            writer.writerow({name: row.get(name, "") for name in file_columns})

    by_version: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in deletable:
        by_version[row["version"]].append(row)

    summary_rows: list[dict[str, str | int]] = []
    for version, version_rows in by_version.items():
        total_bytes = sum(int_field(row, "size_bytes") for row in version_rows)
        total_mb = sum(float_field(row, "size_mb") for row in version_rows)
        summary_rows.append(
            {
                "version": version,
                "file_count": len(version_rows),
                "total_size_bytes": total_bytes,
                "total_size_mb": f"{total_mb:.3f}",
            }
        )
    summary_rows.sort(key=lambda row: version_sort_key(str(row["version"])))

    with output_summary.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["version", "file_count", "total_size_bytes", "total_size_mb"]
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    todo_lines: list[str] = [
        "# PyPI Cleanup TODO by Version",
        "",
        f"Generated on: {date.today().isoformat()}",
        "",
        "Rule: nexus+bandersnatch+devpi > 0 and pip+uv+poetry+requests = 0",
        "",
        f"Total candidate files: {len(deletable)}",
        f"Total candidate size: {sum(float_field(row, 'size_mb') for row in deletable):.3f} MB",
        "",
    ]

    for summary in summary_rows:
        version = str(summary["version"])
        version_rows = sorted(
            by_version[version], key=lambda row: int_field(row, "rank_cleanup")
        )
        todo_lines.append(
            f"## {version} ({summary['file_count']} files, {summary['total_size_mb']} MB)"
        )
        todo_lines.append("")
        for row in version_rows:
            todo_lines.append(
                "- [ ] "
                f"`{row['filename']}`, rank={int_field(row, 'rank_cleanup')}, "
                f"size={float_field(row, 'size_mb'):.3f} MB, "
                f"downloads_all_30d={int_field(row, 'downloads_all_30d')}, "
                f"nexus={int_field(row, 'downloads_installer_nexus_30d')}, "
                f"bandersnatch={int_field(row, 'downloads_installer_bandersnatch_30d')}, "
                f"devpi={int_field(row, 'downloads_installer_devpi_30d')}"
            )
        todo_lines.append("")

    output_todo.write_text("\n".join(todo_lines), encoding="utf-8")

    print(f"input={input_path}")
    print(f"output_files={output_files}")
    print(f"output_summary={output_summary}")
    print(f"output_todo={output_todo}")
    print(f"deletable_files={len(deletable)}")
    print(f"deletable_versions={len(summary_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
