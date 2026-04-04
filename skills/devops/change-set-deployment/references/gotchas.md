# Gotchas — Change Set Deployment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Profiles Replace Entirely, Not Incrementally

**What happens:** When a Profile metadata type is included in a change set and deployed, Salesforce replaces the full profile definition in the target org with the version from the source. Any production-only customizations — additional app assignments, custom tab visibility, custom permission grants, or field-level security settings that were manually added in production after the last sandbox refresh — are silently overwritten with no warning or diff shown in the UI.

**Why:** Profile metadata is a monolithic XML file. The change set mechanism has no merge logic. The target profile becomes an exact copy of what was in the source. There is no conflict detection.

**How to avoid:** Default to permission sets for all new feature access grants. If a profile must be deployed (e.g., because a new object requires profile-level object permissions that cannot be separated), retrieve the target production profile first using the Metadata API or CLI, compare it to the source version, reconcile all differences, and re-deploy the merged version. Never blindly include profiles generated from a refreshed sandbox without this reconciliation step.

---

## Gotcha 2: Re-Uploading After Validation Resets the Quick Deploy Clock

**What happens:** A team validates a change set in production on Monday, earning a 10-day quick deploy window through Thursday of the following week. On Wednesday someone notices a missing field and decides to add it. They go back to the source sandbox, edit the outbound change set, and re-upload. The inbound change set in production is now a new upload — the previous validation result is no longer linked to it. Quick Deploy is no longer available.

**Why:** A validated inbound change set is a specific snapshot tied to that upload. When you re-upload (even from the same outbound change set), production receives a new artifact. The system has no validated record for this new version.

**How to avoid:** Finalize the change set completely before uploading for validation. Use the review checklist to walk every component before upload. If a missing component is discovered after upload, evaluate whether it can be handled in a separate follow-up change set rather than invalidating the current validated set. When re-upload is unavoidable, schedule a new validation cycle immediately — do not assume the window carries over.

---

## Gotcha 3: "Add Dependencies" Misses Indirect and Runtime Dependencies

**What happens:** A developer uses "Add Dependencies" in the outbound change set UI and gets a clean component list. After uploading, validation fails with a missing component error. The missed component was not a direct schema reference but was referenced at runtime — for example, an Apex class called via an `InvocableMethod` annotation from a Flow, a custom label used inside an Apex class, or a custom metadata type record referenced in Apex logic.

**Why:** The dependency scanner in the change set UI analyzes direct metadata references in XML (field-to-object, layout-to-field, class-to-class inheritance). It does not execute or statically analyze Apex code for dynamic references, custom label lookups, or custom metadata record dependencies.

**How to avoid:** After running "Add Dependencies," manually walk through the logic of every component you are deploying. For Apex classes, check for: `Type.forName()` calls (dynamic class instantiation), custom label references (`Label.My_Label`), custom metadata type queries (`[SELECT ... FROM My_CMT__mdt]`), named credentials used in callouts, and invocable method chains from flows. Add these to the change set explicitly. Keep a change set component checklist as part of the release plan.

---

## Gotcha 4: Flow Deployment Does Not Activate the Flow

**What happens:** A Flow is set to Active in the source sandbox. It is added to the outbound change set. After deployment to production, the Flow exists in production but shows as Inactive. Users trigger the expected process and nothing happens. No error — just silence.

**Why:** Change set deployment preserves the metadata state of the Flow as it existed when the component was captured for the change set. Salesforce does not automatically activate flows as part of deployment. The Flow arrives in the target in whatever active/inactive state the metadata export recorded — and sandbox-to-production promotions often involve flows that were intentionally left inactive for testing.

**How to avoid:** Include Flow activation as an explicit post-deploy step in the release plan. Assign it to a named person with a confirmation step. If you want the Flow to arrive active, ensure it is set to Active in the source org before creating the change set. Note that deploying an Active Flow version to production creates a new version — if an older version was already active in production, Salesforce will deactivate the old version and activate the new one only if the deployment specifies the active version.

---

## Gotcha 5: Code Coverage Is Aggregate, Not Per-Class

**What happens:** A developer deploys a change set containing one new Apex class with 100% test coverage in the sandbox. Production deployment fails with "Average test coverage across all Apex Classes and Triggers is 71%, at least 75% is required."

**Why:** Salesforce enforces the 75% coverage threshold across all Apex in the entire production org, not just the classes in the change set. If production already has legacy Apex classes with poor coverage, adding a well-tested new class does not raise the org average enough to meet the threshold.

**How to avoid:** Before any Apex deploy to production, check the current org-wide coverage using Developer Console > Test > Apex Test Execution > View > Code Coverage. If the aggregate is below 80% (leaving headroom), proactively improve coverage for low-coverage legacy classes in a sandbox, include those test classes in the change set, and restore org coverage before deploying the feature. Never treat 75% as a threshold to aim for — treat it as a floor to stay above.
