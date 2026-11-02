// #![allow(unused)]

use lazy_static::lazy_static;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyList, PyString};

#[cfg(all(feature = "lite", feature = "full"))]
compile_error!(
    "features `lite` and `full` are mutually exclusive; build the full-precision \
     variant with `--no-default-features --features full`"
);

#[cfg(not(any(feature = "lite", feature = "full")))]
compile_error!("enable exactly one data feature: `lite` (default) or `full`");

/// Lite: the ~4 MB lite.tzb expanded into owned polygons. Fastest queries
/// (hundreds of nanoseconds), ~40 MB resident.
#[cfg(feature = "lite")]
type Finder = tzf_rs::DefaultFinder;

/// Full precision: the ~14 MB full.tzb queried in place. `DefaultFinder`
/// over the full data expands to ~200 MB resident, which is the wrong trade
/// for a library embedded in long-lived services; `EmbeddedFinder` keeps the
/// footprint at roughly the file itself and pays with microsecond queries on
/// preindex misses. Results are identical between the two finders.
#[cfg(all(not(feature = "lite"), feature = "full"))]
type Finder = tzf_rs_full::EmbeddedFinder;

#[cfg(feature = "lite")]
fn new_finder() -> Finder {
    Finder::new()
}

/// `EmbeddedFinder::new()` still loads the lite data under the `full`
/// feature, and tzf-rs has no `new_full()` on it, so read full.tzb straight
/// from tzf-dist. The bytes live in the extension's read-only data segment
/// and are borrowed, not copied.
#[cfg(all(not(feature = "lite"), feature = "full"))]
fn new_finder() -> Finder {
    Finder::from_tzb(tzf_dist_full::load_full_tzb())
        .expect("tzf-dist full.tzb is validated at release")
}

lazy_static! {
    static ref FINDER: Finder = new_finder();
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

/// Position of the point's zone in `timezonenames()`, or `None`.
#[cfg(feature = "lite")]
fn tz_index(lng: f64, lat: f64) -> Option<usize> {
    FINDER.get_tz_index(lng, lat)
}

/// `EmbeddedFinder` has no index API, so map the name back to its position.
#[cfg(all(not(feature = "lite"), feature = "full"))]
fn tz_index(lng: f64, lat: f64) -> Option<usize> {
    use std::collections::HashMap;
    use std::sync::LazyLock;
    static POS: LazyLock<HashMap<&'static str, usize>> = LazyLock::new(|| {
        FINDER
            .timezonenames()
            .into_iter()
            .enumerate()
            .map(|(i, n)| (n, i))
            .collect()
    });
    match FINDER.get_tz_name(lng, lat) {
        "" => None,
        name => POS.get(name).copied(),
    }
}

/// One Python string per zone (slot 0 = `""` for no zone), built once and
/// shared, so a batch answer costs a reference per point, not a new string.
static ZONE_STRS: PyOnceLock<Vec<Py<PyString>>> = PyOnceLock::new();

fn zone_strs(py: Python<'_>) -> &[Py<PyString>] {
    ZONE_STRS.get_or_init(py, || {
        std::iter::once("")
            .chain(FINDER.timezonenames())
            .map(|n| PyString::new(py, n).unbind())
            .collect()
    })
}

/// Coordinates from a C-contiguous float64 buffer (numpy array,
/// `array('d')`, ...) when the object offers one, else from any sequence of
/// floats.
fn coords(obj: &Bound<'_, PyAny>) -> PyResult<Vec<f64>> {
    if let Ok(buf) = pyo3::buffer::PyBuffer::<f64>::get(obj)
        && buf.is_c_contiguous()
    {
        return buf.to_vec(obj.py());
    }
    obj.extract()
}

#[pyfunction]
pub fn get_tz_batch<'py>(
    py: Python<'py>,
    lngs: &Bound<'py, PyAny>,
    lats: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyList>> {
    let (lngs, lats) = (coords(lngs)?, coords(lats)?);
    if lngs.len() != lats.len() {
        return Err(PyValueError::new_err(format!(
            "lngs and lats differ in length: {} != {}",
            lngs.len(),
            lats.len()
        )));
    }
    let strs = zone_strs(py);
    let pos: Vec<u32> = py.detach(|| {
        lngs.iter()
            .zip(&lats)
            .map(|(&lng, &lat)| tz_index(lng, lat).map_or(0, |i| i as u32 + 1))
            .collect()
    });
    PyList::new(py, pos.iter().map(|&i| strs[i as usize].bind(py)))
}

#[pymodule]
fn tzfpy(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_tz, m)?)?;
    m.add_function(wrap_pyfunction!(get_tzs, m)?)?;
    m.add_function(wrap_pyfunction!(get_tz_batch, m)?)?;
    m.add_function(wrap_pyfunction!(timezonenames, m)?)?;
    m.add_function(wrap_pyfunction!(data_version, m)?)?;
    m.add_function(wrap_pyfunction!(get_tz_polygon_geojson, m)?)?;
    m.add_function(wrap_pyfunction!(get_tz_index_geojson, m)?)?;
    Ok(())
}
