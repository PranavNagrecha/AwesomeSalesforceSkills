# Slack Salesforce Integration Setup — Work Template

## Scope

**Skill:** `slack-salesforce-integration-setup`

**Request summary:** (fill in: first-time connection, troubleshooting, governance review)

## Pre-Flight Checks

- **Government Cloud or Government Cloud Plus org?** [ ] No  [ ] Yes (cannot connect)
- **FedRAMP, HIPAA, or Blackjack requirement?** [ ] No  [ ] Yes (not certified)
- **Slack plan:** ______ (multiple orgs documented for Pro, Business+, Enterprise)
- **Additional orgs already connected:** ___ (up to 20 additional on those plans)
- **Connection plan checked:** `check_slack_salesforce_integration_setup.py --plan ...` [ ] Clean

## Three-Party Handshake Roster

| Role | Person | Status |
|---|---|---|
| Slack Workspace Owner/Admin (Step 1: request) | | [ ] Available |
| Salesforce System Admin (Step 2: approve) | | [ ] Available |
| Slack Owner or Salesforce Admin system role (Step 3: activate) | | [ ] Available |

## Connection Steps

- [ ] Step 1: Request the connection in Slack (Tools & settings > Manage Salesforce Organizations)
- [ ] Step 2: Salesforce System Admin approves in Setup > Platform Tools > Slack > Manage Slack Connection
- [ ] Step 3: Owner or Salesforce Admin system role activates in Slack
- [ ] Connect Salesforce with Slack permission assigned to every Slack user
- [ ] Account mapping configured; users connected their Salesforce accounts

## Data Governance

- **Sensitive Salesforce objects that should not be shared in Slack:**
  (list object names)
- **Unfurling option per object:** (Do Not Share Data / Preview Button Only / ... )
- **URL Unfurling Slack Record Layouts for sensitive objects:** (list)
- **Channel governance policy:** (which record types allowed in which channel types)

## Checklist

- [ ] Compliance gate and plan confirmed
- [ ] Three-step handshake completed in order by the documented roles
- [ ] Connect Salesforce with Slack permission assigned
- [ ] Record preview data exposure risk documented and communicated
- [ ] Individual users connected personal accounts
- [ ] Channel governance policy defined

## Notes

(Record coordination issues, Government Cloud blocking, org count concerns)
