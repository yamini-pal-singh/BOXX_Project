"""
Pytest configuration and fixtures for the BOXX Chatbot Test Automation Suite.
"""

import csv
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from boxx_client import BOXXClient
from test_loader import load_test_cases, load_sample_cases

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)

logger = logging.getLogger("conftest")

# Session-level tracking
_session_start: float = 0.0


def _get_results_dir() -> Path:
    """Return the results/ directory, creating it if needed."""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


# ---------------------------------------------------------------------------
# pytest hooks
# ---------------------------------------------------------------------------


def pytest_addoption(parser):
    parser.addoption(
        "--test-sheet",
        action="store",
        default=None,
        help="Path to the test case sheet (CSV or XLSX). Uses built-in samples if omitted.",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="BOXX API base URL (overrides env/ default).",
    )
    parser.addoption(
        "--api-key",
        action="store",
        default=None,
        help="BOXX API key (overrides env/ default).",
    )
    parser.addoption(
        "--results-dir",
        action="store",
        default=None,
        help="Custom directory for results CSV output (default: ./results/)",
    )


def pytest_configure(config):
    """Register custom markers and configure."""
    global _session_start
    _session_start = __import__("time").time()
    config.addinivalue_line("markers", "smoke: quick smoke test to verify API reachability.")
    config.addinivalue_line("markers", "sample: test using built-in sample data (runs without a sheet file).")
    # Store start time in config for hooks
    config._boxx_start = _session_start  # type: ignore[attr-defined]


def pytest_collectstart():
    """Ignore non-test classes that pytest may try to collect."""
    pass  # handled via __test__ attribute below


# Prevent TestCase dataclass from being collected as a test
import test_loader as _tl
_tl.TestCase.__test__ = False  # type: ignore[attr-defined]


def pytest_generate_tests(metafunc):
    """Parametrize 'test_case' fixtures from loaded test data at collection time."""
    if "test_case" not in metafunc.fixturenames:
        return

    sheet_path = metafunc.config.getoption("--test-sheet", default=None)
    if sheet_path:
        path = Path(sheet_path)
        if not path.exists():
            # Try relative to project root
            alt = Path(__file__).parent / sheet_path
            if alt.exists():
                path = alt
            else:
                pytest.exit(f"Test sheet not found: {sheet_path}", returncode=1)
        cases = load_test_cases(path)
    else:
        logger.info("No --test-sheet provided; using built-in sample test cases.")
        cases = load_sample_cases()

    if not cases:
        pytest.exit("No test cases loaded!", returncode=1)

    metafunc.parametrize(
        "test_case",
        cases,
        ids=[c.test_id for c in cases],
    )


def pytest_sessionfinish(session, exitstatus):
    """Write all accumulated test results to a timestamped CSV."""
    # Import results from test module
    from test_boxx_scam_flows import TEST_RESULTS

    if not TEST_RESULTS:
        logger.info("No test results to write.")
        return

    results_dir = _get_results_dir()
    config = session.config
    custom_dir = config.getoption("--results-dir", default=None)
    if custom_dir:
        results_dir = Path(custom_dir)
        results_dir.mkdir(parents=True, exist_ok=True)

    # Compute session duration
    start = getattr(config, "_boxx_start", 0)
    duration_s = __import__("time").time() - start
    duration_str = f"{duration_s / 60:.1f} min" if duration_s > 120 else f"{duration_s:.0f}s"

    # Count stats
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in TEST_RESULTS if r["status"] in ("FAIL", "ERROR"))
    skipped = sum(1 for r in TEST_RESULTS if r["status"] == "SKIP")

    # Determine test source
    sheet_path = config.getoption("--test-sheet", default=None)
    source_desc = sheet_path or "built-in samples"

    # Timestamp for filename
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"boxx_results_{ts}.csv"
    filepath = results_dir / filename

    # Collect all field names from results (in a consistent order)
    fieldnames = [
        "timestamp", "test_id", "language", "scenario_type",
        "status", "turn_count", "input_messages",
        "expected_keywords", "expected_classification", "expected_journey", "expected_emotion",
        "latency_ms", "classification", "journey", "emotion", "emotion_language",
        "loss_assessment", "persona_archetype", "persona_confidence", "response_style",
        "keywords_matched", "expected_not_found",
        "bot_reply", "full_analysis",
        "error_message", "notes", "source_sheet",
    ]

    # Write CSV
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")

        # ── Metadata header ──
        f.write(f"# BOXX Test Automation — Results\n")
        f.write(f"# Run Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Test Source:   {source_desc}\n")
        f.write(f"# Duration:      {duration_str}\n")
        f.write(f"# Total Tests:   {total}\n")
        f.write(f"# Passed:        {passed}\n")
        f.write(f"# Failed:        {failed}\n")
        f.write(f"# Skipped:       {skipped}\n")
        f.write(f"# API Base URL:  {os.environ.get('BOXX_BASE_URL', 'https://boxxv2.shunyalabs.ai')}\n")
        f.write(f"#\n")

        writer.writeheader()
        for row in TEST_RESULTS:
            writer.writerow(row)

        # ── Summary footer ──
        f.write(f"\n# SUMMARY: TOTAL={total}  PASS={passed}  FAIL={failed}  SKIP={skipped}  DURATION={duration_str}\n")

    logger.info("\n"
                "╔══════════════════════════════════════════════════════════╗\n"
                "║  Results written to: %-32s  ║\n"
                "║  TOTAL: %-4d  |  PASS: %-4d  |  FAIL: %-4d  |  SKIP: %-4d       ║\n"
                "║  Duration: %-65s ║\n"
                "╚══════════════════════════════════════════════════════════╝"
                "", filepath, total, passed, failed, skipped, duration_str)

    # Also write a latest symlink/copy (overwrite the "latest" file)
    latest_path = results_dir / "boxx_results_latest.csv"
    import shutil
    shutil.copy2(filepath, latest_path)
    logger.info("Latest results also available at: %s", latest_path)


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def boxx_client(request) -> BOXXClient:
    """Create a single BOXXClient for the whole session."""
    base_url = request.config.getoption("--base-url") or None
    api_key = request.config.getoption("--api-key") or None
    client = BOXXClient(base_url=base_url, api_key=api_key)
    # Run health check once at session start
    ok = client.health_check()
    if not ok:
        pytest.exit(
            "BOXX API health check FAILED.\n"
            f"  URL: {client.base_url}\n"
            "  Check that the API is running and your API key is valid.\n"
            "  Set BOXX_BASE_URL / BOXX_API_KEY env vars if defaults are wrong.",
            returncode=1,
        )
    return client
