# Examples — Flow for Slack

## Example 1: Opportunity Stage Change Slack Notification

**Context:** A sales operations team wants to notify a dedicated "#deal-alerts" Slack channel whenever an Enterprise Opportunity moves to "Negotiation" stage.

**Problem:** A developer built a record-triggered Flow with a Slack notification action, but it failed in the before-save (synchronous) execution path because Slack actions are callouts and cannot run synchronously.

**Solution:**

1. Create a Record-Triggered Flow on Opportunity object.
2. Set execution to **After the record is saved** and run in **Asynchronous path**.
3. Add condition: `StageName = 'Negotiation'` AND record is new or stage has changed.
4. Add Action element: **Send Slack Message**.
5. Configure:
   - Channel: `C0123456789` (Slack channel ID for #deal-alerts)
   - Message: `New Negotiation Opportunity: {!$Record.Name} — ${!$Record.Amount} — Owner: {!$Record.Owner.Name}`
6. Save and activate.

**Why it works:** After-save asynchronous execution allows callout-based actions like Slack. Channel ID is used rather than display name for reliability (display names can change; IDs are stable).

---

## Example 2: Auto-Create Deal Room Slack Channel for New Enterprise Opportunities

**Context:** The sales team wants a dedicated Slack channel automatically created for each new Enterprise Opportunity to consolidate deal-related communications.

**Problem:** Channels were being manually created with inconsistent naming conventions. The team forgot to add key stakeholders to some channels.

**Solution:**

1. Create a Record-Triggered Flow on Opportunity, After Save, Asynchronous path.
2. Add condition: `RecordTypeId = [Enterprise RT ID]` AND `IsNew = true`.
3. Add Formula variable for channel name: `LOWER(SUBSTITUTE(LEFT({!$Record.Name}, 60), ' ', '-'))` — produces lowercase, hyphen-separated, max-60-char channel name.
4. Add Action: **Create Channel** with Channel Name = formula result. Capture output `channelId`.
5. Add Action: **Add Users to Channel** with Channel ID = `{!channelId}` and Users = `{!$Record.OwnerId}`, `{!$Record.Account.OwnerId}`.
6. Save the returned `channelId` to a custom Opportunity field for future reference.

**Why it works:** Channel name formula produces Slack-compatible names (lowercase, hyphens, <80 chars). Capturing the channelId enables future flow actions targeting the same channel.

---

## Anti-Pattern: Calling Slack Actions in Before-Save Flow

**What practitioners do:** Add a "Send Slack Message" action in the before-save (synchronous) path of a record-triggered Flow, expecting it to send before the record is committed.

**What goes wrong:** Slack actions are callout-based. Salesforce prohibits callouts in synchronous transaction contexts (before-save record-triggered flows). The flow throws a governor limit error: "You have uncommitted work pending — cannot perform a callout from a trigger, a Visualforce page, or an after method."

**Correct approach:** Always place Slack actions in the after-save, asynchronous execution path of a record-triggered Flow. The record will be committed before the Slack action executes.
