# Gotchas — Custom Metadata Types And Settings

## Custom Setting Records Do Not Deploy

**What happens:** An admin or developer deploys a Custom Setting field definition through a change set or SFDX push. The field definition arrives in the target org correctly, but all values — org default, profile-level records, and user-level records — are blank. The feature behaves as if the setting does not exist.

**When it occurs:** Every time a Custom Setting is included in a deployment for the first time in a new org, or when a new environment (sandbox, scratch org) is provisioned. Teams that do this step manually forget it during high-pressure release windows.

**How to avoid:** Document a post-deploy data-setup script that upserts the org-default record using `SetupOwnerId = UserInfo.getOrganizationId()`. Run this script as a deployment step. Never rely on Custom Setting records being present unless they were explicitly created in that org.

---

## `getInstance()` Returns Org Default In System Mode Contexts

**What happens:** Apex running in a Batch class, a Platform Event trigger, or a System-mode context calls `getInstance()` expecting to get the running user's resolved value. Instead, it gets the org default because the "running user" in that context is the automated process user or system, which has no profile or user-level override.

**When it occurs:** Batch Apex, scheduled Apex, Platform Event subscribers, and any context where the running user is not a human with an assigned profile and potential user-level override.

**How to avoid:** In these contexts, pass the relevant User ID explicitly: `MySettings__c.getInstance(targetUserId)`. If the batch processes many users, query user IDs upfront and resolve settings per user rather than once per batch execution. Document this requirement in the code comments so future maintainers do not silently regress to `getInstance()`.

---

## CMT Records Are Accessible In Apex Tests Without DML Setup

**What happens:** An Apex test queries `[SELECT ... FROM MyConfig__mdt]` and gets records back without any `insert` or `Test.loadData()` call. This surprises developers who expect tests to run in clean isolation like sObject tests. The test passes in one org but fails in another that has different CMT records — or has no records at all.

**When it occurs:** When tests rely on CMT records that exist in the org but may not exist in all orgs (such as a developer's personal sandbox vs a CI scratch org). The CMT query returns whatever is in the org's metadata cache, not a controlled test fixture.

**How to avoid:** Design CMT access code defensively — handle the case where `getValues()` returns null or a SOQL query returns an empty list. In tests that need specific CMT values, check whether the test can control the behavior through dependency injection (passing a config object) rather than relying on org-level metadata. Note: you cannot insert CMT records via DML in tests (they are metadata), so defensive fallback defaults are the only reliable strategy.

---

## List Custom Settings Are Deprecated And Create Invisible Debt

**What happens:** A developer creates a new `List` Custom Setting because the Setup UI still allows it. The feature works in Classic and partially in Lightning. Over time, Salesforce removes or restricts the UI for managing list settings, automated scan tools flag the org for deprecated feature use, and the team discovers the setting cannot be included in a package.

**When it occurs:** When developers choose List Custom Settings for flat key-value lookups without checking the deprecation status, or when migrating old code to Lightning Experience.

**How to avoid:** Never create new List Custom Settings. Use Custom Metadata Types for flat, non-hierarchical configuration. For existing List Custom Settings, plan a migration: create an equivalent CMT type, copy records, update all Apex and Flow consumers, and deprecate the old setting.

---

## Hierarchical Custom Settings Require Explicit Setup For Each Environment

**What happens:** A team sets up a thoughtful hierarchy in production (org default + 3 profile overrides + 10 user overrides). They provision a new developer sandbox. The sandbox has no Custom Setting records. Code that calls `getInstance()` returns null, causing NullPointerExceptions or silent wrong-behavior.

**When it occurs:** Every time a new sandbox is created or a scratch org is provisioned. Custom Setting records are org-specific data and do not copy into refreshed sandboxes (unless a partial or full sandbox copy is used and the records are in scope).

**How to avoid:** Maintain a setup script (Apex anonymous or a post-deploy script) that creates at minimum the org-default record for each Hierarchical Custom Setting. Document this as a required step in the org setup runbook and include it in the CI/CD pipeline for scratch orgs. Always add null-checks in Apex: `if (settings == null) { use fallback; }`.
