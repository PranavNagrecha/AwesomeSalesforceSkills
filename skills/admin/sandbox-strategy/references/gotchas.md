# Gotchas: Sandbox Strategy

---

## Refreshing Over Active Work

**What happens:** A sandbox is refreshed while admins or developers still have uncommitted work. Metadata and test data disappear, and everyone blames Salesforce.

**When it bites you:** Shared admin sandboxes, rushed UAT windows, and teams without source discipline.

**How to avoid it:** Require changes to be committed or backed up before refresh approval, and publish refresh windows in advance.

---

## Treating Partial Copy Like a Production Clone

**What happens:** Teams assume a Partial Copy gives reliable production realism for every test scenario. It does not.

**When it bites you:** Performance tests, complex edge-case UAT, and data-volume validation.

**How to avoid it:** Use Partial Copy for sampled realism and reserve Full Sandbox for true production rehearsal.

---

## Forgetting Post-Refresh Configuration

**What happens:** Refresh completes, but logins, integrations, email behavior, or schedules remain broken because no one owns the post-refresh tasks.

**When it bites you:** Named Credentials, connected apps, email deliverability, and integration users.

**How to avoid it:** Maintain a runbook with environment-specific reset steps and owners.

---

## Leaving Production Data Unmasked

**What happens:** Sensitive production data is copied to non-production and remains readable by a broader audience than policy allows.

**When it bites you:** Public sector, healthcare, education, and any org under audit pressure.

**How to avoid it:** Make masking a standard refresh step, validate it, and document exceptions if any exist.
