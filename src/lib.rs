// #![allow(unused)]

use lazy_static::lazy_static;
use pyo3::prelude::*;
use tzf_rs::DefaultFinder;

lazy_static! {
    static ref FINDER: DefaultFinder = DefaultFinder::default();
}

#[pyfunction]
pub fn get_tz(lng: f64, lat: f64) -> PyResult<String> {
    Ok(FINDER.get_tz_name(lng, lat).to_string())
}

#[pyfunction]
pub fn get_tzs(_py: Python, lng: f64, lat: f64) -> PyResult<Vec<&str>> {
    Ok(FINDER.get_tz_names(lng, lat))
}

#[pyfunction]
pub fn timezonenames(_py: Python) -> PyResult<Vec<&str>> {
    return Ok(FINDER.timezonenames());
}

#[pyfunction]
pub fn data_version(_py: Python) -> PyResult<String> {
    return Ok(FINDER.data_version().to_string());
}

#[pymodule]
fn tzfpy(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_tz, m)?)?;
    m.add_function(wrap_pyfunction!(get_tzs, m)?)?;
    m.add_function(wrap_pyfunction!(timezonenames, m)?)?;
    m.add_function(wrap_pyfunction!(data_version, m)?)?;
    Ok(())
}
