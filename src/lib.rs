// #![allow(unused)]

use lazy_static::lazy_static;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

#[cfg(all(feature = "lite", feature = "full"))]
compile_error!(
    "features `lite` and `full` are mutually exclusive; build the full-precision \
     variant with `--no-default-features --features full`"
);

#[cfg(not(any(feature = "lite", feature = "full")))]
compile_error!("enable exactly one data feature: `lite` (default) or `full`");

#[cfg(feature = "lite")]
use tzf_rs::DefaultFinder;
#[cfg(all(not(feature = "lite"), feature = "full"))]
use tzf_rs_full::DefaultFinder;

/// Loads the lite dataset bundled by tzf-dist (~4 MB).
#[cfg(feature = "lite")]
fn new_finder() -> DefaultFinder {
    DefaultFinder::new()
}

/// Loads the full-precision dataset (~14 MB, no topology simplification).
/// `DefaultFinder::new()` still returns the lite data under this feature, so
/// the full variant has to go through `new_full()`.
#[cfg(all(not(feature = "lite"), feature = "full"))]
fn new_finder() -> DefaultFinder {
    DefaultFinder::new_full()
}

lazy_static! {
    static ref FINDER: DefaultFinder = new_finder();
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
    match FINDER.get_tz_geojson(timezone_name) {
        Some(boundary) => Ok(boundary.to_string()),
        None => Err(PyValueError::new_err(format!(
            "unknown timezone: {timezone_name}"
        ))),
    }
}

#[pyfunction]
pub fn get_tz_index_geojson(timezone_name: &str) -> PyResult<String> {
    match FINDER.get_tz_preindex_geojson(timezone_name) {
        Some(boundary) => Ok(boundary.to_string()),
        None => Err(PyValueError::new_err(format!(
            "no preindex tiles for timezone: {timezone_name}"
        ))),
    }
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
