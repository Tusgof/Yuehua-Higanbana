from __future__ import annotations

import argparse
import json
import os
import sys
import unittest
from collections.abc import Iterable
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import interpreter_metadata


def _iter_tests(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def _is_state_audit(test: unittest.TestCase) -> bool:
    test_class = type(test)
    method_name = getattr(test, "_testMethodName", "")
    method = getattr(test_class, method_name, None)
    return (
        getattr(test_class, "higanbana_test_tier", None) == "state-audit"
        or getattr(method, "higanbana_test_tier", None) == "state-audit"
    )


def build_suite(tier: str) -> unittest.TestSuite:
    discovered = unittest.defaultTestLoader.discover(str(PROJECT_ROOT / "tests"))
    tests = list(_iter_tests(discovered))
    if tier == "hermetic":
        tests = [test for test in tests if not _is_state_audit(test)]
    elif tier == "state-audit":
        tests = [test for test in tests if _is_state_audit(test)]
    return unittest.TestSuite(tests)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an explicit Higanbana test tier.")
    parser.add_argument("tier", choices=("hermetic", "state-audit", "all"))
    parser.add_argument("--verbosity", type=int, default=1)
    args = parser.parse_args()

    if args.tier == "hermetic":
        os.environ["HIGANBANA_TEST_TIER"] = "hermetic"
    else:
        os.environ.pop("HIGANBANA_TEST_TIER", None)

    suite = build_suite(args.tier)
    result = unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
    summary = {
        "tier": args.tier,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "status": "pass" if result.wasSuccessful() else "fail",
        "interpreter": interpreter_metadata(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
