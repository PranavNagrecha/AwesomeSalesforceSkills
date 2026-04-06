# Multi Channel Service Architecture — Work Template

Use this template when designing or evaluating a multi-channel service architecture.

## Scope

**Skill:** `multi-channel-service-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Active channels:** (list each channel: phone, email, chat, SMS, social)
- **Legacy channels in use:** (Live Agent? Social Studio? List any that need migration)
- **Monthly volume per channel:** (phone: ___, email: ___, chat: ___, SMS: ___, social: ___)
- **Average handle time per channel:** (phone: ___ min, chat: ___ min, email: ___ min)
- **Licensing in place:** (Service Cloud? Digital Engagement? Service Cloud Voice?)
- **Current routing model:** (queue-based, skills-based, none)

## Channel Architecture Map

| Channel | Salesforce Feature | Object Created | Service Channel Object | Capacity Weight | License Required |
|---|---|---|---|---|---|
| Phone | Service Cloud Voice | VoiceCall -> Case | VoiceCall | ___ | Voice Add-On |
| Email | Email-to-Case (on-demand / org-wide) | Case | Case | ___ | Service Cloud |
| Chat | Messaging for In-App/Web | MessagingSession -> Case | MessagingSession | ___ | Digital Engagement |
| SMS | Messaging (SMS) | MessagingSession -> Case | MessagingSession | ___ | Digital Engagement |
| Social | Social Customer Service | Case | Case | ___ | Social Customer Service |

## Omni-Channel Routing Design

- **Routing strategy:** (queue-based / skills-based / attribute-based)
- **Queue structure:** (list topic-based queues, not channel-based)
  - Queue 1: ___ (channels: ___)
  - Queue 2: ___ (channels: ___)
  - Queue 3: ___ (channels: ___)
- **Agent total capacity:** ___ units
- **Presence Statuses:**
  - Status 1: ___ (mapped channels: ___)
  - Status 2: ___ (mapped channels: ___)

## Migration Plan (if applicable)

- **Legacy feature:** (Live Agent / Social Studio / other)
- **Target feature:** (Messaging for In-App/Web / Social Customer Service)
- **Migration approach:** (phased / big-bang)
- **Parallel running period:** ___ weeks
- **Downstream dependencies to update:** (reports, Flows, Apex, Lightning components)

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Hub-and-spoke channel architecture (greenfield or redesign)
- [ ] Phased channel migration (legacy to current)

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] All channels map to current (non-legacy) Salesforce features
- [ ] Omni-Channel uses a single routing strategy across all channels
- [ ] Capacity weights assigned per Service Channel, reflecting real handle times
- [ ] Every channel creates or links to Case for unified timeline
- [ ] Agent console includes components for all active channels
- [ ] Email-to-Case variant explicitly chosen and documented
- [ ] Migration plan exists for any legacy features

## Notes

Record any deviations from the standard pattern and why.
