# Examples — OmniStudio Admin Configuration

## Example 1: Enabling Standard Runtime in a Greenfield Org

**Context:** A new Salesforce org has been provisioned with an Industries Cloud license that includes OmniStudio. No Vlocity managed package is installed. The admin needs to configure OmniStudio before the first OmniScript can be authored.

**Problem:** Without explicit configuration, the Runtime Namespace field in OmniStudio Settings is blank. The first attempt to activate an OmniScript fails with a generic "activation error" and no actionable detail. The admin also forgot to assign the PSL before the permission set, resulting in a silent failure that leaves the builder unable to see the OmniStudio app tab.

**Solution:**

```
Setup > OmniStudio Settings
  Standard OmniStudio Runtime:  ENABLED
  Runtime Namespace:            omnistudio
  Disable Managed Package Runtime: ENABLED (no managed package is present)

User provisioning order (required):
  1. Assign OmniStudioPSL Permission Set License to the user
  2. Assign OmniStudio Admin permission set to the builder user
  3. Assign OmniStudio User permission set to consumer users

Verification:
  - Open OmniStudio app > OmniScripts tab loads without error
  - Create a test OmniScript, add one Step, Activate
  - Activation completes without errors
  - Consumer user previews the OmniScript and it renders
```

**Why it works:** Setting the Runtime Namespace to `omnistudio` satisfies the platform's namespace resolution logic. Enabling Standard Runtime routes component rendering through native LWC. The PSL-first provisioning order ensures that permission set assignment has a valid license to attach to.

---

## Example 2: Granting OmniStudio Access to Experience Cloud Community Users

**Context:** An org has OmniStudio correctly configured for internal users. A new Experience Cloud site is being built, and authenticated partner community users need to fill out an OmniScript enrollment flow embedded on a community page.

**Problem:** The admin assigns the `OmniStudio User` permission set to the community profile. Community users authenticate and navigate to the page, but the OmniScript component returns an access-denied error. The OmniScript component does not appear in Experience Cloud Builder's component palette either.

**Solution:**

```
Step 1 — Create a new Permission Set named "OmniStudio Community Consumer"
  Custom Permissions:
    - OmniStudio Community User: ENABLED

Step 2 — Assign this permission set to the partner community profile
  (or to the Experience Cloud Permission Set Group if one is in use)

Step 3 — Verify in Experience Cloud Builder
  - OmniScript component now appears in the component palette
  - Drag the component onto a page and configure it with the target OmniScript

Step 4 — Test as community user
  - Log in as a community test user
  - Navigate to the page
  - OmniScript loads and submits without errors
```

**Why it works:** The standard `OmniStudio User` permission set grants access to OmniStudio records but does not satisfy the community-specific platform check. The `OmniStudio Community User` custom permission is evaluated separately at runtime for Experience Cloud contexts. Both permission sets must be present simultaneously for a community user to load an OmniScript.

---

## Anti-Pattern: Assigning OmniStudio Admin to All Users for Quick Access

**What practitioners do:** To avoid dealing with multiple permission sets, an admin assigns the `OmniStudio Admin` permission set to every user who needs to interact with OmniScripts, including consumers who will never open the designer.

**What goes wrong:** `OmniStudio Admin` grants access to the OmniStudio designer, configuration tabs, and all authoring surfaces. Assigning it to non-admin users violates least-privilege principles, expands the blast radius of accidental component modifications, and creates audit findings in security reviews. In regulated industries, this is often a compliance blocker.

**Correct approach:** Assign `OmniStudio Admin` only to the builders and administrators who author components. Assign `OmniStudio User` to everyone else. If a specific group needs to run OmniScripts in Experience Cloud, they also need the community consumer custom permission — but not admin access.
