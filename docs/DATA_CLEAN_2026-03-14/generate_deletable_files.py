#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

MIRROR_INSTALLERS = {"nexus", "bandersnatch", "devpi"}
IGNORED_INSTALLERS = MIRROR_INSTALLERS | {"browser", "unknown"}
VERSION_EFFECTIVE_DOWNLOADS_THRESHOLD = 10
FILE_EFFECTIVE_DOWNLOADS_THRESHOLD = 10

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


def installer_name_from_col(col_name: str) -> str:
    prefix = "downloads_installer_"
    suffix = "_30d"
    if not col_name.startswith(prefix) or not col_name.endswith(suffix):
        return ""
    return col_name[len(prefix) : -len(suffix)].lower()


def calculate_row_downloads(row: dict[str, str]) -> tuple[int, int, int]:
    installer_columns = [
        name
        for name in row
        if name.startswith("downloads_installer_") and name.endswith("_30d")
    ]
    if installer_columns:
        mirror = 0
        unknown_browser = 0
        effective = 0
        for col in installer_columns:
            installer = installer_name_from_col(col)
            value = int_field(row, col)
            if installer in MIRROR_INSTALLERS:
                mirror += value
            elif installer in IGNORED_INSTALLERS:
                unknown_browser += value
            else:
                effective += value
        return mirror, unknown_browser, effective

    # Legacy fallback when installer breakdown columns are absent.
    mirror = sum(int_field(row, col) for col in MIRROR_COLUMNS)
    unknown_browser = int_field(row, "downloads_installer_browser_30d") + int_field(
        row, "downloads_installer_unknown_30d"
    )
    cli = sum(int_field(row, col) for col in CLI_COLUMNS)
    effective = cli
    if effective == 0:
        effective = max(0, int_field(row, "downloads_all_30d") - mirror)
    return mirror, unknown_browser, effective


def is_file_deletable(row: dict[str, str]) -> bool:
    return (
        int_field(row, "downloads_effective_30d") < FILE_EFFECTIVE_DOWNLOADS_THRESHOLD
    )


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

    rows_by_version: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        enriched = dict(row)
        mirror, unknown_browser, effective = calculate_row_downloads(enriched)
        enriched["downloads_mirror_30d"] = str(mirror)
        enriched["downloads_unknown_browser_30d"] = str(unknown_browser)
        enriched["downloads_effective_30d"] = str(effective)
        rows_by_version[enriched["version"]].append(enriched)

    deletable: list[dict[str, str]] = []
    whole_version_delete_flags: dict[str, bool] = {}
    version_delete_reasons: dict[str, str] = {}
    for version, version_rows in rows_by_version.items():
        version_effective_downloads = sum(
            int_field(row, "downloads_effective_30d") for row in version_rows
        )
        all_files_deletable = all(is_file_deletable(row) for row in version_rows)
        whole_version_delete = (
            version_effective_downloads < VERSION_EFFECTIVE_DOWNLOADS_THRESHOLD
            or all_files_deletable
        )
        whole_version_delete_flags[version] = whole_version_delete
        if version_effective_downloads < VERSION_EFFECTIVE_DOWNLOADS_THRESHOLD:
            reason = "version_effective_downloads_lt_10"
        elif all_files_deletable:
            reason = "all_files_effective_downloads_lt_10"
        else:
            reason = "partial_file_cleanup"
        version_delete_reasons[version] = reason

        for row in version_rows:
            if whole_version_delete or is_file_deletable(row):
                item = dict(row)
                item["whole_version_delete"] = (
                    "true" if whole_version_delete else "false"
                )
                item["delete_reason"] = (
                    reason if whole_version_delete else "file_effective_downloads_lt_10"
                )
                item["version_effective_downloads_30d"] = str(
                    version_effective_downloads
                )
                deletable.append(item)

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
        "downloads_effective_30d",
        "downloads_mirror_30d",
        "downloads_unknown_browser_30d",
        "whole_version_delete",
        "delete_reason",
        "version_effective_downloads_30d",
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
        all_version_rows = rows_by_version[version]
        version_effective_downloads = sum(
            int_field(row, "downloads_effective_30d") for row in all_version_rows
        )
        total_bytes = sum(int_field(row, "size_bytes") for row in version_rows)
        total_mb = sum(float_field(row, "size_mb") for row in version_rows)
        summary_rows.append(
            {
                "version": version,
                "file_count": len(version_rows),
                "total_file_count": len(all_version_rows),
                "whole_version_delete": "true"
                if whole_version_delete_flags.get(version, False)
                else "false",
                "delete_reason": version_delete_reasons.get(
                    version, "partial_file_cleanup"
                ),
                "version_effective_downloads_30d": version_effective_downloads,
                "total_size_bytes": total_bytes,
                "total_size_mb": f"{total_mb:.3f}",
            }
        )
    summary_rows.sort(key=lambda row: version_sort_key(str(row["version"])))

    with output_summary.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "version",
                "file_count",
                "total_file_count",
                "whole_version_delete",
                "delete_reason",
                "version_effective_downloads_30d",
                "total_size_bytes",
                "total_size_mb",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    whole_version_count = sum(
        1 for row in summary_rows if str(row.get("whole_version_delete")) == "true"
    )
    todo_lines: list[str] = [
        "# PyPI Cleanup TODO by Version",
        "",
        f"Generated on: {date.today().isoformat()}",
        "",
        "Rule:",
        "- Effective downloads exclude mirror installers (nexus, bandersnatch, devpi)",
        "- Effective downloads exclude unknown and browser",
        f"- Whole version delete when version effective downloads < {VERSION_EFFECTIVE_DOWNLOADS_THRESHOLD}",
        f"- File delete when file effective downloads < {FILE_EFFECTIVE_DOWNLOADS_THRESHOLD}",
        "",
        f"Total candidate files: {len(deletable)}",
        f"Total candidate size: {sum(float_field(row, 'size_mb') for row in deletable):.3f} MB",
        f"Whole-version delete candidates: {whole_version_count}",
        "",
    ]

    for summary in summary_rows:
        version = str(summary["version"])
        version_rows = sorted(
            by_version[version], key=lambda row: int_field(row, "rank_cleanup")
        )
        all_version_rows = sorted(
            rows_by_version[version], key=lambda row: int_field(row, "rank_cleanup")
        )
        deletable_filenames = {row["filename"] for row in version_rows}
        keep_rows = [
            row
            for row in all_version_rows
            if row["filename"] not in deletable_filenames
        ]
        whole_version_delete = str(summary.get("whole_version_delete")) == "true"
        reason = str(summary.get("delete_reason", "partial_file_cleanup"))
        version_effective_downloads = int(
            summary.get("version_effective_downloads_30d", 0)
        )
        file_count = int(summary["file_count"])
        total_file_count = int(summary.get("total_file_count", file_count))
        todo_lines.append(
            f"## {version} ({file_count}/{total_file_count} files, {summary['total_size_mb']} MB, "
            f"version_effective_downloads_30d={version_effective_downloads}, "
            f"whole_version_delete={'yes' if whole_version_delete else 'no'}, reason={reason})"
        )
        todo_lines.append("")
        file_markdown_list: list[str] = []
        for row in version_rows:
            file_markdown_list.append(
                "- [ ] "
                f"`{row['filename']}`, rank={int_field(row, 'rank_cleanup')}, "
                f"size={float_field(row, 'size_mb'):.3f} MB, "
                f"downloads_all_30d={int_field(row, 'downloads_all_30d')}, "
                f"downloads_effective_30d={int_field(row, 'downloads_effective_30d')}, "
                f"mirror={int_field(row, 'downloads_mirror_30d')}, "
                f"unknown_browser={int_field(row, 'downloads_unknown_browser_30d')}, "
                f"nexus={int_field(row, 'downloads_installer_nexus_30d')}, "
                f"bandersnatch={int_field(row, 'downloads_installer_bandersnatch_30d')}, "
                f"devpi={int_field(row, 'downloads_installer_devpi_30d')}"
            )
        if whole_version_delete:
            todo_lines.append("- [ ] Consolidated deletion for the whole version")
            todo_lines.append("")
            todo_lines.append("<details>")
            todo_lines.append("<summary>Version file list (Markdown)</summary>")
            todo_lines.append("")
            todo_lines.append("```markdown")
            todo_lines.extend(file_markdown_list)
            todo_lines.append("```")
            todo_lines.append("</details>")
        else:
            todo_lines.extend(file_markdown_list)
            if keep_rows:
                todo_lines.append("")
                todo_lines.append("Retained files:")
                for row in keep_rows:
                    todo_lines.append(
                        "* "
                        f"`{row['filename']}`, rank={int_field(row, 'rank_cleanup')}, "
                        f"size={float_field(row, 'size_mb'):.3f} MB, "
                        f"downloads_all_30d={int_field(row, 'downloads_all_30d')}, "
                        f"downloads_effective_30d={int_field(row, 'downloads_effective_30d')}, "
                        f"mirror={int_field(row, 'downloads_mirror_30d')}, "
                        f"unknown_browser={int_field(row, 'downloads_unknown_browser_30d')}"
                    )
        todo_lines.append("")

    output_todo.write_text("\n".join(todo_lines), encoding="utf-8")

    print(f"input={input_path}")
    print(f"output_files={output_files}")
    print(f"output_summary={output_summary}")
    print(f"output_todo={output_todo}")
    print(f"deletable_files={len(deletable)}")
    print(f"deletable_versions={len(summary_rows)}")
    print(f"whole_version_delete_candidates={whole_version_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
