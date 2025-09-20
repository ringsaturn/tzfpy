from citiespy import all_cities

from tzfpy import data_version, get_tzs, timezonenames


def test_with_pytz():
    from pytz import timezone

    for tz in timezonenames():
        timezone(tz)


def test_with_tzdata():
    from zoneinfo import ZoneInfo

    for tz in timezonenames():
        ZoneInfo(tz)


def test_no_empty():
    for city in all_cities():
        tznames = get_tzs(city.lng, city.lat)
        assert len(tznames) != 0


def test_version_support():
    assert data_version() not in [None, ""]


def test_arrow_with_tzdata():
    from zoneinfo import ZoneInfo

    import arrow

    for tz in timezonenames():
        arrow.now(ZoneInfo(tz))


def test_whenever_with_tzdata():
    from whenever import Instant

    for tz in timezonenames():
        Instant.now().to_tz(tz)
