# Messaging and Chat Setup — Work Template

Use this template when configuring or reviewing a Messaging for In-App and Web (MIAW) channel deployment.

## Scope

**Skill:** `messaging-and-chat-setup`

**Request summary:** (fill in what the user asked for — e.g., "Set up MIAW chat on support portal" or "Troubleshoot widget not loading on staging")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before proceeding.

- **Messaging for In-App and Web enabled?** Yes / No (Setup > Messaging Settings)
- **Omni-Channel enabled?** Yes / No
- **Widget domains (list all, including staging/UAT):**
  - Production: `https://`
  - Staging: `https://`
  - Other: `https://`
- **Routing strategy:** Queue-Based / Flow-Based / Unknown
- **Capacity model:** Status-Based / Tab-Based / Not yet decided
- **Pre-chat fields required:** Yes / No — if Yes, list fields and target object (Contact / Case):
  - Field label: _____ Target: _____
  - Field label: _____ Target: _____

## Approach

Which pattern from SKILL.md applies?
- [ ] Greenfield MIAW Deployment with Queue Routing
- [ ] Flow-Based Routing with Business-Hours Fallback
- [ ] Troubleshooting existing deployment
- [ ] Other: ___________

Why this pattern: (brief justification)

## Configuration Checklist

Work through these steps and check off as complete:

- [ ] Messaging for In-App and Web enabled in Messaging Settings
- [ ] Messaging Channel record created
  - Channel Type: Messaging for In-App and Web
  - Routing Queue or Omni-Channel Flow assigned
  - Fallback Queue assigned
  - Off-hours auto-response message set
- [ ] Pre-chat fields configured on Messaging Channel (if required)
  - Field mapping to Contact/Case fields verified
  - Contact lookup automation (Flow or trigger) created and tested
- [ ] Embedded Service Deployment created
  - Type: Messaging for In-App and Web
  - Messaging Channel linked correctly
  - Branding configured (colors, label, avatar)
- [ ] CORS Trusted Sites registered for all widget domains
- [ ] CSP Trusted Sites registered for all widget domains (matching CORS list)
- [ ] Presence Configuration updated with Status-Based capacity for messaging
- [ ] Code snippet copied from deployment record and added to website
- [ ] End-to-end test in sandbox completed
  - Customer session created successfully
  - Session routed to correct queue/agent
  - Pre-chat data visible on MessagingSession record
  - Contact linked (if applicable)
  - Off-hours message fires outside business hours

## Routing Flow Notes (if applicable)

Omni-Channel Flow name: _____________

| Branch | Condition | Target Queue |
|---|---|---|
| Default | (all sessions) | |
| Language ES | PreChatLanguage = 'ES' | |
| Off-hours | Outside BusinessHours | End session with message |
| Fault / Fallback | Flow error | Fallback Queue |

## Notes

Record any deviations from the standard pattern and why.

- Deviation 1:
- Deviation 2:

## Sign-Off

- [ ] Review checklist in SKILL.md completed
- [ ] All widget domains confirmed in both CORS and CSP
- [ ] Fallback queue confirmed on Messaging Channel record
- [ ] Stakeholder / requestor sign-off received
