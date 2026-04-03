# Permission Set Architecture Design Template

Use this template when designing or documenting a Permission Set model for a feature, team, or org migration.

---

## Context

| Field | Value |
|-------|-------|
| Feature / Project | TODO: e.g. "Credit Review Module" |
| Date | TODO: YYYY-MM-DD |
| Author | TODO |
| Salesforce Org | TODO: Sandbox / Production |
| Review Status | Draft / Reviewed / Approved |

---

## User Personas

List the distinct user types who need access to this feature.

| Persona | Description | Approximate User Count | Existing Profile |
|---------|-------------|----------------------|-----------------|
| TODO: e.g. Credit Analyst | TODO: Reviews credit applications | TODO: 15 | TODO: Standard_Internal |
| TODO | TODO | TODO | TODO |

---

## Permission Sets to Create

For each atomic permission grant, define a Permission Set:

### Permission Set: `[Name following Object_Action_Context convention]`

| Property | Value |
|----------|-------|
| **API Name** | TODO: e.g. `CreditApplication_ReadCreate` |
| **Label** | TODO: e.g. `Credit Application: Read and Create` |
| **Description** | TODO: One sentence — who uses this and why |

**Object Access:**
| Object | Read | Create | Edit | Delete | View All | Modify All |
|--------|------|--------|------|--------|----------|------------|
| TODO | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

**Field-Level Security:**
| Object | Field | Read | Edit |
|--------|-------|------|------|
| TODO | TODO | ☐ | ☐ |

**Custom Permissions Granted:**
- TODO: e.g. `Approve_Credit_Application` — needed to bypass validation rule on approval

---

*(Repeat for each Permission Set)*

---

## Permission Set Groups

Group Permission Sets into personas:

| PSG Name | PSG API Name | Included Permission Sets | Assigned Personas |
|----------|-------------|--------------------------|-------------------|
| TODO: e.g. Credit Analyst - Core | `CreditAnalyst_Core` | TODO: List PSes | TODO: Personas |
| TODO | TODO | TODO | TODO |

---

## Base Profile Assignment

| Profile | Who Gets It | Login Hours | IP Restrictions |
|---------|-------------|------------|----------------|
| TODO: e.g. `SFUser_MinimumAccess` | All internal users | TODO: Business hours only? | TODO: Office IPs only? |

---

## Object-Level Access Matrix

Summary view across all PSGs. ✓ = access granted via the PSG.

| Object | Persona A PSG | Persona B PSG | Persona C PSG |
|--------|--------------|--------------|--------------|
| Account | ✓ R | ✓ RCE | ✓ RCED |
| TODO Object | TODO | TODO | TODO |

*R=Read, C=Create, E=Edit, D=Delete*

---

## FLS Audit Checklist

Before go-live, verify for each persona:

- [ ] Can see all fields they need on each object
- [ ] Cannot see restricted fields (e.g. salary, SSN, credit card)
- [ ] Cannot edit fields they should only read
- [ ] Effective Access check run via Setup → Users → [User] → View Summary

---

## Testing Protocol

| Test Scenario | Persona | Expected Result | Tester | Date Tested |
|--------------|---------|----------------|--------|-------------|
| Can create a Credit Application | Credit Analyst | ✅ Can create | TODO | TODO |
| Cannot delete a Credit Application | Credit Analyst | ✅ Delete button absent | TODO | TODO |
| Can approve (set Approval_Status) | Credit Manager | ✅ Field editable | TODO | TODO |
| Cannot see Salary__c on Contact | All | ✅ Field not visible | TODO | TODO |

---

## Migration Plan (if applicable)

| Phase | Action | Affected Users | Target Date | Rollback Plan |
|-------|--------|---------------|-------------|--------------|
| 1 | Create Permission Sets + PSGs | None (setup only) | TODO | Delete PSGs if issue |
| 2 | Test with test users | 2-3 test users | TODO | Remove PSG assignments |
| 3 | Migrate [Persona A] users | TODO count | TODO | Revert to old profile |
| 4 | Migrate [Persona B] users | TODO count | TODO | Revert to old profile |
| 5 | Decommission old profiles | N/A | TODO (30 days after final migration) | Re-enable profile |

---

## Approval

| Role | Name | Approved | Date |
|------|------|----------|------|
| Salesforce Admin | TODO | ☐ | |
| Security/Compliance | TODO | ☐ | |
| Business Owner | TODO | ☐ | |
