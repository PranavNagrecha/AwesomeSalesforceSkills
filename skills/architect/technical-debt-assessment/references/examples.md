# Examples — Technical Debt Assessment

## Example 1: Pre-Project Audit for a Service Cloud Expansion

**Scenario:** A company is planning a significant Service Cloud feature expansion — introducing a new Case categorisation taxonomy, SLA automation, and an agent productivity console. Before the build starts, the Architect runs a full technical debt assessment to understand what debt will affect the project.

**What the audit found:**

- **40 inactive Process Builder flows** on the Case object, accumulated over 4 years. Most were "paused" rather than deleted when teams shipped Flow replacements. None were cleaned up. The org had 1,847 active Flow versions out of the 2,000 limit — leaving only 153 version slots before the org would reject new Flow activations. UNVERIFIED (2026-10-03): the 2,000 figure rests on a Flow limit that no fetched guide confirms (see `gotchas.md` Gotcha 1); treat the headroom framing as illustrative.
- **3 automation overlap conflicts** on the Case object: a Record-Triggered Flow setting `Status` to `In Progress` on assignment, an Apex trigger also updating `Status` on the same `after update` event, and a Workflow Rule sending an email on status change. The Workflow Rule was supposed to have been migrated two years earlier. Result: the email was sometimes sent twice (once from the Workflow Rule's email alert and once from the Flow's Send Email action), and the final value of `Status` depended on which automation ran last — non-deterministic behavior.
- **Hardcoded Queue ID** in an Apex trigger: a 15-character Queue ID embedded in an `if` statement that routed escalated cases. This ID was valid in production but broken in all three sandboxes, which is why the QA team had been manually re-routing escalated test cases for months without understanding why.
- **2 Apex classes at 0% coverage**: `CaseMergeUtility` and `LegacyIntegrationHelper`. Both were written in 2019 and had never been updated since. Neither was referenced by any other class or metadata. Both were safe to delete.

**Remediation backlog produced:**

| Finding | Severity | Effort | Owner |
|---|---|---|---|
| Automation overlap: Flow + Apex both write `Status` | Critical | M | Developer + Architect |
| 40 inactive Process Builder flows — version sprawl (limit risk UNVERIFIED, see Gotcha 1) | High | S | Admin |
| Hardcoded Queue ID in Apex trigger | High | XS | Developer |
| Duplicate email alert from Workflow Rule and Flow | Medium | S | Admin |
| 2 dead Apex classes (0% coverage, no references) | Medium | XS | Developer |

**Outcome:** The team cleaned inactive Flow versions and deleted dead code before the project started. The automation overlap was redesigned to use a single Record-Triggered Flow as the canonical owner of `Status` changes, with the Apex trigger refactored to a read-only audit log writer. The build proceeded with a clean baseline.

---

## Example 2: Targeted Automation Overlap Review — Duplicate Email Alerts on Case

**Scenario:** The support team reports that agents are receiving two copies of the same email notification when a Case is escalated. The CRM admin has checked the Flow and sees only one Send Email action. The ticket is escalated to the Architect for investigation.

**Investigation using this skill (Mode 2: Targeted Automation Review):**

1. The Architect pulls all active automation on the Case object: 1 Record-Triggered Flow (active), 0 Process Builder flows (confirmed inactive), 1 Workflow Rule (status: Active — this was not expected).
2. Both the Record-Triggered Flow and the Workflow Rule respond to `after update` on Case when `Escalated__c` changes to `true`.
3. The Record-Triggered Flow has a Send Email action using a Flow template. The Workflow Rule has an Email Alert action using a classic email template. Both target the `OwnerId` of the Case.
4. **Root cause confirmed:** two active automations responding to the same trigger event, both executing an email action to the same recipient. The Workflow Rule predates the Flow by 3 years. When the Flow was built, no one checked for existing Workflow Rules.

**Findings documented:**

- **Finding:** Active Workflow Rule `Case_Escalation_Email_Alert` overlaps with Record-Triggered Flow `Case_Escalation_Notifications` — both send an email to Case Owner when `Escalated__c` = true.
- **Severity:** High (user experience degradation — agents receive duplicate notifications on every escalation).
- **Remediation:** Deactivate the Workflow Rule. Confirm the Flow's email template covers the same content. If not, update the Flow template first, then deactivate the Workflow Rule.
- **Effort:** XS (30 minutes for a developer or admin with access to both Setup and Flow Builder).
- **Prevention note added to backlog:** The org needs an automation registry — a single table mapping each object's trigger events to their canonical automation owner — to prevent this class of overlap from recurring silently.

**Outcome:** The Workflow Rule was deactivated after confirming the Flow email template covered the same message content. Duplicate alerts stopped within 15 minutes of the change. The Architect added an automation overlap check to the org's standard pre-release checklist.

---

## Example 3: Evidence Pack and Findings Register for a 9-Year-Old Sales Cloud Org

**Scenario:** A Sales Cloud Enterprise Edition org, live since 2017, is about to start a CPQ project. The architect has two weeks for a full assessment (Mode 1). The org has two managed packages (placeholder namespaces `acmesign` and `docgen`), no Shield, and a nightly ETL that loads Opportunity data through the REST API.

**Answers to the Questions to Ask:**

| Question | Answer recorded |
|---|---|
| Namespaces that are not ours | `acmesign`, `docgen`; findings in these namespaces go to Vendor Debt |
| Last full test run | None in 41 days; run scheduled in the full-copy sandbox before evidence collection |
| Event Monitoring | Not licensed. API Total Usage is available at no cost; Apex Trigger events are not |
| API clients | ETL tool (REST), marketing sync (REST, pinned to an old version), one Apex callout to an ERP |
| Legacy automation beside flows | Opportunity: 3 active processes, 2 Workflow Rules with field updates, 1 trigger, 2 record-triggered flows |
| Dynamic Apex entry points | 4 scheduled jobs; `Integration_Setting__mdt.Handler_Class__c` stores class names |

**Evidence collection (Salesforce CLI, run against the full-copy sandbox alias `fullcopy`).** Commands use flags documented in the Salesforce CLI Command Reference (`apex run test`, `data query`).

```bash
# 1. Refresh coverage first: coverage is stale until tests rerun (Gotcha 5)
sf apex run test --test-level RunLocalTests --code-coverage \
  --result-format json --output-dir evidence/tests --target-org fullcopy --wait 60

# 2. Org-wide and per-class coverage from the Tooling API
sf data query --use-tooling-api --target-org fullcopy --result-format csv \
  --query "SELECT PercentCovered FROM ApexOrgWideCoverage" > evidence/org-coverage.csv
sf data query --use-tooling-api --target-org fullcopy --result-format csv \
  --file queries/zero-coverage.soql > evidence/zero-coverage.csv

# 3. Legacy automation and flow version sprawl
sf data query --use-tooling-api --target-org fullcopy --result-format csv \
  --file queries/active-processes.soql > evidence/active-processes.csv
sf data query --use-tooling-api --target-org fullcopy --result-format csv \
  --file queries/obsolete-flow-versions.soql > evidence/obsolete-versions.csv

# 4. Old API version clients (API Total Usage is a no-cost event type)
sf data query --target-org fullcopy --result-format csv \
  --query "SELECT LogDate, LogFile FROM EventLogFile WHERE EventType = 'ApiTotalUsage' AND LogDate = LAST_N_DAYS:7" \
  > evidence/api-total-usage-index.csv
```

The query files referenced above follow. Field names come from the Tooling API Developer Guide objects `ApexCodeCoverageAggregate`, `Flow` and `MetadataComponentDependency`.

`queries/zero-coverage.soql` (Tooling API):

```soql
SELECT ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered
FROM ApexCodeCoverageAggregate
WHERE NumLinesCovered = 0
```

`queries/active-processes.soql` (Tooling API). `ProcessType = 'Workflow'` is the record change process built in Process Builder:

```soql
SELECT Definition.DeveloperName, VersionNumber, Status, ProcessType
FROM Flow
WHERE ProcessType = 'Workflow' AND Status = 'Active'
```

`queries/obsolete-flow-versions.soql` (Tooling API):

```soql
SELECT DefinitionId, Definition.DeveloperName, VersionNumber, Status
FROM Flow
WHERE Status = 'Obsolete'
```

`queries/inbound-refs.soql` (Tooling API, one class at a time, by 18-character ID). Name filters are not supported, results cap at 2,000 rows, and reports are excluded (Gotcha 6):

```soql
SELECT MetadataComponentName, MetadataComponentType, MetadataComponentNamespace
FROM MetadataComponentDependency
WHERE RefMetadataComponentId = '01p5g00000ABCDEAA4'
```

**Findings register (the decision record this skill produces):**

| ID | Area | Finding | Evidence | Severity | Effort | Owner | Decision |
|---|---|---|---|---|---|---|---|
| TD-01 | Integration | Marketing sync calls REST API v29.0; versions 21.0–30.0 were retired in Summer '25 and return `410 GONE` | `api-total-usage` rows with `API_VERSION` = 29.0, `STATUS_CODE` = 410 | Critical | S | Release Manager | Upgrade client to current version this sprint |
| TD-02 | Automation | Workflow Rule `Opp_Set_Close_Quarter` field update re-fires `OpportunityTrigger` before/after update; trigger creates a follow-up Task without a recursion guard | `Workflow` metadata for Opportunity; trigger handler code | High | M | Developer | Move field update into the before-save flow; add idempotency check |
| TD-03 | Automation | 3 active processes on Opportunity run in no guaranteed order (order-of-execution step 13) beside 2 record-triggered flows | `active-processes.csv` | High | L | Architect | Consolidate into record-triggered flows with explicit `triggerOrder`; hand to `flow/process-builder-to-flow-migration` |
| TD-04 | Dead code | 11 org classes at 0 covered lines after a fresh run; 4 have no inbound dependency rows and are not named in `Integration_Setting__mdt` or scheduled jobs | `zero-coverage.csv`, `inbound-refs` per class | Medium | S | Developer | Delete the 4; keep the other 7 pending owner review |
| TD-05 | Dead code | 6 classes in `docgen` show 0% in the Developer Console | Namespace column | Informational | n/a | Vendor | Vendor Debt; excluded from org coverage per the Apex Developer Guide |
| TD-06 | Automation | 214 obsolete flow versions across 9 flows | `obsolete-versions.csv` | Low | S | Admin | Delete all but the latest obsolete version per flow, after clearing paused interviews |
| TD-07 | Dead code | `LegacyLeadScorer` trigger suspected dead | Inferred only: no Event Monitoring Apex Trigger data | Low | XS | Architect | Mark as inferred; re-check if Event Monitoring is bought |

**Why it works:** each row names its evidence file, so a reviewer can re-run the query. The register keeps vendor debt (TD-05) and inferred findings (TD-07) visible without letting them crowd the actionable backlog. Severity follows the platform behavior (a 410 is an outage, a re-fired trigger doubles work), not the count of components.

