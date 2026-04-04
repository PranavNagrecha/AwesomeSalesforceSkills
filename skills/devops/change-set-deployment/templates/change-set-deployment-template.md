# Change Set Deployment Plan

Use this template for every change set being promoted to a connected org. Fill every field before the deployment window opens.

---

## Release Summary

| Property | Value |
|---|---|
| Change set name | |
| Source org | |
| Target org | |
| Planned deploy window | |
| Release owner | |
| Approver | |
| Ticket / change ref | |

---

## Component Inventory

List every component in the change set by type. Mark any that carry overwrite risk.

| Component Type | API Name | Overwrite Risk? | Notes |
|---|---|---|---|
| | | Yes / No | |
| | | Yes / No | |
| | | Yes / No | |

**Profiles included?** Yes / No — If Yes, document the reconciliation steps below.

---

## Dependency Verification

- [ ] "Add Dependencies" was run in the outbound change set
- [ ] Indirect dependencies were manually checked (custom labels, custom metadata records, invocable methods, named credentials)
- [ ] All dependencies exist in target org OR are included in this change set
- [ ] No components from unrelated features were accidentally included

Missing dependencies identified (if any):

| Missing Component | Resolution |
|---|---|
| | |

---

## Test Plan

**Test level selected:** Default / Run specified tests / Run all tests in org

**Test classes to run (if "Run specified tests"):**

-
-
-

**Minimum acceptable coverage:** 75% org-wide aggregate

**Validation target org:** (sandbox / production)

**Validation date/time:**

**Validation result:** Pass / Fail / Not yet run

**Quick Deploy window expires:** (10 days from successful validation)

---

## Post-Deploy Manual Steps

List every manual action required after the change set deploys. Assign an owner and confirmation method for each.

| Step | Owner | How to Confirm |
|---|---|---|
| Activate Flow: [Flow API Name] | | Setup > Flows > confirm Active |
| Assign permission set: [PS Name] to [group/users] | | Verify user access in target org |
| Update Named Credential: [name] | | Test connected integration |
| Smoke test: [feature/page] | | [test steps] |

---

## Rollback Plan

**Rollback trigger:** (define the condition that would trigger rollback, e.g., "any P1 bug reported within 2 hours of deploy")

**Rollback method:**

- [ ] Re-deploy prior metadata version via change set: [prior change set name or Metadata API path]
- [ ] Deactivate Flow: [Flow name]
- [ ] Revoke permission set assignment
- [ ] Other: ___

**Rollback owner:**

**Rollback rehearsed?** Yes / No

---

## Sign-Off

| Role | Name | Confirmation |
|---|---|---|
| Developer / Admin | | Change set validated: Yes / No |
| Release manager | | Release plan reviewed: Yes / No |
| Business stakeholder | | Go / No-Go |

---

## Post-Deploy Confirmation

Completed by release owner after deployment:

- [ ] Deployment status shows "Succeeded"
- [ ] All post-deploy manual steps completed
- [ ] Smoke tests passed
- [ ] No P1/P2 issues reported within [SLA window]
- [ ] Change record closed / ticket updated
