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

## Configuration Checklist

### Queues

- [ ] Case queues exist with correct names and members
- [ ] Each queue has "Case" in its Supported Objects list
- [ ] Queue email addresses configured for notifications

### Assignment Rules

- [ ] One active case assignment rule exists
- [ ] Rule entries ordered from specific to catch-all
- [ ] Catch-all entry exists as the last entry
- [ ] Tested: cases from Web-to-Case and Email-to-Case route to correct queue

### Auto-Response Rules

- [ ] Assignment rule confirmed to fire before configuring auto-response
- [ ] Auto-response rule active with valid email template per entry
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

### Entitlements and Milestones (if applicable)

- [ ] Entitlement Management enabled in Setup
- [ ] Business hours attached to entitlement process
- [ ] Milestones configured with warning and violation actions
- [ ] Automation (Flow or Apex) applies entitlements to new cases
- [ ] Lightning limitation acknowledged: no template-on-product UI

## Approach

Which pattern from SKILL.md applies? Why?

(fill in)

## Deviations

Record any deviations from the standard pattern and why.

(fill in)
