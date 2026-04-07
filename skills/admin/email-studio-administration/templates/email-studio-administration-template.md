# Email Studio Administration — Work Template

Use this template when working on email creation, send configuration, or pre-send validation tasks in Marketing Cloud Email Studio and Content Builder.

## Scope

**Skill:** `email-studio-administration`

**Request summary:** (fill in what the user asked for)

**Send type:** (Scheduled batch / Triggered / Journey Builder send)

**Legal classification:** (Commercial / Transactional — confirm before proceeding)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Business unit:** (which BU owns this send)
- **Subscriber data structure:** (List or Data Extension; which fields are available for dynamic content rules)
- **Legal classification confirmed:** (Commercial or Transactional; rationale)
- **Known constraints:** (IP pool, SAP affinity, suppression list requirements)
- **Failure modes to watch for:** (Triggered Send activation status, dynamic content default coverage, A/B test audience size)

## Send Classification Configuration

- **Send Classification name:**
- **Sender Profile:** (From Name / From Address)
- **Delivery Profile:** (IP pool / physical address)
- **Unsubscribe Profile:** (Commercial global unsubscribe / Transactional separate opt-out)
- **CAN-SPAM footer:** (Required — Yes/No based on classification)

## Content Build Approach

- **Build method:** (Drag-and-drop blocks / Raw HTML)
- **Dynamic content blocks:** (List each block, its rule conditions in order, and the default variation)

| Block Name | Rule 1 | Rule 2 | Rule N | Default |
|---|---|---|---|---|
| (e.g., Hero Image) | Condition + variation | Condition + variation | ... | Default variation |

## A/B Test Configuration (if applicable)

- **Test dimension:** (Subject line / From name / Content / Send time)
- **Version A:**
- **Version B:**
- **Test split:** % → A / % → B / % → Holdout
- **Winner criteria:** (Open rate / Click rate / Manual)
- **Evaluation window:** (hours)
- **Auto-send winner:** (Yes / No)
- **Minimum open events per arm to trust the result:** (calculate from historical open rate)

## Suppression Configuration

- [ ] Auto-suppression active (bounces, global unsubscribes, spam complaints)
- [ ] Publication list suppression confirmed for send
- [ ] Global Suppression List reviewed — current address count: ____
- [ ] Emergency suppression process documented if needed during active send

## Pre-Send Validation Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Send Classification assigned and confirmed (Commercial / Transactional)
- [ ] CAN-SPAM footer present and correct for Commercial sends
- [ ] Every Dynamic Content block has a valid default variation
- [ ] Dynamic content rules tested with representative subscriber data per segment
- [ ] Content Detective run — spam score result: ____
- [ ] Test send delivered to seed list and reviewed by email owner
- [ ] Inbox Preview completed (Litmus) — target clients tested: ____
- [ ] Global Suppression List active and address count reviewed
- [ ] For A/B tests: winner criteria, evaluation window, and holdout % confirmed
- [ ] For Triggered Sends: definition status confirmed as "Active"
- [ ] Approval workflow completed (if required by BU policy)

## Approach

Which pattern from SKILL.md applies? Why?

(e.g., "Dynamic Content for Segmented Personalization — subscriber data has LoyaltyTier attribute with 4 values. Single email with 4-rule dynamic content blocks used instead of separate versions.")

## Notes

Record any deviations from the standard pattern and why.

(e.g., "Email build uses raw HTML because the design requires custom background image CSS not supported by drag-and-drop blocks.")
