# LLM Anti-Patterns — Change Set Deployment

Common mistakes AI coding assistants make when generating or advising on Salesforce change set deployments.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Including Dependent Components in the Change Set

**What the LLM generates:** "Add the Apex class to the change set and deploy" without mentioning that dependent components (custom fields referenced by the class, custom objects, custom metadata types, permission sets) must be included or already exist in the target org.

**Why it happens:** Change set dependency resolution is manual — unlike SFDX deploys that can use a manifest. LLMs describe the happy path without the dependency analysis step that is required for change sets.

**Correct pattern:**

```text
Change set dependency checklist:
1. Use "View/Add Dependencies" button after adding primary components
2. Salesforce will show required dependent components
3. Add ALL dependencies to the change set

Common missed dependencies:
- Custom fields referenced in Apex, Flow, or validation rules
- Custom objects for new custom fields
- Record Types referenced in page layout assignments
- Picklist values (must add the field, not just the value)
- Connected App configurations for Named Credentials
- Custom Labels referenced in Apex code
- Static Resources used by LWC or Visualforce pages
```

**Detection hint:** Flag change set instructions that do not include a dependency review step. Look for missing "View/Add Dependencies" button usage.

---

## Anti-Pattern 2: Recommending Change Sets for Complex or Frequent Deployments

**What the LLM generates:** "Use change sets for your weekly release cadence" or "Deploy your 200-component release via change set" without noting that change sets are not suitable for complex, frequent, or automated deployments.

**Why it happens:** Change sets are the simplest deployment method in Salesforce and heavily represented in admin-focused training data. LLMs recommend them without evaluating whether the deployment complexity warrants SFDX, unlocked packages, or DevOps Center.

**Correct pattern:**

```text
Change sets are appropriate for:
- Small, infrequent deployments (< 20 components)
- Admin-managed declarative changes
- Orgs without source control or CI/CD infrastructure

Change sets are NOT appropriate for:
- Frequent releases (weekly or more) — no automation possible
- Large deployments (> 50 components) — manual component selection is error-prone
- Destructive changes — change sets cannot delete components
- Rollback scenarios — no built-in rollback mechanism
- Team development — no merge/conflict resolution

For complex deployments, use:
- sf project deploy start (SFDX CLI) with manifest
- Unlocked packages for modular deployments
- DevOps Center for admin-friendly source-tracked deployments
```

**Detection hint:** Flag change set recommendations for deployments described as "large," "frequent," "automated," or involving "destructive changes."

---

## Anti-Pattern 3: Deploying to Production Without Validate-Only First

**What the LLM generates:** "Upload the change set to production and deploy it" without recommending a validate-only deployment first to catch errors before committing to the actual deploy.

**Why it happens:** The validate-only step is an extra action in the UI. LLMs skip it for brevity, but skipping validation in production risks failed deployments that can leave the org in an inconsistent state.

**Correct pattern:**

```text
Change set deployment to production procedure:

1. Upload change set from sandbox to production
2. In production: Setup > Inbound Change Sets
3. Click "Validate" (NOT "Deploy" yet)
   - Runs Apex tests (required for production)
   - Checks all component dependencies
   - Does NOT make any changes to the org
4. Review validation results:
   - All tests pass? Code coverage >= 75%?
   - No dependency errors?
5. Only after successful validation: click "Deploy"

The validate step catches most deployment failures without risk.
Quick Deploy: if validation succeeds with RunLocalTests, you get a
"Quick Deploy" option that deploys without re-running tests (valid for 10 days).
```

**Detection hint:** Flag production deployment instructions that go directly to "Deploy" without a "Validate" step. Look for missing test execution discussion.

---

## Anti-Pattern 4: Assuming Change Sets Can Handle Destructive Changes

**What the LLM generates:** "Remove the old field by deploying a change set without it" or "Delete the Apex class via change set" — implying that change sets can remove components from the target org.

**Why it happens:** LLMs conflate change set behavior with SFDX destructive manifest behavior. Change sets can only ADD or UPDATE components — they cannot delete fields, classes, or other metadata.

**Correct pattern:**

```text
Change set limitations — destructive changes:

Change sets CANNOT:
- Delete custom fields
- Delete Apex classes or triggers
- Delete Flows, Process Builders, or Workflow Rules
- Remove components from page layouts
- Remove picklist values

To delete components, use:
1. SFDX CLI: sf project deploy start with destructiveChangesPost.xml
2. Metadata API: deploy with destructive manifest
3. Manual deletion in the target org via Setup UI

Best practice: deploy the change set first (add new components),
then manually delete deprecated components in the target org.
```

**Detection hint:** Flag change set instructions that describe removing or deleting components. Look for "delete," "remove," or "destructive" in change set context.

---

## Anti-Pattern 5: Not Accounting for Change Set Deployment Connection Setup

**What the LLM generates:** "Upload the change set from your developer sandbox to production" without verifying that a deployment connection exists between the source and target orgs.

**Why it happens:** Deployment connections are a one-time setup step. LLMs assume they exist because most training examples skip the setup.

**Correct pattern:**

```text
Change set prerequisites:

1. Deployment connection must exist between source and target orgs:
   - Setup > Deploy > Deployment Settings (in target org)
   - The source sandbox must be listed and "Allow Inbound Changes" enabled

2. Both orgs must be in the same production org family:
   - Sandbox to Production: always connected
   - Sandbox to Sandbox: requires authorization in target sandbox
   - Production to Production: NOT possible via change sets

3. After sandbox refresh: deployment connections may need to be re-established

4. Change sets can only flow UP the environment chain:
   - Developer sandbox -> Full sandbox -> Production (valid)
   - Production -> Sandbox (NOT valid via change sets — use SFDX or packages)
```

**Detection hint:** Flag change set instructions that do not mention deployment connections or that suggest deploying from production to sandbox (not possible via change sets).
