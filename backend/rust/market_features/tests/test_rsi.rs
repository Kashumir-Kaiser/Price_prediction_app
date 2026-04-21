#[cfg(test)]
mod tests {
    use crate::rsi::compute_rsi;

    #[test]
    fn test_rsi_length_preserved() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + i as f64).collect();
        let result = compute_rsi(prices.clone(), 14);
        assert_eq!(result.len(), prices.len());
    }

    #[test]
    fn test_rsi_first_n_are_nan() {
        let prices: Vec<f64> = (0..30).map(|i| 100.0 + i as f64 * 0.5).collect();
        let result = compute_rsi(prices, 14);
        for i in 0..14 {
            assert!(result[i].is_nan(), "index {} should be NaN", i);
        }
    }

    #[test]
    fn test_rsi_in_range() {
        let prices: Vec<f64> = vec![
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.15, 43.61, 44.33, 44.83, 45.10,
            45.15, 43.61, 44.33, 44.83,
        ];
        let result = compute_rsi(prices, 14);
        for v in result.iter().filter(|v| !v.is_nan()) {
            assert!(*v >= 0.0 && *v <= 100.0, "RSI out of range: {}", v);
        }
    }
}
