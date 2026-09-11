"""Probably the fastest Python package to convert longitude/latitude to timezone name(s).

Backed by `tzf-rs <https://github.com/ringsaturn/tzf-rs>`_ 2.x, which reads the
TZF embedded binary format (``.tzb``) shipped by ``tzf-dist``. The finder is
built lazily on the first call and shared for the lifetime of the process.

All coordinates are ``(longitude, latitude)`` — longitude first.
"""

def get_tz(lng: float, lat: float) -> str:
    """Return one timezone name for the location, or ``""`` if none covers it.

    Answered from the pre-index tiles when one covers the point (the vast
    majority of queries) and by exact point-in-polygon otherwise. Where
    timezones overlap, this returns the first match; use :func:`get_tzs` to
    see every match.
    """

def get_tzs(lng: float, lat: float) -> list[str]:
    """Return every timezone name covering the location, sorted alphabetically.

    Always polygon-exact — it never uses the pre-index fast path — so it is
    slower than :func:`get_tz`. Overlapping timezones and points that lie
    exactly on a shared border yield more than one name; a point in no
    timezone yields an empty list.
    """

def timezonenames() -> list[str]:
    """Return every timezone name present in the bundled dataset."""

def data_version() -> str:
    """Return the boundary dataset release, e.g. ``"2026c"``.

    This is the timezone-boundary-builder release the polygons come from, not
    the version of this package.
    """

def get_tz_polygon_geojson(timezone_name: str) -> str:
    """Return the timezone's boundary polygons as a GeoJSON FeatureCollection string.

    Intended for visualization. Raises :exc:`ValueError` when the dataset has
    no such timezone.
    """

def get_tz_index_geojson(timezone_name: str) -> str:
    """Return the timezone's pre-index tiles as a GeoJSON FeatureCollection string.

    One Feature whose MultiPolygon holds each tile's bounding box — the area
    where :func:`get_tz` answers from the fast path instead of exact
    point-in-polygon. Intended for visualization and debugging. Raises
    :exc:`ValueError` when the dataset has no such timezone or no tile names
    it.
    """
