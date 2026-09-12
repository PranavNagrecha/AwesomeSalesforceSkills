# Metadata Examples — User Story Writing For Salesforce

Three worked stories at three sizes, each carrying the INVEST check, the Given/When/Then criteria, the metadata artefacts a build agent turns the story into, and the actual `check_invest.py` run. The point of this file is the traceability: the story's own `Then` text and the deployed metadata's user-facing text are the same string, not two independent descriptions that can drift apart.

Metadata field names and their sources are cited to the Metadata API Developer Guide dump (`api_meta L<n>`); where a claim about run-time ordering or file-size limits matters to the story, it is cited the same way rather than asserted from memory.

---

## Example 1 (S): Validation Rule

**Context:** Finance keeps finding Closed Won Opportunities with a blank Amount, which understates the forecast rollup. The fix is declarative — one rule, one object, no automation.

**Story markdown:**

```markdown
## US-OPP-014 — Block Closed Won Opportunities With No Amount

**As a** Inside Sales Rep with the Sales User profile,
**I want** a save on an Opportunity to fail when Amount is blank and Stage is "Closed Won",
**So that** revenue reporting never shows a $0 closed deal and the forecast rollup stays accurate.

**Acceptance Criteria:**

- *Given* an Opportunity with StageName = "Closed Won" and Amount blank,
  *When* the rep saves,
  *Then* the save fails with the error "Amount is required before marking an Opportunity Closed Won."

- *Given* an Opportunity with StageName = "Closed Won" and Amount populated,
  *When* the rep saves,
  *Then* the save succeeds.

- *Given* an Opportunity with StageName other than "Closed Won" and Amount blank,
  *When* the rep saves,
  *Then* the save succeeds — the rule only evaluates on Closed Won.

**Complexity:** S

**Notes:** Declarative-only. Single validation rule, no dependency on any other story.
```

**Handoff JSON:**

```json
{
  "story_id": "US-OPP-014",
  "title": "Block Closed Won Opportunities With No Amount",
  "as_a": "Inside Sales Rep with the Sales User profile",
  "i_want": "a save on an Opportunity to fail when Amount is blank and Stage is Closed Won",
  "so_that": "revenue reporting never shows a $0 closed deal and the forecast rollup stays accurate",
  "acceptance_criteria": [
    "Given an Opportunity with StageName = Closed Won and Amount blank, When the rep saves, Then the save fails with the error Amount is required before marking an Opportunity Closed Won.",
    "Given an Opportunity with StageName = Closed Won and Amount populated, When the rep saves, Then the save succeeds.",
    "Given an Opportunity with StageName other than Closed Won and Amount blank, When the rep saves, Then the save succeeds."
  ],
  "complexity": "S",
  "recommended_agents": ["object-designer"],
  "recommended_skills": ["admin/validation-rules"],
  "dependencies": [],
  "notes": "Declarative-only. Single validation rule on Opportunity."
}
```

**INVEST check:**

| Letter | Verdict | Why |
|---|---|---|
| Independent | Pass | No dependency on another story |
| Negotiable | Pass | The body never says "validation rule" — that's the build agent's read of the AC, not a story instruction |
| Valuable | Pass | Names the outcome (forecast rollup accuracy), not "the system works" |
| Estimable | Pass | Single object, single rule — the team can size it on sight |
| Small | Pass | S per the heuristic — single object, single field/perm-shaped change, no automation |
| Testable | Pass | Every `Then` is a save outcome (fails / succeeds) with the exact error text |

**Metadata artefacts implied:**

| Metadata type | Field | Value the story implies | Source |
|---|---|---|---|
| `ValidationRule` (declared inside the object's `CustomObject` metadata) | `errorConditionFormula` | `AND(ISPICKVAL(StageName, "Closed Won"), ISBLANK(Amount))` | api_meta L45385 (field is required) |
| `ValidationRule` | `errorMessage` | The story's `Then` text, verbatim, and ≤255 characters | api_meta L45402 |
| `ValidationRule` | `active` | `true` | api_meta L45380 (field), sample definition at L45418 |

```xml
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <validationRules>
        <fullName>Closed_Won_Requires_Amount</fullName>
        <active>true</active>
        <errorConditionFormula>AND(ISPICKVAL(StageName, "Closed Won"), ISBLANK(Amount))</errorConditionFormula>
        <errorMessage>Amount is required before marking an Opportunity Closed Won.</errorMessage>
    </validationRules>
</CustomObject>
```

**Checker run** (`python3 scripts/check_invest.py --file <this-story>.md`):

```
[PASS] US-OPP-014 — Block Closed Won Opportunities With No Amount

Summary: 1/1 stories passed (0 ERROR, 0 WARN).
```

Note the checker does not, and cannot, know whether `AND(ISPICKVAL(...))` is the right formula — it lints the story's shape (persona, AC, complexity), not the metadata a human or build agent derives from it.

---

## Example 2 (S/M): Permission Set + Permission Set Group

**Context:** A new custom object, `Escalation__c`, needs to be editable by support team leads without handing out a broader profile. The access should be assignable and revocable independently of anyone's profile.

**Story markdown:**

```markdown
## US-ESC-005 — Support Leads Can Edit Escalation Records

**As a** Support Team Lead with the Support Lead permission set,
**I want** edit access to Escalation__c granted through a permission set group rather than a profile change,
**So that** a lead can be added to or removed from escalation duty in minutes instead of waiting for a profile clone and reassignment.

**Acceptance Criteria:**

- *Given* a user assigned to the Escalation_Leads permission set group,
  *When* they open an Escalation__c record,
  *Then* they can edit the Status__c and Resolution_Notes__c fields and save changes.

- *Given* a user who is not assigned to the Escalation_Leads permission set group,
  *When* they open an Escalation__c record,
  *Then* the record is visible but Status__c and Resolution_Notes__c are read-only, and any attempted edit is rejected.

- *Given* a user is removed from the Escalation_Leads permission set group,
  *When* the removal is saved,
  *Then* their edit access to Escalation__c is revoked without any change to their profile.

**Complexity:** S

**Notes:** No new object permissions beyond Read/Edit on Escalation__c; Create/Delete stay with the existing owning profile.
```

**Handoff JSON:**

```json
{
  "story_id": "US-ESC-005",
  "title": "Support Leads Can Edit Escalation Records",
  "as_a": "Support Team Lead with the Support Lead permission set",
  "i_want": "edit access to Escalation__c granted through a permission set group rather than a profile change",
  "so_that": "a lead can be added to or removed from escalation duty in minutes instead of waiting for a profile clone and reassignment",
  "acceptance_criteria": [
    "Given a user assigned to the Escalation_Leads permission set group, When they open an Escalation__c record, Then they can edit Status__c and Resolution_Notes__c and save changes.",
    "Given a user who is not assigned to the Escalation_Leads permission set group, When they open an Escalation__c record, Then the record is read-only on those fields and any attempted edit is rejected.",
    "Given a user is removed from the Escalation_Leads permission set group, When the removal is saved, Then their edit access to Escalation__c is revoked without any change to their profile."
  ],
  "complexity": "S",
  "recommended_agents": ["permission-set-architect"],
  "recommended_skills": ["admin/permission-set-architecture", "admin/permission-set-group-composition"],
  "dependencies": ["Escalation__c object and its Status__c / Resolution_Notes__c fields already exist"],
  "notes": "Group wraps one permission set for now; add a second permission set to the same group later without touching this one if a second grant is needed."
}
```

**INVEST check:**

| Letter | Verdict | Why |
|---|---|---|
| Independent | Pass — `dependencies[]` names the one real precondition (the object/fields must already exist) |
| Negotiable | Pass — body says "through a permission set group," which is the *access model* the persona experiences (assignable/revocable independent of profile), not a build step |
| Valuable | Pass — the outcome is a time-to-provision number (minutes vs. a profile clone cycle) |
| Estimable | Pass — one object, one grant shape |
| Small | Pass — S: single object, single permission change, no automation |
| Testable | Pass — each AC is a yes/no on whether the fields are editable, plus the revocation AC as the sad/negative path |

**Metadata artefacts implied:**

| Metadata type | Field | Value the story implies | Source |
|---|---|---|---|
| `PermissionSet` | `label` | "Escalation Edit" (required, ≤80 characters) | api_meta L94824 |
| `PermissionSet` | `description` | ≤255 characters | api_meta L94788 |
| `PermissionSet` → `fieldPermissions[]` | `field`, `editable`, `readable` | One entry per field named in the AC (`Escalation__c.Status__c`, `Escalation__c.Resolution_Notes__c`), `editable=true` | api_meta L94802, L95040, L95043 |
| `PermissionSet` → `objectPermissions[]` | `object`, `allowRead`, `allowEdit` | `Escalation__c`, both `true` (Create/Delete stay `false` per Notes) | api_meta L94836, L95069–L95081, L95102 |
| `PermissionSetGroup` | `label`, `permissionSets` | Groups the permission set above so it can be assigned/revoked as one unit | api_meta L95360–L95362 (sample definition) |

```xml
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Escalation_Leads</fullName>
    <label>Escalation Leads</label>
    <description>Support team leads who can edit Escalation records.</description>
    <permissionSets>Escalation_Edit_PS</permissionSets>
</PermissionSetGroup>
```

```xml
<!-- excerpt: the permission set referenced by the group above -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Escalation_Edit_PS</fullName>
    <label>Escalation Edit</label>
    <description>Grants edit on Escalation__c Status and Resolution Notes.</description>
    <fieldPermissions>
        <field>Escalation__c.Status__c</field>
        <editable>true</editable>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <field>Escalation__c.Resolution_Notes__c</field>
        <editable>true</editable>
        <readable>true</readable>
    </fieldPermissions>
    <objectPermissions>
        <object>Escalation__c</object>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
    </objectPermissions>
</PermissionSet>
```

**Checker run** (`python3 scripts/check_invest.py --file <this-story>.md`):

```
[PASS] US-ESC-005 — Support Leads Can Edit Escalation Records

Summary: 1/1 stories passed (0 ERROR, 0 WARN).
```

---

## Example 3 (M): Record-Triggered Flow

**Context:** Support wants a documented follow-up on every high-priority Case within 30 minutes. Two automations already exist on Case (an assignment flow and an SLA escalation flow), so this story has to say so rather than pretend the object is untouched — see `SKILL.md` Gotcha 13.

**Story markdown:**

```markdown
## US-CASE-027 — Auto Follow-Up Task For High-Priority Cases

**As a** Support Team Lead with the Support Lead permission set,
**I want** a Task created automatically for the Case owner whenever a Case's Priority becomes "High" while the Case is not Closed,
**So that** no high-priority case goes more than 30 minutes without a documented follow-up.

**Acceptance Criteria:**

- *Given* a Case is created with Priority = "High" and Status not "Closed",
  *When* it saves,
  *Then* a Task is created with Subject "High Priority Follow-Up", OwnerId equal to the Case's OwnerId, and ActivityDate = today.

- *Given* an existing Case's Priority changes from "Medium" to "High" while Status is not "Closed",
  *When* it saves,
  *Then* a Task is created the same way, unless an open Task with that Subject already exists on the Case.

- *Given* a Case is created or updated with Priority = "High" but Status = "Closed",
  *When* it saves,
  *Then* no Task is created — closed cases do not get a follow-up.

- *Given* a Case's Priority stays "High" across an unrelated field update (for example, only Description changes),
  *When* it saves,
  *Then* no additional Task is created.

**Complexity:** M

**Notes:** Case already carries an assignment flow (owner routing) and an SLA escalation flow. This story's flow must run after assignment so OwnerId is final before the Task is created — the run order is a build-time decision (see SKILL.md Gotcha 13), not something this story fixes, but the existing automation is named here so the build agent knows to check it.
```

**Handoff JSON:**

```json
{
  "story_id": "US-CASE-027",
  "title": "Auto Follow-Up Task For High-Priority Cases",
  "as_a": "Support Team Lead with the Support Lead permission set",
  "i_want": "a Task created automatically for the Case owner whenever a Case's Priority becomes High while the Case is not Closed",
  "so_that": "no high-priority case goes more than 30 minutes without a documented follow-up",
  "acceptance_criteria": [
    "Given a Case is created with Priority = High and Status not Closed, When it saves, Then a Task is created with Subject High Priority Follow-Up, OwnerId equal to the Case's OwnerId, and ActivityDate = today.",
    "Given an existing Case's Priority changes from Medium to High while Status is not Closed, When it saves, Then a Task is created the same way, unless an open Task with that Subject already exists on the Case.",
    "Given a Case is created or updated with Priority = High but Status = Closed, When it saves, Then no Task is created.",
    "Given a Case's Priority stays High across an unrelated field update, When it saves, Then no additional Task is created."
  ],
  "complexity": "M",
  "recommended_agents": ["flow-builder"],
  "recommended_skills": ["flow/record-triggered-flow-patterns"],
  "dependencies": ["Case assignment flow and SLA escalation flow already exist — run order must be coordinated, not assumed"],
  "notes": "triggerOrder must be set explicitly once the existing two flows' order is confirmed; do not accept an unset default on a third same-object flow."
}
```

**INVEST check:**

| Letter | Verdict | Why |
|---|---|---|
| Independent | Pass — the collision with existing automation is surfaced in `dependencies[]`, not hidden |
| Negotiable | Pass — the body never says Flow, trigger type, or run order; those are named only in `notes` and the metadata table below, for the build agent |
| Valuable | Pass — "no case goes more than 30 minutes without a follow-up" is a measurable SLA outcome |
| Estimable | Pass — one object, one new automation, a named collision to check — sizeable as M |
| Small | Pass — M per the heuristic: single object, one declarative automation |
| Testable | Pass — every AC names a concrete Task (or its absence) with field values |

**Metadata artefacts implied:**

| Metadata type | Field | Value the story implies | Source |
|---|---|---|---|
| `Flow` | `triggerType` | `RecordAfterSave` — the Task is a side effect created once the Case commits | api_meta L72524 |
| `Flow` | `recordTriggerType` | `CreateAndUpdate` — the AC covers both a brand-new Case and an existing one whose Priority changes | api_meta L72452 |
| `Flow` | `triggerOrder` | An explicit integer, 1–2,000, coordinated with the two existing Case flows (Gotcha 13) rather than left to the org default | api_meta L68438 |
| `Flow` (object scope) | object | `Case` | story text |

No Flow XML is shown here — a Flow's decision/assignment element graph is exactly the kind of implementation detail the story must not prescribe (INVEST-Negotiable), and inventing a plausible-looking element structure would be worse than naming just the three fields a build agent actually needs before opening Flow Builder.

**Checker run** (`python3 scripts/check_invest.py --file <this-story>.md`):

```
[PASS] US-CASE-027 — Auto Follow-Up Task For High-Priority Cases

Summary: 1/1 stories passed (0 ERROR, 0 WARN).
```

---

## Running all three together

```
python3 scripts/check_invest.py --manifest-dir <dir containing all three story files>
```

exits 0 with `Summary: 3/3 stories passed (0 ERROR, 0 WARN).` — see `SKILL.md` § Recommended Workflow step 6 and `references/gotchas.md` for what each of the checks above is guarding against.
