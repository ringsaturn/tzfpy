from pytest import mark, raises

from tzfpy import (
    get_tz,
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
