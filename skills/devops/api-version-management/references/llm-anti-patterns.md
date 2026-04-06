# LLM Anti-Patterns — API Version Management

Common mistakes AI coding assistants make when generating or advising on Salesforce API version management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming sourceApiVersion Controls Runtime Behavior

**What the LLM generates:** "Set `sourceApiVersion` to `63.0` in `sfdx-project.json` and all your Apex classes will run at API version 63.0."

**Why it happens:** LLMs conflate the project-level configuration with per-component runtime versioning. The name `sourceApiVersion` sounds like it should control the source code's API version. Training data often shows `sfdx-project.json` changes without the corresponding per-component updates.

**Correct pattern:**

```text
sourceApiVersion in sfdx-project.json controls the API version used by
the Salesforce CLI during deploy/retrieve operations. Each component's
runtime API version is determined by the <apiVersion> element in its
own -meta.xml file. Both must be updated for a true version upgrade.
```

**Detection hint:** Look for advice that mentions only `sfdx-project.json` without also mentioning per-component `-meta.xml` updates.

---

## Anti-Pattern 2: Using a Hardcoded Retired API Version in Code Examples

**What the LLM generates:** Apex class examples with `<apiVersion>28.0</apiVersion>` or REST endpoint examples targeting `/services/data/v28.0/`, where version 28.0 has been retired since Summer '22.

**Why it happens:** LLMs are trained on older documentation, blog posts, and Stack Exchange answers that used API versions current at the time of writing. Versions 7.0-30.0 are well-represented in training data but are now retired.

**Correct pattern:**

```xml
<!-- Use a current, supported version -->
<apiVersion>63.0</apiVersion>
```

```text
REST endpoint: /services/data/v63.0/sobjects/Account
Minimum safe version as of 2025: 31.0
```

**Detection hint:** Flag any `apiVersion` value below 31.0 or any REST/SOAP URL containing `/v[0-9]{1,2}\.0/` where the version number is 30 or below.

---

## Anti-Pattern 3: Omitting apiVersion from LWC .js-meta.xml Files

**What the LLM generates:** A `.js-meta.xml` file without an `<apiVersion>` element, relying on implicit org-level versioning.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
</LightningComponentBundle>
```

**Why it happens:** Much of the LWC training data predates Spring '25, when explicit version declaration became required. Older examples and tutorials do not include `<apiVersion>`.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
</LightningComponentBundle>
```

**Detection hint:** Any `.js-meta.xml` output that does not contain `<apiVersion>`.

---

## Anti-Pattern 4: Recommending a Big-Bang Upgrade Without Risk Assessment

**What the LLM generates:** "Update all your Apex classes to API version 63.0 by running a find-and-replace on all -meta.xml files." No mention of behavior changes between versions, no incremental approach, no test strategy.

**Why it happens:** LLMs optimize for concise answers. A one-line find-and-replace is technically correct for changing the version number but ignores the runtime behavior changes that occur across API versions (null handling, SOQL semantics, trigger context changes).

**Correct pattern:**

```text
1. Audit current versions and group components into tiers by version range.
2. Review Salesforce release notes for behavior changes in each version jump.
3. Upgrade Tier 1 (oldest) first and run the full test suite.
4. Proceed to next tier only after all tests pass.
5. Update sourceApiVersion last, after all components are at the target.
```

**Detection hint:** Advice that suggests updating all components at once without mentioning test isolation, behavior changes, or release notes review.

---

## Anti-Pattern 5: Confusing package.xml Version with Component API Version

**What the LLM generates:** "Set the version in `package.xml` to 63.0 to upgrade all your components to the latest API version."

**Why it happens:** Both `package.xml` and component `-meta.xml` files contain version numbers, and LLMs frequently conflate them. The `package.xml` version controls which metadata types are visible to the Metadata API during retrieve/deploy. It does not change the runtime API version of any component.

**Correct pattern:**

```text
package.xml <version>63.0</version> — controls Metadata API visibility
  (which types/fields can be retrieved or deployed).

Component -meta.xml <apiVersion>63.0</apiVersion> — controls runtime
  behavior (which platform features and method signatures the component uses).

These are independent settings. Updating package.xml does NOT upgrade
component versions.
```

**Detection hint:** Advice that mentions only `package.xml` version as a solution for upgrading component API versions, without also addressing per-component `-meta.xml` files.

---

## Anti-Pattern 6: Ignoring Transport API Versions in Integration Advice

**What the LLM generates:** Integration guidance that uses a vague or outdated version in endpoint URLs (e.g., `/services/data/v50.0/`) without explaining that this is a distinct version layer from metadata component versions, and without checking whether the chosen version is approaching retirement.

**Why it happens:** LLMs copy endpoint URLs from training data without evaluating whether the version is current. The distinction between transport API version and component API version is rarely explained in tutorials.

**Correct pattern:**

```text
Use the current or recent API version in endpoint URLs:
  /services/data/v63.0/sobjects/Account

Monitor transport API versions separately from metadata versions.
Query ApiTotalUsage event logs to detect deprecated version usage:
  SELECT ApiVersion, Client, Count FROM ApiTotalUsage WHERE ApiVersion < 45
```

**Detection hint:** REST or SOAP endpoint URLs in generated code where the version is more than 3 major releases behind the current release.
