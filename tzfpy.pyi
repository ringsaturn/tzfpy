"""Probably the fastest Python package to convert longitude/latitude to timezone name(s)."""

def get_tz(lng: float, lat: float) -> str:
    """Get timezonename for location.

    It will return the first positive match.
    """

def get_tzs(lng: float, lat: float) -> list[str]:
    """Get timezonenames for location.

    It will iter all polygon and return all positive match.
    """

def timezonenames() -> list[str]:
    """Show all support timezone names."""

def data_version() -> str:
    """Show current tzdata version"""

def get_tz_polygon_geojson(timezone_name: str) -> str:
    """Get timezone polygon as GeoJSON string from PolygonFinder."""

def get_tz_index_geojson(timezone_name: str) -> str:
    """Get timezone polygon as GeoJSON string from FuzzyFinder."""
