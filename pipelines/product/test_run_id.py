"""Salesforce Apex test run id checks.

Async Apex test run ids are 15- or 18-character Ids that start with ``707``.
The product never guesses a run id and never starts a test run.
"""

from __future__ import annotations

import re

_TEST_RUN_ID_RE = re.compile(r"^707[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?$")


def normalize_test_run_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    return value


def is_well_formed_test_run_id(raw: str | None) -> bool:
    value = normalize_test_run_id(raw)
    if value is None:
        return False
    return bool(_TEST_RUN_ID_RE.match(value))
