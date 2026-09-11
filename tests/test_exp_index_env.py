"""The `_TZFPY_DISABLE_Y_STRIPES` switch was removed in tzfpy 2.0.

tzf-rs 2 dropped `FinderOptions`; the YStripes index is always on. Setting the
old environment variable must stay a harmless no-op rather than an error or a
different result, so users who still export it keep working.
"""

import os
import subprocess
import sys

from pytest import mark

REMOVED_ENV = "_TZFPY_DISABLE_Y_STRIPES"


def _run_import_and_query(disable_y_stripes: str | None = None) -> str:
    env = os.environ.copy()
    if disable_y_stripes is None:
        env.pop(REMOVED_ENV, None)
    else:
        env[REMOVED_ENV] = disable_y_stripes

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


def test_removed_env_unset():
    assert _run_import_and_query() == "Asia/Shanghai"


@mark.parametrize("disable_y_stripes", ["1", "true", "yes", "on"])
def test_removed_env_is_ignored(disable_y_stripes):
    assert _run_import_and_query(disable_y_stripes) == "Asia/Shanghai"
