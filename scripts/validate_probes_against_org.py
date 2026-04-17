#!/usr/bin/env python3
"""Validate every probe recipe's SOQL against a real Salesforce org.

Extracts every fenced SOQL block from `agents/_shared/probes/*.md`, swaps
placeholder values for discovered real ones (first User Id, first PSG Id,
etc.), and runs each query via `sf data query`. Classifies failures
against the six modes in `skills/admin/salesforce-object-queryability`.

This is the test that would have caught the ExampleOrg incident —
`PermissionSetGroupAssignment` would have failed here as Mode 1
(object doesn't exist) instead of failing in a customer's Cursor session.

Usage:
    python3 scripts/validate_probes_against_org.py --target-org sfskills-dev
    python3 scripts/validate_probes_against_org.py --target-org sfskills-dev --probe user-access-comparison
    python3 scripts/validate_probes_against_org.py --target-org sfskills-dev --out docs/validation/

The report is written to docs/validation/probe_report_<date>.md.
The script is READ-ONLY — it never issues DML.

Exit codes:
  0 — all queries classified as SUCCESS or EXPECTED-EMPTY
  1 — at least one query failed in an unexpected way
  2 — setup error (org not connected, sf CLI missing)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBES_DIR = REPO_ROOT / "agents" / "_shared" / "probes"
DEFAULT_OUT = REPO_ROOT / "docs" / "validation"

# Known placeholder patterns to swap for discovered values.
PLACEHOLDER_PATTERNS = [
    (re.compile(r"<user_a?_id>|<user_id>|<user_b_id>|'005[A-Za-z0-9]*'|:userId"), "user_id"),
    (re.compile(r"<username>"), "username"),
    (re.compile(r"<psg_name>"), "psg_name"),
    (re.compile(r"<every-effective-ps-id-across-both-users>|<effective-ps-ids>|<list-of-psg-ids-from-query-2>"), "ps_id_list"),
]


# ── sf CLI helpers ────────────────────────────────────────────────────────────

def sf_cli_available() -> bool:
    return shutil.which("sf") is not None


def sf_query(soql: str, target_org: str, tooling: bool = False) -> tuple[bool, dict]:
    """Run a SOQL query via sf CLI. Returns (success, parsed_json)."""
    cmd = ["sf", "data", "query", "--query", soql, "--target-org", target_org, "--json"]
    if tooling:
        cmd.insert(3, "--use-tooling-api")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, {"error": "TIMEOUT", "message": "Query exceeded 30s"}

    try:
        payload = json.loads(result.stdout) if result.stdout else json.loads(result.stderr)
    except json.JSONDecodeError:
        return False, {"error": "PARSE_ERROR", "message": result.stderr or result.stdout}

    if result.returncode == 0 and payload.get("status") == 0:
        return True, payload.get("result", {})
    return False, payload


# ── Failure classification (six modes) ────────────────────────────────────────

def classify_error(payload: dict) -> tuple[str, str]:
    """Map an sf CLI error payload to one of the six queryability modes.
    Returns (mode_id, human_explanation).
    """
    msg_all = json.dumps(payload).lower()

    # Extract the Salesforce error code if present.
    err_code = ""
    if isinstance(payload.get("message"), str):
        # Messages often look like: "INVALID_TYPE: sObject type 'X' is not supported."
        m = re.match(r"^([A-Z_]+):", payload["message"])
        if m:
            err_code = m.group(1)

    if "invalid_type" in msg_all or "sobject type" in msg_all and "not supported" in msg_all:
        return "MODE_1_OBJECT_DOES_NOT_EXIST", (
            "Object name not recognized by the org. Could be: hallucinated name, "
            "edition-gated object, managed-package namespace missing, or API version mismatch. "
            "Check `GET /sobjects/` listing to disambiguate."
        )
    if err_code == "INSUFFICIENT_ACCESS_OR_READONLY" or "insufficient" in msg_all:
        return "MODE_3_PERMISSION_DENIED", (
            "Query is well-formed but the running user lacks access. Not a query bug."
        )
    if err_code == "INVALID_FIELD" or "no such column" in msg_all or "invalid field" in msg_all:
        return "MODE_4_FIELD_LEVEL_ERROR", (
            "Object exists but a named field doesn't. Fix the projection."
        )
    if "can not be filtered" in msg_all or "cannot be filtered" in msg_all:
        return "MODE_4_FIELD_LEVEL_ERROR", (
            "Field exists but is not filterable in WHERE clauses. Fetch it in the "
            "projection and filter client-side (classic example: ApexClass.Body)."
        )
    if "query_timeout" in msg_all or "timeout" in msg_all:
        return "MODE_TRANSIENT_TIMEOUT", (
            "Query exceeded CPU budget. Narrow filter or add LIMIT."
        )
    if "malformed_query" in msg_all:
        return "MODE_4_FIELD_LEVEL_ERROR", (
            "SOQL syntax error."
        )
    return "MODE_UNCLASSIFIED", (
        "Did not match any of the six known failure modes. Review manually: " +
        str(payload)[:200]
    )


# ── Probe parsing ─────────────────────────────────────────────────────────────

# Strictly match ```sql or ```soql fences — NOT bare ``` fences. Probes use
# bare fences for regex patterns, JSON samples, and notes; those aren't SOQL.
_FENCE = re.compile(r"```(?:sql|soql)\s*\n(.*?)\n```", re.DOTALL)


def extract_queries(probe_md: Path) -> list[str]:
    """Return every fenced SOQL block from the probe markdown.

    Only blocks tagged `sql` or `soql` are extracted. Bare ``` fences are
    assumed to be regex patterns, JSON samples, or other non-SOQL content.
    """
    text = probe_md.read_text(encoding="utf-8")
    queries = []
    for q in _FENCE.findall(text):
        stripped = q.strip()
        # Drop any block that doesn't start with a SQL keyword.
        first_word = stripped.split(None, 1)[0].upper() if stripped else ""
        if first_word in {"SELECT", "FIND", "DESCRIBE"}:
            queries.append(stripped)
    return queries


def substitute_placeholders(soql: str, ctx: dict) -> tuple[str, list[str]]:
    """Replace placeholders with discovered values. Returns (substituted_soql, unfilled_placeholders).

    Key subtlety: probe authors sometimes write `<user_id>` (raw placeholder) and
    sometimes write `'<user_id>'` (quoted placeholder). The substitution must NOT
    double-quote — it checks the surrounding characters and emits a single-quoted
    string or a bare Id as appropriate.
    """
    out = soql

    def _replace_id_placeholder(match_str: str, value: str, text: str) -> str:
        """Replace a placeholder with a quoted Id, taking care of existing quotes."""
        # Find every occurrence and decide per-site.
        result_chunks = []
        cursor = 0
        pattern = re.compile(re.escape(match_str))
        for m in pattern.finditer(text):
            start, end = m.span()
            # Peek one char on each side.
            pre = text[start - 1] if start > 0 else ""
            post = text[end] if end < len(text) else ""
            if pre == "'" and post == "'":
                # Already quoted → substitute value only (no extra quotes).
                result_chunks.append(text[cursor:start])
                result_chunks.append(value)
            else:
                result_chunks.append(text[cursor:start])
                result_chunks.append(f"'{value}'")
            cursor = end
        result_chunks.append(text[cursor:])
        return "".join(result_chunks)

    if "user_id" in ctx:
        for placeholder in ("<user_a_id>", "<user_b_id>", "<user_id>"):
            out = _replace_id_placeholder(placeholder, ctx["user_id"], out)
        out = re.sub(r":userId\b", f"'{ctx['user_id']}'", out)
    if "username" in ctx:
        out = out.replace("<username>", ctx["username"])
    if "psg_name" in ctx:
        out = out.replace("<psg_name>", ctx["psg_name"])

    # Context-aware id-list placeholder substitution. Probes sometimes write
    # `'<id>'` (quoted) and sometimes write `IN (<ids>)` (unquoted). We must
    # not double-quote. Use the same peek-for-surrounding-quotes trick.
    def _replace_placeholder_context_aware(placeholder: str, value: str, text: str) -> str:
        result = []
        cursor = 0
        for m in re.finditer(re.escape(placeholder), text):
            start, end = m.span()
            pre = text[start - 1] if start > 0 else ""
            post = text[end] if end < len(text) else ""
            if pre == "'" and post == "'":
                result.append(text[cursor:start] + value)
            else:
                result.append(text[cursor:start] + f"'{value}'")
            cursor = end
        result.append(text[cursor:])
        return "".join(result)

    # Id-list placeholders that the probes use.
    for ph in ["<ids>", "<list-of-psg-ids-from-query-2>",
               "<list-of-psg-ids>", "<every-effective-ps-id-across-both-users>",
               "<effective-ps-ids>", "<id>", "<psg_id>"]:
        if ph in out:
            out = _replace_placeholder_context_aware(ph, "001000000000000", out)

    # Generic object placeholder fallback.
    out = out.replace("<object>", "Account")
    # Field-reference probe parameters (apex-references-to-field probe).
    out = out.replace("<field>", "Industry")
    out = out.replace("<managed_filter>", "NamespacePrefix = null")
    out = out.replace("<limit_per_query>", "5")
    out = out.replace("<offset>", "0")

    # Flag anything still unfilled.
    leftover = re.findall(r"<[a-zA-Z_-]+>", out)
    unfilled = sorted(set(leftover))
    return out, unfilled


# ── Context discovery ─────────────────────────────────────────────────────────

def discover_context(target_org: str) -> dict:
    """Find real Ids/usernames to use in probe queries."""
    ctx = {}
    ok, result = sf_query("SELECT Id, Username FROM User WHERE IsActive = true LIMIT 1", target_org)
    if ok and result.get("records"):
        rec = result["records"][0]
        ctx["user_id"] = rec["Id"]
        ctx["username"] = rec["Username"]
    ok, result = sf_query("SELECT DeveloperName FROM PermissionSetGroup LIMIT 1", target_org)
    if ok and result.get("records"):
        ctx["psg_name"] = result["records"][0]["DeveloperName"]
    return ctx


# ── Query execution ──────────────────────────────────────────────────────────

# Objects that are Tooling-API-only; route these directly without a Data API round-trip.
TOOLING_ONLY_OBJECTS = {
    "ApexClass", "ApexTrigger", "ApexPage", "ApexComponent", "Flow",
    "FlowDefinition", "ValidationRule", "RoutingConfiguration",
    "WorkflowRule", "CustomField", "EntityDefinition", "FieldDefinition",
}

# Objects that only exist when a platform feature is enabled. Mode 1 failure on
# these is not a probe bug — the probe MUST document this gating. The validator
# surfaces these as EXPECTED-SKIP instead of FAILED.
FEATURE_GATED_OBJECTS = {
    "UserTerritory2Association": "Enterprise Territory Management",
    "Territory2Model": "Enterprise Territory Management",
    "Territory2": "Enterprise Territory Management",
    "ServiceAppointment": "Field Service",
    "ServiceTerritory": "Field Service",
    "WorkOrder": "Service Cloud or Field Service",
    "HealthCondition": "Health Cloud",
    "PatientMedicationDosage": "Health Cloud",
    "LiveChatTranscript": "Chat / Messaging",
    "MessagingSession": "Messaging",
}


def _likely_tooling_only(soql: str) -> bool:
    """True if the main FROM clause references a Tooling-API-only object."""
    m = re.search(r"\bFROM\s+([A-Za-z_0-9]+)", soql, re.IGNORECASE)
    if not m:
        return False
    return m.group(1) in TOOLING_ONLY_OBJECTS


def _feature_gate_for_soql(soql: str) -> str | None:
    """If the FROM clause targets a feature-gated object, return the feature name."""
    m = re.search(r"\bFROM\s+([A-Za-z_0-9]+)", soql, re.IGNORECASE)
    if not m:
        return None
    return FEATURE_GATED_OBJECTS.get(m.group(1))


def run_query_with_retry(soql: str, target_org: str) -> tuple[str, str, dict]:
    """Try Data API first; if INVALID_TYPE, retry via Tooling API.
    Returns (status, explanation, raw_payload).
    Status: SUCCESS | EMPTY-RESULT | FAILED | SUCCESS-VIA-TOOLING
    """
    # Route Tooling-only objects directly.
    if _likely_tooling_only(soql):
        ok, payload = sf_query(soql, target_org, tooling=True)
        if ok:
            count = payload.get("totalSize", 0) if isinstance(payload, dict) else 0
            if count == 0:
                return "EMPTY-RESULT", f"Query succeeded via Tooling API, 0 rows", payload
            return "SUCCESS-VIA-TOOLING", f"Query succeeded via Tooling API, {count} row(s)", payload
        mode, explanation = classify_error(payload)
        return "FAILED", f"{mode}: {explanation}", payload

    ok, payload = sf_query(soql, target_org, tooling=False)
    if ok:
        count = payload.get("totalSize", 0) if isinstance(payload, dict) else 0
        if count == 0:
            return "EMPTY-RESULT", f"Query succeeded, 0 rows", payload
        return "SUCCESS", f"Query succeeded, {count} row(s)", payload

    mode, explanation = classify_error(payload)
    if mode == "MODE_1_OBJECT_DOES_NOT_EXIST":
        # Before declaring a failure, check whether this is a known feature-gated object.
        feature = _feature_gate_for_soql(soql)
        if feature:
            return "EXPECTED-SKIP", f"Object is gated by '{feature}' which is not enabled in this org (correct behavior, not a probe bug)", payload
        # Retry via Tooling API.
        ok2, payload2 = sf_query(soql, target_org, tooling=True)
        if ok2:
            count = payload2.get("totalSize", 0)
            return "SUCCESS-VIA-TOOLING", f"Query succeeded via Tooling API, {count} row(s)", payload2

    return "FAILED", f"{mode}: {explanation}", payload


# ── Report generation ────────────────────────────────────────────────────────

def render_report(runs: list[dict], org_info: dict, out_path: Path) -> None:
    today = dt.date.today().isoformat()
    total = len(runs)
    success = sum(1 for r in runs if r["status"] in {"SUCCESS", "EMPTY-RESULT", "SUCCESS-VIA-TOOLING", "EXPECTED-SKIP"})
    failed = total - success

    lines: list[str] = []
    lines.append(f"# Probe Validation Report — {today}")
    lines.append("")
    lines.append("**Status:** Wave 9 live-org validation")
    lines.append(f"**Org alias:** `{org_info.get('alias', 'unknown')}`")
    lines.append(f"**Org Id:** `{org_info.get('id', 'unknown')}`")
    lines.append(f"**API version:** `{org_info.get('apiVersion', 'unknown')}`")
    lines.append(f"**Total queries tested:** {total}")
    lines.append(f"**Passed:** {success} ({success / total * 100:.0f}% if total else 0)")
    lines.append(f"**Failed:** {failed}")
    lines.append("")
    lines.append("Validated by `scripts/validate_probes_against_org.py`. Re-run on any probe edit.")
    lines.append("")
    lines.append("---")
    lines.append("")

    by_probe: dict[str, list[dict]] = {}
    for r in runs:
        by_probe.setdefault(r["probe"], []).append(r)

    for probe_name, probe_runs in sorted(by_probe.items()):
        lines.append(f"## Probe: `{probe_name}`")
        lines.append("")
        probe_pass = sum(1 for r in probe_runs if r["status"] in {"SUCCESS", "EMPTY-RESULT", "SUCCESS-VIA-TOOLING", "EXPECTED-SKIP"})
        lines.append(f"**Queries:** {len(probe_runs)} — **Passed:** {probe_pass} — **Failed:** {len(probe_runs) - probe_pass}")
        lines.append("")
        lines.append("| # | Status | Explanation |")
        lines.append("|---|---|---|")
        for i, r in enumerate(probe_runs, 1):
            status_icon = {
                "SUCCESS": "✅ success",
                "EMPTY-RESULT": "⚠️ empty",
                "SUCCESS-VIA-TOOLING": "✅ tooling",
                "EXPECTED-SKIP": "⏭️ feature-gated",
                "FAILED": "❌ FAIL",
            }.get(r["status"], r["status"])
            expl = r["explanation"][:200]
            lines.append(f"| {i} | {status_icon} | {expl} |")
        lines.append("")

        # Detail any failures inline for quick fix.
        failed_here = [r for r in probe_runs if r["status"] == "FAILED"]
        if failed_here:
            lines.append("### Failures detail")
            lines.append("")
            for r in failed_here:
                lines.append(f"**Query #{r['query_index']}** (classified as `{r['mode']}`):")
                lines.append("```sql")
                lines.append(r["soql"][:500])
                lines.append("```")
                lines.append(f"- **Explanation:** {r['explanation']}")
                if r.get("unfilled_placeholders"):
                    lines.append(f"- **Unfilled placeholders:** {', '.join(r['unfilled_placeholders'])}")
                lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Takeaways")
    lines.append("")
    if failed == 0:
        lines.append("All probe queries validated successfully. No Mode 1 hallucinations detected.")
    else:
        lines.append(f"{failed} quer(y|ies) failed. Each failure is classified against the six modes "
                     f"from `skills/admin/salesforce-object-queryability`. Review the Failures Detail "
                     f"sections above and patch the probe recipes.")
    lines.append("")
    lines.append("### What passing means")
    lines.append("")
    lines.append("- ✅ **SUCCESS** — query executed, returned rows.")
    lines.append("- ⚠️ **EMPTY-RESULT** — query executed, returned zero rows (structurally valid; org may simply not have matching data).")
    lines.append("- ✅ **SUCCESS-VIA-TOOLING** — query failed on Data API, succeeded on Tooling API (the probe recipe should document this).")
    lines.append("- ❌ **FAILED** — classified error (see mode). Requires probe fix or explicit documentation that this org lacks the feature.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate probe SOQL against a live Salesforce org.")
    parser.add_argument("--target-org", required=True, help="sf CLI org alias")
    parser.add_argument("--probe", help="Validate one probe instead of all")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Report output directory")
    args = parser.parse_args()

    if not sf_cli_available():
        print("ERROR: `sf` CLI not found in PATH. Install Salesforce CLI first.", file=sys.stderr)
        return 2

    # Verify org is connected.
    result = subprocess.run(
        ["sf", "org", "display", "--target-org", args.target_org, "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: org '{args.target_org}' is not reachable.\n{result.stderr}", file=sys.stderr)
        return 2
    org_info = json.loads(result.stdout)["result"]
    print(f"✓ Connected to {org_info.get('alias')} ({org_info.get('id')}) @ API v{org_info.get('apiVersion')}")

    ctx = discover_context(args.target_org)
    print(f"✓ Context discovered: {list(ctx.keys())}")

    probe_files = sorted(PROBES_DIR.glob("*.md"))
    if args.probe:
        probe_files = [p for p in probe_files if p.stem == args.probe]
        if not probe_files:
            print(f"No probe named '{args.probe}'", file=sys.stderr)
            return 2
    # Exclude README.
    probe_files = [p for p in probe_files if p.stem != "README"]

    runs: list[dict] = []
    for probe_md in probe_files:
        queries = extract_queries(probe_md)
        print(f"\n→ {probe_md.stem}: {len(queries)} quer(y|ies)")
        for i, raw_soql in enumerate(queries, 1):
            substituted, unfilled = substitute_placeholders(raw_soql, ctx)
            status, explanation, payload = run_query_with_retry(substituted, args.target_org)
            mode = ""
            if status == "FAILED":
                mode, _ = classify_error(payload)
            runs.append({
                "probe": probe_md.stem,
                "query_index": i,
                "soql": substituted,
                "raw_soql": raw_soql,
                "status": status,
                "explanation": explanation,
                "mode": mode,
                "unfilled_placeholders": unfilled,
            })
            icon = {
                "SUCCESS": "✅",
                "EMPTY-RESULT": "⚠️ empty",
                "SUCCESS-VIA-TOOLING": "✅ tooling",
                "EXPECTED-SKIP": "⏭️ skip",
                "FAILED": "❌",
            }.get(status, "?")
            print(f"   {icon}  Q{i}: {explanation[:90]}")

    # Write report.
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"probe_report_{dt.date.today().isoformat()}.md"
    render_report(runs, org_info, report_path)
    print(f"\n✓ Report written to {report_path.relative_to(REPO_ROOT) if report_path.is_relative_to(REPO_ROOT) else report_path}")

    failed = [r for r in runs if r["status"] == "FAILED"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
