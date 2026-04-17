#!/usr/bin/env python3
"""Wave 10 follow-up: add a Dimensions sub-section under each multi-dimensional
agent's Output Contract.

This is agent-specific content (each agent has a different dimension set),
so the dimensions are hand-curated here rather than auto-generated.

Idempotent. Skips agents whose Output Contract already mentions "Dimensions"
or "dimensions_compared".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"


DIMENSIONS_BY_AGENT = {
    "user-access-diff": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`. Partial or count-only coverage is recorded with `state: count-only | partial`, not elided.

| Dimension | Notes |
|---|---|
| `profile` | Profile ID + name |
| `permission-sets` | Direct PSA rows (excluding expired) |
| `psg-components` | Flattened via `PermissionSetGroupComponent` |
| `object-crud` | Per-sObject read/create/edit/delete/view-all/modify-all |
| `fls` | Opt-in via `include_field_permissions=true`; default `state: not-run` with `confidence_impact: NONE` |
| `system-perms` | ModifyAllData, ViewAllUsers, AuthorApex, etc. |
| `apex-classes` | SetupEntityAccess where SetupEntityType='ApexClass' |
| `vf-pages` | SetupEntityAccess where SetupEntityType='ApexPage' |
| `flow-access` | SetupEntityAccess where SetupEntityType='FlowDefinition' |
| `custom-perms` | SetupEntityAccess where SetupEntityType='CustomPermission' |
| `named-credentials` | SetupEntityAccess where SetupEntityType IN ('NamedCredential', 'ExternalDataSource') |
| `public-groups` | GroupMember where Group.Type='Regular' |
| `queues` | GroupMember where Group.Type='Queue' |
| `territories` | `UserTerritory2Association`; `state: not-run` when ETM not enabled |
""",

    "deployment-risk-scorer": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `metadata-surface` | Components in the deployment package |
| `test-coverage-delta` | Projected change in org coverage |
| `destructive-changes` | Removals + dependents |
| `cross-object-refs` | Apex/Flow references across the package boundary |
| `permission-churn` | PS / PSG / Profile drift |
| `production-traffic-impact` | Touched objects' production write volume |
| `rollback-feasibility` | Whether the package is safely reversible |
""",

    "security-scanner": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `apex-crud-fls` | CRUD/FLS enforcement in Apex |
| `soql-injection` | Dynamic-SOQL concatenation smells |
| `callout-auth` | Named Credential vs hard-coded endpoints |
| `sharing-posture` | `with sharing` / `without sharing` / inherited |
| `open-redirects` | Redirect params without validation |
| `exposed-endpoints` | Site / Guest-user-exposed Apex |
| `secret-leakage` | Logged tokens, hard-coded keys |
""",

    "audit-router": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every classifier below in either `dimensions_compared[]` or `dimensions_skipped[]`. Classifier state reflects whether the underlying probe ran fully, partially, or not at all.

Domain classifiers (one dimension per `--domain` value):
`validation_rule`, `picklist`, `approval_process`, `record_type_layout`, `report_dashboard`, `case_escalation`, `lightning_record_page`, `list_view_search_layout`, `quick_action`, `report_folder_sharing`, `field_history`, `sharing`, `org_drift`, `my_domain_session`, `prompt_library`.
""",

    "field-impact-analyzer": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `apex-references` | ApexClass/Trigger Body mentions via probe |
| `flow-references` | Flow Metadata XML mentions |
| `validation-rules` | VR formulas referencing the field |
| `reports-dashboards` | Reports + dashboard filters using the field |
| `layouts` | Page layouts / compact layouts placing the field |
| `permission-sets` | PS + profile grants on the field |
| `data-exports` | Recent export jobs referencing the field |
| `external-integrations` | CDC / PE / REST mappings exposing the field |
""",

    "waf-assessor": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every Well-Architected pillar below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `security` | FLS, sharing, auth, secret handling |
| `reliability` | Fault paths, governor headroom, recovery |
| `performance` | SOQL selectivity, CPU, heap |
| `scalability` | LDV patterns, bulk safety, async design |
| `user-experience` | Path guidance, navigation, error messaging |
| `operational-excellence` | Monitoring, deploy hygiene, incident runbooks |
""",

    "data-model-reviewer": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `object-design` | Standard vs custom, record-type usage, fields |
| `relationships` | Lookup vs master-detail vs junction |
| `sharing-posture` | OWD + sharing rules + teams |
| `indexes` | Custom indexes, skinny tables, LDV markers |
| `history-tracking` | Field History + Audit Trail configuration |
| `external-id-coverage` | Upsert-ready external IDs per integration |
| `validation-rule-hygiene` | VR count, bypass pattern compliance |
""",

    "profile-to-permset-migrator": """
### Dimensions (Wave 10 contract)

The agent's envelope MUST place every permission category below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `object-crud` | Per-sObject CRUD from profile → target PS |
| `fls` | Per-field permissions |
| `system-permissions` | Boolean system flags |
| `apex-class-access` | SetupEntityAccess (ApexClass) |
| `vf-page-access` | SetupEntityAccess (ApexPage) |
| `tab-settings` | Tab visibility |
| `app-access` | App visibility |
| `custom-permissions` | SetupEntityAccess (CustomPermission) |
| `named-credentials` | SetupEntityAccess (NamedCredential) |
| `residue` | License + default RT + default app + page layouts + login IP/hours + session (stays on profile) |
""",
}


def inject_dimensions(path: Path, agent_id: str, block: str) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8")

    if "### Dimensions" in text or "dimensions_compared" in text:
        return "already-has-dimensions", False

    # Find the "## Output Contract" section.
    m = re.search(r"^(##\s+Output Contract)$", text, re.MULTILINE)
    if not m:
        return "no-output-contract-section", False

    section_start = m.end()
    next_heading = re.search(r"^## ", text[section_start:], re.MULTILINE)
    section_end = section_start + next_heading.start() if next_heading else len(text)

    # Insert before the next "## " heading.
    insertion = block.strip() + "\n\n"
    new_text = text[:section_end].rstrip() + "\n\n" + insertion + text[section_end:]

    path.write_text(new_text, encoding="utf-8")
    return "updated", True


def main() -> int:
    for agent_id, block in DIMENSIONS_BY_AGENT.items():
        path = AGENTS_DIR / agent_id / "AGENT.md"
        if not path.exists():
            print(f"  SKIP {agent_id}: no AGENT.md")
            continue
        status, changed = inject_dimensions(path, agent_id, block)
        verb = "✓ injected" if changed else f"— {status}"
        print(f"  {verb} — {agent_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
