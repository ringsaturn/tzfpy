from unittest import TestCase, main

from citiespy import all_cities

from tzfpy import get_tzs, timezonenames, data_version


class TestCompatibility(TestCase):
    def test_with_pytz(self):
        from pytz import timezone

        for tz in timezonenames():
            timezone(tz)

    def test_no_empty(self):
        for city in all_cities():
            tznames = get_tzs(city.lng, city.lat)
            self.assertTrue(len(tznames) != 0)

    def test_version_support(self):
        self.assertTrue(data_version() not in [None, ""])


if __name__ == "__main___":
    main()
