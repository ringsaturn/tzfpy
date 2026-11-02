import math
from array import array

from pytest import importorskip, mark, raises

from tzfpy import (
    get_tz,
    get_tz_batch,
    get_tz_index_geojson,
    get_tz_polygon_geojson,
    get_tzs,
)


@mark.parametrize(
    "lng, lat, tz",
    [
        (116.3883, 39.9289, "Asia/Shanghai"),
        (120.347287, 22.598127, "Asia/Taipei"),
        (2.3522, 48.8566, "Europe/Paris"),
        (-0.1276, 51.5074, "Europe/London"),
        (13.4049, 52.5200, "Europe/Berlin"),
        (-74.0060, 40.7128, "America/New_York"),
        (-118.2437, 34.0522, "America/Los_Angeles"),
    ],
)
def test_get_tz(lng, lat, tz):
    assert get_tz(lng, lat) == tz
    _ = get_tz_polygon_geojson(tz)
    _ = get_tz_index_geojson(tz)


def test_get_tzs_is_sorted_and_overlap_aware():
    # Overlapping timezones: the point is inside both Asia/Shanghai and
    # Asia/Urumqi. tzf-rs 2 returns every match, sorted alphabetically.
    names = get_tzs(87.4160, 44.0400)
    assert names == sorted(names)
    assert names == ["Asia/Shanghai", "Asia/Urumqi"]


def test_get_tz_matches_first_of_get_tzs_on_land():
    for lng, lat in [(116.3883, 39.9289), (2.3522, 48.8566), (-74.0060, 40.7128)]:
        assert get_tz(lng, lat) in get_tzs(lng, lat)


def test_unknown_timezone_geojson_raises():
    with raises(ValueError):
        get_tz_polygon_geojson("Not/A/Timezone")
    with raises(ValueError):
        get_tz_index_geojson("Not/A/Timezone")


def _grid():
    lngs, lats = [], []
    for i in range(-180, 181, 7):
        for j in range(-90, 91, 7):
            lngs.append(i + 0.123)
            lats.append(j + 0.456)
    lngs += [116.3883, 0.0, 180.0, -180.0, 200.0, math.nan]
    lats += [39.9289, 0.0, 90.0, -90.0, 0.0, 0.0]
    return lngs, lats


def test_get_tz_batch_matches_get_tz():
    lngs, lats = _grid()
    want = [get_tz(x, y) for x, y in zip(lngs, lats)]
    assert get_tz_batch(lngs, lats) == want
    assert get_tz_batch(tuple(lngs), tuple(lats)) == want
    assert get_tz_batch(array("d", lngs), array("d", lats)) == want
    # Non-contiguous buffers fall back to the sequence path.
    two = array("d", [v for x in lngs for v in (x, 0.0)])
    assert get_tz_batch(memoryview(two)[::2], lats) == want


def test_get_tz_batch_numpy():
    np = importorskip("numpy")
    lngs, lats = _grid()
    want = [get_tz(x, y) for x, y in zip(lngs, lats)]
    assert get_tz_batch(np.array(lngs), np.array(lats)) == want
    assert (
        get_tz_batch(np.array(lngs, dtype=np.float32).astype(np.float64), lats) == want
    )
    big = np.array([lngs, lats])
    assert get_tz_batch(big[0], big[1]) == want
    assert get_tz_batch(big.T[:, 0], big.T[:, 1]) == want


def test_get_tz_batch_edge_cases():
    assert get_tz_batch([], []) == []
    assert get_tz_batch(array("i", [116]), array("i", [40])) == ["Asia/Shanghai"]
    with raises(ValueError):
        get_tz_batch([1.0, 2.0], [1.0])
    with raises(TypeError):
        get_tz_batch(["a"], ["b"])
