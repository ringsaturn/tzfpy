#![allow(unused)]

use lazy_static::lazy_static;
use pyo3::prelude::*;
use tzf_rs::DefaultFinder;

lazy_static! {
    static ref FINDER: DefaultFinder = DefaultFinder::new();
}

#[pyfunction]
pub fn get_tz(lng: f64, lat: f64) -> PyResult<String> {
    Ok(FINDER.get_tz_name(lng, lat).to_string())
}

#[pyfunction]
pub fn timezonenames(py: Python) -> PyResult<Vec<&str>>{
    return Ok(FINDER.timezonenames());
}


#[pymodule]
fn tzfpy(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_tz, m)?)?;
    m.add_function(wrap_pyfunction!(timezonenames, m)?)?;
    Ok(())
}
