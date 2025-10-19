"""Probably the fastest Python package to convert longitude/latitude to timezone name(s)."""

from typing import List

def get_tz(lng: float, lat: float) -> str:
    """Get timezonename for location.

    It will return the first positive match.
    """
    ...

def get_tzs(lng: float, lat: float) -> List[str]:
    """Get timezonenames for location.

    It will iter all polygon and return all positive match.
    """
    ...

def timezonenames() -> List[str]:
    """Show all support timezone names."""
    ...

def data_version() -> str:
    """Show current tzdata version"""
    ...

def get_tz_geojson_from_polygonfinder(timezone_name: str) -> str:
    """Get timezone polygon as GeoJSON string from PolygonFinder."""
    ...

def get_tz_geojson_from_fuzzy(timezone_name: str) -> str:
    """Get timezone polygon as GeoJSON string from FuzzyFinder."""
    ...
