# Gotchas — Permission Set Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Permission Set Group Recalculation Delays Effective Access

**What happens:** Admins update a PSG or muting definition, assign it, and expect the user to have the new access immediately.

**When it occurs:** After editing or deploying permission set groups, especially in larger orgs where recalculation takes time.

**How to avoid:** Check recalculation status, plan deployments with validation time, and verify effective access with a real user after the group finishes processing.

---

## Capability Bundles Break At License Boundaries

**What happens:** A beautifully designed permission set or PSG cannot be assigned to a subset of users because their licenses do not support one or more contained permissions.

**When it occurs:** In mixed-license orgs using Salesforce, Platform, Partner, or managed-package-specific user licenses.

**How to avoid:** Design bundle families around license boundaries first, then persona composition second. Validate with representative users from each license type.

---

## Moving Object Access But Forgetting Apex Class Access Creates False Migrations

**What happens:** Teams migrate object and field permissions into permission sets, but controllers, invocable Apex, tabs, or apps still depend on old profile access.

**When it occurs:** Profile-minimization projects that focus only on CRUD/FLS exports and ignore other setup entity access.

**How to avoid:** Review object, field, tab, app, Apex class, and custom permission access together for each persona before declaring the migration complete.

---

## Muting Is Not A Cleanup Tool For Bad Bundle Design

**What happens:** Every exception gets handled with more muting, and the effective access model becomes harder to reason about than the profiles it replaced.

**When it occurs:** Teams skip capability design and jump straight to one giant PSG plus many muted variants.

**How to avoid:** Split oversized bundles into smaller capability-based permission sets before reaching for muting.
