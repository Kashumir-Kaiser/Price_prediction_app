#[cfg(test)]
mod tests {
    use crate::macd::compute_macd;

    #[test]
    fn test_macd_length_preserved() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64).sin()).collect();
        let (line, sig, hist) = compute_macd(prices.clone(), 12, 26, 9);
        assert_eq!(line.len(), prices.len());
        assert_eq!(sig.len(), prices.len());
        assert_eq!(hist.len(), prices.len());
    }

    #[test]
    fn test_macd_histogram_is_diff() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64).sin()).collect();
        let (line, sig, hist) = compute_macd(prices, 12, 26, 9);
        for i in 0..line.len() {
            if !line[i].is_nan() && !sig[i].is_nan() {
                let expected = line[i] - sig[i];
                assert!((hist[i] - expected).abs() < 1e-9, "histogram mismatch at index {}", i);
            }
        }
    }
}
