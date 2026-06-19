"""Run the golden eval against a live FactoryOps API.

Posts each question to /copilot/chat and scores it on:
  * tool grounding — required tool(s) appear in the answer's tool_trace
    (all of them, or any one when "match_any_tool" is set)
  * key terms   — every string in must_include appears in the answer

Prints per-case PASS/FAIL and an overall pass rate; exits non-zero below the
0.80 target so it can gate CI.

    python eval/run_eval.py --api http://localhost:8000
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import httpx

TARGET = 0.80
HERE = pathlib.Path(__file__).parent


def score_case(case: dict, resp: dict) -> tuple[bool, str]:
    answer = (resp.get("answer") or "").lower()
    tools = {t["tool"] for t in resp.get("tool_trace", [])}

    expect = case.get("expect_tools", [])
    if expect:
        if case.get("match_any_tool"):
            if not (set(expect) & tools):
                return False, f"no expected tool called (wanted any of {expect}, got {sorted(tools)})"
        else:
            missing = set(expect) - tools
            if missing:
                return False, f"missing tools {sorted(missing)} (got {sorted(tools)})"

    for term in case.get("must_include", []):
        if term.lower() not in answer:
            return False, f"answer missing term {term!r}"
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    cases = json.loads((HERE / "golden.json").read_text())["cases"]
    passed = 0
    with httpx.Client(timeout=60.0) as client:
        for i, case in enumerate(cases, 1):
            try:
                r = client.post(f"{args.api}/copilot/chat",
                                json={"question": case["q"]})
                r.raise_for_status()
                ok, reason = score_case(case, r.json())
            except httpx.HTTPError as exc:
                ok, reason = False, f"request failed: {exc}"
            passed += ok
            mark = "PASS" if ok else "FAIL"
            print(f"[{mark}] {i:2d}. {case['q']}")
            if not ok or args.verbose:
                print(f"        -> {reason}")

    rate = passed / len(cases)
    print(f"\n{passed}/{len(cases)} passed = {rate:.0%} (target {TARGET:.0%})")
    return 0 if rate >= TARGET else 1


if __name__ == "__main__":
    sys.exit(main())
