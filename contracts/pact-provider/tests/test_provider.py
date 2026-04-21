"""Contract tests — Pact provider verification."""
import pytest
import subprocess
from pathlib import Path

PACT_DIR = Path(__file__).parent.parent / "pact-consumer/tests/pacts"


def test_provider_contract():
    """Verify backend satisfies all consumer contracts."""
    # In CI, this runs after the consumer job uploads pacts as artifacts.
    # Locally, you must run consumer tests first to generate the pact files.
    if not PACT_DIR.exists():
        pytest.skip(f"Pact files not found at {PACT_DIR}. Run consumer tests first.")

    pact_files = list(PACT_DIR.glob("*.json"))
    if not pact_files:
        pytest.skip("No pact files to verify.")

    # Verify using pact-verifier CLI (or pact-python's verifier)
    for pact_file in pact_files:
        result = subprocess.run(
            [
                "pact-verifier",
                "--provider", "backend",
                "--provider-base-url", "http://localhost:8000",
                "--pact-file", str(pact_file),
                "--provider-app-version", "1.0.0",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Pact verification failed:\n{result.stdout}\n{result.stderr}"
