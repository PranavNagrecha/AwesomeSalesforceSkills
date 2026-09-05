# Duplicate Governance Template

Fill this in before turning on new matching or duplicate rules, and keep it with the metadata. Every row maps to something that ends up in `matchingRules/<Object>.matchingRule-meta.xml` or `duplicateRules/<Object>.<Name>.duplicateRule-meta.xml`, or to a person. Rows are pre-filled with a worked Contact example — replace the values, keep the shape.

---

## Scope

| Property | Value | Where it lands |
|----------|-------|----------------|
| Object | Contact | The matching-rule file name and the duplicate rule's `<Object>.` prefix |
| Object supported by Duplicate Management? | Yes — confirm with `SELECT SobjectType FROM DuplicateRule` in the target org | If no, this template does not apply; use a unique external id plus a before-save flow |
| Business owner | VP Sales Operations | Signs off on Block vs Alert |
| Data steward | Sales Ops analyst, named individual not a team | Works the `DuplicateRecordSet` queue |
| Main duplicate source | Mixed — web-to-lead conversion and a nightly CRM sync | Decides whether the control belongs in the rule or upstream in the integration key |
| Records the rule should ignore | Archived and test-account Contacts | `duplicateRuleFilter` |

## Matching Strategy

One row per `matchingRuleItems` entry. `matchingMethod` must come from the documented enum: `Exact`, `FirstName`, `LastName`, `CompanyName`, `Phone`, `City`, `Street`, `Zip`, `Title`.

| Field (`fieldName`) | `matchingMethod` | `blankValueBehavior` | Confidence | Notes |
|-----------------|------------|------------|------------|------|
| `Email` | `Exact` | `NullNotAllowed` | High | Business email; `NullNotAllowed` is the default and stops emailless records matching each other |
| `FirstName` | `FirstName` | `NullNotAllowed` | Medium | Fuzzy; handles Bob / Robert style variation |
| `LastName` | `LastName` | `NullNotAllowed` | Medium | Fuzzy; only meaningful combined with another field |
| `Phone` | `Phone` | `NullNotAllowed` | Low | Normalise punctuation in a before-save flow first — duplicate rules run after before-save automation |

**`booleanFilter`:** `1 OR (2 AND 3)` — email alone, or first plus last name together. Leaving `booleanFilter` off ANDs every item, which is a different rule.

**Rule status:** deploy as `Active`; verify with `SELECT DeveloperName, RuleStatus FROM MatchingRule WHERE SobjectType = 'Contact'` because activation is asynchronous and can land on `ActivationFailed`.

## Rule Behavior

| Operation | `actionOn*` | `operationsOn*` | Rationale |
|-----------|----------|-----------|-----------|
| Create | `Block` | (not set — operations only apply to `Allow`) | Confidence on exact email is high enough that a new duplicate is never wanted |
| Edit | `Allow` | `Alert`, `Report` | An edit that collides is usually a legitimate correction; warn and record it |
| Integration / Import | `Allow` on the integration's own rule, or the same rule with the integration scoped out via `duplicateRuleFilter` | `Report` | A Block rule halts the save before after-triggers, assignment rules and workflow — see `references/gotchas.md` |

**`alertText`:** "A Contact with this email already exists. Update the existing record instead." Legal on this rule only because `actionOnUpdate` is `Allow`; a rule that blocks both operations must omit `alertText` or the deploy fails validation.

**`securityOption`:** `BypassSharingRules`. Under `EnforceSharingRules` a duplicate the running user cannot see is saved with no message at all.

**Apex bypass:** the nightly sync sets `dml.DuplicateRuleHeader.allowSave = true` and `runAsCurrentUser = true`. This works only against `Allow` + `Alert` rules and only on Apex DML paths, never the UI.

## Survivorship and Merge Rules

Merge mechanics — which field values and child records the platform keeps — belong to `data/record-merge-implications`. This section records the policy, not the behaviour.

| Item | Decision |
|------|----------|
| Master record selection | Oldest `CreatedDate` with a non-blank `AccountId`; ties broken by most recent `LastActivityDate` |
| Field-level survivorship | Email and Phone: most recently modified non-blank value. Owner: from the master. Description: master's value, losing record appended to a note |
| Related record handling | Confirm Opportunity and Case counts before and after; see `data/record-merge-implications` |
| Exception path | Any merge crossing two Account hierarchies goes to the business owner, not the steward |
| Volume threshold | Above roughly a few thousand pairs this stops being a merge queue and becomes a project — hand off to `data/large-scale-deduplication` |

## Metrics

Baseline these before go-live so tuning has a comparison. All four come from `DuplicateRecordSet` and `DuplicateRecordItem`, which the `Report` operation populates.

| Metric | Source | Baseline | Target |
|---|---|---|---|
| Duplicate sets created per week | `SELECT COUNT() FROM DuplicateRecordSet WHERE CreatedDate = LAST_N_DAYS:7` | measure for two weeks before activating | trending down |
| Merges completed per week | Steward log or `DuplicateRecordSet` deletions | 0 at go-live | at least the weekly set-creation rate, or the queue grows |
| False positives sampled | Steward reviews 20 sets per month and records the verdict | n/a | under 10% of sampled sets |
| Recurrent duplicate source | Group `DuplicateRecordItem.RecordId` records by `CreatedById` and `Contact.LeadSource` | n/a | one named system or process, fixed upstream |

Steward reporting on `DuplicateRecordSet` and `DuplicateRecordItem` needs read and write access granted by an admin; reporting on `DuplicateRule` or `MatchingRule` additionally needs View Setup and Configuration.
