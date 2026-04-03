# Gotchas: Change Management and Deployment

---

## Hidden Dependencies in Change Sets

**What happens:** A seemingly simple change set misses a required field, permission, or Flow dependency. Production validation fails late.

**When it bites you:** Admin-heavy orgs with loosely tracked metadata dependencies.

**How to avoid it:** Validate scope in lower environments and move toward source-driven release methods for recurring work.

---

## Flow Deployment Without Activation Planning

**What happens:** A Flow deploys successfully, but activation timing or version handling causes unexpected runtime behavior.

**When it bites you:** Record-triggered automation, entry-criteria changes, and cutovers replacing old automation.

**How to avoid it:** Treat activation as a release decision with smoke tests and fallback steps.

---

## Metadata Rollback Cannot Undo Data Damage

**What happens:** The team redeploys prior metadata and assumes the release is reversed. Data changes made by the release remain behind.

**When it bites you:** validation-rule relaxations, auto-updates, owner changes, and cutovers with record edits.

**How to avoid it:** Pair metadata rollback with data rollback or data repair steps when production records can change.

---

## Profiles Slip Into Every Release

**What happens:** Broad profile deployments create noisy diffs, accidental permission changes, and hard-to-review release packages.

**When it bites you:** older orgs and admin teams that never shifted to permission-set-centric delivery.

**How to avoid it:** isolate access changes into permission sets wherever possible and review profile deployments as exceptions.
