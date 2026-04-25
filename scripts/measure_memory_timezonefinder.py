"""Measure memory usage of tzfpy."""

import os
import tracemalloc

import psutil


def measure():
    proc = psutil.Process(os.getpid())

    rss_before = proc.memory_info().rss
    tracemalloc.start()

    from timezonefinder import TimezoneFinder  # noqa: F401

    # trigger lazy init
    tf = TimezoneFinder(in_memory=True)
    _ = tf.timezone_at(lng=116.3883, lat=39.9289)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rss_after = proc.memory_info().rss

    print(f"tracemalloc current : {current / 1024 / 1024:.2f} MB")
    print(f"tracemalloc peak    : {peak / 1024 / 1024:.2f} MB")
    print(f"RSS delta (psutil)  : {(rss_after - rss_before) / 1024 / 1024:.2f} MB")
    print(f"RSS total (psutil)  : {rss_after / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    measure()
