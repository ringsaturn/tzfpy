from unittest import TestCase, main

from pytz import timezone

from tzfpy import timezonenames


class TestCompatibility(TestCase):
    def test_with_pytz(self):
        for tz in timezonenames():
            timezone(tz)


if __name__ == "__main___":
    main()
