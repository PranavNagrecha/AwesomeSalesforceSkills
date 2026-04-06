# Gotchas — Multi Channel Service Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Messaging Sessions Are Not the Same Object as Live Chat Transcripts

**What happens:** After migrating from Live Agent to Messaging for In-App/Web, existing reports, dashboards, Flows, and Process Builders that reference `LiveChatTranscript` return empty results or error. Routing rules targeting the old Service Channel stop working. Historical Live Agent data remains on `LiveChatTranscript` but new conversations land on `MessagingSession`.

**When it occurs:** Any org migrating from Live Agent to Messaging for In-App/Web. The objects are not related and there is no automatic migration of automation references.

**How to avoid:** Before migration, audit every automation, report, and Lightning component that references `LiveChatTranscript`, `LiveChatButton`, or `LiveAgentSession`. Create a mapping document. Rebuild each reference against `MessagingSession`, `MessagingEndUser`, and `MessagingChannel` objects. Run both systems in parallel long enough to validate all downstream dependencies.

---

## Gotcha 2: Email-to-Case On-Demand Silently Drops Oversized Emails

**What happens:** Emails exceeding 25 MB (including attachments) that are sent to the Email-to-Case on-demand address are silently discarded. No Case is created. No bounce notification is sent to the customer. The email simply vanishes.

**When it occurs:** Customers attach large files — CAD drawings, high-resolution photos, video files. Common in manufacturing, construction, and design industries.

**How to avoid:** Set customer-facing email instructions to warn about attachment limits. Configure a monitoring Flow or scheduled job to compare inbound email volume (from email server logs) against created Case volume to detect gaps. Consider providing an alternative file-upload mechanism (Experience Cloud portal with file upload component) for large attachments and referencing it in auto-reply rules.

---

## Gotcha 3: Omni-Channel Presence Statuses Apply Globally, Not Per Channel

**What happens:** An agent sets their status to "Available" expecting to receive only chats, but also receives phone calls and email cases. There is no built-in way to be "Available for Chat" and "Unavailable for Phone" using a single presence status without explicit configuration.

**When it occurs:** Orgs that assume Omni-Channel presence works per-channel by default. It does not. A Presence Status is mapped to one or more Service Channels, and the agent gets work from all mapped channels when using that status.

**How to avoid:** Create multiple Presence Statuses mapped to specific Service Channel combinations: "Available - All Channels," "Available - Chat Only," "Available - Phone Only." Train agents on which status to select. Note that this requires agents to actively manage their status, which adds operational complexity.

---

## Gotcha 4: Service Cloud Voice Requires Separate Amazon Connect Instance Per Salesforce Org

**What happens:** Organizations with multiple Salesforce orgs (e.g., production + full-copy sandbox used for training) attempt to share a single Amazon Connect instance. Call routing breaks or calls are delivered to the wrong org. Amazon Connect contact flows cannot distinguish which Salesforce org should receive the call.

**When it occurs:** Multi-org environments, particularly during UAT or training when a sandbox needs live phone testing.

**How to avoid:** Provision a separate Amazon Connect instance for each Salesforce org that needs Voice functionality. Use Amazon Connect's test features for non-production testing when possible. Budget for additional Amazon Connect instances in the licensing estimate.

---

## Gotcha 5: Capacity Weight of Zero Means Unlimited Work Items

**What happens:** Setting a Service Channel's capacity weight to 0 does not block that channel — it means the channel consumes no capacity, so Omni-Channel will push an unlimited number of those work items to an agent. Agents get buried in dozens of simultaneous email cases or chat sessions.

**When it occurs:** Admins set weight to 0 thinking it will "disable" the channel or make it "free." This is a common misconfiguration during initial multi-channel setup.

**How to avoid:** Always assign a positive capacity weight to every active Service Channel. If you want a channel to be very low priority, use a small weight (e.g., 5) rather than zero. If you want to disable a channel for certain agents, remove that Service Channel from their Presence Status rather than setting weight to 0.
