use pyo3::prelude::*;

/// One-pass rolling mean + sample std using a window of values.
/// Returns (upper, lower, percent_b, bandwidth)
#[pyfunction]
#[pyo3(signature = (prices, period=20, num_std=2.0))]
pub fn compute_bollinger(
    prices: Vec<f64>,
    period: usize,
    num_std: f64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
    let n = prices.len();
    let nan = f64::NAN;
    let (mut upper, mut lower, mut pct_b, mut bw) =
        (vec![nan; n], vec![nan; n], vec![nan; n], vec![nan; n]);
    for i in (period - 1)..n {
        let window = &prices[(i + 1 - period)..=i];
        let mean: f64 = window.iter().sum::<f64>() / period as f64;
        let variance: f64 = window.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / (period - 1) as f64;
        let std_dev = variance.sqrt();
        let u = mean + num_std * std_dev;
        let l = mean - num_std * std_dev;
        upper[i] = u;
        lower[i] = l;
        let range = u - l;
        pct_b[i] = if range == 0.0 { nan } else { (prices[i] - l) / range };
        bw[i] = if mean == 0.0 { nan } else { range / mean };
    }
    (upper, lower, pct_b, bw)
}
