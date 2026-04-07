# Marketing Cloud Engagement Setup — Work Template

Use this template when setting up or auditing Marketing Cloud Engagement account configuration.

## Scope

**Skill:** `marketing-cloud-engagement-setup`

**Request summary:** (fill in what the user asked for — e.g., "provision two new BUs for Brand A and Brand B" or "audit existing Send Classifications")

---

## Context Gathered

Answer these before starting any configuration work:

- **Account model:** [ ] Enterprise 2.0   [ ] Standalone
- **Existing BU count:** ____  BUs currently active (list names below)
  - BU 1: ___________________________
  - BU 2: ___________________________
  - BU 3: ___________________________
- **New BUs requested:** [ ] Yes — support case opened?  [ ] No
- **Dedicated IP provisioned:** [ ] Yes — IP address: ____________   [ ] No (shared IP)
- **Sending domains to authenticate (SPF/DKIM):** ________________________
- **CAN-SPAM physical address(es) to use:** ________________________
- **Known compliance constraints (CASL, GDPR, etc.):** ________________________

---

## Business Unit Plan

For each BU being configured or audited, complete this block:

### BU Name: _______________________

| Field | Value |
|---|---|
| Locale / Language | |
| Primary Sending Domain | |
| Brand / Division | |
| Support Case # (if new) | |

**Sender Profile(s):**

| Profile Name | From Name | From Address | Reply-To Address |
|---|---|---|---|
| | | | |
| | | | |

**Delivery Profile:**

| Profile Name | Physical Address | IP / IP Pool |
|---|---|---|
| | | |

**Send Classifications:**

| Classification Name | Type (Commercial / Transactional) | Sender Profile | Delivery Profile |
|---|---|---|---|
| | | | |
| | | | |

**User Role Assignments:**

| Username | Role | Justification |
|---|---|---|
| | | |
| | | |

**Reply Mail Management:**

| Setting | Value |
|---|---|
| Reply Address | |
| Auto-Reply Rule | |
| Bounce Management | |

---

## Approach

Which patterns from SKILL.md apply to this task?

- [ ] Multi-brand Enterprise BU isolation
- [ ] Transactional Send Classification for business-critical emails
- [ ] Custom role provisioning per BU
- [ ] IP warm-up coordination across BUs
- [ ] Other: ________________________

---

## Checklist

Copy and tick as each item is confirmed complete:

- [ ] All required BUs provisioned and active in Setup > Business Units
- [ ] Each BU has at least one Sender Profile with authenticated sending domain
- [ ] Each BU has a Delivery Profile with valid CAN-SPAM physical address
- [ ] Each BU has a Commercial Send Classification (and Transactional if needed)
- [ ] Transactional Send Classifications approved in writing for legally transactional message types only
- [ ] User roles assigned per-BU at least-privilege level
- [ ] Reply Mail Management configured and tested in every active BU
- [ ] IP warm-up plan documented and coordinated across all BUs sharing the dedicated IP
- [ ] Test send completed from each BU — From Name, From Address, footer, and unsubscribe link verified

---

## Notes

Record any deviations from the standard pattern and why:

-
-
