# Gotchas — Salesforce DevOps Tooling Selection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DevOps Center Only Supports GitHub

**What happens:** Teams that use GitLab, Bitbucket, or Azure DevOps as their source control provider discover during setup that Salesforce DevOps Center exclusively integrates with GitHub. There is no adapter or plugin for other providers.

**When it occurs:** During initial DevOps Center configuration when the team attempts to connect their existing repository. This is not documented prominently in marketing materials and is often discovered after the decision to adopt DevOps Center has already been socialized.

**How to avoid:** Verify Git provider compatibility as the first elimination criterion before evaluating any tool's feature set. If the team is on GitLab or Bitbucket and unwilling to mirror to GitHub, DevOps Center is not a viable option.

---

## Gotcha 2: Managed-Package Tools Consume Org Custom Object and Apex Limits

**What happens:** Copado and Flosum install significant metadata into the org — custom objects, Apex classes, Apex triggers, and Flows. In orgs that are already near the custom object limit (2,000 for Enterprise Edition) or the Apex character limit (6 MB), installing the managed package can fail or push the org past a governance threshold.

**When it occurs:** During package installation in orgs with large existing codebases or orgs that already have multiple managed packages installed (e.g., CPQ, Vlocity/OmniStudio, NPSP).

**How to avoid:** Run a pre-installation audit: query `SELECT count() FROM EntityDefinition WHERE IsCustomizable = true` to check custom object count, and review Apex code size via Setup > Apex Classes. Compare remaining headroom against the tool vendor's published package footprint.

---

## Gotcha 3: SaaS Tools May Not Support All Metadata Types on Release Day

**What happens:** Salesforce introduces new metadata types (or changes existing ones) in each seasonal release. SaaS tools like Gearset and AutoRABIT must update their metadata parsers independently of Salesforce's release cycle. There is typically a 2-6 week lag after a Salesforce release before the tool supports new types.

**When it occurs:** Immediately after a major Salesforce release (Spring, Summer, Winter) when the team tries to deploy metadata types that were introduced or restructured in that release.

**How to avoid:** Check the tool's release notes and metadata type coverage page before each Salesforce release. Plan a buffer period after major releases before deploying new metadata types through the tool. For urgent deployments of unsupported types, fall back to Salesforce CLI direct deployment.

---

## Gotcha 4: Tool-Level Rollback Is Not the Same as Metadata API Rollback

**What happens:** Many tools advertise "one-click rollback," but the actual behavior varies significantly. Some tools redeploy the previous version of changed components (which can fail if dependent components have changed). Others create a destructive changes manifest (which can delete data-bearing custom fields). True transactional rollback does not exist in the Metadata API.

**When it occurs:** During a production deployment failure when the team clicks "rollback" and discovers that the rollback itself fails due to dependency conflicts, or succeeds but causes data loss by removing custom fields that were part of the original deployment.

**How to avoid:** Test the tool's rollback behavior during proof-of-concept using a realistic deployment that includes dependent components (e.g., a custom field referenced by a Flow and a validation rule). Understand whether rollback redeploys previous versions or issues destructive changes. Document the rollback behavior for the ops team before go-live.

---

## Gotcha 5: Pricing Models Shift Dramatically at Scale

**What happens:** SaaS tools that price per user appear affordable for small teams but become the most expensive option as the team scales. Conversely, managed-package tools with flat org-based pricing have high upfront cost but become cheaper per person as team size grows. Teams that select a tool for a 10-person team may find it unaffordable when the team grows to 50.

**When it occurs:** During annual license renewal when the team has grown, or during budget planning when a new business unit is onboarded to the same Salesforce org and needs DevOps access.

**How to avoid:** Model pricing at current team size AND at 2x and 3x team size. Request volume discount schedules from vendors during evaluation. Include a contractual price-cap or price-lock clause in procurement. Consider hybrid approaches where power users get full licenses and occasional users get read-only or viewer access.

---

## Gotcha 6: Backup and Audit-Trail Features Are Not Equivalent Across Tools

**What happens:** Teams assume that all DevOps tools provide equivalent backup and audit-trail capabilities. In reality, some tools only back up metadata (not data), some only capture deployment history (not org-level change tracking), and some charge separately for backup features.

**When it occurs:** During a compliance audit when the team is asked to demonstrate a complete audit trail of all metadata changes over the past 12 months, including who initiated each change and whether it was approved.

**How to avoid:** Define backup and audit requirements during the evaluation phase. Verify whether the tool captures: (a) metadata snapshots on a schedule, (b) deployment-level audit records with initiator and approver, (c) data backups if needed, and (d) exportable audit logs for compliance reporting. These features are often add-on modules, not included in base licensing.
