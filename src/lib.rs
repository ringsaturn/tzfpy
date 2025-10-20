// #![allow(unused)]

use lazy_static::lazy_static;
use pyo3::prelude::*;
use tzf_rs::{DefaultFinder};

lazy_static! {
    static ref FINDER: DefaultFinder = DefaultFinder::default();
}

#[pyfunction]
pub fn get_tz(lng: f64, lat: f64) -> PyResult<String> {
    Ok(FINDER.get_tz_name(lng, lat).to_string())
}

#[pyfunction]
pub fn get_tzs(lng: f64, lat: f64) -> PyResult<Vec<&'static str>> {
    Ok(FINDER.get_tz_names(lng, lat))
}

#[pyfunction]
pub fn timezonenames() -> PyResult<Vec<&'static str>> {
    return Ok(FINDER.timezonenames());
}

#[pyfunction]
pub fn data_version() -> PyResult<String> {
    return Ok(FINDER.data_version().to_string());
}

#[pyfunction]
pub fn get_tz_polygon_geojson(timezone_name: &str) -> PyResult<String> {
    Ok(FINDER.finder.get_tz_geojson(timezone_name).unwrap().to_string())
}

#[pyfunction]
pub fn get_tz_index_geojson(timezone_name: &str) -> PyResult<String> {
    Ok(FINDER.fuzzy_finder.get_tz_geojson(timezone_name).unwrap().to_string())
}

#[pymodule]
fn tzfpy(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_tz, m)?)?;
    m.add_function(wrap_pyfunction!(get_tzs, m)?)?;
    m.add_function(wrap_pyfunction!(timezonenames, m)?)?;
    m.add_function(wrap_pyfunction!(data_version, m)?)?;
    m.add_function(wrap_pyfunction!(get_tz_polygon_geojson, m)?)?;
    m.add_function(wrap_pyfunction!(get_tz_index_geojson, m)?)?;
    Ok(())
}
