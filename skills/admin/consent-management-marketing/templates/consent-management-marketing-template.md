# Consent Management Marketing — Work Template

Use this template when working on consent management tasks in Marketing Cloud.

## Scope

**Skill:** `consent-management-marketing`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these questions before proceeding. They determine which pattern applies.

- **Regulatory scope:** US CAN-SPAM only / GDPR / CCPA / combination: ___
- **MC Connect installed and opt-out writeback configured:** Yes / No / Unknown
- **Self-service mechanism:** Use MC Subscription Center / Build CloudPages Preference Center
- **Double opt-in required:** Yes / No
- **Publication lists in scope:** List them: ___
- **Privacy Center configured:** Yes / No / In progress

---

## Pattern Selection

Based on context above, choose the applicable pattern from SKILL.md:

| Pattern | Use when |
|---|---|
| MC Subscription Center + Send Classification | US CAN-SPAM only, no branding requirements, zero dev budget |
| CloudPages Preference Center | Custom branding required, one-click unsubscribe with immediate processing |
| Double opt-in (confirmed opt-in) flow | GDPR EU subscribers, auditable consent records required |
| Privacy Center erasure workflow | GDPR/CCPA right-to-erasure request to process |

**Selected pattern:** ___

**Reason:** ___

---

## Pre-Work Checklist

- [ ] All Subscribers global opt-out behavior confirmed (test with a suppressed address)
- [ ] Publication list taxonomy designed; no internal/operational lists exposed to subscribers
- [ ] Send Classification with Delivery Profile (physical address) assigned to all send types
- [ ] MC Connect opt-out writeback status confirmed (in or out of scope)

---

## Implementation Notes

(Record deviations from the standard pattern and why)

---

## Go-Live Checklist

Copy from SKILL.md Review Checklist and tick each item:

- [ ] Every commercial template includes unsubscribe link (`%%subscription_center_url%%` or custom CloudPage link)
- [ ] Every commercial template includes physical mailing address (via Delivery Profile or literal)
- [ ] Send Classification with correct Delivery Profile assigned to all send types (User-Initiated, Triggered, Journey)
- [ ] Global opt-out tested: subscriber on All Subscribers with `HasOptedOutOfEmail=true` does not receive sends
- [ ] If GDPR: consent-tracking DE is populated on acquisition; double opt-in tested end-to-end
- [ ] If GDPR: Privacy Center configured; erasure tested against test subscriber
- [ ] If MC Connect in scope: opt-out writeback to CRM Contact/Lead verified
- [ ] If custom Preference Center: unsubscribe processes immediately on URL visit (no confirmation interstitial)
- [ ] List-Unsubscribe email header present in Delivery Profile (Google/Yahoo 2024 requirement)
- [ ] No internal/operational publication lists visible to subscribers in Subscription Center

---

## Consent-Tracking DE Schema (GDPR)

Use this schema for the consent event record. Keep it separate from the subscriber profile DE so that consent evidence survives erasure.

| Field | Type | Notes |
|---|---|---|
| `ConsentEventId` | Text(36) | GUID — primary key |
| `SubscriberHashId` | Text(64) | SHA-256 of email address (not raw PII) |
| `EmailAddress` | EmailAddress | Raw address — erased when right-to-erasure processed |
| `ConsentTimestamp` | Date | UTC timestamp of initial consent capture |
| `ConfirmedTimestamp` | Date | UTC timestamp of double opt-in confirmation (null if single opt-in) |
| `CaptureSource` | Text(100) | e.g., "WebForm_EU_2026", "Import_Partner" |
| `LawfulBasis` | Text(50) | "Consent", "LegitimateInterest", "Contract" |
| `ConsentVersion` | Text(20) | Version of consent language shown at capture |
| `IsConfirmed` | Boolean | True after double opt-in confirmation |
| `IsErased` | Boolean | Set to True when erasure processed; EmailAddress cleared |

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, or decisions made during implementation)
