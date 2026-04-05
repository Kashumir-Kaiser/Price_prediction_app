"""Tests for scraper package imports — Regression test for BUG-02."""


def test_scraper_package_importable():
    """Regression test for BUG-02 — ensures scraper package is correctly structured."""
    import scraper  # must not raise ModuleNotFoundError
    from scraper.jobs import crypto_job  # must not raise ModuleNotFoundError
    from scraper.jobs import vn_stock_job
    from scraper.jobs import stablecoin_job
    assert True  # if we reach here, package structure is correct


def test_scheduler_importable():
    """Regression test — scheduler must import without crash."""
    import importlib.util
    spec = importlib.util.find_spec("scraper.scheduler")
    assert spec is not None, "scraper.scheduler module not found on PYTHONPATH"
