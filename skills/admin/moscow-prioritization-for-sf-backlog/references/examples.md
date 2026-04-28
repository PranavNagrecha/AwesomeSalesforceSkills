# Examples — MoSCoW Prioritization for Salesforce Backlog

Three worked backlogs. Each shows the canonical handoff JSON schema and the rationale that produced it.

---

## Example 1: 20-Row Greenfield Sales Cloud Backlog (Capacity-Bounded Commit)

**Context:** A mid-market manufacturer is implementing Sales Cloud for the first time. Two-sprint horizon, four-person admin team, capacity = ~30 person-days per sprint after meetings, leave, and UAT support. The product owner is in the room.

**Problem:** The intake list has 20 stories. Stakeholders insist 17 are "must-have for go-live". MoSCoW alone produces a wishlist; effort tiers expose the lie.

**Solution — prioritized table (excerpt):**

```json
[
  {"story_id":"STORY-001","moscow":"M","moscow_subtag":null,"effort":"M","value":5,"wsjf_score":null,"release_target":"sprint-1","rationale":"Account/Contact/Lead model — go-live blocker"},
  {"story_id":"STORY-002","moscow":"M","moscow_subtag":null,"effort":"L","value":5,"wsjf_score":null,"release_target":"sprint-1","rationale":"Opportunity stages aligned to MEDDIC — sales process foundation"},
  {"story_id":"STORY-003","moscow":"M","moscow_subtag":null,"effort":"S","value":4,"wsjf_score":null,"release_target":"sprint-1","rationale":"Profile + permission set baseline"},
  {"story_id":"STORY-004","moscow":"M","moscow_subtag":null,"effort":"M","value":4,"wsjf_score":null,"release_target":"sprint-1","rationale":"Lead conversion rules"},
  {"story_id":"STORY-005","moscow":"M","moscow_subtag":null,"effort":"S","value":3,"wsjf_score":null,"release_target":"sprint-1","rationale":"Org-wide defaults locked"},
  {"story_id":"STORY-006","moscow":"S","moscow_subtag":null,"effort":"M","value":4,"wsjf_score":null,"release_target":"sprint-2","rationale":"Pipeline dashboard — sales leadership ask"},
  {"story_id":"STORY-007","moscow":"S","moscow_subtag":null,"effort":"M","value":3,"wsjf_score":null,"release_target":"sprint-2","rationale":"Email-to-Lead integration"},
  {"story_id":"STORY-008","moscow":"S","moscow_subtag":null,"effort":"S","value":3,"wsjf_score":null,"release_target":"sprint-2","rationale":"Lead assignment rules by region"},
  {"story_id":"STORY-009","moscow":"C","moscow_subtag":null,"effort":"S","value":2,"wsjf_score":null,"release_target":"sprint-2","rationale":"Custom Lightning record page polish"},
  {"story_id":"STORY-010","moscow":"C","moscow_subtag":null,"effort":"S","value":2,"wsjf_score":null,"release_target":"backlog","rationale":"Quote PDF branding"},
  {"story_id":"STORY-018","moscow":"W","moscow_subtag":"won't-this-release","effort":"L","value":3,"wsjf_score":null,"release_target":"backlog","rationale":"CPQ — deferred to Phase 2; unblocks no Phase 1 outcome"},
  {"story_id":"STORY-019","moscow":"W","moscow_subtag":"won't-this-release","effort":"L","value":3,"wsjf_score":null,"release_target":"backlog","rationale":"Marketing Cloud Connector — Phase 2"},
  {"story_id":"STORY-020","moscow":"W","moscow_subtag":"won't-ever","effort":"M","value":1,"wsjf_score":null,"release_target":"archived","rationale":"Custom UI to bypass Lightning — violates platform standard"}
]
```

**Capacity math:** Sprint-1 Must effort = S + M + M + L + S ≈ 12 days. Within 30-day capacity. Sprint-2 Should effort = M + M + S ≈ 6 days. Could items act as stretch goals.

**Why it works:** The 60% Must rule held — Musts are 5 of 20 rows (~40% by effort), not 17. The Won't list is split: deferred items live in `backlog`; the violation-of-platform-standards row is `archived` so it stops re-surfacing.

---

## Example 2: Regulatory Project — Audit Trail by Q3 (Mandatory Must, Pleased-Regulator Should)

**Context:** A financial services firm has 60 days to deliver a Salesforce audit trail to satisfy a regulator's order. The Must items are non-negotiable. The Should items are "the regulator will be impressed but won't fine us".

**Problem:** Without disciplined tagging, scope-creep adds Could-tier polish ("nicer-looking compliance reports") to a release that has no slack for polish.

**Solution — prioritized rows (excerpt):**

```json
[
  {"story_id":"REG-001","moscow":"M","moscow_subtag":null,"effort":"L","value":5,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Field history tracking on regulated objects — regulator order paragraph 4.2"},
  {"story_id":"REG-002","moscow":"M","moscow_subtag":null,"effort":"M","value":5,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Setup Audit Trail export pipeline — paragraph 4.3"},
  {"story_id":"REG-003","moscow":"M","moscow_subtag":null,"effort":"M","value":5,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Login history retention — paragraph 4.5"},
  {"story_id":"REG-004","moscow":"M","moscow_subtag":null,"effort":"L","value":5,"wsjf_score":7.0,"release_target":"2026-Q3","rationale":"Restriction Rules on regulated cases — WSJF tie-break vs REG-005 (CoD 14 / Job Size 2)"},
  {"story_id":"REG-005","moscow":"M","moscow_subtag":null,"effort":"L","value":5,"wsjf_score":4.3,"release_target":"2026-Q4","rationale":"Sharing rule rebuild — WSJF 4.3 lost the tie-break to REG-004; deferred one quarter"},
  {"story_id":"REG-006","moscow":"S","moscow_subtag":null,"effort":"M","value":4,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Compliance dashboard — regulator pleased, not required"},
  {"story_id":"REG-007","moscow":"S","moscow_subtag":null,"effort":"S","value":4,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Daily compliance digest email"},
  {"story_id":"REG-008","moscow":"C","moscow_subtag":null,"effort":"S","value":2,"wsjf_score":null,"release_target":"backlog","rationale":"Branded compliance report header"},
  {"story_id":"REG-009","moscow":"W","moscow_subtag":"won't-ever","effort":"M","value":1,"wsjf_score":null,"release_target":"archived","rationale":"Custom UI overlay on regulated objects — violates auditability"}
]
```

**Why it works:** Each Must row cites the specific clause of the regulator's order in the rationale — no hand-waving. The WSJF tie-break (REG-004 vs REG-005) is recorded with a numeric score so the deferral is auditable. The Should items are honest about what they buy: regulator goodwill, not compliance.

---

## Example 3: Post-Launch Enhancement Backlog (Mostly Could)

**Context:** A retailer's Service Cloud has been live for nine months. The intake is 30 enhancement requests from agents and team leads. There are no regulatory items, no contractual deadlines, and no production-down defects.

**Problem:** Stakeholders are anchored on "we want it all". Without MoSCoW, every quarterly enhancement release tries to ship 30 things and ships 12, leaving 18 stakeholders disappointed.

**Solution — prioritized rows (excerpt):**

```json
[
  {"story_id":"ENH-001","moscow":"M","moscow_subtag":null,"effort":"S","value":5,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Case escalation rule fix — agents working around a real bug"},
  {"story_id":"ENH-002","moscow":"S","moscow_subtag":null,"effort":"M","value":4,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Knowledge article search filter — top agent ask"},
  {"story_id":"ENH-003","moscow":"S","moscow_subtag":null,"effort":"M","value":3,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Macro for refund processing"},
  {"story_id":"ENH-004","moscow":"C","moscow_subtag":null,"effort":"S","value":2,"wsjf_score":null,"release_target":"2026-Q3","rationale":"List view default sort"},
  {"story_id":"ENH-005","moscow":"C","moscow_subtag":null,"effort":"S","value":2,"wsjf_score":null,"release_target":"2026-Q3","rationale":"Compact layout reorder"},
  {"story_id":"ENH-006","moscow":"C","moscow_subtag":null,"effort":"S","value":2,"wsjf_score":null,"release_target":"backlog","rationale":"Lightning page redesign — wait for Lightning Page Optimizer report"},
  {"story_id":"ENH-024","moscow":"W","moscow_subtag":"won't-this-release","effort":"L","value":2,"wsjf_score":null,"release_target":"backlog","rationale":"Live chat redesign — defer pending Service Cloud Voice rollout"},
  {"story_id":"ENH-030","moscow":"W","moscow_subtag":"won't-ever","effort":"M","value":1,"wsjf_score":null,"release_target":"archived","rationale":"Custom button to override case routing — undermines routing rules"}
]
```

**Why it works:** Most rows ended up Could — the honest signal that this is an enhancement release, not a transformation. The single Must is a real bug surfacing as a story. Could items are sequenced by effort, not value, so the team picks up the cheapest wins first.

---

## Anti-Pattern: Tagging MoSCoW Without Effort Tiers

**What practitioners do:** Run a prioritization session where every row gets M/S/C/W but no effort tier. The output looks complete; the sprint commit fails.

**What goes wrong:** Capacity math is impossible. The team commits 20 Musts and ships 8. Stakeholders learn the team cannot estimate. Trust drops.

**Correct approach:** Refuse to commit a Must row without an effort tier. Pair MoSCoW + effort + value at the same session, even if value tiers are coarse on the first pass.
