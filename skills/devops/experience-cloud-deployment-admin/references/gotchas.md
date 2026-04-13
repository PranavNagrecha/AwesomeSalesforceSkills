# Gotchas — Experience Cloud Deployment Admin

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SiteDotCom Blob Is Automatically Retrieved But Must Never Be Deployed with ExperienceBundle

**What happens:** When retrieving an Experience Cloud site using the Metadata API or Salesforce CLI, Salesforce automatically includes a `SiteDotCom` component in the retrieved package alongside the `ExperienceBundle`. If this `SiteDotCom` component is left in the deployment manifest and deployed at the same time as `ExperienceBundle`, the entire deployment fails. The error message typically points to the ExperienceBundle component rather than SiteDotCom, making the root cause difficult to identify.

**When it occurs:** Any time a practitioner retrieves an Experience Builder site and deploys the output without reviewing and cleaning the manifest. It is especially common when automating retrieval/deploy cycles without a manifest review step.

**How to avoid:** After every retrieval of Experience Cloud site metadata, explicitly check the `package.xml` for `SiteDotCom` entries and remove them before deploying. If using a file-based project (`force-app`), also delete the `siteDotCom/` directory from the deployment payload. Add a pre-deploy validation step to the CI pipeline that fails the build if `SiteDotCom` is present in the manifest alongside `ExperienceBundle`.

---

## Gotcha 2: Successful Deployment Leaves the Site in Unpublished Draft Status

**What happens:** After a fully successful ExperienceBundle deployment — no errors, deployment status shows Succeeded — end users report they cannot access the site, or the site URL shows a "Site Under Construction" page. The deployment completed correctly, but the site remains in **Draft** status until an admin manually publishes it.

**When it occurs:** Every ExperienceBundle deployment, regardless of whether the site was Published in the source org. Publishing status is not transferred as part of the deployment. This catches teams off guard on the first production deployment and on every subsequent deployment if publishing is not included in the release runbook.

**How to avoid:** Include a mandatory Publish step in the deployment runbook immediately after the ExperienceBundle deploy succeeds. Options are: (1) open Experience Builder in the target org and click Publish, or (2) call `POST /services/data/vXX.0/connect/communities/{communityId}/publish` via the Connect REST API to automate the step in a pipeline. Add a post-deploy smoke test that checks the site's `Status` field in the `Network` object is `Live`.

---

## Gotcha 3: Enable Experience Bundle Metadata API Must Be Enabled Independently in Every Org

**What happens:** The **Enable Experience Bundle Metadata API** checkbox in Setup > Digital Experiences > Settings is org-specific. When a sandbox is refreshed from production, or when a new scratch org is created, this setting is not automatically carried over. Attempting to retrieve or deploy ExperienceBundle in an org where the flag is disabled results in a failure. The error message does not always clearly state that the flag is missing — it may present as a generic metadata retrieval or component-not-found error.

**When it occurs:** After a sandbox refresh, when onboarding a new sandbox environment, or when using scratch orgs for Experience Cloud development. Teams often enable the flag in their primary sandbox and forget to enable it in newly provisioned orgs.

**How to avoid:** Add verification of this flag to the environment setup checklist and to the pre-deployment checklist. For scratch orgs, include `"hasSitesEnabled": true` and `"hasCommunityEnabled": true` in the scratch org definition file, and add a post-create script that navigates to Digital Experience settings and enables the checkbox (it cannot be set via the scratch org definition JSON directly). For sandbox refreshes, add the flag enablement as a post-refresh runbook step.

---

## Gotcha 4: Network Record Name Must Match Exactly Between Source and Target

**What happens:** If the Experience Cloud site was renamed in the source org after the Network record was originally created, the ExperienceBundle references the original network `fullName`. Deploying to a target org where the Network record name does not match the ExperienceBundle's reference causes a deployment failure because ExperienceBundle cannot locate its parent Network.

**When it occurs:** When sites have been renamed in the source org, or when the target org has a Network record with a slightly different name (e.g., `CustomerPortal` vs `Customer_Portal`). Also occurs when deploying to a scratch org where the Network was created with an auto-generated name.

**How to avoid:** Before deploying ExperienceBundle, verify that the `Network` metadata component's `fullName` in the retrieved XML matches the `fullName` of the Network record in the target org exactly (case-sensitive). If they differ, either rename the target Network record to match, or retrieve and redeploy the Network metadata with the correct name before deploying ExperienceBundle.

---

## Gotcha 5: Guest User Profile Permissions Are Not Included in ExperienceBundle and Do Not Transfer Automatically

**What happens:** Every Experience Cloud site has a dedicated Guest User Profile that controls what unauthenticated visitors can access (object CRUD, FLS, Apex class access, record visibility). This profile is a separate `Profile` metadata component and is not embedded in ExperienceBundle. After deploying the site to a target org, the Guest User Profile in the target org does not automatically reflect permission changes made in the source. The site may appear to work for authenticated users but fail for guests, or expose data that should be restricted.

**When it occurs:** On every ExperienceBundle deployment when the Guest User Profile has been modified in the source org. Teams frequently overlook this because the Profile is not visually grouped with the Experience Cloud site components in the Setup UI.

**How to avoid:** Always retrieve the site's Guest User Profile explicitly and include it as a `Profile` component in the deployment package (as a separate deploy step). The Guest User Profile can be identified by its naming convention: `[SiteName] Profile`. After deployment, manually verify object permissions, FLS, Apex class access, and connected app settings on the Guest User Profile in the target org.
