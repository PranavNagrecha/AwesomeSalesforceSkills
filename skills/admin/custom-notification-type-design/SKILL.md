---
name: custom-notification-type-design
description: "Use when designing Custom Notification Types that fire via Flow, Apex, or Process Builder to Lightning bell, desktop, mobile (push), and Slack. Covers channel enablement, targeting, deliverability, consent, and anti-spam discipline. Does NOT cover email templates (see modernize-email-templates) or Salesforce Notifications API general reference."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "custom notification salesforce setup"
  - "send desktop push notification flow"
  - "salesforce bell notification from apex"
  - "slack custom notification salesforce"
  - "notification fatigue prevention"
tags:
  - admin
  - notifications
  - custom-notification-type
  - push
  - slack
inputs:
  - What triggers the notification
  - Target audience and channels (bell / desktop / mobile / Slack)
  - Frequency expectations
outputs:
  - Custom Notification Type setup (metadata)
  - Targeting and consent design
  - Throttling / de-duplication plan
  - Observability + governance
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Custom Notification Type Design

## Purpose

Salesforce Custom Notification Types (CNTs) push messages to the bell,
desktop, mobile, and now Slack. They are easy to enable and easy to
abuse. Teams ship a new CNT per feature without a global view, which
turns into notification fatigue — users silence the bell, disable mobile
push, and ignore Slack. This skill frames CNT design as a product and
governance problem, not a Setup click-through.

## Recommended Workflow

1. **Justify the notification.** Does the recipient need to act, or is
   email/dashboard sufficient? If not actionable, do not notify.
2. **Pick channels.** Bell (in-app), desktop (browser), mobile push,
   Slack. Each has its own opt-in.
3. **Design targeting.** Role? Queue? Explicit list? Record owner? A
   user who can't act is a user you shouldn't notify.
4. **Set frequency rules.** Per record, per day, per user. Bundle where
   possible.
5. **Design deep-link.** Every notification should open the thing the
   recipient needs to look at.
6. **Plan governance.** Which notifications exist, who owns them, when
   they are reviewed.
7. **Measure.** Bell clicks, mobile open rates, Slack click-through. Low
   engagement = noise = cut.

## Channel Characteristics

| Channel | Good For | Fatigue Risk |
|---|---|---|
| Bell | Persistent cross-page awareness | Low individually, high in aggregate |
| Desktop browser | Immediate attention when tab is away | Medium — intrusive if mis-used |
| Mobile push | Urgent field/oncall work | High — users silence fastest |
| Slack | Team / channel broadcast | Depends heavily on channel culture |

## Targeting Patterns

- **Owner:** simplest; record owner + delegated users.
- **Queue members:** shared responsibility; membership must be current.
- **Dynamic list via Flow:** derive audience at runtime. Great for
  approvals/escalations.
- **Explicit User list:** avoid for anything that scales; stale membership
  is a liability.

## Consent And Preferences

- Users set their own notification preferences; your CNT only fires when
  their preferences allow.
- Bell-only is safest default; opt-in to desktop / mobile / Slack as
  explicit uplift.
- Do NOT bypass user preferences via email workarounds — that is the
  fatigue accelerator.

## Throttling / De-Dup

- One record update can fan out multiple triggers; coalesce. Use a "last
  notified at" field to suppress rapid repeats.
- Daily digests for non-urgent categories.
- Quiet hours where supported.

## Deep-Link Design

- Bell: open the relevant record.
- Desktop/Mobile: same.
- Slack: link to a record or queue with minimal summary — do not dump
  the full record into the message.

## Governance

- Registry custom object `Notification_Type__c` listing every CNT,
  owner, trigger, measurable outcome, review cadence.
- Quarterly review: engagement < 20% → cut or redesign.
- New CNT requires registry entry.

## Anti-Patterns (see references/llm-anti-patterns.md)

- "Every change notifies every user."
- Mobile push for non-urgent stuff.
- Notifications whose deep-link lands on a list view, not the record.
- No ownership of who can add a CNT.

## Official Sources Used

- Custom Notification Types — https://help.salesforce.com/s/articleView?id=sf.custom_notifications_overview.htm
- Notification Builder in Flow — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_action_core_custom_notification.htm
- Send Custom Notification in Apex — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_CustomNotification.htm
- Notification Delivery Settings — https://help.salesforce.com/s/articleView?id=sf.notif_builder_send.htm
