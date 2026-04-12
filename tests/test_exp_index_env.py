import os
import subprocess
import sys

from pytest import mark


def _run_import_and_query(disable_y_stripes: str | None = None) -> str:
    env = os.environ.copy()
    if disable_y_stripes is None:
        env.pop("_TZFPY_DISABLE_Y_STRIPES", None)
    else:
        env["_TZFPY_DISABLE_Y_STRIPES"] = disable_y_stripes

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


def test_disable_y_stripes_env_unset():
    assert _run_import_and_query() == "Asia/Shanghai"


@mark.parametrize("disable_y_stripes", ["1", "true", "yes", "on"])
def test_disable_y_stripes_env_variants(disable_y_stripes):
    assert _run_import_and_query(disable_y_stripes) == "Asia/Shanghai"
