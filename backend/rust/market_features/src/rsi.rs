use pyo3::prelude::*;

/// Compute RSI for a price series.
/// prices: closing prices as a Python list of f64
/// period: smoothing period (default 14)
/// Returns a Vec of the same length; first `period` values are NaN (f64::NAN).
#[pyfunction]
#[pyo3(signature = (prices, period=14))]
pub fn compute_rsi(prices: Vec<f64>, period: usize) -> Vec<f64> {
    let n = prices.len();
    let mut rsi = vec![f64::NAN; n];
    if n <= period {
        return rsi;
    }
    // Compute initial average gain / loss over first `period` deltas
    let mut avg_gain = 0.0_f64;
    let mut avg_loss = 0.0_f64;
    for i in 1..=period {
        let delta = prices[i] - prices[i - 1];
        if delta > 0.0 {
            avg_gain += delta;
        } else {
            avg_loss += delta.abs();
        }
    }
    avg_gain /= period as f64;
    avg_loss /= period as f64;
    if avg_loss == 0.0 {
        rsi[period] = 100.0;
    } else {
        rsi[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss);
    }
    // Wilder's smoothing for the rest of the series
    for i in (period + 1)..n {
        let delta = prices[i] - prices[i - 1];
        let (gain, loss) = if delta >= 0.0 {
            (delta, 0.0)
        } else {
            (0.0, delta.abs())
        };
        avg_gain = (avg_gain * (period as f64 - 1.0) + gain) / period as f64;
        avg_loss = (avg_loss * (period as f64 - 1.0) + loss) / period as f64;
        rsi[i] = if avg_loss == 0.0 {
            100.0
        } else {
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        };
    }
    rsi
}
