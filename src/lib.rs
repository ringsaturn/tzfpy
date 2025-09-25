use lazy_static::lazy_static;
use pyo3::prelude::*;
use tzf_rs::DefaultFinder;
use pyo3_stub_gen::{derive::gen_stub_pyfunction, define_stub_info_gatherer};

lazy_static! {
    static ref FINDER: DefaultFinder = DefaultFinder::default();
}

#[gen_stub_pyfunction]
#[pyfunction]
pub fn get_tz(lng: f64, lat: f64) -> PyResult<String> {
    Ok(FINDER.get_tz_name(lng, lat).to_string())
}

#[gen_stub_pyfunction]
#[pyfunction]
pub fn get_tzs(lng: f64, lat: f64) -> PyResult<Vec<&'static str>> {
    Ok(FINDER.get_tz_names(lng, lat))
}

#[gen_stub_pyfunction]
#[pyfunction]
pub fn timezonenames() -> PyResult<Vec<&'static str>> {
    return Ok(FINDER.timezonenames());
}

#[gen_stub_pyfunction]
#[pyfunction]
pub fn data_version() -> PyResult<String> {
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

define_stub_info_gatherer!(stub_info);
