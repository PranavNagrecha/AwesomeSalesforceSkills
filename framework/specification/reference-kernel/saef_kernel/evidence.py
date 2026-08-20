from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def lint_claims(claims: Iterable[dict], evidence: Iterable[dict]) -> list[dict]:
    evidence_by_id={item.get("id"):item for item in evidence if item.get("id")}
    findings=[]
    for claim in claims:
        cid=claim.get("id","<missing>")
        links=claim.get("support") or []
        valid=[]
        for link in links:
            eid=link.get("evidence_id")
            if eid not in evidence_by_id:
                findings.append({"severity":"blocking","code":"missing_evidence_ref","claim_id":cid,"evidence_id":eid})
            else:
                valid.append((link,evidence_by_id[eid]))
        if claim.get("material") and claim.get("type") not in {"unknown"} and not valid:
            findings.append({"severity":"blocking","code":"unsupported_material_claim","claim_id":cid})
        if claim.get("status")=="supported" and any(link.get("relation")=="contradicts" for link,_ in valid):
            findings.append({"severity":"blocking","code":"supported_despite_contradiction","claim_id":cid})
        if claim.get("type")=="observation" and any(ev.get("source_type")=="model-inference" for _,ev in valid):
            findings.append({"severity":"blocking","code":"inference_used_as_observation","claim_id":cid})
        for _,ev in valid:
            if ev.get("classification")=="credential-secret":
                findings.append({"severity":"blocking","code":"secret_evidence_exposed","claim_id":cid,"evidence_id":ev.get("id")})
            if ev.get("truncated") and claim.get("confidence",{}).get("label")=="high":
                findings.append({"severity":"warning","code":"high_confidence_on_truncated_evidence","claim_id":cid,"evidence_id":ev.get("id")})
    return findings


def calculate_confidence(claim: dict, evidence_by_id: dict[str, dict], now: datetime | None = None) -> dict:
    now=now or datetime.now(timezone.utc)
    links=[x for x in claim.get("support",[]) if x.get("evidence_id") in evidence_by_id]
    if not links:
        return {"score":0.0,"label":"low","rationale":["No valid evidence links"]}
    scores=[]; rationale=[]; contradiction=False; truncated=False; stale=False
    for link in links:
        ev=evidence_by_id[link["evidence_id"]]
        authority=float(ev.get("authority",0))/5.0
        directness=float(ev.get("directness",0))/5.0
        score=0.55*authority+0.45*directness
        if link.get("relation")=="contradicts":
            contradiction=True
        if ev.get("truncated"):
            truncated=True; score-=0.15
        fresh_until=_parse_dt(ev.get("fresh_until"))
        if fresh_until and fresh_until < now:
            stale=True; score-=0.2
        scores.append(max(0.0,min(1.0,score)))
    score=sum(scores)/len(scores)
    if contradiction: score-=0.35
    score=max(0.0,min(1.0,score))
    if contradiction: rationale.append("Unresolved contradictory evidence")
    if truncated: rationale.append("One or more evidence items are truncated")
    if stale: rationale.append("One or more evidence items are stale")
    rationale.append(f"{len(links)} valid evidence link(s)")
    rationale.append(f"Mean authority/directness contribution {sum(scores)/len(scores):.2f}")
    label="high" if score>=0.8 and not contradiction else "medium" if score>=0.5 else "low"
    return {"score":round(score,4),"label":label,"rationale":rationale}
