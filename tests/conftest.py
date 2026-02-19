"""
Pytest configuration and shared fixtures.

collect_ignore: script-style files moved from the repo root that were never
part of the automated test suite. They require real LLM API keys, Playwright
browsers, or hardcoded machine paths, so they are excluded from CI collection.
Run them manually when needed:

    python tests/test_complete_integration.py
    python tests/test_phase4_meta_analysis_additional.py
"""

collect_ignore = [
    "test_complete_integration.py",
    "test_phase3_retry.py",
    "test_phase3_workflow.py",
    "test_phase4_meta_analysis_additional.py",
    "test_real_cases.py",
    "test_stage_tracking.py",
]
