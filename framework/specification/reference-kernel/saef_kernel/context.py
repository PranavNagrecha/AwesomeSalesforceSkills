from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from math import ceil
from typing import Iterable


@dataclass(frozen=True)
class ContextBudget:
    target_files: int = 8
    hard_files: int = 12
    max_tool_page_bytes: int = 32768
    output_reserve_fraction: float = 0.15

    def validate(self) -> None:
        if self.target_files < 1 or self.hard_files < self.target_files:
            raise ValueError("hard_files must be >= target_files >= 1")
        if self.max_tool_page_bytes < 1024:
            raise ValueError("max_tool_page_bytes must be at least 1024")
        if not 0 <= self.output_reserve_fraction <= 0.5:
            raise ValueError("output_reserve_fraction must be between 0 and 0.5")


@dataclass(frozen=True)
class ContextCandidate:
    id: str
    kind: str
    source: str
    reason: str
    content: str
    priority: int = 0
    relevance: float = 0.0
    required: bool = False

    @property
    def bytes(self) -> int:
        return len(self.content.encode("utf-8"))

    @property
    def estimated_tokens(self) -> int:
        return ceil(len(self.content) / 4)

    @property
    def digest(self) -> str:
        return sha256(self.content.encode("utf-8")).hexdigest()


def _sort_key(item: ContextCandidate) -> tuple:
    return (-int(item.required), -item.priority, -item.relevance, item.estimated_tokens, item.source, item.id)


def compile_context_manifest(
    run_id: str,
    stage: str,
    candidates: Iterable[ContextCandidate],
    budget: ContextBudget | None = None,
) -> dict:
    budget = budget or ContextBudget()
    budget.validate()
    unique: dict[str, ContextCandidate] = {}
    for candidate in candidates:
        existing = unique.get(candidate.id)
        if existing is None or _sort_key(candidate) < _sort_key(existing):
            unique[candidate.id] = candidate

    ordered = sorted(unique.values(), key=_sort_key)
    required = [x for x in ordered if x.required]
    optional = [x for x in ordered if not x.required]

    selected: list[ContextCandidate] = list(required)
    overflow = len(required) > budget.hard_files
    overflow_reason = None
    if overflow:
        overflow_reason = f"{len(required)} required files exceed hard limit {budget.hard_files}"
        selected = required[: budget.hard_files]
    else:
        desired = max(budget.target_files, len(required))
        for item in optional:
            if len(selected) >= desired:
                break
            selected.append(item)
        # Hard limit remains a safety check if callers intentionally raise target elsewhere.
        if len(selected) > budget.hard_files:
            selected = selected[: budget.hard_files]
            overflow = True
            overflow_reason = "selected context exceeded hard limit"

    items=[]
    for item in selected:
        items.append({
            "id": item.id,
            "kind": item.kind,
            "source": item.source,
            "reason": item.reason,
            "priority": item.priority,
            "required": item.required,
            "estimated_tokens": item.estimated_tokens,
            "bytes": item.bytes,
            "digest": item.digest,
            "conflicts_with": [],
        })
    return {
        "run_id": run_id,
        "stage": stage,
        "budget": asdict(budget),
        "items": items,
        "totals": {
            "files": len(items),
            "estimated_tokens": sum(x["estimated_tokens"] for x in items),
            "bytes": sum(x["bytes"] for x in items),
        },
        "overflow": overflow,
        "overflow_reason": overflow_reason,
        "candidate_count": len(unique),
        "omitted_count": max(0, len(unique)-len(items)),
    }


def bound_tool_payload(payload: bytes | str, max_bytes: int = 32768) -> tuple[bytes, bool]:
    data = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
    if len(data) <= max_bytes:
        return data, False
    return data[:max_bytes], True
