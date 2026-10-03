# LLM Anti-Patterns: Flow for Slack

## Anti-Pattern 1: Presenting Slack Actions as Always Available in Flow Builder

**What the LLM generates:** "In Flow Builder, add an Action element and search for 'Send Slack Message' to post a notification to Slack."

**Why it happens:** LLMs present the action as a standard part of Flow Builder without mentioning prerequisites. The Slack Apps Setup steps, app installation, and permissions are not part of base Flow Builder knowledge.

**Correct pattern:** Before prescribing Slack actions in Flow Builder, confirm: (1) Salesforce for Slack Integrations is enabled in Setup > Slack Apps Setup, (2) the Salesforce Slack app is installed in the workspace from the Slack App Directory, (3) the running user has the Connect Salesforce with Slack system permission plus the app's permission set (Slack Sales User or Slack Service User), (4) the user has connected their Salesforce account in Slack. UNVERIFIED (2026-10-03): a separate AppExchange managed package is not part of the setup in the Summer '26 Slack Integrations guide.

**Detection hint:** Instructions that say "search for Send Slack Message in Flow Builder" without mentioning prerequisites are incomplete.

---

## Anti-Pattern 2: Placing Slack Actions in Before-Save Execution Path

**What the LLM generates:** A record-triggered Flow design that places Send Slack Message in the before-save (synchronous) path to notify before the record is committed.

**Why it happens:** Developers want to send notifications "immediately" when a record changes. They place the action before save, not realizing that callouts (including Slack) are prohibited in synchronous contexts.

**Correct pattern:** Place Slack actions on an `AsyncAfterCommit` path of an after-save flow, which "runs asynchronously after a save" (Metadata API, FlowScheduledPath). The record is committed first, then the message is sent. UNVERIFIED (2026-10-03): Salesforce Help states the async-path requirement for Slack actions; the fetched sources don't.

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

**Correct pattern:** Every Slack action element in Flow should have a fault connector leading to a fault handler, at minimum, a Create Record action that logs the fault message, or an assignment that stores the fault and sends an alert. Slack actions fail silently without fault paths, leaving no trace when permissions change or the OAuth token is revoked.

**Detection hint:** Flow designs with action elements and no fault connector (no red connector from the action element) are missing fault handling.

---

## Anti-Pattern 5: Confusing Slack Workflow Builder with Flow Core Actions

**What the LLM generates:** "Use Slack Workflow Builder to trigger a Salesforce Flow when a Slack message is received, which then sends another Slack message back."

**Why it happens:** Both involve "Flow" and "Slack" and the directions are frequently conflated. Slack Workflow Builder calls Salesforce Flows from Slack (Slack → Salesforce). Flow Core Actions send messages from Salesforce to Slack (Salesforce → Slack). These are opposite directions with different authoring tools.

**Correct pattern:** Use Salesforce Flow Core Actions (Salesforce → Slack direction) for Salesforce-initiated Slack notifications. Use Slack Workflow Builder (Slack → Salesforce direction) for Slack-initiated Salesforce actions. They are complementary, not the same tool.

**Detection hint:** Instructions that conflate "Slack Workflow Builder" with "Flow Core Actions for Slack" as interchangeable tools are incorrect.

---

## Anti-Pattern 6: Pointing Send Message to Launch Flow at an Autolaunched Flow

**What the LLM generates:** "Use Send Message to Launch Flow so clicking the Slack button runs your autolaunched approval flow."

**Why it happens:** The action name suggests a generic trigger, and an earlier version of this very skill said the target must be autolaunched.

**Correct pattern:**

```text
slackSendMessageToLaunchFlow sends a message "that includes a button that a
recipient can use to launch a screen flow" (Metadata API).
- Target: a screen flow saved with <environments>Slack</environments>
- Background logic: call a subflow or autolaunched flow from that screen flow
```

**Detection hint:** A launch-flow button whose target flow has no screens or lacks the Slack environment.

---

## Anti-Pattern 7: Building Channel Names Without Slack's Rules

**What the LLM generates:** `Channel Name = {!$Record.Name}` on Create Slack Channel, or a rule that "only hyphens are allowed."

**Why it happens:** LLMs don't know Slack's naming constraints, or half-remember them.

**Correct pattern:**

```text
Slack: "Channel names may only contain lowercase letters, numbers, hyphens,
and underscores, and must be 80 characters or less."
Formula sketch:
  LEFT(SUBSTITUTE(LOWER(TRIM({!$Record.Name})), " ", "-"), 60)
then strip characters outside [a-z0-9-_] before calling Create Slack Channel.
```

**Detection hint:** A raw record field passed as the channel name, or advice that bans underscores.

