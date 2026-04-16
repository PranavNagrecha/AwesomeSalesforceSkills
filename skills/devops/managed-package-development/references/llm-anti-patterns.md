# LLM Anti-Patterns — Managed Package Development

Common mistakes AI coding assistants make when generating or advising on Salesforce 1GP managed package development.

---

## Anti-Pattern 1: Recommending `sf package version create` CLI for 1GP Package Upload

**What the LLM generates:** `sf package version create --package "My App" --code-coverage --installation-key test1234` for uploading a 1GP managed package.

**Why it happens:** LLMs associate Salesforce package management with the modern CLI commands which are widely documented for 2GP packages.

**Correct pattern:** 1GP packages are uploaded via Setup > Package Manager > Upload in the packaging org, or via the Tooling API `PackageUploadRequest` object. The `sf package version create` CLI command only works with second-generation (2GP) packages using 0Ho-prefixed package IDs.

**Detection hint:** If CLI package upload instructions appear in a 1GP context, they are incorrect.

---

## Anti-Pattern 2: Performing Large DML in PostInstall Script

**What the LLM generates:** `onInstall()` method that inserts thousands of Custom Metadata or data records directly in the PostInstall Apex handler.

**Why it happens:** LLMs model the PostInstall script as the natural place to do all setup work, not knowing about subscriber org governor limit constraints.

**Correct pattern:** PostInstall scripts run in the subscriber org under governor limits. Large data operations (thousands of records) will exceed DML limits and cause the install to fail. For large setup tasks, enqueue a Queueable from the PostInstall script: `System.enqueueJob(new MySetupQueueable())`. The Queueable executes asynchronously after install completes.

**Detection hint:** If `onInstall()` contains direct DML for more than a few hundred records, governor limit failure risk is high in subscriber orgs.

---

## Anti-Pattern 3: Assuming Flows Can Be Deleted from Packaging Org After Release

**What the LLM generates:** "To remove the Flow from the next package version, delete it from the packaging org and upload a new version."

**Why it happens:** LLMs model Flows as standard deletable Salesforce components. They do not model the managed package component lock that prevents deletion after release.

**Correct pattern:** Flows included in a released managed package cannot be deleted from the packaging org. They can be deactivated and replaced with newer versions, but the Flow entity remains permanently in the packaging org's package scope.

**Detection hint:** If instructions say to delete a Flow from a packaging org that has already been used for a Released or Beta package upload, the action will fail.

---

## Anti-Pattern 4: Using Developer Edition Scratch Orgs for 1GP Package Development

**What the LLM generates:** Instructions to use scratch orgs or Dev Hub-linked environments for 1GP managed package development, following 2GP patterns.

**Why it happens:** LLMs conflate 1GP and 2GP development models. Scratch orgs and Dev Hub are 2GP concepts.

**Correct pattern:** 1GP development happens in the packaging org — a persistent Developer Edition org that serves as the single source of truth for all package components. Scratch orgs are not used in 1GP development workflows. Testing is done in the packaging org itself or in a separate sandbox linked to the subscriber installation.

**Detection hint:** If instructions reference scratch org creation or Dev Hub for a 1GP package workflow, the development model is wrong.

---

## Anti-Pattern 5: Treating 1GP Package Namespace as Changeable

**What the LLM generates:** "If you want to rebrand, you can update the namespace prefix in your packaging org Settings after the package is released."

**Why it happens:** LLMs do not model the permanent binding of a namespace prefix once it is registered and the package is released.

**Correct pattern:** A namespace prefix is registered in a Developer Edition org and is permanent. Once a package is released with a namespace, the namespace cannot be changed, transferred to another org, or reused. Rebranding requires creating a new package with a new namespace from scratch.

**Detection hint:** Any suggestion that namespace prefix can be changed after release is incorrect.
