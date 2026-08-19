"""Salesforce Metadata API deploy job-id checks.

Deploy / validation IDs from the Metadata API are 15- or 18-character Ids
that start with ``0Af``. The product never guesses a job id and never uses
``--use-most-recent``.
"""

from __future__ import annotations

import re

_JOB_ID_RE = re.compile(r"^0Af[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?$")


def normalize_job_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    return value


def is_well_formed_job_id(raw: str | None) -> bool:
    value = normalize_job_id(raw)
    if value is None:
        return False
    return bool(_JOB_ID_RE.match(value))
