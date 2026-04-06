# Gotchas — Messaging and Chat Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CORS and CSP Are Both Required — Missing Either Silently Breaks the Widget

**What happens:** The chat widget fails to load or the chat button never appears on the page. Customers see no error; the button is simply absent. Agents see no incoming sessions.

**When it occurs:** Any time the widget is embedded on a domain that is not registered in both CORS Trusted Sites (Setup > CORS) and CSP Trusted Sites (Setup > CSP Trusted Sites). This affects every non-production domain (staging, QA, UAT) that was not explicitly registered. It also occurs when the page moves to HTTPS and the old Trusted Site entry used HTTP.

**How to avoid:** Treat CORS and CSP as a pair. Every time you register a new widget domain, add both entries in the same session. Include the exact scheme (`https://`) and hostname. For organizations that use wildcard subdomains on the same apex domain, CSP accepts wildcards (`https://*.example.com`) but CORS requires individual entries per subdomain.

---

## Gotcha 2: Legacy Live Agent Deployments Cannot Be Converted to MIAW

**What happens:** An admin attempts to reuse an existing Embedded Service Deployment that was created with channel type "Chat" (Live Agent). Sessions route to `LiveChatTranscript` records. The Omni-Channel widget shows chat sessions, not messaging sessions. Einstein bot handoff, asynchronous session resumption, and Omni-Channel Flow routing are unavailable.

**When it occurs:** Orgs migrating from Live Agent to MIAW, or orgs where an admin creates the Embedded Service Deployment before selecting the correct channel type and saves with the wrong type. The channel type field becomes read-only after initial save.

**How to avoid:** Always create a new Embedded Service Deployment with type "Messaging for In-App and Web" for MIAW implementations. Run the old and new deployments in parallel during migration. Decommission the Live Agent deployment only after all agents are on the MIAW channel and all custom reports referencing `LiveChatTranscript` have been updated to `MessagingSession`.

---

## Gotcha 3: Pre-Chat Fields Do Not Auto-Link a Contact Record

**What happens:** The Messaging Channel pre-chat form collects First Name, Last Name, and Email from the customer. After the session is created, the `MessagingSession` record has no `ContactId` populated and no linked Contact. Agents cannot see the customer's history.

**When it occurs:** Any time pre-chat fields are configured on the Messaging Channel but no additional automation exists to perform the Contact lookup. The platform stores pre-chat data in the session's pre-chat fields, but does not automatically search for and link a matching Contact by email.

**How to avoid:** Create an Omni-Channel Flow or an Apex trigger on `MessagingSession` (after insert) that queries Contact by the pre-chat email value and updates the `ContactId` field on the session. Document this as a required post-configuration automation step — it is easy to miss because the widget and routing work correctly without it.

---

## Gotcha 4: Status-Based Capacity Is an Org-Wide Toggle — Not Per-Channel

**What happens:** An org enables Status-Based capacity to support MIAW sessions. Agents who were previously handling Live Agent chat with Tab-Based capacity assumptions now find their capacity limits enforced differently. Agents who had five tabs open to manage five chats now hit a numeric capacity limit and cannot accept new sessions even though their tabs are open.

**When it occurs:** When an org switches from Tab-Based to Status-Based in Omni-Channel Settings without reviewing all existing Presence Configurations. Tab-Based capacity counts open interaction tabs; Status-Based counts active work items. An agent with a capacity of 3 under Status-Based can only have 3 open sessions regardless of how many tabs are open.

**How to avoid:** Before enabling Status-Based capacity, audit all Presence Configurations. Set numeric capacity values that reflect the intended concurrent workload for each channel type (voice, messaging, email). Brief agents and supervisors on the change. Test in a full-featured sandbox with realistic concurrent load before enabling in production.

---

## Gotcha 5: Missing Fallback Queue Causes Sessions to Hang Without Error

**What happens:** A new Messaging Session is created but never routed to an agent. The customer sees "Please wait…" indefinitely. No error appears in the Omni-Channel supervisor view. The session exists in `MessagingSession` with status "Waiting" but no queue assignment.

**When it occurs:** When an Omni-Channel Flow is configured on the Messaging Channel but the Flow throws a fault, is paused in an unsupported path, or encounters an unhandled condition — and no fallback queue is configured on the Messaging Channel record. Without a fallback queue, a failed routing attempt leaves the session stranded.

**How to avoid:** Always configure a fallback queue on every Messaging Channel record, even when Flow-based routing is the primary path. Monitor the Omni-Channel supervisor's Queued Work view and set up a dashboard alert for sessions that have been waiting more than a defined threshold (e.g., 10 minutes) to catch stalled sessions early.
