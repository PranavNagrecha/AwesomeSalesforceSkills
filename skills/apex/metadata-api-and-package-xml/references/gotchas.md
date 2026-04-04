# Gotchas — Metadata API and Package.xml

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Package.xml Version Tag Overrides Client API Version

**What happens:** The `<version>` element inside package.xml controls the Metadata API version used for the retrieve or deploy operation, regardless of the version your CLI or SOAP client was built against. If you have an old package.xml checked into source control with `<version>40.0</version>`, metadata operations will behave as if the client is v40.0 even when running the latest Salesforce CLI.

**When it occurs:** Whenever a stale or manually edited package.xml is used in a retrieve or deploy without updating the `<version>` tag. Common in repos that have been maintained across multiple Salesforce releases without updating the manifest version.

**How to avoid:** Keep the `<version>` tag updated to the current production API version (the version number for Spring '26 is 66.0). Review package.xml files when upgrading orgs across major releases. The Metadata API supports versions 31.0–66.0; anything older than v31.0 is retired.

---

## Gotcha 2: Wildcards Return Nothing for Standard Objects

**What happens:** Using `<members>*</members>` for the `CustomObject` type retrieves all custom objects successfully but silently omits all standard objects. No error is thrown. Practitioners assume the retrieval captured everything and proceed without standard object customizations.

**When it occurs:** Any time a package.xml relies solely on the wildcard for `CustomObject` and the org has customized standard objects. The impact is most severe during an initial org-to-source-control migration where the developer assumes the resulting package is complete.

**How to avoid:** Enumerate all customized standard objects (Account, Contact, Lead, Opportunity, etc.) explicitly in the package.xml member list alongside the wildcard. Use `sf schema list sobjects` or the Object Manager in Setup to identify which standard objects have customizations that need to be retrieved.

---

## Gotcha 3: 75% Code Coverage Is Enforced Per Component, Not Org-Wide

**What happens:** A deployment to production fails with a code coverage error even when the org's overall Apex coverage is well above 75%. The failure is because one or more individual Apex classes or triggers in the deployment package have less than 75% coverage individually, even if the org-wide average is high.

**When it occurs:** When deploying a subset of Apex classes using `RunSpecifiedTests` with tests that only partially cover the classes in the deployment. Also triggered when a new class is added with minimal test coverage, even if other well-tested classes are in the same deployment.

**How to avoid:** Before any production deployment that includes Apex, check per-class coverage: use the Developer Console's Tests tab, run `sf apex run test` locally, or review the CI coverage report per file. Do not rely on the org-wide coverage percentage. Ensure the specific test classes listed in `RunSpecifiedTests` actually cover each class in the deployment at the 75% threshold.

---

## Gotcha 4: destructiveChanges.xml Cannot Delete Components on Active Lightning Pages

**What happens:** A deployment that includes `destructiveChanges.xml` or `destructiveChangesPost.xml` targeting a component that an active Lightning App Builder page references will fail. The error message is not always obvious about the Lightning page dependency.

**When it occurs:** When a custom object or LWC component has been placed on a Lightning record page, app page, or home page in Lightning App Builder, and then you attempt to delete that component via Metadata API without first removing it from the page configuration.

**How to avoid:** Before including a component in destructive changes, check if it appears on any Lightning page in Lightning App Builder (Setup → Lightning App Builder). Remove the component from all active pages and deactivate any override before running the destructive deployment.

---

## Gotcha 5: User References in Deployments Must Match Target Org Usernames

**What happens:** Metadata components that reference specific users (dashboard running users, workflow email alert recipients, etc.) require matching usernames in the target org. When deploying from production to a sandbox, Salesforce appends the sandbox name to usernames (e.g., `user@company.com` becomes `user@company.com.sandbox`). If the sandbox user does not exist with that username, the deployment stops with an error.

**When it occurs:** Any deployment that includes metadata referencing a specific user, deployed to an org where the user does not exist or has a different username format.

**How to avoid:** Salesforce automatically adapts the org domain portion of usernames during deployment. However, if two or more users match, or if no match is found, the deployment halts. Audit user-referencing metadata (dashboards, workflow email alerts, approval processes with specific approvers) before deploying to a new org. Ensure target-org users exist with expected usernames.
