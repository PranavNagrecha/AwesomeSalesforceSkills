# Examples — Experience Cloud Deployment Admin

## Example 1: First-Time Site Deployment to Production via Change Sets

**Context:** A company has built an Experience Cloud partner portal (LWR template) in a sandbox. The site has never been deployed to production. The admin uses change sets and has no SFDX tooling.

**Problem:** The admin creates a single outbound change set containing all metadata — Apex classes, custom objects, the Network record, CustomSite, and ExperienceBundle — and deploys it in one step. The deployment fails partway through with an error referencing the ExperienceBundle component, even though the ExperienceBundle itself has no syntax errors.

**Solution:**

Split the deployment into two ordered change sets:

**Change Set 1 — Dependencies (deploy first):**
```
Components included:
- ApexClass: PartnerPortalController
- ApexClass: PartnerPortalService
- CustomObject: PartnerAccount__c
- CustomField: PartnerAccount__c.TierLevel__c
- Profile: Partner Community Login User
- PermissionSet: PartnerPortalAccess
- Network: PartnerPortal               ← must be present before ExperienceBundle
- CustomSite: PartnerPortal            ← must be present before ExperienceBundle
```

**Change Set 2 — Site Bundle (deploy after Change Set 1 succeeds):**
```
Components included:
- ExperienceBundle: PartnerPortal
```

After Change Set 2 deploys successfully, the admin opens Experience Builder in production and clicks Publish to make the site live.

**Why it works:** The `Network` and `CustomSite` records must exist in the target org before `ExperienceBundle` can deploy. Splitting the change sets enforces this ordering because Change Set 2 is only uploaded and deployed after Change Set 1 succeeds. Within a single change set, Salesforce does not guarantee a dependency-aware commit order.

---

## Example 2: Automated Site Deployment and Publish via Salesforce CLI

**Context:** A DevOps team uses Salesforce CLI with source-tracked sandboxes and wants a repeatable, automated release pipeline for an Experience Cloud customer portal. The pipeline must publish the site automatically after deployment without manual intervention.

**Problem:** The team's single `package.xml` includes ExperienceBundle, Network, and Apex classes. When the CI pipeline runs `sf project deploy start --manifest package.xml`, the deploy occasionally fails with a dependency error. The team also discovers after each successful deploy that the site is in Draft status and end users cannot access it until someone manually publishes.

**Solution:**

Split the manifest and add a Connect REST API publish step:

**package-deps.xml:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CustomerPortalController</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>CustomerPortal</members>
        <name>Network</name>
    </types>
    <types>
        <members>CustomerPortal</members>
        <name>CustomSite</name>
    </types>
    <version>63.0</version>
</Package>
```

**package-site.xml:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CustomerPortal</members>
        <name>ExperienceBundle</name>
    </types>
    <version>63.0</version>
</Package>
```

**Pipeline steps:**
```bash
# Step 1: Deploy dependencies including Network and CustomSite
sf project deploy start \
  --manifest package-deps.xml \
  --target-org production \
  --wait 30

# Step 2: Deploy ExperienceBundle (only after Step 1 succeeds)
sf project deploy start \
  --manifest package-site.xml \
  --target-org production \
  --wait 30

# Step 3: Publish the site via Connect REST API
COMMUNITY_ID=$(sf data query \
  --query "SELECT Id FROM Network WHERE Name = 'CustomerPortal'" \
  --target-org production \
  --json | jq -r '.result.records[0].Id')

sf org display --target-org production --json | \
  jq -r '.result.accessToken' | \
  xargs -I TOKEN curl -X POST \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    "https://myorg.my.salesforce.com/services/data/v63.0/connect/communities/${COMMUNITY_ID}/publish"
```

**Why it works:** Separating the manifests guarantees that Network and CustomSite exist in the target before ExperienceBundle is deployed. The Connect REST API publish call removes the manual publish step, making the release fully automated and repeatable.

---

## Anti-Pattern: Including SiteDotCom in the ExperienceBundle Deployment Package

**What practitioners do:** When retrieving an Experience Cloud site using `sf project retrieve start` or the Metadata API, Salesforce includes a `SiteDotCom` component in the local retrieval output alongside the ExperienceBundle. Practitioners include this component unchanged in their deployment manifest or change set.

**What goes wrong:** The deployment fails with an error. SiteDotCom stores a binary blob representing the legacy site structure and is not intended to be deployed together with ExperienceBundle for Experience Builder sites. Including it in the same deployment package causes the entire deploy to fail, even when the ExperienceBundle metadata itself is valid. The error message often references the ExperienceBundle rather than SiteDotCom, leading teams to debug the wrong component.

**Correct approach:** After retrieving site metadata, open the `package.xml` and remove any `SiteDotCom` entries before deploying. If using a file-based project structure, also delete the retrieved `SiteDotCom` directory from the deployment payload. Deploy only `Network`, `CustomSite`, and `ExperienceBundle` in the site-specific deploy step.
