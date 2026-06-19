"""Unit tests for the line_id allowlist guard.

`safe_line_id` is the only user-supplied value interpolated into ClickHouse SQL
(time windows are bound as parameters). This is the SQL-injection boundary, so
it gets explicit coverage.
"""
import pathlib
import sys

import pytest

API = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API))

from db import clickhouse  # noqa: E402


@pytest.mark.parametrize("ok", ["line-1", "line_2", "L3", "abc-123", "A" * 40])
def test_valid_line_ids_pass(ok):
    assert clickhouse.safe_line_id(ok) == ok


@pytest.mark.parametrize("bad", [
    "line-1' OR 1=1--",     # quote-based injection
    "a; DROP TABLE x",      # statement injection
    ") OR 1=1--",           # quoteless injection
    "line 1",               # space
    "",                     # empty
    "A" * 41,               # over length cap
    "lïne",                 # non-ascii
])
def test_injection_and_invalid_rejected(bad):
    with pytest.raises(clickhouse.BadLineID):
        clickhouse.safe_line_id(bad)
