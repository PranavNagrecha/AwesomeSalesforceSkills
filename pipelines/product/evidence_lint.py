"""Deterministic evidence lint for deployment triage drafts."""

from __future__ import annotations

import re
from typing import Any

_HIGH_CONFIDENCE = {"HIGH", "VERY_HIGH", "CERTAIN"}
_ALLOWED_STATUS = {"completed", "partial", "refused", "failed"}
_UNSAFE_REMEDIATION_MARKERS = (
    "sf project deploy start",
    "sf project deploy validate",
    "sf project deploy quick",
    "sf project deploy cancel",
    "sf project deploy resume",
    "sf apex run test",
    "sf apex run ",
)
_SECRET_RE = re.compile(
    r"(sfdxAuthUrl|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|Bearer\s+ey[A-Za-z0-9_-]+\.)",
    re.IGNORECASE,
)
_BANNED_FIELDS = ("transcript", "chain_of_thought", "hidden_reasoning", "full_chat_history")


def _is_high_confidence(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return float(value) >= 0.9
    return str(value).strip().upper() in _HIGH_CONFIDENCE


def _refs(container: Any) -> list[Any]:
    if not isinstance(container, dict):
        return []
    refs = container.get("evidence_refs") or container.get("evidence_ids") or []
    if isinstance(refs, list):
        return refs
    return [refs] if refs else []


def _iter_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, str):
        found.append((path, value))
    elif isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path != "$" else key
            found.extend(_iter_strings(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_iter_strings(item, f"{path}[{index}]"))
    return found


def _evidence_universe(draft: dict) -> set[str]:
    ids: set[str] = set()
    for key in ("evidence_index", "evidence_ids", "evidence_refs"):
        value = draft.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    ids.add(item)
                elif isinstance(item, dict) and item.get("id"):
                    ids.add(str(item["id"]))
        elif isinstance(value, dict):
            ids.update(str(k) for k in value.keys())
    for group in draft.get("groups") or []:
        if isinstance(group, dict):
            ids.update(str(x) for x in _refs(group))
            if group.get("group_id"):
                ids.add(str(group["group_id"]))
            for eid in group.get("evidence_ids") or []:
                ids.add(str(eid))
    for failure in draft.get("component_failures") or []:
        if isinstance(failure, dict) and failure.get("evidence_id"):
            ids.add(str(failure["evidence_id"]))
    ids.update(str(x) for x in _refs(draft))
    return ids


def lint_diagnosis(draft: dict, *, evidence_ids: list[str] | None = None) -> dict:
    """Return a deterministic lint verdict for a triage draft."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(draft, dict):
        errors.append({"code": "invalid_draft", "path": "$", "message": "draft must be an object"})
        return {
            "ok": False,
            "passed": False,
            "verdict": "fail",
            "issues": errors,
            "errors": errors,
            "warnings": warnings,
            "stats": {"error_count": 1},
        }

    for banned in _BANNED_FIELDS:
        if banned in draft:
            errors.append(
                {
                    "code": "banned_field",
                    "path": banned,
                    "message": f"handoff/draft must not include {banned}",
                }
            )

    universe = _evidence_universe(draft)
    if evidence_ids:
        universe.update(str(x) for x in evidence_ids)

    status = draft.get("status") or draft.get("outcome")
    if status is not None and str(status).lower() not in _ALLOWED_STATUS:
        errors.append(
            {
                "code": "invalid_status",
                "path": "status",
                "message": "status/outcome must be completed|partial|refused|failed",
            }
        )

    mapping_unavailable = any(
        "local_mapping_unavailable" in str(item) for item in (draft.get("unknowns") or [])
    )
    for path, text in _iter_strings(draft.get("local_paths") or []):
        if mapping_unavailable and text:
            errors.append(
                {
                    "code": "invented_local_path",
                    "path": path,
                    "message": "source paths are asserted while project inspection was unavailable",
                }
            )

    hypotheses = draft.get("hypotheses") or []
    if isinstance(hypotheses, list):
        for index, hypothesis in enumerate(hypotheses):
            if not isinstance(hypothesis, dict):
                continue
            refs = _refs(hypothesis) or _refs(draft)
            if _is_high_confidence(hypothesis.get("confidence")) and not refs:
                errors.append(
                    {
                        "code": "unsupported_high_confidence",
                        "path": f"hypotheses[{index}]",
                        "message": "HIGH-confidence hypothesis lacks evidence_refs or evidence_ids",
                    }
                )
            for ref in refs:
                if universe and str(ref) not in universe:
                    errors.append(
                        {
                            "code": "unknown_evidence_id",
                            "path": f"hypotheses[{index}]",
                            "message": f"referenced evidence id {ref!r} is not in the evidence set",
                        }
                    )
            if _is_high_confidence(hypothesis.get("confidence")) and (
                mapping_unavailable or draft.get("truncated") or (draft.get("unknowns") or [])
            ):
                if draft.get("truncated") or mapping_unavailable:
                    errors.append(
                        {
                            "code": "overconfident_incomplete_evidence",
                            "path": f"hypotheses[{index}].confidence",
                            "message": "confidence is HIGH while evidence is truncated or mapping is unavailable",
                        }
                    )

    facts = draft.get("facts") or []
    if isinstance(facts, list):
        for index, fact in enumerate(facts):
            if not isinstance(fact, dict):
                continue
            if "claim" not in fact:
                continue
            refs = _refs(fact)
            if not refs:
                errors.append(
                    {
                        "code": "missing_fact_citation",
                        "path": f"facts[{index}]",
                        "message": "material fact claim lacks evidence_refs",
                    }
                )

    findings = draft.get("findings") or []
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            if not _refs(finding) and finding.get("severity") in {"critical", "high", "HIGH"}:
                errors.append(
                    {
                        "code": "unsupported_material_claim",
                        "path": f"findings[{index}]",
                        "message": "material finding lacks evidence_ids",
                    }
                )

    if (not _refs(draft) and not universe) and hypotheses:
        warnings.append(
            {
                "code": "missing_unknowns",
                "path": "unknowns",
                "message": "unknowns should be present when evidence is incomplete",
            }
        )

    marked_forbidden = False
    for path, text in _iter_strings(draft):
        if _SECRET_RE.search(text):
            errors.append(
                {
                    "code": "secret_shaped_value",
                    "path": path,
                    "message": "secret-shaped value present",
                }
            )
        lowered = text.lower()
        for marker in _UNSAFE_REMEDIATION_MARKERS:
            if marker.strip() in lowered:
                if "shown" in lowered or "not run" in lowered or "forbidden" in lowered:
                    marked_forbidden = True
                    continue
                errors.append(
                    {
                        "code": "unsafe_remediation",
                        "path": path,
                        "message": f"draft recommends forbidden command: {marker}",
                    }
                )
                break

    _ = marked_forbidden
    passed = not errors
    return {
        "ok": passed,
        "passed": passed,
        "verdict": "pass" if passed else "fail",
        "issues": errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {"error_count": len(errors), "warning_count": len(warnings)},
    }
