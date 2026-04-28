---
name: duplicate-rule-person-account-edge-cases
description: "When and how to author Duplicate Rules and Matching Rules in B2C / Person Account orgs without breaking lead conversion, cross-object matching, or PII hygiene. Covers PA's dual-record (001/003) shape, PersonEmail vs Contact.Email, multi-phone normalization, IsPersonAccount filtering, RecordType filtering for PA, and Lead-to-PA convert. NOT for B2B duplicate management — see data/duplicate-management. NOT for Data.com / Lightning Data — see integration/data-com."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - duplicate-rules
  - matching-rules
  - person-account
  - b2c
  - data-quality
  - pii
  - lead-conversion
triggers:
  - "duplicate rule not catching person account duplicates"
  - "matching rule on Account.PersonEmail vs Contact.Email"
  - "person account match rule firing on business accounts"
  - "lead convert duplicate rule fires twice on PA orgs"
  - "phone matching across PersonHomePhone PersonMobilePhone Phone"
  - "IsPersonAccount filter missing in match formula"
  - "B2B match rule reused on B2C org breaks"
  - "GDPR delete person account cascades contact"
inputs:
  - Whether the org has Person Accounts enabled (sObject Account has IsPersonAccount field)
  - Existing duplicate rules under `objects/Account/duplicateRules/` and matching rules under `matchingRules/`
  - Whether B2B and B2C records coexist in the same Account object
  - Lead conversion path (Lead → Account, Lead → Contact, Lead → PA) the org uses
  - Locale and phone-format conventions for the customer base
outputs:
  - PA-aware Matching Rule and Duplicate Rule metadata XML
  - IsPersonAccount filter on every PA-targeted match formula
  - PersonEmail / phone field mapping and normalization formulas
  - Lead-convert duplicate-rule wiring (which rule fires on convert)
  - Skill-local checker pass on the org's duplicate / matching rule set
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Duplicate Rule Person Account Edge Cases

Activate this skill when authoring or reviewing Duplicate Rules and Matching Rules in an org that has Person Accounts enabled (B2C, FSC, or mixed B2B/B2C). Person Accounts are a dual-record beast: one logical "consumer" is stored as a `001`-prefix Account row plus a `003`-prefix Contact row, kept in lock-step by the platform. Rules written for B2B Accounts or for stand-alone Contacts will silently mis-fire on PA — surfacing wrong matches, missing real duplicates, breaking Lead conversion, or worse, exposing PII across record-type boundaries.

This skill is NOT a general duplicate-management primer (see `data/duplicate-management` for the platform model) and does NOT cover Data.com / Lightning Data (see `integration/data-com`). It assumes the practitioner already knows what a Matching Rule, a Duplicate Rule, and a Match Formula are.

---

## Before Starting

Gather this context before writing or editing any rule:

- **Is `IsPersonAccount` true on any record in the org?** Run `SELECT Count() FROM Account WHERE IsPersonAccount = true`. If non-zero, every Account-targeted matching rule must consider PA.
- **Is the org *exclusively* B2C, or mixed?** A mixed org needs RecordType / IsPersonAccount filters on every match rule so a B2B "Acme Corp" never matches a B2C "Acme Smith".
- **Which lead-convert path is in use?** Convert can resolve to an Account-only, Contact-only, or PA target. The duplicate rule that fires depends on what the convert action lands on.
- **What is the source of the consumer email and phone?** PA exposes `Account.PersonEmail` (synced to `Contact.Email`), `Account.PersonHomePhone`, `Account.PersonMobilePhone`, plus the regular `Account.Phone` and `Account.OtherPhone`. The match formula must reference the *Account-side* fields when the rule is built on `Account` — referencing `Contact.Email` from an Account match rule does not compile.
- **Locale and dialing conventions** — international customers need a normalized phone (E.164 or stripped digits) before any equality match.

The single most common wrong assumption: "PA is just an Account with a flag, so my B2B match rule will work." It will not. PA matching needs Account-side person fields, an `IsPersonAccount = true` filter, and (in mixed orgs) a RecordType filter.

---

## Core Concepts

### 1. Person Account is a composite record (one `001` + one `003`)

A Person Account is **two physical rows** that the platform keeps synced:

| Side | Id prefix | Field surface |
|---|---|---|
| Account row | `001` | `Account.PersonEmail`, `Account.PersonHomePhone`, `Account.PersonMobilePhone`, `Account.Name` (computed from FirstName/LastName), `Account.IsPersonAccount = true`, `Account.RecordType.IsPersonType = true` |
| Person Contact row | `003` | `Contact.Email` (synced from `Account.PersonEmail`), `Contact.HomePhone`, `Contact.MobilePhone`, `Contact.AccountId` points at the matching `001` |

A Match Rule is built on **one** SObject. If it is built on `Account`, the formula must reference `Account.PersonEmail` (not `Contact.Email`). If it is built on `Contact`, it can reference `Contact.Email` and the Person Contact row will be matched — but the *Account*-side row will not, so de-dupe on Account UI/imports will miss the duplicate.

**Implication for B2C orgs:** build the consumer match rule on `Account`, target Person fields, and add `IsPersonAccount = true` to the formula.

### 2. The `IsPersonAccount` filter is load-bearing in mixed orgs

In an org that holds both B2B Accounts ("Acme Corp") and B2C PAs ("Acme Smith"), a match rule that compares `Account.Name` without an `IsPersonAccount` filter will report Acme Corp as a duplicate of Acme Smith — same name, different universe. The fix is a Match Formula gate:

```text
IsPersonAccount = TRUE AND <person-field comparisons>
```

Without this gate, the rule produces noise that will be ignored by reps until a real duplicate slips through unnoticed. Salesforce's UI does not warn when the filter is missing.

### 3. Email matching: `Account.PersonEmail`, not `Contact.Email`

`Account.PersonEmail` and `Contact.Email` are kept in sync by the platform, but a match rule references **fields on a single SObject**. An Account-built rule that lists `Contact.Email` as a match field will fail validation; a B2B rule copy-pasted onto a B2C org that lists `PersonEmail` on a non-PA-enabled org will also fail. Email matching is **case-insensitive by default** when the matching method is `Exact` on an Email-type field; this is correct behaviour and should not be "fixed" with a `LOWER()` formula (see anti-patterns).

### 4. Phone matching: pick the right field, normalize first

PA exposes four phone fields on the Account side:

| Field | Typical use | Synced to Contact? |
|---|---|---|
| `Account.PersonHomePhone` | residential landline | `Contact.HomePhone` |
| `Account.PersonMobilePhone` | mobile | `Contact.MobilePhone` |
| `Account.Phone` | primary / "best" phone | `Contact.Phone` (the Person Contact only) |
| `Account.OtherPhone` | secondary | `Contact.OtherPhone` |

Two pitfalls:

1. Matching only on `Account.Phone` misses every PA whose primary phone is recorded as `PersonMobilePhone`.
2. Phone equality is **case-sensitive on the wire** (the comparison is byte-equality after light normalization). `+1 (555) 010-1234` does not equal `5550101234` does not equal `+15550101234`. Normalize before storing — Salesforce's standard Matching Rule has a built-in "Phone" matching method that strips formatting; use it. If you need cross-region matching, store an E.164 normalized value in a custom field and match on that.

### 4. Lead-to-PA convert — which rule fires?

When a Lead converts in a PA-enabled org, Salesforce evaluates the active Duplicate Rule on the **target object**:

- If convert creates an Account (B2B path) → Account-targeted Duplicate Rule fires.
- If convert creates a Contact (B2B path with existing Account) → Contact-targeted rule fires.
- If convert creates a Person Account → the **Account**-targeted rule fires (the Account row is created; the Person Contact row is created automatically and inherits the result). A separate Contact-targeted rule does **not** fire on the synced Person Contact row.

Practical consequence: B2C orgs need their Account-targeted Duplicate Rule to be PA-aware (`IsPersonAccount` filter, PersonEmail match, etc.) **specifically because** that is the rule lead-convert will run.

---

## Common Patterns

### Pattern A — Consumer email + phone match rule for a pure B2C org

**When to use:** the org is exclusively Person Accounts (no B2B Accounts at all).

**How it works:** build the matching rule on `Account`, reference `PersonEmail` (Exact, email-aware) and a normalized phone (Exact via the standard Phone matching method). No `IsPersonAccount` filter is strictly required because every record is PA — but include it anyway as forward-compatibility insurance for the day someone adds a B2B record.

```xml
<MatchingRule fullName="Account.B2C_Person_Match">
    <booleanFilter>1 AND 2 AND 3</booleanFilter>
    <description>B2C consumer match: PersonEmail OR (PersonMobilePhone AND IsPersonAccount).</description>
    <label>B2C Person Match</label>
    <matchingRuleItems>
        <fieldName>PersonEmail</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>PersonMobilePhone</fieldName>
        <matchingMethod>Phone</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
</MatchingRule>
```

**Why not the alternative:** building this on `Contact` would catch the Person Contact row but leave Account-UI dedupe and lead-convert blind, since lead-convert evaluates the Account-targeted rule.

### Pattern B — Mixed B2B + B2C org, parallel match rules

**When to use:** the same org has Acme Corp (B2B) and Acme Smith (B2C PA) on the Account object.

**How it works:** two Account-targeted matching rules, both required to fire conditionally:

1. **B2B rule** — `IsPersonAccount = false`, matches on `Name` + `BillingStreet` + `Website`.
2. **B2C rule** — `IsPersonAccount = true`, matches on `PersonEmail` + `PersonMobilePhone`.

Each rule's first match-formula clause is the `IsPersonAccount` gate. The Duplicate Rule sits on top and chooses the right matching rule by `IsPersonAccount`.

**Why not the alternative:** a single rule that tries to OR together B2B Name and B2C PersonEmail will fire on every record-type boundary crossing — Acme Corp matched against Acme Smith because they share a tokenized "Acme".

### Pattern C — Lead convert wired to the PA Duplicate Rule

**When to use:** every B2C org. Configure once at duplicate-rule deploy time.

**How it works:** the Account-targeted Duplicate Rule is set to `actionOnInsert = Block` (or `Allow with alert`), and lead-convert runs as an insert against Account. Confirm the rule's `<isActive>true</isActive>` and that it points at the PA-aware matching rule from Pattern A. Add `Lead.IsConverted = false` is NOT a thing — the lead-side rule is separate and lives under `objects/Lead/duplicateRules/`.

**Why not the alternative:** wiring the Lead-targeted rule and forgetting the Account-targeted one means convert succeeds even when the resulting PA collides with an existing Person Account — the dupe is silently created.

---

## Decision Guidance

| Match goal in a B2C / PA org | Build rule on | Key fields | Filter | Notes |
|---|---|---|---|---|
| **PA email match** | `Account` | `PersonEmail` (Exact, email-aware) | `IsPersonAccount = true` | Do NOT use `Contact.Email` from an Account rule — wrong SObject. Email match is case-insensitive by default; do not wrap with `LOWER()`. |
| **PA phone match** | `Account` | `PersonMobilePhone` and/or `Phone` (matching method `Phone`) | `IsPersonAccount = true` | Pick the canonical phone field your data-entry path populates. Normalize to E.164 in a custom field if cross-region. |
| **PA name+address fuzzy** | `Account` | `FirstName` + `LastName` (Fuzzy: First Name, Last Name) + `BillingStreet` (Fuzzy: Street) | `IsPersonAccount = true` AND a record-type-name filter | Use Salesforce-supplied fuzzy methods, not custom `Levenshtein` formulas. Add `BillingPostalCode` Exact as a tie-breaker to suppress cross-city false positives. |
| **Lead-to-PA convert dedupe** | `Account` (this is the rule that fires) | Whatever the PA email/phone rule above defines | `IsPersonAccount = true` (the converted record will be PA) | The Lead-targeted rule does NOT fire on the synced Person Contact row. Make the Account-side rule the source of truth on convert. |

---

## Recommended Workflow

1. **Confirm PA is enabled and inventory record counts** — `SELECT IsPersonAccount, Count(Id) FROM Account GROUP BY IsPersonAccount`. If the B2B side is non-trivial, plan parallel rules (Pattern B). If B2C-only, plan Pattern A.
2. **List existing rules** — read every file under `objects/Account/duplicateRules/*.duplicateRule-meta.xml`, `objects/Lead/duplicateRules/*`, and `matchingRules/*.matchingRule-meta.xml`. Note which reference `PersonEmail` vs `Contact.Email`, which carry an `IsPersonAccount` filter, which use the standard `Phone` matching method.
3. **Author the PA-aware matching rule** — start from `templates/duplicate-rule-person-account-edge-cases-template.md`. Build on `Account`, target `PersonEmail` + a chosen Person phone field, gate with `IsPersonAccount = true`, add a record-type filter in mixed orgs.
4. **Wire the duplicate rule** — link the matching rule, set `actionOnInsert` and `actionOnUpdate` deliberately (Block for hard duplicates, Allow with alert for soft), and confirm the rule will fire on lead-convert (it fires when convert inserts/updates Account).
5. **Validate with the skill-local checker** — `python3 scripts/check_duplicate_rule_person_account_edge_cases.py path/to/manifest`. Resolve every P0 (missing `IsPersonAccount` filter on PA-enabled orgs, `Contact.Email` referenced from an Account rule, phone match without normalization).
6. **Test with deliberate fixtures** — create one PA, one B2B Account with a similar name, one Lead that should convert into a duplicate PA. Confirm the rule blocks/alerts only the PA-vs-PA case and that lead-convert respects the rule.
7. **Document the GDPR / right-to-be-forgotten path** — deletion of a PA cascades to the Person Contact automatically; capture this in the org's data-retention runbook. Do NOT model "delete the Contact only" as a privacy operation on PA.

---

## Review Checklist

Run through these before marking the rule deployment complete:

- [ ] Every Account-targeted matching rule used in a PA-enabled org has an `IsPersonAccount` clause in its match formula
- [ ] No Account-targeted matching rule references `Contact.*` fields (it would not compile, but copy-paste from B2B examples sometimes lands here)
- [ ] Phone-targeted match items use the standard `Phone` matching method (which strips formatting), or a normalized custom field — never raw `Exact` on the user-facing phone fields
- [ ] In mixed B2B + B2C orgs, two parallel matching rules exist and each is gated by `IsPersonAccount`
- [ ] The Account-targeted Duplicate Rule is active and is what lead-convert will fire against; the Lead-targeted rule is separate
- [ ] Email match items are case-insensitive (the default for `matchingMethod=Exact` on Email type) and are NOT wrapped in a `LOWER()` formula
- [ ] Fuzzy-name matching uses Salesforce-supplied `Fuzzy: First Name` / `Fuzzy: Last Name` / `Fuzzy: Street` methods, not hand-rolled Levenshtein logic
- [ ] The skill-local checker passes (`scripts/check_duplicate_rule_person_account_edge_cases.py`)
- [ ] Right-to-be-forgotten runbook acknowledges that deleting the PA Account row cascades to the Person Contact automatically — no separate Contact delete required

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviours that cause real production problems:

1. **Match rule built on Contact does not catch PA dedupes on Account UI** — the rule fires when a Person Contact is touched directly (rare), but the standard "Save" path on a PA writes to the Account side first; Account-targeted rules are the source of truth for PA dedupe.
2. **Lead-convert only runs the rule on the *resulting* SObject** — convert that lands on PA fires the Account-targeted rule, not a (non-existent) "PA-targeted" rule. There is no PA-only Duplicate Rule type.
3. **`PersonEmail` is null on B2B Accounts** — a match formula that references `PersonEmail` without an `IsPersonAccount` gate matches every B2B record against every other (null = null is FALSE in match logic, but the platform sometimes evaluates it surprisingly; gate explicitly).
4. **GDPR cascade is automatic** — `delete account` of a PA deletes both the `001` and the `003` rows in one DML; manual `delete contact` on the Person Contact throws `CANNOT_DELETE_LAST_DATED_CONVERSION` style errors. Architect retention around the Account row.
5. **Time-zone of creation does not affect match** — Duplicate Rules compare field values, not record-creation timestamps. Date-based dedupe needs an explicit Date or Datetime field in the match formula; it does not "drift" with the user's TZ.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `Account.<rule>.matchingRule-meta.xml` | PA-aware matching rule on Account, gated by `IsPersonAccount`, targeting Person fields with the right matching methods |
| `Account.<rule>.duplicateRule-meta.xml` | Duplicate rule that consumes the matching rule above and is active for the lead-convert path |
| Optional parallel B2B matching rule | When the org is mixed; gated by `IsPersonAccount = false` |
| Checker run | Clean exit from `scripts/check_duplicate_rule_person_account_edge_cases.py` |
| Retention note | One-paragraph runbook entry confirming PA delete cascades both rows |

---

## Related Skills

- `data/duplicate-management` — general duplicate-rule platform model (B2B-flavoured)
- `data/data-quality-and-governance` — broader data quality framing (rule lifecycle, KPIs)
- `data/external-id-strategy` — when matching on PersonEmail is not enough and an external Id is needed for upserts
- `admin/person-accounts` — Person Account enablement, record types, page layouts
- `data/consent-data-model-health` — consent and PII fields adjacent to PA data quality
