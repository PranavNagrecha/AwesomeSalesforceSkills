# Sharing Rules — Design and Deployment Record

Fill this in before building anything. It is the artefact that survives the admin who wrote it.

---

## 1. Scope

**Object:** `[REPLACE: API name, e.g. Account or Program__c]`

**Requirement, in one sentence:** `[REPLACE: quote the stakeholder's words, not a paraphrase]`

**Requested by / approved by:** `[REPLACE: name and date]`

---

## 2. Baseline Check

A sharing rule is only meaningful under a restrictive baseline, and only necessary if nothing already delivers the access.

| Check | Value | Rule still needed? |
|---|---|---|
| Internal org-wide default | `[REPLACE: Private / Public Read Only / Public Read Write]` | No if Public Read/Write |
| External org-wide default | `[REPLACE: Private / Public Read Only / N/A]` | Relevant only for external users |
| Role hierarchy already delivers it? | `[REPLACE: yes / no + which roles]` | No if yes |
| Existing rules on this object | `[REPLACE: total count / of which criteria-based + guest — get from the retrieved metadata]` | Cap is 300 total, of which max 50 criteria-based or guest |
| Broad grants that would make this redundant | `[REPLACE: View All / Modify All / View All Data holders, or "none found"]` | Remove these in the same change |

> If the answer to "rule still needed" is No on any row, stop and record why here rather than building it anyway.

---

## 3. Rule Type Decision

Read the requirement sentence from section 1.

- [ ] It is a sentence about **people who own records** → **owner-based** (`sharingOwnerRules`)
- [ ] It is a sentence about **what is on the record** → **criteria-based** (`sharingCriteriaRules`)
- [ ] It is about **unauthenticated site visitors** → **guest** (`sharingGuestRules`, Read only)
- [ ] It is about **territory membership** → **territory** (`sharingTerritoryRules`)
- [ ] None of these fit → this is not a sharing rule. Route to teams, `apex/apex-managed-sharing`, or `admin/restriction-rules` and stop.

**Chosen type:** `[REPLACE]`
**Why the other types were rejected:** `[REPLACE: one line each — this is the part reviewers read]`

---

## 4. Rule Definition

| Setting | Value | Notes |
|---|---|---|
| `fullName` (API name) | `[REPLACE: Underscored_Api_Name]` | Immutable once deployed |
| `label` | `[REPLACE: Human readable]` | Required |
| `description` | `[REPLACE: what and why, max 1,000 chars]` | Required by convention here, optional in the API |
| Rule type | `[REPLACE: sharingOwnerRules / sharingCriteriaRules / sharingGuestRules / sharingTerritoryRules]` | |
| `sharedFrom` (owner-based only) | `[REPLACE: group / role / roleAndSubordinatesInternal + API name]` | Source population |
| `sharedTo` | `[REPLACE: group / role / queue / territory / guestUser + API name]` | Prefer a public group |
| `accessLevel` | `[REPLACE: Read or Edit]` | Guest rules: `Read` only |
| `includeRecordsOwnedByAll` (criteria) | `[REPLACE: true or false]` | **Write-once.** Records owned by users who can't have a role |
| `includeHVUOwnedRecords` (guest) | `[REPLACE: true or false]` | **Write-once.** High-volume site-user-owned records |

### Account rules only — child access

Every one of these is required on an Account rule. Default to `None`; raise only what the requirement names.

| Child | Value | Justification |
|---|---|---|
| `caseAccessLevel` | `[REPLACE: None / Read / Edit]` | `[REPLACE]` |
| `contactAccessLevel` | `[REPLACE: None / Read / Edit]` | `[REPLACE]` |
| `opportunityAccessLevel` | `[REPLACE: None / Read / Edit]` | `[REPLACE]` |

### Criteria (criteria-based and guest rules)

| # | Field | Operation | Value | Stable? |
|---|---|---|---|---|
| 1 | `[REPLACE: API name]` | `[REPLACE: equals / notEqual / contains / ...]` | `[REPLACE]` | `[REPLACE: yes / no — how often does this change on an existing record?]` |
| 2 | `[REPLACE]` | `[REPLACE]` | `[REPLACE]` | `[REPLACE]` |

**`booleanFilter`:** `[REPLACE: e.g. 1 AND 2 — indexes are 1-based positions into the rows above; omit for a single criterion]`

> If any row above answers "no" to Stable, note the expected edit volume. A criteria field that changes on most records regularly turns routine data maintenance into continuous sharing recalculation.

---

## 5. Metadata

```xml
<!-- force-app/main/default/sharingRules/[REPLACE: Object].sharingRules-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <[REPLACE: sharingOwnerRules | sharingCriteriaRules | sharingGuestRules]>
        <fullName>[REPLACE: Api_Name]</fullName>
        <accessLevel>[REPLACE: Read | Edit]</accessLevel>
        <description>[REPLACE]</description>
        <label>[REPLACE]</label>
        <sharedTo>
            <[REPLACE: group | role | roleAndSubordinatesInternal | queue | guestUser]>[REPLACE: Api_Name]</[REPLACE: same element]>
        </sharedTo>
        <!-- owner-based only -->
        <!-- <sharedFrom><group>[REPLACE]</group></sharedFrom> -->
        <!-- criteria/guest only -->
        <!-- <booleanFilter>[REPLACE]</booleanFilter>
             <criteriaItems>
                 <field>[REPLACE]</field>
                 <operation>[REPLACE]</operation>
                 <value>[REPLACE]</value>
             </criteriaItems>
             <includeRecordsOwnedByAll>[REPLACE: true|false]</includeRecordsOwnedByAll> -->
    </[REPLACE: matching close tag]>
</SharingRules>
```

Retrieve the object's existing file first and add to it — a retrieved file already carries the element order the API validates against:

```bash
sf project retrieve start -m "SharingCriteriaRule:[REPLACE: Object].*" -m "SharingOwnerRule:[REPLACE: Object].*"
```

**package.xml entries:**

```xml
<types>
    <members>[REPLACE: Object.Rule_Api_Name]</members>
    <name>[REPLACE: SharingCriteriaRule | SharingOwnerRule | SharingTerritoryRule]</name>
</types>
```

---

## 6. Validation

Run before declaring the change complete.

```bash
python3 skills/admin/sharing-rules/scripts/check_sharing_rules.py --manifest-dir [REPLACE: path to metadata root]
```

**Wait for recalculation.** Setup → Background Jobs shows the sharing recalculation; Salesforce also emails when it completes for all affected objects. Org-wide defaults and this object's sharing rules are locked against edits while it runs.

| Check | Value |
|---|---|
| Background Jobs entry seen at | `[REPLACE: time]` |
| Completion email received at | `[REPLACE: time, or "not received — investigate"]` |

**Positive test — the grants exist.** Run twice, several minutes apart. A rising count means recalculation is still running; do not edit the rule while it climbs.

```soql
SELECT COUNT(Id)
FROM [REPLACE: AccountShare | Object__Share]
WHERE RowCause = 'Rule'
  AND UserOrGroupId = '[REPLACE: 00G... target group Id]'
```

| Reading | Time | Count |
|---|---|---|
| First | `[REPLACE]` | `[REPLACE]` |
| Second | `[REPLACE]` | `[REPLACE]` |
| Settled | `[REPLACE]` | `[REPLACE]` |

**Grant attribution on a sample record** — confirms nothing else is already granting the same access:

```soql
SELECT RowCause, COUNT(Id)
FROM [REPLACE: AccountShare | Object__Share]
WHERE [REPLACE: AccountId | ParentId] = '[REPLACE: record Id]'
GROUP BY RowCause
```

**Negative test.** Log in as a member of the target group and open a record that must NOT match.

- Record used: `[REPLACE: Id and why it should not match]`
- Result: `[REPLACE: not visible / VISIBLE — investigate before shipping]`

---

## 7. Checklist

- [ ] OWD is Private or Public Read Only — the rule is not inert
- [ ] Rule type matches the grammar of the requirement in section 1
- [ ] `sharedTo` targets a public group rather than a bare role or named users
- [ ] `accessLevel` is the minimum that satisfies the requirement
- [ ] Account rules: all three `accountSettings` values chosen deliberately and justified
- [ ] `includeRecordsOwnedByAll` / `includeHVUOwnedRecords` set correctly — it cannot be changed later
- [ ] `booleanFilter` indexes all resolve to criteria that exist
- [ ] Guest rules use `sharingGuestRules` with `accessLevel` of `Read`
- [ ] Criteria fields reviewed for churn
- [ ] Any broad grant this rule replaces (`View All` / `Modify All` / relaxed OWD) removed in the same change
- [ ] Rule count on this object recorded against the 300 / 50 caps
- [ ] Checker script run and clean
- [ ] Positive and negative tests recorded above
- [ ] Rule added to the object's rule inventory in version control

---

## 8. Recalculation Plan

Complete only if this change ships alongside a reorg, a bulk load, or a mass ownership transfer.

| Item | Value |
|---|---|
| Structural changes batched into this window | `[REPLACE: list them]` |
| Defer sharing calculation enabled? | `[REPLACE: yes / no]` |
| Which processes suspended | `[REPLACE: group membership calculation / sharing rule calculation / both]` |
| Load order | `[REPLACE: users into roles -> record data with owners -> public groups and queues -> sharing rules one at a time]` |
| Who resumes, and when | `[REPLACE: name + scheduled window — the resume IS the maintenance event]` |
| Full recalculation manually initiated after resume | `[REPLACE: who, when — the Security Guide requires this to prevent errors]` |
| Confirmation both processes are back on | `[REPLACE: who checked, when]` |

---

## 9. Notes and Deviations

`[REPLACE: anything that departs from the patterns in SKILL.md, and why. If a gotcha from references/gotchas.md was knowingly accepted, name it here.]`
