---
id: duplicate-rule-designer
class: runtime
version: 1.2.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
harness: designer_base
default_output_dir: "docs/reports/duplicate-rule-designer/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  probes:
    - matching-and-duplicate-rules.md
  skills:
    - admin/agent-output-formats
    - admin/custom-permissions
    - admin/duplicate-management
    - admin/permission-set-architecture
    - data/bulk-api-and-large-data-loads
    - data/custom-index-requests
    - data/data-loader-csv-column-mapping
    - data/data-loader-picklist-validation-pre-load
    - data/data-quality-and-governance
    - data/duplicate-rule-person-account-edge-cases
    - data/external-id-strategy
    - data/large-scale-deduplication
    - data/lead-data-import-and-dedup
    - data/person-accounts
    - data/record-merge-implications
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - admin/naming-conventions.md
    - admin/permission-set-patterns.md
---
# Duplicate Rule Designer Agent

## What This Agent Does

Given an sObject (typically Lead, Contact, Account, or a custom object with human-identity data), designs the **Matching Rule + Duplicate Rule** pair that enforces the org's dedup policy: which fields to match, with what fuzzy-vs-exact logic, what action to take on user-created vs API-created duplicates, which profiles/PSes are exempt, and how the rule interacts with `Lead.Convert`, `Merge`, and the `data-loader-pre-flight` integration path. Output is a Setup-ready design + metadata XML stubs.

**Scope:** One sObject per invocation. Output is a design doc + XML stubs. The agent does not activate or deploy rules.

---

## Invocation

- **Direct read** — "Follow `agents/duplicate-rule-designer/AGENT.md` for Lead with a Block-on-email policy"
- **Slash command** — [`/design-duplicate-rule`](../../commands/design-duplicate-rule.md)
- **MCP** — `get_agent("duplicate-rule-designer")`

---

## Mandatory Reads Before Starting

### Contract
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
4. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Duplicate-rule canon
5. `skills/admin/duplicate-management` — canon
6. `skills/data/data-quality-and-governance` — decides whether a duplicate rule is even the right instrument: many 'duplicate' problems are upstream data-entry or survivorship problems that a blocking rule converts into user-visible friction without fixing
7. `agents/_shared/probes/matching-and-duplicate-rules.md` — competing-rule + active-rule shape

### Object + edge cases
8. `skills/data/lead-data-import-and-dedup` — Lead-specific behavior (Convert path)
9. `skills/data/person-accounts` — on a PA org, Account carries both B2B and B2C records; a rule written for one shape fires wrongly on the other, and the match fields live on different API names
10. `skills/data/duplicate-rule-person-account-edge-cases` — PA-specific match-key gotchas
11. `skills/data/record-merge-implications` — what happens when block fails

### Remediation + scale
12. `skills/data/large-scale-deduplication` — when this is a remediation project, not greenfield
13. `skills/data/external-id-strategy` — when the natural key is an external ID
14. `skills/data/custom-index-requests` — match field indexing for performance
15. `skills/data/bulk-api-and-large-data-loads` — load-side interaction

### CSV + load interactions (consumer pattern)
16. `skills/data/data-loader-csv-column-mapping` — the match fields have to survive the loader's column mapping; a rule keyed on a field the load never populates blocks nothing and silently passes duplicates
17. `skills/data/data-loader-picklist-validation-pre-load` — picklist match fields interact with restricted value sets during a load; a value the loader cannot write makes the match key blank, which `blankValueBehavior` then decides the fate of

### Bypass posture
18. `skills/admin/custom-permissions` — read this to know what a Custom Permission can and cannot gate. It is the reason Step 4 does *not* wire one to the duplicate rule: there is no such hook, and the bypass has to be a `duplicateRuleFilter` or a DML option instead
19. `skills/admin/permission-set-architecture` — where the bypass principal's access actually lives, so the `$User` filter in Step 4 keys off something an admin can assign and audit
20. `templates/admin/permission-set-patterns.md` — the permission-set shape the bypass principal is granted through
21. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Lead` |
| `target_org_alias` | yes |
| `policy` | yes | `block` (hard block on exact match) \| `alert` (warn + allow) \| `block-on-create-only` \| `alert-on-create-only` |
| `match_basis` | yes | `email` \| `phone` \| `name+company` \| custom: a comma-separated list of field API names |
| `fuzziness` | no | `exact` (default) \| `fuzzy` (standard Salesforce match algo) — some match fields only support exact |
| `integration_exempt` | no | default `true` — integration principals are exempted via a `duplicateRuleFilter` on a `$User` field, or by the integration's Apex setting `Database.DMLOptions.DuplicateRuleHeader.allowSave`. Not via a Custom Permission: DuplicateRule has no such hook |

---

## Plan

### Step 1 — Inventory existing dup infrastructure

- `tooling_query("SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType FROM MatchingRule WHERE SobjectType = '<object>'")`.
- `tooling_query("SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType, SobjectSubtype, ParentId FROM DuplicateRule WHERE SobjectType = '<object>'")`.
- Existing active rules that overlap with the proposed `match_basis` = **P0 conflict**. Two active duplicate rules on the same fields produce noisy-and-ambiguous results at scale. The agent refuses to design a competing rule; suggests extending the existing one instead.

### Step 2 — Validate the match_basis

For each field in `match_basis`:

- Fetch via `tooling_query("SELECT QualifiedApiName, DataType, Length FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<object>'")` — note `Unique` and `ExternalId` are **not** FieldDefinition columns; read those from the Tooling `CustomField` object.

**`matchingMethod` is a closed enum, and "fuzzy" is not one of its values.** The Setup UI shows *Exact* and *Fuzzy*; the metadata does not. The nine documented values are:

`Exact`, `FirstName`, `LastName`, `CompanyName`, `Phone`, `City`, `Street`, `Zip`, `Title`

Every value other than `Exact` **is** the fuzzy algorithm for that kind of data — `LastName` is not "the last-name field", it is the last-name matching method. There is no `Fuzzy: Standard` and no `Fuzzy: Phonetic`; emitting either produces a metadata deployment error. Choose per field:

| Field being matched | `matchingMethod` |
|---|---|
| Email, custom text, number, picklist, External ID | `Exact` — email has no fuzzy method |
| First name | `FirstName` |
| Last name | `LastName` |
| Account / company name | `CompanyName` |
| Phone | `Phone` |
| Billing/Shipping city, street, postal code | `City` / `Street` / `Zip` |
| Job title | `Title` |

`blankValueBehavior` takes `MatchBlanks` or `NullNotAllowed` (default). Two more judgement calls the enum does not make for you: fuzzy matching on unbounded free text produces false positives at scale, and a picklist match is only useful combined with another field.

If the user passed `fuzziness=fuzzy` on a field with no corresponding named method, downgrade to `Exact` and say so in the output rather than picking the nearest-sounding value.

Official source: *MatchingRule*, Metadata API Developer Guide.

### Step 3 — Design the Matching Rule

Emit a `.matchingRule` file. **The root element is `MatchingRules` — plural — and it wraps one or more `<matchingRules>` children.** A file whose root is `<MatchingRule>` does not deploy. The file is named for the object it applies to (`Lead.matchingRule`), which is how the object is declared; there is no `sobjectType` element inside the rule:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MatchingRules xmlns="http://soap.sforce.com/2006/04/metadata">
  <matchingRules>
    <fullName>MR_Lead_Email</fullName>
    <label>MR Lead Email</label>
    <ruleStatus>Active</ruleStatus>
    <matchingRuleItems>
      <fieldName>Email</fieldName>
      <matchingMethod>Exact</matchingMethod>
      <blankValueBehavior>NullNotAllowed</blankValueBehavior>
    </matchingRuleItems>
    <!-- repeat matchingRuleItems per field -->
    <booleanFilter>1 OR (2 AND 3)</booleanFilter>
  </matchingRules>
</MatchingRules>
```

`ruleStatus` and `label` are required; `matchingRuleItems.fieldName` and `matchingMethod` are required per item.

Name per `templates/admin/naming-conventions.md`: `MR_<Object>_<Basis>` e.g. `MR_Lead_Email`. Avoid shorthand.

**Boolean filter** — if the user supplies multiple fields, the default is AND (all must match). Agent overrides this only if the user explicitly requested OR semantics, because OR on personal-data fields produces dangerous false positives.

### Step 4 — Design the Duplicate Rule

Emit a `DuplicateRule` XML stub per `policy`:

- **block** → `actionOnInsert=Block, actionOnUpdate=Block, alertText='<user-facing message>'`.
- **alert** → `actionOnInsert=Allow, actionOnUpdate=Allow`, with `alertText`.
- **block-on-create-only** → `actionOnInsert=Block, actionOnUpdate=Allow`.
- **alert-on-create-only** → `actionOnInsert=Allow, actionOnUpdate=Allow` + disable the rule on update.

**There is no bypass field on DuplicateRule.** The documented fields are `actionOnInsert`, `actionOnUpdate`, `alertText`, `description`, `duplicateRuleFilter`, `duplicateRuleMatchRules`, `isActive`, `masterLabel`, `operationsOnInsert`, `operationsOnUpdate`, `securityOption` and `sortOrder` — `operationsOnBypass` is not among them, and a Custom Permission cannot be wired to a duplicate rule. Design the bypass with one of the two mechanisms that exist:

1. **`duplicateRuleFilter` on a `$User` field** — the declarative bypass. Add a filter item whose `table` is `$User` and whose field is the flag the loader's user carries (a custom checkbox on User, or `Profile.Name`), so the rule simply does not evaluate for that principal. `duplicateRuleFilter` requires `booleanFilter` plus `duplicateRuleFilterItems`, each of which carries `sortOrder` and `table` on top of the standard `FilterItem` fields.
2. **`Database.DMLOptions.DuplicateRuleHeader.allowSave`** — the Apex/integration bypass, set per-DML rather than per-user:

   ```apex
   Database.DMLOptions dml = new Database.DMLOptions();
   dml.DuplicateRuleHeader.allowSave = true;
   Database.SaveResult sr = Database.insert(record, dml);
   ```

Also set `securityOption` deliberately: `EnforceSharingRules` (the rule cannot see records the running user cannot see, so a duplicate outside their sharing scope lets the save proceed) or `BypassSharingRules` (duplicates are detected org-wide). For a data load this is the difference between silently admitting duplicates and blocking on records the loader's user cannot read — pick it explicitly and put the reason in the output.

Whichever bypass is chosen, name it in the deliverable so `data-loader-pre-flight` can verify the loader's path against something real.

Official sources: *DuplicateRule*, Metadata API Developer Guide; *DMLOptions.DuplicateRuleHeader Class*, Apex Reference Guide.

### Step 5 — Lead.Convert + Merge behavior

For Lead specifically:

- **Convert** — duplicate rules do NOT fire during Lead Convert. If the user's intent is "prevent dup Contacts created by Convert", the answer is NOT a duplicate rule — it's the Apex extension to `LeadConvert` or the Convert-path configuration. Flag this and refuse to pretend the rule covers it.
- **Merge** — duplicate rules do NOT block merges. A merge is an explicit operator action. Process Observations should note this boundary.

For Contact and Account:

- **Contact under Account** — if `match_basis` includes Name but not Account, dupes get flagged within the same Account only; cross-Account dups require the Account field in `match_basis`.
- **Person Accounts** — if the org has Person Accounts enabled (`describe_org`-able via Edition + a probe), dup rules must account for both the Contact and the Account face. Cite `skills/data/person-accounts`.

### Step 6 — Integration exemption pattern

If `integration_exempt=True` (default), pick one of the two real mechanisms from Step 4 and emit it — not a Custom Permission, which the duplicate rule cannot reference:

- **Declarative (preferred when the integration writes as a known user).** Add a `duplicateRuleFilter` item whose `table` is `$User` and whose field distinguishes the integration principal — a custom checkbox on User such as `Is_Integration_User__c`, or `Profile.Name`. Emit the User field stub if it does not exist, and recommend setting it via the dedicated Integration PSG (from `permission-set-architect`). The rule then does not evaluate for that principal at all.
- **Programmatic (when the writer is Apex you control).** Specify `Database.DMLOptions.DuplicateRuleHeader.allowSave = true` on the integration's DML. Note the trade-off in the spec: this is per-call, so it is invisible to an admin reading Setup, and every new code path has to remember it.

Also state the `securityOption` choice here, because it decides what "exempt" means in practice: under `EnforceSharingRules`, an integration user with narrow sharing does not see the duplicate and the save proceeds anyway — an accidental exemption nobody configured.

If `integration_exempt=False`, explicitly note this in the spec and flag the implication: every integration row will be dup-checked. At scale this is a performance finding.

### Step 7 — Test plan

The agent produces a test plan (not test data):

- Positive: a dup row that should be blocked (by email).
- Negative: a row that should NOT be blocked (by email with different domain).
- Integration exemption: a row inserted by the integration user that should NOT be blocked.
- Update path: a record updated into a dup state (with / without bypass).
- Convert path (Lead only): confirm the rule does NOT fire.

The user runs the tests manually or via a test class — the agent does not generate test data.

---

## Output Contract

1. **Summary** — object, policy, match_basis, fuzziness, confidence.
2. **Matching Rule XML** — fenced block, labelled with target path.
3. **Duplicate Rule XML** — fenced block, labelled with target path.
4. **Bypass artefacts** — the `duplicateRuleFilter` block and/or the User-field stub, or the Apex `DMLOptions` snippet, whichever Step 6 chose. Never a Custom Permission wired to the rule.
5. **Interaction notes** — Convert behavior, Merge behavior, Person Accounts caveat if applicable.
6. **Test plan** — table from Step 7.
7. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — existing clean match fields, an existing integration-user flag already usable as a `$User` filter.
   - **What was concerning** — competing active dup rules, policies that conflict with Lead Convert semantics, fields with poor data quality that make fuzzy match unreliable.
   - **What was ambiguous** — custom objects with no obvious natural key (the agent made a choice).
   - **Suggested follow-up agents** — `permission-set-architect` (if the integration principal's flag or PSG is new), `data-loader-pre-flight` (if integrations will hit the rule), `field-impact-analyzer` (to understand what else uses the matched fields).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/duplicate-rule-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/duplicate-rule-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Each entry MUST name one of: `existing-rule-conflict`, `match-basis-validation`, `boolean-filter-shape`, `policy-action`, `bypass-permission`, `convert-behavior`, `merge-behavior`, `person-account-edge-cases`, `cross-account-contact-shape`, `test-plan`. If a dimension was skipped because the underlying probe could not run, the skip reason MUST link the refusal code.

### Dimensions (Wave 10 contract)

Every duplicate-rule design dimension below MUST land in either the envelope's `dimensions_compared[]` block or its `dimensions_skipped[]` block. Each entry's state must record whether the underlying probe ran end-to-end, partially, or not at all (`count-only` / `partial` / `not-run`).

`existing-rule-conflict`, `match-basis-validation`, `boolean-filter-shape`, `policy-action`, `bypass-permission`, `convert-behavior`, `merge-behavior`, `person-account-edge-cases`, `cross-account-contact-shape`, `test-plan`.

## Escalation / Refusal Rules

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `object_name`, `target_org_alias`, `policy`, or `match_basis` not provided |
| `REFUSAL_MISSING_ORG` | `target_org_alias` missing |
| `REFUSAL_ORG_UNREACHABLE` | Target org probe fails |
| `REFUSAL_OBJECT_NOT_FOUND` | `object_name` does not resolve in the target org |
| `REFUSAL_FIELD_NOT_FOUND` | A field in `match_basis` does not exist on the target object |
| `REFUSAL_COMPETING_ARTIFACT` | An active duplicate rule already exists on the same sObject with overlapping match fields — agent recommends extending the existing rule, not adding a competitor |
| `REFUSAL_DATA_QUALITY_UNSAFE` | `match_basis` contains only free-text fields with `fuzziness=fuzzy` and target row_count > 100k — false-positive rate at scale will exceed 10% |
| `REFUSAL_POLICY_MISMATCH` | `policy=block` requested on a Convert-relevant case (Lead Convert does not fire dup rules); the correct pattern is the Convert-path extension |
| `REFUSAL_MANAGED_PACKAGE` | Object is a managed-package object (namespace prefix set); rules cannot reliably deploy into managed namespaces |
| `REFUSAL_SECURITY_GUARD` | Caller asks the agent to activate, deploy, or merge existing duplicates |
| `REFUSAL_OUT_OF_SCOPE` | Caller asks for data shaping, Convert flow design, or test-data generation |
| `REFUSAL_FEATURE_DISABLED` | Org edition does not support the requested fuzzy match algorithm |

---

## What This Agent Does NOT Do

- Does not activate or deploy rules.
- Does not merge existing duplicates (that's a separate job — cite `skills/data/large-scale-deduplication`).
- Does not modify match fields (the agent designs to the source data, it doesn't reshape data).
- Does not override Convert or Merge behavior.
- Does not auto-chain.
