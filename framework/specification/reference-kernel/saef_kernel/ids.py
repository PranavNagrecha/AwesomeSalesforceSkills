from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: Any) -> str:
    payload = value if isinstance(value, (bytes, bytearray)) else canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stable_evidence_id(source_type: str, source_locator: str, content: Any) -> str:
    digest = sha256_hex({"source_type": source_type, "source_locator": source_locator, "content": content})
    return "EV-" + digest[:24].upper()


def stable_claim_id(product_id: str, claim_type: str, text: str) -> str:
    digest = sha256_hex({"product_id": product_id, "type": claim_type, "text": " ".join(text.split())})
    return "CL-" + digest[:24].upper()


def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"RUN-{stamp}-{uuid.uuid4().hex[:10].upper()}"
