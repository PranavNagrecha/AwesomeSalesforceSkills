# Restriction Rule Design Record — [REPLACE: rule name, e.g. Sales Contracts Only]

Fill this in before authoring the `.rule` file. Sections 1–3 are the design; section 4 is the deployable artefact; sections 5–7 are the gates.

---

## 1. Requirement

| Field | Value |
|---|---|
| Requested by | [REPLACE: name and role] |
| Stated requirement | [REPLACE: verbatim, in the requester's words] |
| Target object (API name) | [REPLACE: e.g. Contract] |
| Org edition | [REPLACE: Enterprise / Performance / Unlimited / Developer] |
| Is this requirement regulatory or contractual? | [REPLACE: Yes / No — if Yes, see section 5 before proceeding] |

**Eligibility check.** `enforcementType` `Restrict` supports `Contract`, `Event`, `Quote`, `Task`, `TimeSheet`, `TimeSheetEntry`, custom objects, and external objects.

- [ ] Target object is on that list. If not, stop — route to `admin/sharing-and-visibility`.
- [ ] Object is not an external object, or the adapter is OData 2.0, OData 4.0, or Cross-Org.
- [ ] Active `Restrict` rules already on this object: [REPLACE: count]
- [ ] That count is below the restriction-rule ceiling (2 for Enterprise/Developer, 5 for Performance/Unlimited).
- [ ] Active `Scoping` rules already on this object: [REPLACE: count] — counted against a separate ceiling, not this one.
- [ ] No user matched by this rule's `userCriteria` is already matched by another active restriction OR scoping rule on this object (that constraint does span both kinds).

---

## 2. Bypass inventory — complete this BEFORE writing the rule

Every row is a documented path around the rule. Fill each one with who currently holds it in this org, then get the requester to sign.

| Path | Who holds it here | Accepted? |
|---|---|---|
| Code executed in system mode (Apex, integrations) | [REPLACE: named classes / integration users, or "none identified"] | [REPLACE: Yes / No] |
| View All Records / View All Data on this object | [REPLACE: profiles, permission sets, permission set groups] | [REPLACE: Yes / No] |
| Modify All Records / Modify All Data on this object | [REPLACE: profiles, permission sets, permission set groups] | [REPLACE: Yes / No] |
| `UserRecordAccess`-based audit tooling reports pre-restriction access | [REPLACE: which dashboards / classes read it] | [REPLACE: Yes / No] |
| Calendar Show Details (Event targets only) | [REPLACE: who has it] | [REPLACE: Yes / No] |
| Subordinates' events visible in calendars (Event targets only) | [REPLACE: applicable hierarchy] | [REPLACE: Yes / No] |
| Global search box shortcuts retain previously seen records | [REPLACE: in scope / not in scope] | [REPLACE: Yes / No] |
| Chatter publisher exposes Event and Task record names in the post | [REPLACE: in scope / not in scope] | [REPLACE: Yes / No] |
| Salesforce Classic still reachable by the restricted population | [REPLACE: Yes / No — the guide recommends turning Classic off first] | [REPLACE: Yes / No] |

**Sign-off:** [REPLACE: name, date] acknowledges the residual paths above.

---

## 3. Criteria design

The language supports one EQUALS test per side. No `AND`, no `OR`, no negation, no formulas.

| Side | Expression | Notes |
|---|---|---|
| `userCriteria` | [REPLACE: e.g. `$User.ProfileId = '00exx0000000AAA'`] | Prefer portable fields (`$User.IsActive`, `$User.UserType`, `$User.Department`) over Ids where possible |
| `recordFilter` | [REPLACE: e.g. `OwnerId = $User.Id`] | 15-character Ids only; `Owner:User.` for Owner traversal; comma-separated list for multiple values |

- [ ] Neither expression contains `AND`, `OR`, `!=`, `<`, `>`, `LIKE`, `IN (`, or a formula.
- [ ] Any composite condition has been precomputed into a single stored field, and that field is backfilled on every existing record.
- [ ] The record field used in `recordFilter` is never blank on a record that must survive.
- [ ] If `recordFilter` traverses a lookup, records with an empty lookup are expected to be filtered out, and that is acceptable.
- [ ] Every Id literal is 15 characters.
- [ ] No other active rule on this object matches the same users — audiences are disjoint.

**Child objects.** A rule on this object does not restrict its children.

| Child object | Needs its own rule? | Eligible target entity? |
|---|---|---|
| [REPLACE: child object API name] | [REPLACE: Yes / No] | [REPLACE: Yes / No] |

---

## 4. The artefact

```xml
<!-- restrictionRules/[REPLACE: File_Name].rule -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>false</active>
    <description>[REPLACE: what this rule does and who asked for it]</description>
    <enforcementType>Restrict</enforcementType>
    <masterLabel>[REPLACE: human-readable rule name]</masterLabel>
    <recordFilter>[REPLACE: single EQUALS expression from section 3]</recordFilter>
    <targetEntity>[REPLACE: object API name]</targetEntity>
    <userCriteria>[REPLACE: single EQUALS expression from section 3]</userCriteria>
    <version>1</version>
</RestrictionRule>
```

Ship with `active` set to `false`. Section 5 decides when it flips.

---

## 5. Pre-activation measurement

Express the `recordFilter` as a query and run it against the target object.

```soql
-- Survivors under the proposed filter
SELECT COUNT() FROM [REPLACE: object] WHERE [REPLACE: recordFilter as a WHERE clause]

-- Total, for comparison
SELECT COUNT() FROM [REPLACE: object]
```

| Measure | Expected | Actual |
|---|---|---|
| Total records on object | [REPLACE: number] | [REPLACE: number] |
| Records surviving the filter | [REPLACE: number, agreed in advance] | [REPLACE: number] |
| Records removed | [REPLACE: number] | [REPLACE: number] |
| Query time | [REPLACE: baseline] | [REPLACE: with filter — budget 3–5% overhead on large-data-volume objects] |

- [ ] Actual survivor count matches the number agreed in advance. If it does not, the filter is wrong — do not activate.

---

## 6. Post-activation verification

Run every row as a user matched by `userCriteria`, then repeat as a user who is not matched. Both halves are required: the second proves the rule is scoped and has not caught the whole org.

| Surface | Matched user expects | Result | Non-matched user expects | Result |
|---|---|---|---|---|
| List view | Restricted rows absent | [REPLACE: pass / fail] | Rows present | [REPLACE: pass / fail] |
| Report | Restricted rows absent | [REPLACE: pass / fail] | Rows present | [REPLACE: pass / fail] |
| Related list on parent | Restricted rows absent | [REPLACE: pass / fail] | Rows present | [REPLACE: pass / fail] |
| Global search | Restricted rows absent | [REPLACE: pass / fail] | Rows present | [REPLACE: pass / fail] |
| API query as that user | Restricted rows absent | [REPLACE: pass / fail] | Rows present | [REPLACE: pass / fail] |

- [ ] Verification did **not** use `UserRecordAccess` — that object reports the pre-restriction answer.
- [ ] For Task or Event targets: Open Activities and Activity History related lists have been replaced with the Activity Timeline on affected layouts.

---

## 7. Deployment

| Item | Value |
|---|---|
| Delivery mechanism | [REPLACE: change set / unlocked package] |
| Source org | [REPLACE: org name] |
| Target orgs | [REPLACE: org names, in promotion order] |

**Id remap table.** Every org-specific Id in `recordFilter` or `userCriteria` must be restated per target org — deployment does not translate them.

| Id in source org | What it is | Value in [REPLACE: target org] |
|---|---|---|
| [REPLACE: 15-char Id] | [REPLACE: e.g. Sales User profile] | [REPLACE: 15-char Id] |

- [ ] Checker run clean: `python3 skills/admin/restriction-rules/scripts/check_restriction_rules.py --manifest-dir <metadata-dir>`
- [ ] Remap table applied and re-verified in each target org after deployment.
