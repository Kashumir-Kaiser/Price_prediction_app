/// Shared helpers for technical indicators.

/// Compute simple moving average (SMA) for a slice.
pub fn sma(data: &[f64], window: usize) -> Vec<f64> {
    let n = data.len();
    let mut out = vec![f64::NAN; n];
    for i in (window - 1)..n {
        let sum: f64 = data[(i + 1 - window)..=i].iter().sum();
        out[i] = sum / window as f64;
    }
    out
}

/// Compute rolling mean and std in one pass.
pub fn rolling_mean_std(data: &[f64], window: usize) -> (Vec<f64>, Vec<f64>) {
    let n = data.len();
    let mut means = vec![f64::NAN; n];
    let mut stds = vec![f64::NAN; n];
    for i in (window - 1)..n {
        let window_slice = &data[(i + 1 - window)..=i];
        let mean = window_slice.iter().sum::<f64>() / window as f64;
        let variance = window_slice.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / (window - 1) as f64;
        means[i] = mean;
        stds[i] = variance.sqrt();
    }
    (means, stds)
}
