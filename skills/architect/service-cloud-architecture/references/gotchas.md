# Gotchas — Service Cloud Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Omni-Channel Presence Status Resets on Browser Refresh

**What happens:** When an agent refreshes their browser or navigates away from the Service Console and returns, their Omni-Channel presence status resets to the default status configured in their Presence Configuration — not the status they were in before the refresh. If the default is "Offline," the agent drops out of the routing pool silently. If the default is "Available," an agent who was on break suddenly receives new work items.

**When it occurs:** Any time an agent refreshes the browser tab, closes and reopens the Console, or experiences a network interruption that causes a page reload. Happens frequently in environments with VPN instability or thin client setups.

**How to avoid:** Set the default presence status in the Presence Configuration to the most common working status (usually "Available"). Train agents to check their Omni-Channel widget after any page reload. Monitor the "Agent Presence" event in Event Monitoring to detect unexpected status transitions. Consider building a Flow-triggered notification when an agent's presence changes unexpectedly.

---

## Gotcha 2: Email-to-Case Has a 25 MB Attachment Limit That Silently Truncates

**What happens:** Email-to-Case (both On-Demand and traditional) has a 25 MB limit per email. If an inbound email exceeds this limit, the case is still created but the attachment is silently dropped. The agent sees the case with the email body but no attachment. The customer believes they sent the attachment successfully.

**When it occurs:** Common in industries where customers send large files — engineering drawings, medical images, legal documents, financial spreadsheets with embedded images.

**How to avoid:** Configure the Email-to-Case error handling address to receive notifications about oversized emails. Set up an auto-response rule that warns customers when their email exceeds size limits and directs them to a portal upload. For organizations that regularly receive large files, implement a file upload portal using Experience Cloud with Files Connect or an external storage integration.

---

## Gotcha 3: Skills-Based Routing Timeout Does Not Cascade — It Re-Routes from Scratch

**What happens:** When a skills-based routing configuration times out and the work item is re-routed with relaxed skill requirements, the item goes back to the beginning of the routing queue for the new configuration. It does not maintain its original queue position or priority. A case that waited 3 minutes for a specialist and then timed out to the general pool starts at the back of the general pool line.

**When it occurs:** High-volume periods when both the specialized and general pools are busy. The re-routed item arrives behind items that were originally routed to the general pool, even though it has been waiting longer overall.

**How to avoid:** Account for this in capacity planning — the timeout should be short enough that the general pool is not already saturated when overflow items arrive. Consider using Omni-Channel Flow to manually set priority on re-routed items so they receive a priority boost when re-entering the routing queue. Test timeout behavior extensively during peak volume simulation.

---

## Gotcha 4: Service Cloud Voice (Amazon Connect) Has Separate Capacity From Omni-Channel

**What happens:** Service Cloud Voice integrates Amazon Connect for telephony. While voice calls do appear as work items in Omni-Channel, the Amazon Connect Contact Control Panel (CCP) manages its own agent state independently. An agent can be "Available" in Omni-Channel but "Offline" in the CCP (or vice versa), creating a split-brain scenario where voice calls route differently than expected.

**When it occurs:** When agents forget to sign into the CCP embedded in the Service Console, when the CCP session expires (default 10-hour session), or when network issues disconnect the CCP WebSocket while the Omni-Channel connection remains active.

**How to avoid:** Configure the Omni-Channel presence sync with Amazon Connect so that CCP state changes propagate to Omni-Channel status automatically. Train agents to use a single sign-in workflow that opens both Omni-Channel and CCP. Monitor for agents who are "Available" in Omni-Channel but not receiving voice calls — this almost always indicates a CCP session issue.

---

## Gotcha 5: Knowledge Data Category Visibility and Sharing Are Separate Systems

**What happens:** Knowledge article visibility is controlled by Data Category Visibility settings on roles and permission sets, which is a completely separate system from standard Salesforce sharing (OWD, sharing rules, role hierarchy). Granting a user "Read" access to the Knowledge object via profile does not mean they can see articles in categories they lack Data Category Visibility for. Conversely, giving a user Data Category Visibility does not grant them object-level access to Knowledge.

**When it occurs:** When architects design the Knowledge security model using only standard sharing concepts and forget to configure Data Category Visibility. Results in agents who can "see" the Knowledge tab but find zero articles, or Experience Cloud users who see all articles including internal-only content.

**How to avoid:** Design both layers explicitly: (1) object-level access to Knowledge via profiles/permission sets, and (2) Data Category Visibility settings on roles or permission sets for each audience (internal agents, partners, customers). Test each audience persona end-to-end in a sandbox before go-live. Document both layers in the security model section of the architecture document.

---

## Gotcha 6: Entitlement Milestone Clock Pauses Only on Specific Case Statuses

**What happens:** Milestone timers in entitlement processes only pause when the case enters a status that is explicitly configured as a "Stopped" status in the milestone criteria. If you add a new case status (e.g., "Waiting on Customer") but forget to add it to the milestone's stop criteria, the SLA clock keeps running while the agent is waiting for the customer to respond. This silently inflates SLA violation rates.

**When it occurs:** During iterative case lifecycle changes — someone adds a new picklist value to Case Status but does not update the entitlement milestone stop criteria. Common in orgs where the admin managing case statuses is different from the admin who configured entitlements.

**How to avoid:** Document every case status and whether it should pause the SLA clock. Create a validation checklist: every time a case status is added or renamed, the entitlement milestone configurations must be reviewed. Consider a checker script that compares active case statuses against milestone stop criteria to detect mismatches.
