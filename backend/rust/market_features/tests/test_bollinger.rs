#[cfg(test)]
mod tests {
    use crate::bollinger::compute_bollinger;

    #[test]
    fn test_bollinger_length_preserved() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64).sin()).collect();
        let (upper, lower, pct_b, bw) = compute_bollinger(prices.clone(), 20, 2.0);
        assert_eq!(upper.len(), prices.len());
        assert_eq!(lower.len(), prices.len());
        assert_eq!(pct_b.len(), prices.len());
        assert_eq!(bw.len(), prices.len());
    }

    #[test]
    fn test_bollinger_bands_ordered() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64).sin()).collect();
        let (upper, lower, _pct_b, _bw) = compute_bollinger(prices, 20, 2.0);
        for i in 19..upper.len() {
            assert!(upper[i] >= lower[i], "upper band below lower band at index {}", i);
        }
    }
}
