# Gotchas — Experience Cloud Security

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: External OWD Is Silently Capped at Internal OWD

**What happens:** When you attempt to set external OWD to a value more permissive than the internal OWD, Salesforce silently overrides it to match the internal OWD. No error is displayed. The Setup UI may appear to show the value you set, but the effective runtime value is capped.

**When it occurs:** A developer sets Case internal OWD to Private for internal data protection, then sets external OWD to Public Read Only expecting portal users to see all cases — but portal users still see no cases because the effective external OWD is Private.

**How to avoid:** Always configure internal OWD first, then set external OWD within the allowed range (equal to or more restrictive than internal OWD). Use Sharing Sets for relationship-based access instead of trying to make external OWD more permissive.

---

## Gotcha 2: Changing External OWD Triggers a Background Sharing Recalculation

**What happens:** Any change to external OWD for an object triggers a background sharing recalculation job. During recalculation, portal users may see stale sharing results — either more or fewer records than they should. The recalculation job can take minutes to hours in large orgs with many records.

**When it occurs:** External OWD changes made in production during business hours while portal users are active.

**How to avoid:** Make external OWD changes during a maintenance window or low-traffic period. Monitor the sharing recalculation job in Setup > Apex Jobs. Inform portal users of potential access inconsistencies during the recalculation window.

---

## Gotcha 3: Sharing Sets Do Not Support All Standard Objects

**What happens:** Not all Salesforce standard objects support Sharing Sets. The available object list in the Sharing Set configuration UI shows only objects that have a supported lookup relationship to Account or Contact. Attempting to use a Sharing Set for an unsupported object (e.g., custom objects with no Account/Contact lookup) is not possible through the UI and provides no error — the object simply does not appear in the dropdown.

**When it occurs:** A developer tries to configure a Sharing Set for a custom object or standard object without an Account/Contact lookup relationship.

**How to avoid:** For objects not supported by Sharing Sets, use Apex sharing (`insert new ObjectName__Share(...)`) triggered by a Flow or trigger, or use guest sharing rules if appropriate. Verify object eligibility in the Sharing Set configuration UI before planning the data access model.

---

## Gotcha 4: Guest User Apex Without Sharing Overrides External OWD

**What happens:** When a guest user calls an Apex method marked `without sharing`, the method runs in the system user context and bypasses external OWD, sharing rules, and the guest profile's object permissions. Records are fully accessible to the method even if the guest profile has no object permissions.

**When it occurs:** Site guest users invoke global Apex classes (via REST, a Visualforce page, or a screen flow) that use `without sharing` — often inherited from code that was never designed for guest users.

**How to avoid:** Audit all Apex classes accessible to the guest profile. Confirm whether each uses `with sharing`, `without sharing`, or `inherited sharing`. Any class that accesses data on behalf of a guest user should use `with sharing` or enforce explicit FLS and CRUD checks. Never mark a class `global without sharing` if it is accessible to external or guest users.
