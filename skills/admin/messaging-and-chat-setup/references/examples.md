# Examples — Messaging and Chat Setup

## Example 1: Greenfield MIAW Deployment for a B2C Support Site

**Context:** A retail company is launching Service Cloud for the first time. They want a chat button on their support portal at `https://support.example.com`. Agents work in a single English-language queue with a capacity of four concurrent sessions each.

**Problem:** Without this skill's guidance, an admin might navigate to the legacy "Chat" setup area, configure a Live Agent Chat Button and deployment, embed the Snap-ins snippet, and deploy. The result looks functional in the sandbox but routes sessions to `LiveChatTranscript` records, not `MessagingSession` records. MIAW-native features (asynchronous session resumption, Einstein bot handoff, Omni-Channel Flow routing) are unavailable. The deployment type cannot be changed after creation.

**Solution:**

Step 1 — Enable Messaging for In-App and Web in Setup > Messaging Settings.

Step 2 — Create the Messaging Channel:
```
Setup > Messaging > Messaging Channels > New
  Channel Type:         Messaging for In-App and Web
  Name:                 Support Portal Chat
  Routing:              Queue — Support Tier 1
  Fallback Queue:       Support Fallback
  Off-Hours Message:    "We are currently offline. Our hours are Mon–Fri 9am–6pm PT."
```

Step 3 — Add pre-chat fields on the Messaging Channel record:
```
Pre-Chat Fields:
  - Label: First Name    Field: Contact.FirstName    Required: true
  - Label: Last Name     Field: Contact.LastName     Required: true
  - Label: Subject       Field: Case.Subject         Required: true
```

Step 4 — Create the Embedded Service Deployment:
```
Setup > Embedded Service Deployments > New
  Type:                 Messaging for In-App and Web
  Name:                 Support Portal Deployment
  Messaging Channel:    Support Portal Chat
```

Step 5 — Register domain in CORS and CSP:
```
CORS Trusted Site:     https://support.example.com
CSP Trusted Site:      https://support.example.com  (Context: All)
```

Step 6 — Copy the snippet from the deployment record and add to `<head>` of the portal pages.

**Why it works:** Using the MIAW channel type throughout ensures sessions land on `MessagingSession` records, agents see sessions in the Omni-Channel widget with correct capacity counting, and the asynchronous session model is available if agents need it.

---

## Example 2: Flow-Based Routing with Language Detection

**Context:** A software company supports English and Spanish customers from two separate Omni-Channel queues. A pre-chat field asks the customer to select their preferred language. Outside business hours, customers should receive an auto-response and the session should end rather than queue indefinitely.

**Problem:** A single queue on the Messaging Channel cannot branch on pre-chat field values. Without a routing Flow, all sessions go to the same queue regardless of language selection, requiring agents to manually transfer sessions.

**Solution:**

Step 1 — Create two Omni-Channel Queues: `Support EN` and `Support ES`.

Step 2 — Create an Omni-Channel Flow (Flow type: Omni-Channel):
```
Flow name: Route Chat by Language and Hours

Elements:
  1. Get Records — Query BusinessHours where IsDefault = true
  2. Decision — IsWithinBusinessHours?
       Yes branch → Decision: LanguageField == 'ES'?
                      Yes → Route To Queue: Support ES
                      No  → Route To Queue: Support EN
       No branch  → Send Message: "We are closed. Contact us during business hours."
                 → End Session
```

Step 3 — On the Messaging Channel, set "Route With" to the Omni-Channel Flow. Set Fallback Queue to `Support Fallback`.

Step 4 — Test with language = "ES" during business hours: session should route to Support ES queue. Test outside hours: session should receive auto-response and close.

**Why it works:** Omni-Channel Flows have native access to session context (including pre-chat field values) and business hours records, making conditional routing reliable without custom Apex. The fallback queue ensures no session is permanently lost if the flow fails.

---

## Anti-Pattern: Using CORS Without CSP (or Vice Versa)

**What practitioners do:** An admin adds a CORS Trusted Site for the widget domain because the browser console shows a CORS error. The chat button still does not appear. The admin assumes CORS is not the issue and starts modifying the deployment snippet.

**What goes wrong:** The widget requires both CORS (to allow the API handshake) and CSP (to allow the script itself to execute). Adding only CORS fixes the API call but the widget script is still blocked by the CSP policy. The browser console shows a separate CSP violation that is easy to miss if the admin stops looking after the CORS error disappears.

**Correct approach:** Always add both a CORS Trusted Site entry and a CSP Trusted Site entry (with context "All") for every domain where the widget is embedded. Treat them as a pair — if you add one, immediately add the other.
