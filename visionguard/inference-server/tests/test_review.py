"""Unit tests for the confidence-gate decision (portfolio guardrail):
below 0.70 -> human review, never auto-accept.
"""
import pathlib
import sys

SRV = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRV))

from review import review_decision  # noqa: E402


def test_no_detections_is_a_pass():
    r = review_decision([])
    assert r["needs_review"] is False


def test_low_confidence_routes_to_human():
    r = review_decision([{"confidence": 0.55, "class_name": "scratch"}])
    assert r["needs_review"] is True
    assert "0.55" in r["reason"]


def test_all_high_confidence_auto_ok():
    r = review_decision([
        {"confidence": 0.91, "class_name": "scratch"},
        {"confidence": 0.80, "class_name": "void"},
    ])
    assert r["needs_review"] is False


def test_one_low_among_high_still_reviews():
    r = review_decision([
        {"confidence": 0.95, "class_name": "scratch"},
        {"confidence": 0.40, "class_name": "void"},
    ])
    assert r["needs_review"] is True
    assert "0.40" in r["reason"]   # worst confidence surfaced


def test_threshold_is_inclusive():
    # exactly 0.70 is NOT below threshold -> auto-acceptable
    r = review_decision([{"confidence": 0.70, "class_name": "scratch"}], threshold=0.70)
    assert r["needs_review"] is False
