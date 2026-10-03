# Examples: Flow for Slack

## Example 1: Opportunity Stage Change Slack Notification

**Context:** A sales operations team wants to notify a dedicated deal-alerts Slack channel whenever an Enterprise Opportunity moves to Negotiation/Review.

**Problem:** The first build put the Slack action directly on the immediate after-save path with no fault handling. When a Slack app permission was removed, alerts stopped and nobody noticed.

**Solution:**

```text
Record-triggered flow   Object: Opportunity   Trigger: A record is created or updated
                        Optimize for: Actions and Related Records (after save)
Entry criteria          StageName = Negotiation/Review, only when updated to meet criteria
Path                    Run Asynchronously  (pathType AsyncAfterCommit)
  Action                Send Slack Message  (actionType slackPostMessage)
    Slack App           from Slack_Config__mdt.Sales_Alerts.App_Id__c
    Slack Workspace     from Slack_Config__mdt.Sales_Alerts.Workspace_Id__c
    Destination ID      from Slack_Config__mdt.Sales_Alerts.Channel_Id__c  (C0123456789)
    Message             "Negotiation: {!$Record.Name} for {!$Record.Account.Name}"
  Fault path            Create Task "Slack alert failed" with {!$Flow.FaultMessage}
```

The deployable XML is in [metadata-examples.md](metadata-examples.md).

**Why it works:** The async path runs after the save commits, so the message describes committed data. The channel ID survives channel renames, and the IDs live in custom metadata, so sandbox and production can point at different workspaces. The fault path turns a silent failure into a Task an owner sees.

---

## Example 2: Auto-Create a Deal Room Slack Channel for New Enterprise Opportunities

**Context:** The sales team wants a Slack channel for each new Enterprise Opportunity.

**Problem:** Channels were created by hand with inconsistent names, and key stakeholders were missed.

**Solution:**

1. Record-triggered flow on Opportunity, after save, async path, entry criteria `RecordType = Enterprise` on create.
2. Formula resource for the channel name. Slack allows only lowercase letters, numbers, hyphens, and underscores, up to 80 characters:

```text
ChannelName (Text formula) =
  LEFT(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(LOWER(TRIM({!$Record.Name})), " ", "-"), ":", ""), "/", "-"), 60)
```

3. **Create Slack Channel** with the formula result; store the returned channel ID.
4. **Invite Users to Slack Channel** with the channel ID, the Opportunity owner, and the Account owner.
5. Save the channel ID to a custom Opportunity field for later actions.
6. Fault paths on both actions.

**Why it works:** The formula keeps names within Slack's rules. The stored channel ID lets later flows post to the same room without searching for it.

---

## Anti-Pattern: Calling Slack Actions in a Before-Save Flow

**What practitioners do:** Add Send Slack Message to a before-save (fast field update) flow, expecting the message to go out before the record commits.

**What goes wrong:** The Metadata API describes `RecordBeforeSave` as a flow that runs "to make more updates to that record before it's saved to the database"; posting to Slack is not that job, and the message would describe data that isn't committed yet. UNVERIFIED (2026-10-03): the specific error text practitioners report (for example an uncommitted-work callout error) is not documented in the fetched sources.

**Correct approach:** Put Slack actions on the `AsyncAfterCommit` path of an after-save flow. The record commits first, then the message is sent.
