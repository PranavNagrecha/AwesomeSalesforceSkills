# Gotchas — Cross-Cloud Deployment Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ExperienceBundle Cross-Reference Error Is an Ordering Problem, Not a Missing Component

**What happens:** Deploying ExperienceBundle or DigitalExperienceBundle in the same transaction as the Network metadata it references produces the error `Entity of type 'Network' named 'X' cannot be found` — even when the Network component is present in the manifest and appears to have been deployed successfully within the same batch.

**When it occurs:** Any deployment where Network and ExperienceBundle are in the same package.xml. The Metadata API processes types in an internal order, but cross-type reference resolution within a single transaction is not guaranteed to treat Network as fully committed before ExperienceBundle is evaluated.

**How to avoid:** Always split Network and ExperienceBundle into separate, sequential deployment transactions. Deploy Network first. Wait for a successful completion response. Then deploy ExperienceBundle in a second transaction. By that point, the Network record exists in the target org as a fully committed object that ExperienceBundle can reference.

---

## Gotcha 2: SiteDotCom Is Silently Included in Metadata Retrievals

**What happens:** Running `sf project retrieve start` with ExperienceBundle in scope causes Salesforce to include `SiteDotCom` blob files in the local project alongside the ExperienceBundle XML. There is no warning during retrieval. If those files are then included in a `package.xml` for deployment, the deploy fails with a generic metadata error that does not clearly identify SiteDotCom as the cause.

**When it occurs:** Any retrieve of an Experience Builder site that uses the older ExperienceBundle type, or any retrieve that spans a broad wildcard (`*`) on the experience types. The SiteDotCom blob is always generated as a side-effect of an Experience Cloud site retrieval.

**How to avoid:** After any retrieve that includes Experience Cloud metadata, scan the local project for `.site` files or `siteDotCom` directories before staging changes. Add a `.forceignore` rule to prevent SiteDotCom from being staged or deployed:

```
**/siteDotCom/**
*.site
```

Confirm package.xml does not include a `SiteDotCom` type block before running any deploy.

---

## Gotcha 3: DigitalExperienceBundle Is Not Backward-Compatible Across API Versions

**What happens:** A deployment that includes `DigitalExperienceBundle` (introduced at API v54.0) to a target org running on an earlier API version fails. The error message may reference an unrecognized metadata type or produce a generic API error rather than clearly stating the version mismatch.

**When it occurs:** When the source org is on API v54.0 or higher and the target org (sandbox or production) is on an older version. This can happen when sandboxes are not refreshed after a Salesforce major release, or when production is still mid-upgrade cycle.

**How to avoid:** Before any cross-cloud deployment that includes Experience Cloud sites, run a version check on both source and target:

```bash
# Check target org API version
sf org display --target-org <alias> --json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'].get('apiVersion','unknown'))"
```

Ensure the target org API version is equal to or greater than the source org version. If not, coordinate with the platform admin to upgrade the target org before proceeding.

---

## Gotcha 4: Permission Sets Referencing New Objects Must Be in the Foundation Batch

**What happens:** Including a permission set that grants access to a custom object in the same batch as the ExperienceBundle — rather than the foundation batch — can cause the permission set to fail deployment if the object was not already present in the target org. Even when the object is in the same package, the Metadata API's internal processing order may evaluate the permission set before the object is committed.

**When it occurs:** Multi-cloud releases where permission sets granting experience user access to custom objects are grouped with Experience layer metadata for convenience, rather than correctly placed in the foundation batch.

**How to avoid:** Always place permission sets in the foundation batch alongside the custom objects they reference. The foundation batch must succeed completely before the experience layer is deployed. This rule applies even when permission sets are Experience Cloud-specific (e.g., granting access to the community site's data model).

---

## Gotcha 5: CustomSite Must Be Deployed Before ExperienceBundle Even When the Network Already Exists

**What happens:** Some practitioners assume that because the `Network` record exists in the target org, the `CustomSite` record can be skipped or deployed alongside ExperienceBundle. In practice, ExperienceBundle references both the Network and the CustomSite. If CustomSite is missing or deployed in the same transaction as ExperienceBundle, the deployment may fail with a reference error.

**When it occurs:** Incremental deployments where the engineer checks that the Network exists and assumes CustomSite is already present (or bundled with Network). If CustomSite was created manually in the source org or is only partially synced to the target, the assumption breaks.

**How to avoid:** Explicitly include `CustomSite` in the network layer package (`network-package.xml`), not the experience layer package. Always deploy the network layer package before the experience layer package, even if you believe the CustomSite already exists in the target. Idempotent deployment of CustomSite is safe and prevents this ordering failure.
