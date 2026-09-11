#!/usr/bin/env python3
"""Benchmark tzfpy and print a Markdown summary table.

tzfpy 2.0 has a single index mode: tzf-rs 2 removed `FinderOptions`, so the
YStripes index is always enabled and the `_TZFPY_DISABLE_Y_STRIPES` switch is
gone. The table therefore has one row; it is kept as a table so CI summaries
and release notes stay comparable across versions.
"""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIB = 1024 * 1024
LABEL = "Default (pre-index + YStripes)"


@dataclass(frozen=True)
class Result:
    label: str
    median_us: float
    mean_us: float
    throughput_kops: float
    memory_mib: float


def run_command(command: list[str]) -> str:
    process = subprocess.run(
        command,
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if process.returncode != 0:
        sys.stderr.write(process.stdout)
        raise subprocess.CalledProcessError(process.returncode, command)
    return process.stdout


def read_benchmark_stats(path: Path) -> tuple[float, float]:
    report = json.loads(path.read_text())
    benchmarks = report.get("benchmarks", [])
    if len(benchmarks) != 1:
        raise ValueError(f"expected one benchmark result, got {len(benchmarks)}")
    stats = benchmarks[0]["stats"]
    return stats["median"], stats["mean"]


def benchmark(benchmark_args: list[str]) -> tuple[float, float]:
    with tempfile.TemporaryDirectory(prefix="tzfpy-benchmark-") as directory:
        output_path = Path(directory) / "benchmark.json"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_bench.py",
            *benchmark_args,
            f"--benchmark-json={output_path}",
        ]
        run_command(command)
        return read_benchmark_stats(output_path)


def measure_memory() -> float:
    command = [sys.executable, "scripts/measure_memory_tzfpy.py", "--json"]
    result = json.loads(run_command(command))
    return result["rss_delta_bytes"] / MIB


def collect_result(benchmark_args: list[str]) -> Result:
    median, mean = benchmark(benchmark_args)
    return Result(
        label=LABEL,
        median_us=median * 1_000_000,
        mean_us=mean * 1_000_000,
        throughput_kops=1 / mean / 1_000,
        memory_mib=measure_memory(),
    )


def format_table(results: list[Result]) -> str:
    rows = [
        "| Index mode | Median (µs) | Mean (µs) | Throughput (Kops/s) | Memory |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    rows.extend(
        f"| {result.label} | {result.median_us:.4f} | {result.mean_us:.4f} | "
        f"{result.throughput_kops:.1f} | ~{result.memory_mib:.1f} MB |"
        for result in results
    )
    return "\n".join(rows)


def main() -> None:
    results = [collect_result(sys.argv[1:])]
    print("Memory is the RSS increase after import and lazy initialization.")
    print()
    print(format_table(results))


if __name__ == "__main__":
    main()
