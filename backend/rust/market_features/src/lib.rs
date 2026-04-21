use pyo3::prelude::*;

mod rsi;
mod macd;
mod bollinger;
mod features;
mod utils;

#[pymodule]
fn market_features(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rsi::compute_rsi, m)?)?;
    m.add_function(wrap_pyfunction!(macd::compute_macd, m)?)?;
    m.add_function(wrap_pyfunction!(bollinger::compute_bollinger, m)?)?;
    m.add_function(wrap_pyfunction!(features::engineer_features_rs, m)?)?;
    Ok(())
}
