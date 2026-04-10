import os
import subprocess
import sys

from pytest import mark


def _run_import_and_query(exp_index: str | None) -> str:
    env = os.environ.copy()
    if exp_index is None:
        env.pop("_TZFPY_EXP_INDEX", None)
    else:
        env["_TZFPY_EXP_INDEX"] = exp_index

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from tzfpy import get_tz; print(get_tz(116.3883, 39.9289))",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return proc.stdout.strip()


@mark.parametrize("exp_index", [None, "rtree", "quadtree"])
def test_exp_index_env_variants(exp_index):
    assert _run_import_and_query(exp_index) == "Asia/Shanghai"
