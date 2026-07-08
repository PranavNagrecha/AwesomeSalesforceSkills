# Case Management Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `case-management-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Inbound channel:** [ ] Email-to-Case  [ ] Web-to-Case  [ ] Both
- **Email-to-Case type:** [ ] On-Demand (recommended)  [ ] Classic
- **Active case assignment rule exists?** [ ] Yes  [ ] No  [ ] Unknown
- **Business hours configured?** [ ] Yes — name: ___  [ ] No
- **SLA requirements:** Response target: ___  Resolution target: ___
- **Entitlements required?** [ ] Yes  [ ] No
- **Entitlement Management enabled in Setup?** [ ] Yes  [ ] No  [ ] Unknown
- **Routing model:** [ ] Queue pull  [ ] Omni-Channel push (→ `admin/omni-channel-routing-setup`)
- **Review cadence agreed?** Owner: ___  Interval: ___

## Active Rule Slot Inventory

Only one assignment, one auto-response, and one escalation rule can be active for
cases at a time. Activating a rule deactivates the incumbent. Record what is in
each slot BEFORE building anything — these names are the rollback targets.

| Slot | Currently active rule name | Replacing it? | Rollback target |
|---|---|---|---|
| Assignment | | [ ] Yes  [ ] No | |
| Auto-Response | | [ ] Yes  [ ] No | |
| Escalation | | [ ] Yes  [ ] No | |

## Configuration Checklist

### Queues

- [ ] Case queues exist with correct names and members
- [ ] Each queue has "Case" in its Supported Objects list
- [ ] Queue email addresses configured for notifications
- [ ] Every queue has at least one active member who will pull from it

### Assignment Rules

- [ ] One active case assignment rule exists
- [ ] Rule entries ordered from specific to catch-all
- [ ] Catch-all entry exists as the last entry
- [ ] Per-region and per-channel logic modeled as entries, not as a second active rule
- [ ] Replacement activated directly (incumbent NOT deactivated first — that opens a routing gap)
- [ ] Post-cutover check: zero cases created today owned by the default case owner
- [ ] Tested: cases from Web-to-Case and Email-to-Case route to correct queue

### Auto-Response Rules

- [ ] Assignment rule confirmed to fire before configuring auto-response
- [ ] Auto-response rule active with valid email template per entry
- [ ] Per-channel acknowledgments modeled as entries within the single active rule
- [ ] "From" address is NOT the Email-to-Case routing address (would create loop)

### Escalation Rules

- [ ] Business hours record created and attached to each rule entry
- [ ] Time thresholds reflect business hours, not calendar hours
- [ ] Deactivation/reactivation impact communicated to stakeholders
- [ ] Tested in sandbox before production activation

### Email-to-Case

- [ ] Routing address created and mail server forward rule configured
- [ ] Thread ID handling tested end-to-end (reply threads into parent case)
- [ ] Subject-line thread ID enabled as fallback if body processing unreliable
- [ ] Body truncation at 32,000 characters communicated to support team

### Web-to-Case

- [ ] Form HTML embedded on external site with client-side validation added
- [ ] Pending request count monitored (hard limit: 50,000)
- [ ] Post-creation Flow configured for server-side validation if needed

### Case Teams (if applicable)

- [ ] Case team roles created with correct access levels
- [ ] Predefined teams built referencing the correct roles
- [ ] Team members are active users

### Case Feed (agent surface)

- [ ] Agent surface validated in the interface agents actually use
- [ ] Noted: official Case Feed setup topics (feed layouts, Case Feed actions, feed
      items) are documented under Salesforce Classic — Lightning is configured via
      the Lightning record page and quick actions
- [ ] Send Email quick action configured if agents reply from the case (→ `admin/case-feed-send-email-action`)

### Entitlements and Milestones (if applicable)

- [ ] Entitlement Management enabled in Setup
- [ ] Business hours attached to entitlement process
- [ ] Milestones configured with warning and violation actions
- [ ] Automation (Flow or Apex) applies entitlements to new cases
- [ ] Lightning limitation acknowledged: no template-on-product UI

### Post-Go-Live (case management is not set-and-forget)

- [ ] Named owner recorded for each of the three active rule slots
- [ ] Recurring review scheduled for rule entries, queue membership, SLA thresholds
- [ ] Reports/dashboards surface routing outcomes and SLA attainment to leaders
- [ ] Rollback target (displaced rule name) documented for each activation

## Approach

Which pattern from SKILL.md applies? Why?

(fill in)

## Deviations

Record any deviations from the standard pattern and why.

(fill in)
