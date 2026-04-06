# Gotchas — Rollback And Hotfix Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Record Types Cannot Be Deleted via Metadata API

**What happens:** A failed deployment created a new Record Type on a standard or custom object. When attempting to roll back by deploying a destructive changes manifest, the deployment fails with an error indicating the component cannot be deleted.

**When it occurs:** Any time a rollback package includes a Record Type in a `destructiveChanges.xml` manifest. The Metadata API does not support deletion of Record Types regardless of whether they are active or assigned.

**How to avoid:** Identify Record Types in the deployment manifest before building the rollback package. Remove them from the destructive manifest and add a manual remediation step: deactivate the Record Type in Setup, remove it from page layout assignments, and remove it from record type assignment in profiles/permission sets.

---

## Gotcha 2: Active Flow Versions Cannot Be Deactivated via Deployment

**What happens:** A deployment activated a new Flow version. The rollback attempts to deploy the previous Flow version as active, but the platform will not deactivate the currently active version through a deployment alone. The rollback deployment either fails or leaves the wrong version active.

**When it occurs:** Any time a Flow was activated as part of the failed deployment. The Metadata API can deploy a Flow definition, but activating a specific version and deactivating the current one requires manual action in Setup or a specific API call sequence.

**How to avoid:** Before deploying the rollback package, manually deactivate the problematic Flow version in Setup. Then deploy the rollback package which includes the previous version. Alternatively, use the Tooling API to set the `ActiveVersionNumber` on the FlowDefinition record.

---

## Gotcha 3: Quick Deploy Validation Expires After 10 Days

**What happens:** A team validates a hotfix on Friday but delays promotion to the following week. By the time they attempt `sf project deploy quick`, the validation has expired and the command fails with an error like "The request to quick-deploy failed because the validation is no longer valid."

**When it occurs:** The 10-day window is calculated from the completion timestamp of the validation job. There is no platform setting to extend it. Weekends and holidays count toward the 10 days.

**How to avoid:** Promote validated deployments as soon as the deployment window opens. If the validation has expired, re-run `sf project deploy validate` to get a fresh job ID. For planned hotfixes, validate no more than 1-2 business days before the intended promotion date.

---

## Gotcha 4: Picklist Values Added in a Failed Deployment Cannot Be Removed via API

**What happens:** A deployment added new picklist values to a field. The rollback attempts to deploy the field definition without those values, but the Metadata API does not remove picklist values that already exist on the field. The values persist in production even after the rollback deployment succeeds.

**When it occurs:** Any deployment that adds values to a standard or custom picklist field. The API is additive-only for picklist values — it will add new values but will not remove existing ones.

**How to avoid:** Document all picklist value additions in the deployment plan. If rollback is needed, manually remove the values in Setup using Field Settings or the Replace Picklist Values feature. If records already reference the new values, those records must be updated first.

---

## Gotcha 5: Rollback of a Deployment That Added New Components Requires Destructive Changes

**What happens:** A team rolls back by re-deploying the pre-deploy archive, but new components that were added in the failed deployment (not updates to existing components) remain in production. The archive only contains the previous versions of components that existed before — it does not know about components that were newly created.

**When it occurs:** Every deployment that includes newly-created metadata types (new Apex classes, new LWC components, new custom fields that did not previously exist). Re-deploying the old state does not remove the new additions.

**How to avoid:** Compare the deployment `package.xml` against the pre-deploy archive contents. Any component in the deployment manifest that is not present in the archive is a new addition and must be listed in a `destructiveChangesPost.xml` for removal. The checker script (`check_rollback_and_hotfix_strategy.py --manifest-dir <path>`) can automate this comparison.

---

## Gotcha 6: Hotfix Branch Merged Only to Production Creates a Future Regression

**What happens:** A hotfix is deployed to production and merged into the production branch, but the team forgets to merge it back into the development branch. The next scheduled release overwrites the hotfix with the old broken code because the development branch never received the fix.

**When it occurs:** High-pressure hotfix scenarios where the team focuses on production recovery and skips the post-deployment merge step. Particularly common in teams using separate long-lived production and development branches.

**How to avoid:** Add a mandatory post-hotfix checklist item: merge the hotfix branch into both the production branch and the main development branch. Automate this with a CI rule that blocks closing the hotfix PR until a corresponding merge PR to develop is also approved.
