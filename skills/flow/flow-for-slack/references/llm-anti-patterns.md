# LLM Anti-Patterns — Flow for Slack

## Anti-Pattern 1: Presenting Slack Actions as Always Available in Flow Builder

**What the LLM generates:** "In Flow Builder, add an Action element and search for 'Send Slack Message' to post a notification to Slack."

**Why it happens:** LLMs present the action as a standard part of Flow Builder without mentioning prerequisites. The managed package, org connection, and permission sets are not part of base Flow Builder knowledge.

**Correct pattern:** Before prescribing Slack actions in Flow Builder, confirm: (1) Salesforce for Slack managed package is installed, (2) org is connected to a Slack workspace, (3) running user has Sales Cloud for Slack or Slack Service User permission set, (4) workspace OAuth token is active. Without all four, actions are invisible or fail at runtime.

**Detection hint:** Instructions that say "search for Send Slack Message in Flow Builder" without mentioning prerequisites are incomplete.

---

## Anti-Pattern 2: Placing Slack Actions in Before-Save Execution Path

**What the LLM generates:** A record-triggered Flow design that places Send Slack Message in the before-save (synchronous) path to notify before the record is committed.

**Why it happens:** Developers want to send notifications "immediately" when a record changes. They place the action before save, not realizing that callouts (including Slack) are prohibited in synchronous contexts.

**Correct pattern:** Slack actions must be placed in the after-save, asynchronous execution path. The record will be committed first, then the Slack message will be sent. There is no way to send a Slack message before the record is saved — nor is this typically a real business requirement.

**Detection hint:** Any Flow design with a Slack action in the before-save trigger path is incorrect.

---

## Anti-Pattern 3: Using Channel Display Names Instead of Channel IDs

**What the LLM generates:** `Channel: #deal-alerts` as the channel input for Send Slack Message.

**Why it happens:** Display names are human-readable and obvious. LLMs use them because they are more interpretable than opaque channel IDs.

**Correct pattern:** Use Slack channel IDs (format: `C0123456789`) in Flow actions. Channel display names can be renamed by Slack admins, breaking hardcoded channel references. Channel IDs are permanent and do not change when channels are renamed. Retrieve the channel ID from the Slack workspace admin interface or the Slack API.

**Detection hint:** Channel references in the format `#channel-name` or `channel-name` (without the `C` prefix ID) are fragile.

---

## Anti-Pattern 4: No Fault Path on Slack Action Elements

**What the LLM generates:** A Flow design with Slack action elements and no fault connector, assuming the actions will always succeed.

**Why it happens:** LLMs design the happy path and often omit fault handling as an "advanced topic."

**Correct pattern:** Every Slack action element in Flow should have a fault connector leading to a fault handler — at minimum, a Create Record action that logs the fault message, or an assignment that stores the fault and sends an alert. Slack actions fail silently without fault paths, leaving no trace when permissions change or the OAuth token is revoked.

**Detection hint:** Flow designs with action elements and no fault connector (no red connector from the action element) are missing fault handling.

---

## Anti-Pattern 5: Confusing Slack Workflow Builder with Flow Core Actions

**What the LLM generates:** "Use Slack Workflow Builder to trigger a Salesforce Flow when a Slack message is received, which then sends another Slack message back."

**Why it happens:** Both involve "Flow" and "Slack" and the directions are frequently conflated. Slack Workflow Builder calls Salesforce Flows from Slack (Slack → Salesforce). Flow Core Actions send messages from Salesforce to Slack (Salesforce → Slack). These are opposite directions with different authoring tools.

**Correct pattern:** Use Salesforce Flow Core Actions (Salesforce → Slack direction) for Salesforce-initiated Slack notifications. Use Slack Workflow Builder (Slack → Salesforce direction) for Slack-initiated Salesforce actions. They are complementary, not the same tool.

**Detection hint:** Instructions that conflate "Slack Workflow Builder" with "Flow Core Actions for Slack" as interchangeable tools are incorrect.
