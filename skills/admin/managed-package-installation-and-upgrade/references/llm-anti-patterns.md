# LLM Anti-Patterns — Managed Package Installation And Upgrade

Common mistakes AI coding assistants make when advising subscriber admins on managed package installs. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending "Install for All Users" because the vendor said to

**What the LLM generates:** "Per the vendor's quickstart, choose Install for All Users at the install prompt. This grants access to everyone immediately."

**Why it happens:** Vendor documentation often optimizes for time-to-first-use, not for security posture or reversibility. Training data is heavy with quickstart guides written by ISV marketing.

**Correct pattern:**

```
At install time, choose Install for Admins Only. After install, grant feature
access via a Permission Set Group that combines the package's bundled
Permission Set with your org's role-specific Permission Sets. This grant is
reversible (unassign), auditable (Permission Set assignment history), and
survives subsequent upgrades.
```

**Detection hint:** Any install guidance that recommends "Install for All Users" without explicitly weighing the irreversibility of profile-based grants against the Permission Set Group alternative.

---

## Anti-Pattern 2: Treating uninstall data export as "Salesforce will keep it for 48 hours"

**What the LLM generates:** "Uninstall the package. Salesforce will email you a data export and keep it for 48 hours if you need to restore."

**Why it happens:** The 48-hour retention is documented and easy to over-trust. LLMs treat documented platform behavior as guaranteed recovery.

**Correct pattern:**

```
Before uninstalling, export all data from package-introduced Custom Objects
via Data Loader or Bulk API to durable subscriber-controlled storage (S3,
archive bucket, secured share). The Salesforce-side 48-hour email export is
a sanity check, not a recovery mechanism. Document the durable-storage
location in the uninstall change record.
```

**Detection hint:** Any uninstall guidance that relies on the 48-hour retention as a primary recovery path, without first calling for pre-export to subscriber-controlled storage.

---

## Anti-Pattern 3: Conflating publisher-side and subscriber-side responsibilities

**What the LLM generates:** "To handle the post-install setup, write an `InstallHandler` Apex class that sets the Named Credential secret and assigns Permission Sets to users."

**Why it happens:** `InstallHandler` is well-documented and LLMs assume "anything related to install" can be done in it. The training data mixes publisher-side (writing the package, including `InstallHandler`) and subscriber-side (installing the package) concerns.

**Correct pattern:**

```
The publisher's InstallHandler runs at install time but cannot set Named
Credential client secrets (the secret value isn't known at install time) or
assign Permission Sets to specific users (the subscriber's user list isn't
known at package build time). These steps belong in the subscriber-authored
post-install configuration checklist, executed by the admin after install
completes.
```

**Detection hint:** Any subscriber-facing install guidance that says "the package's InstallHandler will [secret/user-assignment/subscriber-data-specific action]" — `InstallHandler` is publisher-authored and runs without subscriber-specific context.

---

## Anti-Pattern 4: Installing a beta package in production

**What the LLM generates:** "Install version `04tBETAxxx` in production using the install URL the vendor shared."

**Why it happens:** The beta vs. released distinction isn't visible from the `04t` ID alone. LLMs treat any install URL as production-installable.

**Correct pattern:**

```
Confirm with the publisher in writing that the version ID is "Released," not
"Beta," before any production install. Beta versions install successfully in
sandboxes, Developer Edition orgs, and scratch orgs but fail with a
not-installable error in production. The version's release state is only
visible in the publisher's packaging org records.
```

**Detection hint:** Any production-install recommendation that doesn't explicitly verify the version's released state with the publisher.

---

## Anti-Pattern 5: Ignoring subscriber-code references when planning uninstall

**What the LLM generates:** "To uninstall the package, go to Setup → Installed Packages → Uninstall. Click Yes when prompted."

**Why it happens:** The official uninstall flow is short. LLMs report it verbatim without flagging the prerequisite: subscriber-written Apex, Flows, and Validation Rules that reference the package namespace must be removed first or the uninstall fails.

**Correct pattern:**

```
Before initiating uninstall:
1. Search the org's Apex, Flow, Validation Rules, and Reports for references
   to the package namespace.
2. For each reference, either remove the dependency or refactor it to a
   subscriber-owned equivalent.
3. Run the uninstall in a sandbox first to confirm no references block the
   operation. The error message lists the blocking components.
4. Only then proceed to production uninstall.
```

**Detection hint:** Any uninstall guidance that starts at "click Uninstall" without first calling for a subscriber-code reference audit.
