# LLM Anti-Patterns — CTI Adapter Development

Common mistakes AI coding assistants make when generating or advising on CTI adapter development.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Loading the Open CTI Script Manually

**What the LLM generates:**

```html
<script src="https://[instance].salesforce.com/support/api/60.0/lightning/opencti_min.js"></script>
```

**Why it happens:** LLMs trained on generic JavaScript integration patterns assume all external APIs require an explicit `<script>` import. The platform-injected Open CTI namespace is unusual compared to standard JS library patterns.

**Correct pattern:**

```html
<!-- Do NOT add any script tag for opencti.
     The sforce.opencti namespace is injected automatically by Salesforce
     when this page loads inside the Lightning utility panel iframe.
     Adding a manual script tag causes 404 errors or namespace conflicts. -->
```

**Detection hint:** Look for any `<script src` referencing `opencti` in the adapter HTML. Flag immediately.

---

## Anti-Pattern 2: Using CTIVersion 3.0 for Lightning Adapters

**What the LLM generates:**

```xml
<CTIVersion>3.0</CTIVersion>
```

**Why it happens:** Many code examples and older blog posts document CTI for Salesforce Classic, which used version 3.0. LLMs regurgitate these examples without distinguishing Classic from Lightning.

**Correct pattern:**

```xml
<!-- Always use 4.0 for Lightning Experience / Open CTI for Lightning -->
<CTIVersion>4.0</CTIVersion>
```

**Detection hint:** Grep `callcenter.xml` for `<CTIVersion>3.0</CTIVersion>`. Any occurrence in a Lightning context is wrong.

---

## Anti-Pattern 3: Calling onClickToDial Before enableClickToDial Succeeds

**What the LLM generates:**

```javascript
window.addEventListener('DOMContentLoaded', () => {
  sforce.opencti.enableClickToDial({ callback: () => {} });
  sforce.opencti.onClickToDial({ listener: myHandler }); // wrong: parallel, not sequential
});
```

**Why it happens:** LLMs treat API initialization calls as fire-and-forget setup steps and list them sequentially in code without nesting. They do not model the asynchronous callback contract.

**Correct pattern:**

```javascript
sforce.opencti.enableClickToDial({
  callback: (res) => {
    if (res.success) {
      // Only register the listener AFTER enableClickToDial succeeds.
      sforce.opencti.onClickToDial({ listener: myHandler });
    }
  }
});
```

**Detection hint:** Look for `onClickToDial` called outside of an `enableClickToDial` success callback. If they appear as sibling statements, it is likely wrong.

---

## Anti-Pattern 4: Omitting response.success Checks in saveLog

**What the LLM generates:**

```javascript
sforce.opencti.saveLog({
  value: { Subject: 'Call', Status: 'Completed' },
  callback: (response) => {
    console.log('Log saved');  // wrong: assumes success without checking
  }
});
```

**Why it happens:** LLMs follow the pattern of "call function, log success message" common in tutorial code. The asynchronous `response` object pattern with a `success` boolean is less common in training data than try/catch.

**Correct pattern:**

```javascript
sforce.opencti.saveLog({
  value: { Subject: 'Call', Status: 'Completed', CallType: 'Outbound',
           CallDurationInSeconds: duration, WhoId: contactId },
  callback: (response) => {
    if (!response.success) {
      console.error('saveLog failed:', response.errors);
      showErrorToAgent('Call log failed. Please log manually.');
    }
  }
});
```

**Detection hint:** Any `saveLog` callback that does not reference `response.success` or `response.errors` is incomplete.

---

## Anti-Pattern 5: Recommending Service Cloud Voice Setup Instead of Open CTI

**What the LLM generates:** Instructions to set up an Amazon Connect Contact Flow, Lambda functions, a Service Cloud Voice channel, and CTI Adapter from the AppExchange — when the user asked how to build a custom Open CTI adapter for a non-Amazon telephony system.

**Why it happens:** "CTI" and "Amazon Connect" appear together frequently in Salesforce documentation and blog content. LLMs conflate the two paths. Service Cloud Voice is heavily documented and prominent, while Open CTI for custom adapters is a more specialized developer topic.

**Correct pattern:** When the telephony provider is not Amazon Connect, use Open CTI with a custom adapter hosted page and `callcenter.xml`. Service Cloud Voice is the path for Amazon Connect and provides native transcription and AI coaching. Open CTI is the path for all other telephony vendors. Do not mix the two.

**Detection hint:** If the generated response mentions Amazon Connect, Lambda, or AppExchange CTI adapter installation in a context where the user specified a non-Amazon telephony vendor, it has crossed the streams.

---

## Anti-Pattern 6: Hardcoding Telephony Credentials in the Adapter JavaScript

**What the LLM generates:**

```javascript
const SIP_PASSWORD = 'mySecretPassword123';
const TENANT_ID = 'tenant-abc-prod';
const SOCKET_URL = 'wss://sip.vendor.com:5061';

function connect() {
  vendorSDK.init({ password: SIP_PASSWORD, tenant: TENANT_ID, url: SOCKET_URL });
}
```

**Why it happens:** LLMs generate minimal working examples and do not model deployment environments or secret management. Hardcoded values are the shortest path to a working snippet.

**Correct pattern:**

```javascript
// Retrieve configuration from callcenter.xml CustomSettings at runtime.
sforce.opencti.getCallCenterSettings({
  callback: (res) => {
    if (res.success) {
      const settings = res.returnValue;
      vendorSDK.init({
        url:    settings['reqSalesforceCompatibilityLevel__TelephonyServerUrl'],
        tenant: settings['reqSalesforceCompatibilityLevel__TenantId']
        // Passwords should come from a secure server-side token exchange,
        // not from callcenter.xml CustomSettings (which are visible to org admins).
      });
    }
  }
});
```

**Detection hint:** Any adapter JS with string literals that look like passwords, API keys, tenant IDs, or hardcoded WebSocket URLs should be flagged for externalization.
