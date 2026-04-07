# LLM Anti-Patterns — FSL Mobile App Setup

Common mistakes AI coding assistants make when generating or advising on FSL Mobile App Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating FSL Mobile as the Standard Salesforce Mobile App

**What the LLM generates:** Instructions to configure FSL Mobile behavior through App Manager, Mobile Navigation settings, or Salesforce Mobile App Builder — e.g., "Go to App Manager, find the Salesforce app, and add Work Orders to the navigation items so technicians can access them offline."

**Why it happens:** LLMs conflate FSL Mobile with the standard Salesforce Mobile app because both run on iOS and Android and both access Salesforce data. Training data includes far more documentation about the standard Salesforce Mobile app than the specialized FSL Mobile app.

**Correct pattern:**

```
FSL Mobile configuration lives entirely in:
Setup → Field Service → Field Service Mobile Settings

NOT in:
- App Manager → Salesforce (standard mobile app)
- Mobile Navigation
- Lightning App Builder (mobile form factor)
- Briefcase (standard offline)
```

**Detection hint:** Any instruction that references "App Manager", "Salesforce Mobile App", "Mobile Navigation", or "Briefcase" in the context of configuring what FSL technicians see offline is likely wrong.

---

## Anti-Pattern 2: Suggesting LWC Wire Adapters Inside HTML5 Mobile Extension Toolkit

**What the LLM generates:** Code that imports LWC modules or uses `@wire` decorators inside an HTML5 Mobile Extension Toolkit extension:

```javascript
// WRONG — inside an HTML5 extension
import { LightningElement, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

export default class MyExtension extends LightningElement {
    @wire(getRecord, { recordId: '$recordId', fields: [...] })
    record;
}
```

**Why it happens:** LLMs pattern-match on the mobile context and produce standard LWC patterns because the majority of Salesforce mobile component documentation covers LWC. The HTML5 toolkit is niche and its constraints are underrepresented in training data.

**Correct pattern:**

```javascript
// CORRECT — inside an HTML5 extension, use REST explicitly
const recordId = SfdcApp.AppContext.getRecordId();
fetch(`/services/apexrest/MyResource?recordId=${recordId}`, {
    headers: { 'Authorization': 'Bearer ' + SfdcApp.AppContext.getSessionToken() }
})
.then(r => r.json())
.then(data => { /* render data */ });
```

**Detection hint:** Any `import` statement for LWC modules (`lwc`, `lightning/uiRecordApi`, etc.) inside a file described as an HTML5 Mobile Extension is wrong.

---

## Anti-Pattern 3: Ignoring the 1,000 Page Reference Limit in Priming Advice

**What the LLM generates:** Priming configuration advice that recommends enabling offline sync for all related objects and adding all related lists without mentioning the 1,000 page reference cap:

```
"Enable Data Sync for Work Orders, Work Order Line Items, Products,
Parts, Service Contracts, Entitlements, and all related lists so
technicians have complete access offline."
```

**Why it happens:** The 1,000 page reference limit is a subtle platform constraint not covered in most generic FSL documentation. LLMs default to "enable everything" as a maximalist recommendation without knowing this limit exists.

**Correct pattern:**

```
Before enabling any related list in offline priming:
1. Estimate maximum records per related list per resource per day.
   - Limit: 50 records per related list.
2. Estimate total page references per resource across all enabled objects.
   - Limit: 1,000 page references per resource per priming run.
3. If the estimate approaches 1,000, narrow the priming window or
   remove low-priority related lists.
4. There is no runtime error when the limit is exceeded — records
   are silently dropped.
```

**Detection hint:** Offline priming advice that does not mention page reference counts or the 1,000-reference limit should be flagged for review.

---

## Anti-Pattern 4: Recommending Custom Branding Without Confirming Mobile App Plus License

**What the LLM generates:** Step-by-step branding instructions without any mention of the required add-on:

```
"To customize the FSL Mobile app branding:
1. Go to Setup → Field Service Mobile Settings → Branding.
2. Upload your company logo (PNG, 512x512).
3. Set the primary color hex code.
4. Click Save. Your changes will appear on next app launch."
```

**Why it happens:** The branding UI is always visible in Setup regardless of licensing, so LLMs that describe the UI accurately omit the licensing gate entirely. The licensing requirement is not visible in the configuration surface.

**Correct pattern:**

```
Before beginning any branding configuration:
1. Verify the Mobile App Plus add-on is provisioned:
   Setup → Company Information → Licenses — look for "Mobile App Plus"
2. If the add-on is not present, branding changes will not be applied
   to the app even though Setup accepts the configuration without error.
3. Only proceed with branding work after confirming the license.
```

**Detection hint:** Any branding instructions that do not mention "Mobile App Plus" or license verification should be treated as incomplete.

---

## Anti-Pattern 5: Using the `salesforce://` URI Scheme for FSL Mobile Deep Links

**What the LLM generates:** Deep link instructions that use the standard Salesforce Mobile URI scheme:

```
"To deep link into FSL Mobile, use:
salesforce://RecordDetail?objectType=ServiceAppointment&recordId=0WO..."
```

**Why it happens:** The `salesforce://` scheme is the well-documented URI scheme for the standard Salesforce Mobile app and appears frequently in training data. LLMs generalize this to FSL Mobile without distinguishing the two apps.

**Correct pattern:**

```
FSL Mobile uses its own distinct URI scheme registered through the
Field Service Mobile connected app — NOT the salesforce:// scheme.

The scheme is configured in:
Setup → App Manager → Field Service Mobile (connected app) → Mobile App Settings

Verify the scheme name for your specific connected app configuration.
The salesforce:// scheme opens the standard Salesforce app, not FSL Mobile.
```

**Detection hint:** Any deep link advice for FSL Mobile that uses `salesforce://` as the scheme is pointing to the wrong app.

---

## Anti-Pattern 6: Claiming Offline Data Writes Are Lost If the Device Loses Connectivity

**What the LLM generates:** Warnings that data entered offline in FSL Mobile is not saved or must be re-entered when the device reconnects:

```
"Note: Any records created or updated while offline will be lost
when the device loses connectivity. Ensure technicians sync before
going offline."
```

**Why it happens:** LLMs generalize from web app offline behavior (where unsaved state can be lost) to FSL Mobile. FSL Mobile's offline-first architecture specifically handles this case.

**Correct pattern:**

```
FSL Mobile is built on an offline-first architecture. Records created
or updated while offline are:
1. Queued locally on the device.
2. Durably stored until connectivity is restored.
3. Synced back to the org automatically on reconnection.

Data written offline in FSL Mobile is NOT lost when connectivity drops.
The sync queue persists across app restarts.

Caveats:
- Conflict resolution must be configured if two users edit the same
  record simultaneously (one online, one offline).
- LWC Quick Actions using uiRecordApi/createRecord benefit from LDS
  offline queuing. HTML5 extensions using direct REST calls do NOT —
  those writes fail silently when offline and must implement their
  own queue.
```

**Detection hint:** Any statement claiming offline writes are lost in FSL Mobile is incorrect. Flag advice that tells technicians to "sync before going offline" as if writes won't persist.
