# Permission Set Architecture Design Template

Use this template when designing or documenting a Permission Set model for a feature, team, or org migration.

Replace every `<angle-bracket>` placeholder. Rows written in *italics* are worked examples showing the expected shape — delete them, or overwrite them with your own.

---

## Context

| Field | Value |
|-------|-------|
| Feature / Project | `<the feature or migration this design covers, e.g. "Credit Review Module">` |
| Date | `<YYYY-MM-DD the design was last edited>` |
| Author | `<name and role — who defends this design in review>` |
| Salesforce Org | `<org alias and type: scratch / dev sandbox / full sandbox / production>` |
| Target API version | `<the version in package.xml; element availability depends on it>` |
| Review Status | Draft / Reviewed / Approved |

---

## Base Profile Residue

Fill this first. It is the list of settings with no permission-set equivalent, and it is the only content the base profile is allowed to keep. Anything not on this list belongs in a permission set. See the element table in `references/metadata-examples.md`.

| Profile-only setting | Value in the source profile | Carried to the base profile? | Note |
|---|---|---|---|
| `loginHours` | `<per-day start/end in minutes since midnight, or "none set">` | Yes / No | If "no", say who accepted round-the-clock login |
| `loginIpRanges` | `<ranges with descriptions, or "none set">` | Yes / No | Blocks login outright — not the same as org-wide trusted ranges |
| `layoutAssignments` | `<Object-Layout Name pairs, with record type where applicable>` | Yes / No | No permission-set equivalent exists |
| Default app (`applicationVisibilities` `default=true`) | `<app API name>` | Yes / No | Only one per profile; users notice immediately if it is wrong |
| Default record type (`recordTypeVisibilities` `default=true`) | `<Object.RecordType per object>` | Yes / No | Record type *access* moves; the *default* does not |
| `custom` | true / false | n/a | If `false` this is a standard profile — clone before editing |
| User licence | `<licence name>` | n/a | Bounds everything any permission set can grant |

---

## User Personas

List the distinct user types who need access to this feature. A persona is a job to be done, not a job title — two titles with identical access are one persona.

| Persona | Description | Approximate User Count | Existing Profile | User Licence |
|---------|-------------|----------------------|-----------------|--------------|
| *Credit Analyst* | *Reviews and submits credit applications; cannot approve* | *15* | *Standard_Internal* | *Salesforce* |
| `<persona>` | `<what they do that requires this access>` | `<count>` | `<current profile>` | `<licence>` |

> If one persona's population spans more than one user licence, split it here. A permission set scoped to a licence cannot be assigned across licences.

---

## Permission Sets to Create

For each atomic permission grant, define a Permission Set. Keep each one small enough to be reusable by a second persona.

### Permission Set: `<Object_Action_Context>`

| Property | Value |
|----------|-------|
| **API Name** | `<Object_Action_Context, e.g. CreditApplication_ReadCreate>` |
| **Label** | `<human-readable, max 80 chars, e.g. "Credit Application: Read and Create">` |
| **Description** | `<one sentence: who uses this and why it exists separately>` |
| **`license`** | `<licence name, or "empty" if it must be assignable across licences>` |
| **`hasActivationRequired`** | false, or true if this is a session-based permission set |

**Object Access** — every column must be stated explicitly; the permission-set schema marks all six required.

| Object | Read | Create | Edit | Delete | View All | Modify All |
|--------|------|--------|------|--------|----------|------------|
| *Credit_Application__c* | *☑* | *☑* | *☑* | *☐* | *☐* | *☐* |
| `<Object API name>` | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

> View All / Modify All are record-access grants, not object permissions. Anything ticked in those two columns needs a named approver in the Approval section.

**Field-Level Security**

| Object | Field | Read | Edit |
|--------|-------|------|------|
| *Credit_Application__c* | *Credit_Limit__c* | *☑* | *☐* |
| `<Object>` | `<Field__c>` | ☐ | ☐ |

> Required fields cannot be expressed here. If `viewAllFields` is on for the object, the field list is suppressed entirely on retrieve.

**Other Access Granted**

| Type | Value | Why |
|---|---|---|
| Custom permission | `<name, e.g. Approve_Credit_Application>` | `<what it gates — a validation-rule bypass, a Flow branch, an Apex check>` |
| Apex class | `<class name>` | `<why this persona executes it>` |
| Visualforce page | `<page name>` | `<why this persona opens it>` |
| Tab (`tabSettings`) | `<tab>` = Available / None / Visible | `<note: not the profile enum>` |
| App (`applicationVisibilities`) | `<app>` visible | `<the default lives on the profile, not here>` |
| Record type (`recordTypeVisibilities`) | `<Object.RecordType>` visible | `<the default lives on the profile, not here>` |
| System permission (`userPermissions`) | `<permission name>` | `<justification — this is the row a security reviewer reads first>` |

---

*(Repeat the block above for each Permission Set.)*

---

## Permission Set Groups

Group Permission Sets into personas. Individual permissions are never written in the group — only the names of the sets it composes.

| PSG Name | PSG API Name | Included Permission Sets | Muting Permission Sets | Assigned Personas |
|----------|-------------|--------------------------|------------------------|-------------------|
| *Credit Analyst — Core* | *`CreditAnalyst_Core`* | *`Account_CreditFields_Read`, `CreditApplication_ReadCreate`* | *none* | *Credit Analyst* |
| `<label>` | `<API name>` | `<comma-separated PS API names>` | `<mute PS, or "none">` | `<personas>` |

> A mute only subtracts inside its own group. If the persona also holds the same permission set by direct assignment, the mute does nothing — see `security/permission-set-groups-and-muting`.

---

## Base Profile Assignment

| Profile | Who Gets It | Login Hours | IP Restrictions | Default App | Default Record Type |
|---------|-------------|------------|----------------|-------------|---------------------|
| `<e.g. SFUser_MinimumAccess>` | `<which populations>` | `<window, or "unrestricted — accepted by NAME on DATE">` | `<ranges, or "none — accepted by NAME on DATE">` | `<app API name>` | `<Object.RecordType per object>` |

---

## Object-Level Access Matrix

Summary view across all PSGs. ✓ = access granted via the PSG.

| Object | `<Persona A PSG>` | `<Persona B PSG>` | `<Persona C PSG>` |
|--------|--------------|--------------|--------------|
| Account | ✓ R | ✓ RCE | ✓ RCED |
| `<Object API name>` | `<R / RCE / RCED / —>` | `<…>` | `<…>` |

*R=Read, C=Create, E=Edit, D=Delete*

---

## FLS Audit Checklist

Before go-live, verify for each persona:

- [ ] Can see all fields they need on each object
- [ ] Cannot see restricted fields (e.g. salary, SSN, credit card)
- [ ] Cannot edit fields they should only read
- [ ] No object in any permission set has `viewAllFields` on unless it is listed and justified above
- [ ] Effective Access check run via Setup → Users → [User] → View Summary

---

## Testing Protocol

Test as a real user in a sandbox, not by reading the XML. Each row needs a named tester and a date before the cutover proceeds.

| Test Scenario | Persona | Expected Result | Tester | Date Tested |
|--------------|---------|----------------|--------|-------------|
| Can create a Credit Application | Credit Analyst | Can create | `<name>` | `<YYYY-MM-DD>` |
| Cannot delete a Credit Application | Credit Analyst | Delete button absent | `<name>` | `<YYYY-MM-DD>` |
| Can approve (set Approval_Status) | Credit Manager | Field editable | `<name>` | `<YYYY-MM-DD>` |
| Cannot see Salary__c on Contact | All | Field not visible | `<name>` | `<YYYY-MM-DD>` |
| Lands on the correct default app at login | Every migrated persona | Correct app, no re-navigation | `<name>` | `<YYYY-MM-DD>` |
| Creating a record preselects the correct record type | Every migrated persona | Correct default, no picker surprise | `<name>` | `<YYYY-MM-DD>` |
| Login outside the permitted window is refused | Any persona with login hours | Login blocked | `<name>` | `<YYYY-MM-DD>` |

---

## Migration Plan (if applicable)

| Phase | Action | Affected Users | Target Date | Rollback Plan |
|-------|--------|---------------|-------------|--------------|
| 1 | Create Permission Sets + PSGs | None (setup only) | `<date>` | Delete PSGs if issue |
| 2 | Test with test users | 2–3 test users | `<date>` | Remove PSG assignments |
| 3 | Migrate `<persona A>` users | `<count>` | `<date>` | Revert to old profile |
| 4 | Migrate `<persona B>` users | `<count>` | `<date>` | Revert to old profile |
| 5 | Strip the source profile (destructive) | `<count>` | `<date>` | Redeploy the captured profile file |
| 6 | Decommission old profiles | N/A | `<30 days after phase 5>` | Re-enable profile |

> Phase 5 is the destructive step and it only revokes what the file states explicitly as `false` — deleting a block leaves the permission in place. Capture the source profile file in version control before phase 5 begins, or the rollback column is fiction.

---

## Approval

| Role | Name | Approved | Date |
|------|------|----------|------|
| Salesforce Admin | `<name>` | ☐ | |
| Security/Compliance | `<name>` | ☐ | |
| Business Owner | `<name>` | ☐ | |
