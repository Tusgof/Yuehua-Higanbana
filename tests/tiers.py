from __future__ import annotations

import unittest
import os
from pathlib import Path
from typing import TypeVar


TestType = TypeVar("TestType")


def state_audit(*requirements: tuple[str, Path]):
    missing = [f"{name}={path}" for name, path in requirements if not path.exists()]
    forced_hermetic = os.environ.get("HIGANBANA_TEST_TIER") == "hermetic"
    reason = (
        "state-audit skipped by hermetic tier"
        if forced_hermetic
        else "state-audit skipped; missing root/input: " + ", ".join(missing)
    )

    def decorate(test: TestType) -> TestType:
        setattr(test, "higanbana_test_tier", "state-audit")
        return unittest.skipUnless(not forced_hermetic and not missing, reason)(test)

    return decorate


def state_audit_capability(name: str, available: bool):
    reason = f"state-audit skipped; missing optional capability: {name}"

    def decorate(test: TestType) -> TestType:
        setattr(test, "higanbana_test_tier", "state-audit")
        return unittest.skipUnless(available, reason)(test)

    return decorate
