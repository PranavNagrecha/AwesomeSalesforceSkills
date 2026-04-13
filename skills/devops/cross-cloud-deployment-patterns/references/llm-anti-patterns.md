# LLM Anti-Patterns — Cross-Cloud Deployment Patterns

Common mistakes AI coding assistants make when generating or advising on cross-cloud Salesforce deployments. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Single Package for All Cross-Cloud Metadata

**What the LLM generates:** A single `package.xml` that includes CustomObject, ApexClass, Network, CustomSite, and ExperienceBundle all together, with advice to deploy in one transaction.

**Why it happens:** LLMs treat deployment as a simple "bundle everything and ship it" operation, based on training data where single-package deploys are the most common pattern documented. The ordering constraint specific to cross-cloud Experience Cloud metadata is underrepresented in training data relative to generic deployment documentation.

**Correct pattern:**

```
Split into three ordered deployment transactions:
1. foundation-package.xml → CustomObject, ApexClass, PermissionSet, Profile
2. network-package.xml → Network, CustomSite
3. experience-package.xml → ExperienceBundle or DigitalExperienceBundle (SiteDotCom excluded)

Each batch must complete successfully before the next begins.
```

**Detection hint:** Look for a single `package.xml` that contains both `Network` and `ExperienceBundle` (or `DigitalExperienceBundle`) in the same `<types>` list. This is the anti-pattern.

---

## Anti-Pattern 2: Including SiteDotCom in the Deployment Package

**What the LLM generates:** A `package.xml` that includes a `SiteDotCom` type block, often because the LLM retrieved metadata that included SiteDotCom and assumed it should be included in the deploy.

**Why it happens:** LLMs see `SiteDotCom` in retrieved metadata and treat retrieval coverage as equivalent to deployability. The non-deployable status of SiteDotCom is a platform-specific constraint that is not prominently documented and is often absent from training data.

**Correct pattern:**

```xml
<!-- WRONG — do not include -->
<!-- <types><members>My_Site</members><name>SiteDotCom</name></types> -->

<!-- CORRECT — exclude SiteDotCom from all deployment manifests -->
<!-- Add to .forceignore: -->
<!-- **/siteDotCom/** -->
<!-- *.site -->
```

**Detection hint:** Search the generated `package.xml` for `<name>SiteDotCom</name>`. Its presence in a deploy manifest is always wrong.

---

## Anti-Pattern 3: Ignoring API Version Alignment Between Source and Target

**What the LLM generates:** Deployment instructions for DigitalExperienceBundle with no mention of API version constraints. The LLM assumes the target org can accept any metadata type that the source org produces.

**Why it happens:** API version compatibility is a deployment prerequisite, not a metadata configuration step. LLMs trained on configuration and code generation tasks underweight deployment infrastructure prerequisites. The DigitalExperienceBundle version constraint is also relatively new and may not be well-represented in training data.

**Correct pattern:**

```bash
# Check target org API version before any cross-cloud deploy
sf org display --target-org <alias> --json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('API Version:', d['result'].get('apiVersion','unknown'))"

# Target org version must be >= source org version
# If not, block the deployment until the target is upgraded
```

**Detection hint:** If deployment instructions for DigitalExperienceBundle do not include a pre-flight API version check, the instructions are incomplete.

---

## Anti-Pattern 4: Placing Permission Sets in the Experience Layer Batch

**What the LLM generates:** A deployment plan where permission sets granting access to community users or custom objects are grouped with ExperienceBundle in the experience layer batch, rather than in the foundation batch.

**Why it happens:** LLMs sometimes group permission sets thematically with the feature they support (e.g., "Experience Cloud permission sets go with the Experience Cloud package"). The correct rule is structural: permission sets must deploy after the objects they reference exist but before any experience layer that depends on access being granted.

**Correct pattern:**

```
foundation-package.xml contents:
  - CustomObject (the objects the permission sets grant access to)
  - PermissionSet (the permission sets granting that access)
  - ApexClass
  - LightningComponentBundle

experience-package.xml contents:
  - ExperienceBundle or DigitalExperienceBundle
  - (no permission sets)
```

**Detection hint:** If a generated `experience-package.xml` contains `<name>PermissionSet</name>`, the plan needs to be revised.

---

## Anti-Pattern 5: Treating ExperienceBundle and DigitalExperienceBundle as Interchangeable

**What the LLM generates:** Instructions that use `ExperienceBundle` for a site that requires `DigitalExperienceBundle` (or vice versa), because the LLM does not differentiate between the two types based on the org's API version or site framework.

**Why it happens:** Both types serve the same conceptual purpose (packaging an Experience Builder site), and LLMs may conflate them or default to the more-documented `ExperienceBundle` name regardless of context. The version boundary (API v54.0) is a concrete platform constraint that requires specific knowledge to apply correctly.

**Correct pattern:**

```
Use ExperienceBundle when:
  - Source org API version < 54.0
  - Site was built before the Digital Experiences framework

Use DigitalExperienceBundle when:
  - Source org API version >= 54.0
  - Site is built with the newer Digital Experiences framework

Check by retrieving the site and inspecting the top-level directory:
  - .../digitalExperienceBundles/<SiteName>/ → use DigitalExperienceBundle
  - .../experienceBundle/<SiteName>/         → use ExperienceBundle
```

**Detection hint:** If the generated package.xml specifies `ExperienceBundle` for a site that was retrieved under a `digitalExperienceBundles/` directory, the type name is wrong.

---

## Anti-Pattern 6: Not Verifying Network Record Exists After Network Layer Deploy

**What the LLM generates:** A deployment plan that deploys the network layer and immediately proceeds to deploy the experience layer without verifying the Network record is queryable in the target org.

**Why it happens:** LLMs model deployment as a sequence of commands without modeling the asynchronous verification step between them. Successful deployment completion does not always guarantee immediate queryability, especially in large orgs where post-deploy processing can lag.

**Correct pattern:**

```bash
# After network layer deploy completes, verify the Network record is queryable
sf data query \
  --query "SELECT Id, Name, Status FROM Network WHERE Name = 'Partner_Portal'" \
  --target-org <alias>

# Only proceed to experience layer deploy if the above returns a record
```

**Detection hint:** Any multi-step cross-cloud deployment plan that does not include a `sf data query` or equivalent verification step between the network layer and the experience layer is missing the verification gate.
