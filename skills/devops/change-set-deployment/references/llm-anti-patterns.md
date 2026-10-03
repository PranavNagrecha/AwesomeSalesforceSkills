# LLM Anti-Patterns: Change Set Deployment

Common mistakes AI coding assistants make when generating or advising on Salesforce change set deployments. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Including Dependent Components in the Change Set

**What the LLM generates:** "Add the Apex class to the change set and deploy," with no mention that referenced fields, objects, custom metadata types, or labels must be included or already exist in the target org.

**Why it happens:** Change set dependency resolution is manual. LLMs describe the happy path without the dependency step.

**Correct pattern:**

```text
Change set dependency checklist:
1. Click View/Add Dependencies after adding the primary components
2. Review the proposed list; accept only what belongs in this release
3. Then check runtime references the scanner can miss:
   - Type.forName() dynamic instantiation
   - Label.<Name> custom label references
   - Custom metadata type records queried in Apex
   - Named credentials used in callouts
   - Invocable methods called from flows
   - Static resources used by LWC or Visualforce
```

**Detection hint:** Change set instructions with no dependency review step, or no mention of View/Add Dependencies.

---

## Anti-Pattern 2: Recommending Change Sets for Complex or Frequent Deployments

**What the LLM generates:** "Use change sets for your weekly release cadence" or "Deploy your 200-component release via change set."

**Why it happens:** Change sets are the simplest deployment method and are heavily represented in admin training material.

**Correct pattern:**

```text
Change sets fit:
- Small, infrequent deployments
- Admin-managed declarative changes
- Orgs without source control or CI/CD

Change sets do not fit:
- Frequent releases (no automation)
- Large deployments (manual component selection is error-prone)
- Deletions (use a destructive-changes manifest with sf project deploy start)
- Team development (no merge or conflict resolution)

Alternatives:
- sf project deploy start --manifest manifest/package.xml
- Unlocked packages for modular delivery
- DevOps Center for admin-friendly, source-tracked delivery
```

**Detection hint:** Change set recommendations for deployments described as large, frequent, automated, or destructive.

---

## Anti-Pattern 3: Deploying to Production Without Validating First

**What the LLM generates:** "Upload the change set to production and deploy it."

**Why it happens:** Validate is an extra click, and LLMs skip it for brevity.

**Correct pattern:**

```text
1. Upload the change set from sandbox to production
2. In production: Setup > Inbound Change Sets > open the change set
3. Click Validate (not Deploy)
   - Runs the Apex tests for the chosen test level
   - Checks component dependencies
   - Makes no changes to the org
4. Review results: tests pass, coverage rule met, no dependency errors
5. Quick deploy the validation from Deployment Status within 10 days,
   or click Deploy if the window has passed

Quick deploy is available after a successful validation at any production
test level whose coverage rule was met: 75% overall (default, local, all)
or 75% per deployed class and trigger (Run specified tests).
```

**Detection hint:** Production instructions that go straight to Deploy, or that say quick deploy needs RunLocalTests specifically.

---

## Anti-Pattern 4: Assuming Change Sets Can Delete Components

**What the LLM generates:** "Remove the old field by deploying a change set without it," or "Delete the Apex class via change set."

**Why it happens:** LLMs conflate change sets with destructive-changes manifests.

**Correct pattern:**

```text
Deleting metadata:
1. sf project deploy start --manifest manifest/package.xml \
     --post-destructive-changes manifest/destructiveChangesPost.xml
2. Metadata API deploy with a destructive manifest
3. Manual deletion in the target org through Setup

Note: removing a field from a page layout is a change to the Layout
component, so shipping the updated layout in a change set does work.
UNVERIFIED (2026-10-03): Salesforce Help states change sets can't delete
or rename components; picklist value removal through change sets is not
documented in a fetchable guide.
```

**Detection hint:** "delete", "remove", or "rename" a component as a change set step.

---

## Anti-Pattern 5: Ignoring Deployment Connection Setup

**What the LLM generates:** "Upload the change set from your developer sandbox to production" with no check that the target allows inbound changes from that sandbox. Or the opposite overcorrection: "change sets can only flow up the environment chain."

**Why it happens:** Connections are a one-time setup step that examples skip, and the direction rules are often stated from memory.

**Correct pattern:**

```text
Prerequisites (Apex Developer Guide, Deploy Components to Production):
1. A deployment connection that lets the target org receive inbound
   change sets from the source org
2. The "Create and Upload Change Sets" permission for the uploader
3. Orgs on Enterprise, Performance, Unlimited, or Database.com edition

Direction:
- Only orgs affiliated with the same production org can exchange
  change sets. Production to a different company's production is not possible.
- UNVERIFIED (2026-10-03): Salesforce Help describes connections between
  production and its sandboxes in both directions. Do not tell users that
  production-to-sandbox uploads are impossible without checking Help.
```

**Detection hint:** No mention of deployment connections, or a flat claim that change sets cannot go from production to a sandbox.

---

## Anti-Pattern 6: Claiming a Profile in a Change Set Replaces the Whole Profile

**What the LLM generates:** "Profiles in change sets are full-replace operations; every production customization will be overwritten."

**Why it happens:** It is a widely repeated simplification of the real, scoped behavior.

**Correct pattern:** The Metadata API scopes profile settings to the other components in the deployment. User permissions, login IP ranges, and login hours are the exceptions that always travel. Review those three sections before upload, and grant new access with permission sets.

**Detection hint:** "full replace" or "entire profile is overwritten" in change set advice.

---

## Anti-Pattern 7: Saying Flows Keep Their Source Activation State

**What the LLM generates:** "An active flow in the sandbox arrives active in production."

**Why it happens:** Sandbox-to-sandbox deploys behave that way, because the setting defaults to on outside production.

**Correct pattern:** `enableFlowDeployAsActiveEnabled` defaults to false in production, so flows deploy inactive. Plan activation as a post-deploy step, or enable the setting and plan for the Apex tests it triggers.

**Detection hint:** No flow activation step in a production change set plan.
