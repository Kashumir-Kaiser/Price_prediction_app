use pyo3::prelude::*;

/// Compute EMA in-place from left to right (Wilder-style, initialised with first value).
fn ema(data: &[f64], period: usize) -> Vec<f64> {
    let alpha = 2.0 / (period as f64 + 1.0);
    let mut out = vec![f64::NAN; data.len()];
    // Seed with first non-NaN value
    let seed_idx = data.iter().position(|v| !v.is_nan()).unwrap_or(0);
    out[seed_idx] = data[seed_idx];
    for i in (seed_idx + 1)..data.len() {
        if data[i].is_nan() {
            out[i] = f64::NAN;
        } else {
            out[i] = data[i] * alpha + out[i - 1] * (1.0 - alpha);
        }
    }
    out
}

/// Returns (macd_line, signal_line, histogram) — all same length as prices.
/// fast=12, slow=26, signal=9 by default.
#[pyfunction]
#[pyo3(signature = (prices, fast=12, slow=26, signal=9))]
pub fn compute_macd(
    prices: Vec<f64>,
    fast: usize,
    slow: usize,
    signal: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let ema_fast = ema(&prices, fast);
    let ema_slow = ema(&prices, slow);
    let macd_line: Vec<f64> = ema_fast
        .iter()
        .zip(ema_slow.iter())
        .map(|(f, s)| if f.is_nan() || s.is_nan() { f64::NAN } else { f - s })
        .collect();
    let signal_line = ema(&macd_line, signal);
    let histogram: Vec<f64> = macd_line
        .iter()
        .zip(signal_line.iter())
        .map(|(m, s)| if m.is_nan() || s.is_nan() { f64::NAN } else { m - s })
        .collect();
    (macd_line, signal_line, histogram)
}
