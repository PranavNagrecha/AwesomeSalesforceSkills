# LLM Anti-Patterns — Flow for Experience Cloud

Common mistakes AI coding assistants make when generating or advising on exposing Flows in Experience Cloud sites.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming guest users can access any object a flow references

**What the LLM generates:**

```
"Embed the screen flow on the public page. The flow will handle
creating the Lead record when the guest user submits the form."
```

**Why it happens:** LLMs design flows without considering that guest users have extremely limited object access. The flow runs in the guest user's context and fails silently if CRUD/FLS is missing.

**Correct pattern:**

1. Check the Guest User profile's object and field permissions
2. Grant only the minimum CRUD/FLS needed for the flow's operations
3. Use "Run flow in system context without sharing" only when absolutely necessary and after security review
4. Test the flow as an unauthenticated user, not as an admin

**Detection hint:** Flow design for guest users without mentioning Guest User profile permissions or system context considerations.

---

## Anti-Pattern 2: Using ShowToastEvent in flows embedded in Experience Cloud

**What the LLM generates:**

```
"Add an Apex action that dispatches a ShowToastEvent after the flow completes."
```

**Why it happens:** LLMs apply Lightning Experience patterns to Experience Cloud. `ShowToastEvent` does not work in LWR-based Experience Cloud sites — the toast container does not exist.

**Correct pattern:**

Use a Screen element at the end of the flow to display a confirmation message:

```
[Screen: "Thank you! Your request has been submitted."]
```

Or use a custom LWC screen component that handles notifications in a site-compatible way.

**Detection hint:** `ShowToastEvent` or toast-related advice in a flow described as running in Experience Cloud or a community page.

---

## Anti-Pattern 3: Not specifying the flow's running user context for security

**What the LLM generates:**

```
"Just drag the flow component onto the Experience Builder page."
```

**Why it happens:** LLMs focus on the embedding step and skip the critical security configuration. By default, screen flows in Experience Cloud run in the context of the site user, which may be a guest or external user with limited access.

**Correct pattern:**

Explicitly choose the running context:
- **User or system context**: Set in Flow > Advanced > "Run flow as" configuration
- For guest-facing flows that create records: consider "System Context Without Sharing" with tight entry validation
- For authenticated external users: verify their profile/permission set grants adequate access
- Always review what data the flow can read, create, update, or delete in that context

**Detection hint:** Flow embedding instructions for Experience Cloud without discussing running user context or sharing settings.

---

## Anti-Pattern 4: Embedding a flow with custom Aura components in an LWR site

**What the LLM generates:**

```
"Add the flow to your LWR Experience Cloud site. It uses a custom
Aura screen component for the file upload step."
```

**Why it happens:** LLMs do not distinguish between Aura-based and LWR-based Experience Cloud sites. LWR sites do not support Aura components — flows with Aura screen components will fail.

**Correct pattern:**

For LWR sites:
- Use only LWC-based custom screen components
- Replace any Aura screen components with LWC equivalents
- Test the flow in the actual LWR site preview, not just Flow Builder debug

For Aura-based sites:
- Both Aura and LWC screen components work

**Detection hint:** Flow design for an LWR site that references Aura components, `lightning:flow`, or Aura-only features.

---

## Anti-Pattern 5: Not handling the flow finish event for post-completion navigation

**What the LLM generates:**

```html
<lightning-flow flow-api-name="My_Screen_Flow"></lightning-flow>
<!-- No onstatuschange handler — user sees a blank screen after completion -->
```

**Why it happens:** LLMs embed the flow component without handling what happens after the flow finishes. Without an `onstatuschange` handler, the user is left on a blank or stale screen.

**Correct pattern:**

```html
<lightning-flow
    flow-api-name="My_Screen_Flow"
    onstatuschange={handleFlowStatus}>
</lightning-flow>
```

```javascript
handleFlowStatus(event) {
    if (event.detail.status === 'FINISHED' || event.detail.status === 'FINISHED_SCREEN') {
        // Navigate to confirmation page or refresh
        this[NavigationMixin.Navigate]({
            type: 'comm__namedPage',
            attributes: { name: 'Confirmation__c' }
        });
    }
}
```

**Detection hint:** `<lightning-flow>` tag without an `onstatuschange` handler in an Experience Cloud component.

---

## Anti-Pattern 6: Passing sensitive record IDs through URL parameters to a flow

**What the LLM generates:**

```
"Pass the record ID to the flow via the URL: /my-page?recordId=001xx000003ABCD"
```

**Why it happens:** URL parameters are the simplest way to pass data. But in Experience Cloud, external and guest users can manipulate URL parameters to access records they should not see.

**Correct pattern:**

- Validate the record ID inside the flow before processing
- Use a Decision element to check that the running user has access to the record
- For authenticated users, rely on sharing rules rather than URL-passed IDs
- For guest users, never pass record IDs in URLs — use a lookup or search within the flow instead

**Detection hint:** Flow design that accepts a record ID from a URL parameter without validating the user's access to that record.
