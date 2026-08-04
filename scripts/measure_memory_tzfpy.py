"""Measure memory usage of tzfpy."""

import argparse
import json
import os
import tracemalloc

import psutil


def measure():
    proc = psutil.Process(os.getpid())

    rss_before = proc.memory_info().rss
    tracemalloc.start()

    import tzfpy

    # trigger lazy init
    _ = tzfpy.get_tz(116.3883, 39.9289)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rss_after = proc.memory_info().rss

    return {
        "tracemalloc_current_bytes": current,
        "tracemalloc_peak_bytes": peak,
        "rss_delta_bytes": rss_after - rss_before,
        "rss_total_bytes": rss_after,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON"
    )
    args = parser.parse_args()
    result = measure()

    if args.json:
        print(json.dumps(result))
        return

    mib = 1024 * 1024
    print(f"tracemalloc current : {result['tracemalloc_current_bytes'] / mib:.2f} MB")
    print(f"tracemalloc peak    : {result['tracemalloc_peak_bytes'] / mib:.2f} MB")
    print(f"RSS delta (psutil)  : {result['rss_delta_bytes'] / mib:.2f} MB")
    print(f"RSS total (psutil)  : {result['rss_total_bytes'] / mib:.2f} MB")


if __name__ == "__main__":
    main()
