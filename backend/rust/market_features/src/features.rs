use pyo3::prelude::*;
use polars::prelude::*;

/// Accepts OHLCV columns as Vec<f64>, returns a Polars DataFrame converted to Python via Arrow.
/// Python receives it via polars.from_arrow() or pandas.api.interchange — zero copy.
#[pyfunction]
pub fn engineer_features_rs(
    py: Python<'_>,
    close: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    volume: Vec<f64>,
) -> PyResult<PyObject> {
    let df = DataFrame::new(vec![
        Series::new("close", &close),
        Series::new("high", &high),
        Series::new("low", &low),
        Series::new("volume", &volume),
    ])
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let result = df
        .lazy()
        // Lag features
        .with_columns(vec![
            col("close").shift(1).alias("close_lag1"),
            col("close").shift(2).alias("close_lag2"),
            col("close").shift(3).alias("close_lag3"),
            col("close").shift(5).alias("close_lag5"),
        ])
        // Log returns
        .with_columns(vec![
            (col("close").log(std::f64::consts::E) - col("close").shift(1).log(std::f64::consts::E))
                .alias("log_ret_1d"),
            (col("close").log(std::f64::consts::E) - col("close").shift(5).log(std::f64::consts::E))
                .alias("log_ret_5d"),
        ])
        // Rolling mean and std — 7, 14, 30 day windows
        .with_columns(vec![
            col("close")
                .rolling_mean(RollingOptions::default().window_size(Duration::new(7)))
                .alias("sma_7"),
            col("close")
                .rolling_mean(RollingOptions::default().window_size(Duration::new(20)))
                .alias("sma_20"),
            col("close")
                .rolling_mean(RollingOptions::default().window_size(Duration::new(30)))
                .alias("sma_30"),
            col("volume")
                .rolling_mean(RollingOptions::default().window_size(Duration::new(30)))
                .alias("vol_ma30"),
        ])
        // Volume Z-score = (vol - vol_ma30) / vol_std30
        .with_columns(vec![
            ((col("volume") - col("vol_ma30"))
                / col("volume").rolling_std(RollingOptions::default().window_size(Duration::new(30))))
                .alias("volume_zscore"),
        ])
        .collect()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    // Convert Polars DataFrame to Python object via Arrow IPC
    let arrow_table = result.to_arrow(CompatLevel::newest());

    // Use pyarrow to convert the Arrow table to a Python object
    let pyarrow = py.import("pyarrow")?;
    let batches: Vec<_> = arrow_table.iter().collect();
    let schema = batches.first().map(|b| b.schema().clone()).ok_or_else(|| {
        pyo3::exceptions::PyValueError::new_err("No record batches produced")
    })?;

    let py_batches: Vec<PyObject> = batches
        .into_iter()
        .map(|batch| {
            let py_batch = pyarrow.call_method1("record_batch", (batch,))?;
            Ok::<_, PyErr>(py_batch.into())
        })
        .collect::<Result<Vec<_>, _>>()?;

    let py_schema = pyarrow.call_method1("schema", (schema,))?;
    let table = pyarrow.call_method1("Table", (py_batches, py_schema))?;

    Ok(table.into())
}
