# Flow for Slack — Work Template

## Scope

**Skill:** `flow-for-slack`

**Request summary:** (fill in: which Slack action needed and from which Flow type)

## Prerequisites Check

- [ ] Salesforce for Slack Integrations enabled (Setup > Slack Apps Setup) and the Salesforce Slack app installed in the workspace
- [ ] Salesforce org connected to Slack workspace (Setup > Slack > Manage Slack Connection)
- [ ] Running user has Connect Salesforce with Slack plus the app's permission set (Slack Sales User or Slack Service User)
- [ ] Running user has connected their Salesforce account in Slack (Slack User Mappings)

## Slack Action Selection

- **Action needed:** [ ] Send Slack Message  [ ] Create Channel  [ ] Archive Channel
  [ ] Add Users to Channel  [ ] Check if User Is Connected  [ ] Get Conversation Info
  [ ] Send Message to Launch Flow

## Flow Configuration

- **Flow type:** [ ] Record-Triggered  [ ] Scheduled  [ ] Autolaunched (Platform Event/other)
- **Execution context for Slack actions:** [ ] After Save (Async) — REQUIRED for record-triggered
- **Channel reference:** ID: `C_________` (use channel ID, not display name)
- **Channel name formula (for Create Channel):** `LOWER(SUBSTITUTE(LEFT(Name, 60), ' ', '-'))`

## Fault Handling

- **Fault connector configured?** [ ] Yes  [ ] No — add fault path
- **Fault action:** [ ] Create Record (log error)  [ ] Send admin alert email

## Checklist

- [ ] All four prerequisites confirmed
- [ ] Slack actions in after-save asynchronous path only
- [ ] Channel ID used (not display name)
- [ ] Channel names are lowercase, <80 chars, no spaces for Create Channel
- [ ] Check if User Is Connected before sending DMs
- [ ] Fault path configured on all Slack action elements

## Notes

(Record any prerequisite gaps, channel name transformation logic, or send-message-to-launch-flow details)
