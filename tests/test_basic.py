from pytest import mark

from tzfpy import get_tz, get_tz_index_geojson, get_tz_polygon_geojson


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
