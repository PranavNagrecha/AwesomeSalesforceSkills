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

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/duplicate-management` — canon
4. `skills/data/large-scale-deduplication` — for orgs where this is a remediation project, not a greenfield design
5. `skills/data/lead-data-import-and-dedup` — Lead-specific behavior
6. `skills/data/data-quality-and-governance`
7. `templates/admin/permission-set-patterns.md` — bypass is expressed via a Custom Permission

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Lead` |
| `target_org_alias` | yes |
| `policy` | yes | `block` (hard block on exact match) \| `alert` (warn + allow) \| `block-on-create-only` \| `alert-on-create-only` |
| `match_basis` | yes | `email` \| `phone` \| `name+company` \| custom: a comma-separated list of field API names |
| `fuzziness` | no | `exact` (default) \| `fuzzy` (standard Salesforce match algo) — some match fields only support exact |
| `integration_exempt` | no | default `true` — integration-user identities are exempt via Custom Permission |

---

## Plan

### Step 1 — Inventory existing dup infrastructure

- `tooling_query("SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType FROM MatchingRule WHERE SobjectType = '<object>'")`.
- `tooling_query("SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType, SobjectSubtype, ParentId FROM DuplicateRule WHERE SobjectType = '<object>'")`.
- Existing active rules that overlap with the proposed `match_basis` = **P0 conflict**. Two active duplicate rules on the same fields produce noisy-and-ambiguous results at scale. The agent refuses to design a competing rule; suggests extending the existing one instead.

### Step 2 — Validate the match_basis

For each field in `match_basis`:

- Fetch via `tooling_query("SELECT DataType, Length, Unique, ExternalId FROM FieldDefinition WHERE …")`.
- **Email** fields support `Exact` and `Fuzzy: Standard`.
- **Phone** supports `Exact` and `Fuzzy: Phonetic`.
- **Name** and **Company/Account** support fuzzy + typo correction.
- **Free-text** fields — warn: fuzzy matching on unbounded text produces false positives at scale.
- **Picklist** — only exact, and only useful combined with another field.
- **Number / ID / External ID** — only exact.

If the user passed `fuzziness=fuzzy` on a field that doesn't support fuzzy, downgrade to exact and note it.

### Step 3 — Design the Matching Rule

Emit a `MatchingRule` XML stub:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MatchingRule xmlns="http://soap.sforce.com/2006/04/metadata">
  <label>...</label>
  <masterLabel>...</masterLabel>
  <ruleStatus>Active</ruleStatus>
  <sobjectType>...</sobjectType>
  <matchingRuleItems>
    <fieldName>Email</fieldName>
    <matchingMethod>Exact</matchingMethod>
  </matchingRuleItems>
  <!-- repeat per field -->
  <booleanFilter>1 OR (2 AND 3)</booleanFilter>
</MatchingRule>
```

Name per `templates/admin/naming-conventions.md`: `MR_<Object>_<Basis>` e.g. `MR_Lead_Email`. Avoid shorthand.

**Boolean filter** — if the user supplies multiple fields, the default is AND (all must match). Agent overrides this only if the user explicitly requested OR semantics, because OR on personal-data fields produces dangerous false positives.

### Step 4 — Design the Duplicate Rule

Emit a `DuplicateRule` XML stub per `policy`:

- **block** → `actionOnInsert=Block, actionOnUpdate=Block, alertText='<user-facing message>'`.
- **alert** → `actionOnInsert=Allow, actionOnUpdate=Allow`, with `alertText`.
- **block-on-create-only** → `actionOnInsert=Block, actionOnUpdate=Allow`.
- **alert-on-create-only** → `actionOnInsert=Allow, actionOnUpdate=Allow` + disable the rule on update.

Include the **Bypass Custom Permission**: `Bypass_Duplicate_Rule_<Object>`. The rule references this permission on `operationsOnBypass`. The agent emits a stub for the Custom Permission if one doesn't exist (`list_permission_sets` + `tooling_query` on `CustomPermission`). This is what `data-loader-pre-flight` references when it verifies the loader's bypass.

### Step 5 — Lead.Convert + Merge behavior

For Lead specifically:

- **Convert** — duplicate rules do NOT fire during Lead Convert. If the user's intent is "prevent dup Contacts created by Convert", the answer is NOT a duplicate rule — it's the Apex extension to `LeadConvert` or the Convert-path configuration. Flag this and refuse to pretend the rule covers it.
- **Merge** — duplicate rules do NOT block merges. A merge is an explicit operator action. Process Observations should note this boundary.

For Contact and Account:

- **Contact under Account** — if `match_basis` includes Name but not Account, dupes get flagged within the same Account only; cross-Account dups require the Account field in `match_basis`.
- **Person Accounts** — if the org has Person Accounts enabled (`describe_org`-able via Edition + a probe), dup rules must account for both the Contact and the Account face. Cite `skills/data/person-accounts`.

### Step 6 — Integration exemption pattern

If `integration_exempt=True` (default):

- Emit a Custom Permission stub: `Bypass_Duplicate_Rule_<Object>`.
- Recommend assigning it via the dedicated Integration PSG (from `permission-set-architect`).
- Include the permission in the duplicate rule's bypass list.

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
4. **Custom Permission stub** — fenced block (only if new).
5. **Interaction notes** — Convert behavior, Merge behavior, Person Accounts caveat if applicable.
6. **Test plan** — table from Step 7.
7. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — existing clean match fields, existing Integration PSG with bypass permission.
   - **What was concerning** — competing active dup rules, policies that conflict with Lead Convert semantics, fields with poor data quality that make fuzzy match unreliable.
   - **What was ambiguous** — custom objects with no obvious natural key (the agent made a choice).
   - **Suggested follow-up agents** — `permission-set-architect` (if the bypass Custom Permission is new), `data-loader-pre-flight` (if integrations will hit the rule), `field-impact-analyzer` (to understand what else uses the matched fields).
8. **Citations**.

---

## Escalation / Refusal Rules

- An active duplicate rule already exists on the same sObject with overlapping match fields → refuse to design a competing rule; recommend extending the existing rule.
- `match_basis` contains only free-text fields with `fuzziness=fuzzy` and `row_count` in the target object > 100k → refuse; false-positive rate at scale will exceed 10%. Recommend a curated matching key.
- `policy=block` requested on a Convert-relevant case — refuse to claim Convert coverage; offer the Convert-path extension as the correct pattern and stop.
- Object is a managed-package object (namespace prefix set) → refuse (can't reliably deploy rules into managed namespaces).

---

## What This Agent Does NOT Do

- Does not activate or deploy rules.
- Does not merge existing duplicates (that's a separate job — cite `skills/data/large-scale-deduplication`).
- Does not modify match fields (the agent designs to the source data, it doesn't reshape data).
- Does not override Convert or Merge behavior.
- Does not auto-chain.
