# Gotchas — FSL Mobile App Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Offline Action Disappears — App Builder Placement Is Not Enough

**What happens:** A LWC Quick Action that is added to a Lightning App Builder page for the ServiceAppointment or WorkOrder record page renders correctly when the technician is online. When the device goes offline, the action button is simply absent — no error, no placeholder.

**When it occurs:** Any time the Quick Action is configured only via App Builder (the "Actions in the Salesforce Mobile App and Lightning Experience" override) and not added to the object's main page layout in Setup.

**How to avoid:** After deploying the Quick Action, open Setup > Object Manager > [Target Object] > Page Layouts > [Relevant Layout]. In the "Salesforce Mobile and Lightning Experience Actions" section, add the Quick Action there. This is the step that registers the action for offline availability. The App Builder placement controls what online users see in the dynamic layout; the page layout placement controls what offline users see.

---

## Gotcha 2: "Enable Lightning SDK for FSL Mobile" Permission Set Not Included in FSL License

**What happens:** A user with a full Field Service Mobile license logs into the FSL native app, navigates to a record, and does not see the custom LWC action. Alternatively, they see the action button but tapping it produces a permissions error or blank screen.

**When it occurs:** The "Enable Lightning SDK for FSL Mobile" permission set must be explicitly assigned. It is not automatically included with the Field Service Mobile, Field Service Resource, or Field Service Standard permission sets. This affects all users, including admins and developers testing in production.

**How to avoid:** Create an assignment rule or use a permission set group that includes "Enable Lightning SDK for FSL Mobile" alongside the standard FSL permission sets. Add it to the user provisioning checklist. During development, verify the permission set assignment before troubleshooting component behavior.

---

## Gotcha 3: Briefcase Builder Silently Drops Records Past 1,000 Page References

**What happens:** Technicians prime (sync) their devices but some appointments, work orders, or related records are missing when they go offline. No error is displayed in the app. The Briefcase Builder configuration appears correct. The sync completes without any failure message.

**When it occurs:** The total number of page references in a single priming run exceeds 1,000. This limit applies across all objects in the priming hierarchy for a given technician's session. High-volume territories (technicians with many appointments per sync window) hit this limit silently.

**How to avoid:** Add filter criteria to the Briefcase Builder rules — typically filtering by appointment date range (e.g., next 7 days), territory, and status (Scheduled, Dispatched). Monitor the approximate record counts per technician during testing. A good target is staying below 750 page references to leave a safe buffer.

---

## Gotcha 4: Custom Metadata Types Are Not Primed by Briefcase Builder

**What happens:** An LWC extension wired to an Apex method that queries a Custom Metadata Type works perfectly online. Offline, the wire call returns an error and the component renders without its configuration data (empty picklists, missing thresholds, no routing logic).

**When it occurs:** Briefcase Builder does not support Custom Metadata Types as a priming target. This is a platform-level constraint, not a configuration issue. It affects any extension that relies on CMT records for behavioral configuration.

**How to avoid:** Use the Apex wire + Custom Object cache pattern: on online load, fetch CMT data and write it to a Custom Object record linked to the ServiceResource (which is primed via Briefcase Builder). On offline load, read from the Custom Object via standard `getRecord`. For configuration that never changes between releases, consider embedding values directly in the LWC component as constants.

---

## Gotcha 5: `lightning__GlobalAction` LWC Does Not Render in Lightning Experience

**What happens:** A developer builds an LWC component targeted at `lightning__GlobalAction` for use in FSL Mobile, then tries to test it by opening a record in the browser's Lightning Experience. The action does not appear in the global actions menu or anywhere on the record page.

**When it occurs:** The `lightning__GlobalAction` target renders only inside the FSL native mobile app. It is intentionally excluded from standard Lightning Experience and standard Salesforce Mobile. There is no error — the action is simply not surfaced outside FSL Mobile.

**How to avoid:** Test LWC Global Actions exclusively in the FSL native app on a real device or an FSL-configured simulator. For developer testing, use a device with the FSL app installed and a sandbox org. If you also need the action in Lightning Experience, create a separate Quick Action with a `lightning__RecordAction` target alongside the FSL-targeted one.

---

## Gotcha 6: Deep Link Payload Truncation Has No Runtime Error

**What happens:** A deep link URI is constructed with enough record context and parameters to exceed 1 MB. When the technician taps the link, navigation fails silently or lands on the wrong record. No error toast is displayed. In some cases the app navigates to the root view instead of the intended record.

**When it occurs:** When the deep link payload encodes full record field values, long text fields, or a large number of parameters. The 1 MB limit applies to the encoded URI, not the raw data.

**How to avoid:** Pass record IDs rather than field values in deep link parameters. Retrieve field data after navigation using the standard record page context. Before finalizing any deep link implementation, calculate the encoded string length in bytes and confirm it is well under 1 MB (target < 900 KB to leave headroom).
