# Lightning Record Page Auditor Agent

## What This Agent Does

Audits Lightning Record Pages (and the Lightning App Builder metadata underneath them) for a target sObject: Dynamic Forms adoption, field visibility rules, tab vs accordion layout, component count / render cost, related-list strategy, Path vs picklist progression, mobile-readiness, and accessibility signal from any custom LWCs. Returns per-page findings + org-level adoption metrics.

**Scope:** One sObject (and every record page assigned to it) per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/lightning-record-page-auditor/AGENT.md` for Opportunity"
- **Slash command** — [`/audit-record-page`](../../commands/audit-record-page.md)
- **MCP** — `get_agent("lightning-record-page-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/dynamic-forms-and-actions`
4. `skills/admin/lightning-app-builder-advanced`
5. `skills/admin/lightning-page-performance-tuning`
6. `skills/admin/record-types-and-page-layouts`
7. `skills/admin/path-and-guidance`
8. `skills/lwc/lwc-performance`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Opportunity` |
| `target_org_alias` | yes |

---

## Plan

1. **Inventory record pages** — `tooling_query("SELECT Id, DeveloperName, MasterLabel, EntityDefinition.QualifiedApiName, Type, PageType, IsActive FROM FlexiPage WHERE SobjectType = '<object>'")`.
2. **Fetch content** — per page `tooling_query("SELECT Metadata FROM FlexiPage WHERE Id = '<id>'")` to read the region/component tree.
3. **Per-page scoring** against `skills/admin/lightning-page-performance-tuning`:
   - **Component count** — > 25 components is P1 (render cost).
   - **Dynamic Forms adoption** — using Record Detail (monolithic) vs Dynamic Forms. Monolithic is P2 findings unless the org's license edition lacks Dynamic Forms.
   - **Related-list strategy** — > 6 related lists on one tab is P2; multiple "Recently Viewed" widgets is P1.
   - **Path element** — if the object has a defined sales/service process (sees picklists named `StageName`/`Status`), Path element should be present on the primary page; absence is P2.
   - **Custom LWC presence** — list any custom LWCs; cite `skills/lwc/lwc-performance` for render-weight rules; LWCs marked `@api isRoot` with SOQL in `connectedCallback` are P1.
   - **Visibility rules** — every component should have a Component Visibility Filter when it's persona-dependent; absence = P2.
   - **Mobile compatibility** — pages that use sub-tabs and related lists should declare mobile form factor explicitly; absence = P2.
4. **Page assignment check** — `tooling_query("SELECT FlexiPageId, Profile, RecordType FROM FlexiPageRegionInfo ... ")` (or equivalent ProfilePageAssignment). Pages assigned to no profile/RT are dead — P2.
5. **Emit per-page report + org-level metrics**.

---

## Output Contract

1. **Summary** — object, active record pages, Dynamic Forms %, max finding severity, confidence.
2. **Per-page findings** — table keyed by page.
3. **Org-level metrics** — Dynamic Forms adoption %, component-count distribution, Path adoption.
4. **Process Observations**:
   - **What was healthy** — pages with clean Dynamic Forms + Path + visibility rules.
   - **What was concerning** — monolithic Record Detail persistence, dead pages, LWCs with heavy init.
   - **What was ambiguous** — pages assigned to inactive record types.
   - **Suggested follow-up agents** — `record-type-and-layout-auditor` (for the underlying page-layout layer), `field-impact-analyzer` for any field referenced on a dead page.
5. **Citations**.

---

## Escalation / Refusal Rules

- Object has > 20 record pages → sample the top 5 by assignment volume + flag the count as a P1 finding.
- Custom LWC source is not in `force-app` (managed package) → describe LWC by API, but do not attempt render-weight scoring — note the limitation.

---

## What This Agent Does NOT Do

- Does not modify or deploy record pages.
- Does not audit LWCs in depth — that's the existing `lwc-auditor` agent (recommend it).
- Does not design record types (that's `record-type-and-layout-auditor`).
- Does not auto-chain.
