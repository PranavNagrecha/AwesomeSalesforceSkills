# Examples — Flow For Experience Cloud

## Example 1: Authenticated Partner Case Update Flow

**Context:** A partner portal needs a guided case update experience for authenticated external users.

**Problem:** The team considers exposing an internal service flow directly, even though it assumes broad internal record visibility and admin-only Apex actions.

**Solution:**

```html
<lightning-flow
    flow-api-name="Partner_Case_Update"
    flow-input-variables={inputVariables}
    onstatuschange={handleStatusChange}>
</lightning-flow>
```

**Why it works:** The flow is exposed only to authenticated users, and the wrapper component can handle finish behavior while the data model stays aligned to partner-user access.

---

## Example 2: Guest Intake Flow With Minimal Surface Area

**Context:** A public site needs a support-request form for anonymous visitors.

**Problem:** The original flow tries to search existing contacts and cases before creating the request, which increases guest-user risk and complexity.

**Solution:**

```text
Screen 1: collect contact and issue details
Create Records: Support_Request__c only
Confirmation screen: request submitted and next steps
```

**Why it works:** The guest flow avoids broad lookups and behaves like a narrow public intake endpoint instead of a public data browser.

---

## Anti-Pattern: Reusing An Internal Screen Flow On A Public Site

**What practitioners do:** They take a flow built for employees and place it on an Experience Cloud page without redesigning it for guest or external users.

**What goes wrong:** The flow depends on internal sharing, broad object access, or custom Apex actions that are unsafe or unavailable in the site context.

**Correct approach:** Design a site-specific flow contract and security review for the actual audience, even if the business process overlaps.
