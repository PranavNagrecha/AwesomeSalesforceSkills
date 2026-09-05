# UAT Test Case Design — Engagement Worksheet

Fill this in before authoring cases. It is the record of the answers to
`SKILL.md` § Questions to Ask Before Configuring, plus the decomposition that
produces the case set. Keep it beside the case file; the checker does not read
it, but a reviewer does.

## 1. Scope

**Skill:** `uat-test-case-design`

| Field | Value |
|---|---|
| Release / build | |
| Requirements in scope (`REQ-` ids) | |
| Criteria file (path) | |
| Programme file (`admin/uat-and-acceptance-criteria` plan) | |
| RTM (path) | |

## 2. Answers to the Questions to Ask

| Ask | Answer | Consequence for the case set |
|---|---|---|
| For each expected result, what does the tester actually look at? | | Evidence type and automation verdict per case |
| Which grant carries the feature, and is its recalculation finished? | | The `PermissionSetGroup.Status` gate in the run context |
| For every deny case: what is the persona set up **without**? | | The named absence in `permission_setup` |
| Is a scoping or restriction rule active on the object? | | Whether an empty list view counts as a deny |
| Which UI does each persona use — Lightning desktop, mobile, Classic? | | The form factor in `precondition` |
| Which paths reach the behaviour — UI, Data Loader, Bulk, REST? | | One case per path, and which half of validation each proves |
| Who owns the refresh calendar; is a refresh booked inside the window? | | Whether the evidence survives the cycle |
| Who decides `Fail` versus `Blocked`? | | Named triager on the run sheet |

## 3. Run context

Copy the filled block from `references/worked-examples.md` § 2 and edit it. Record the
sandbox, refresh date, build deploy date, deliverability, personas and the permission gate.

## 4. Decomposition

One row per criterion. A criterion producing more than one case says why in the last column.

| `ac_id` | `req_id` | Personas it applies to | Cases produced | Why more than one |
|---|---|---|---|---|

## 5. Coverage check before authoring steps

- [ ] Every criterion in scope has ≥ 1 case
- [ ] Every requirement has ≥ 1 negative case
- [ ] Every load path named in § 2 has its own case
- [ ] No persona is an administrator, and none is generic
- [ ] Every case has an evidence type and an automation verdict pencilled in

## 6. Deviations

Record any place this set departs from `SKILL.md` § Recommended Workflow, and why. A criterion
you chose not to script goes here with the reason and the person who accepted the gap — an
undocumented omission reads as an oversight a year later.
