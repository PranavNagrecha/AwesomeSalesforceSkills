# Subscriber Data Management — Work Template

Use this template when working on subscriber identity, opt-out, suppression, or deduplication tasks in Marketing Cloud.

---

## Scope

**Skill:** `subscriber-data-management`

**Request summary:** (describe what the practitioner asked for — e.g., "Configure Subscriber Key strategy for new MC org with Sales Cloud Connect")

**Business Unit context:**
- [ ] Single Business Unit
- [ ] Enterprise 2.0 (parent + child BUs) — list child BUs in scope: _______________

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Current Subscriber Key type (email or CRM ID)? | |
| CRM system connected (Sales Cloud / Service Cloud / none)? | |
| Compliance regime (CAN-SPAM / GDPR / CASL / other)? | |
| Approximate subscriber population size? | |
| Any existing Held or globally Unsubscribed records to address? | |
| Auto-Suppression Lists currently in use (yes/no, purpose if yes)? | |

---

## Subscriber Key Assessment

**Current key strategy:** [ ] Email address  [ ] CRM Contact/Lead ID  [ ] Other: ___

**Is migration required?**
- [ ] No — CRM ID already in use (or org is new)
- [ ] Yes — Email is current key; Salesforce Support engagement needed
- [ ] Uncertain — Audit needed (see step below)

**Audit step (if uncertain):** Export 50 sample rows from All Subscribers. Check the `SubscriberKey` column:
- All values match `^[a-zA-Z0-9]{18}$` → CRM ID likely in use
- All values contain `@` → Email is in use as key; migration required

---

## Unsubscribe Authority Review

**All Subscribers global unsubscribe count:** ___ records

**Action for globally unsubscribed records:**
- [ ] Legitimate opt-outs — no action needed
- [ ] Records requiring reactivation (fresh opt-in documented): list keys or attach file

**Publication list opt-out scope:**
- Publication lists in use: _______________
- Are per-list unsubscribes correctly scoped (not triggering global unsubscribes unintentionally)? [ ] Yes [ ] No — remediation needed

---

## Auto-Suppression List Configuration

| List Name | Purpose | Send Classification Scope | Refresh Frequency |
|---|---|---|---|
| (e.g., GDPR-Erasure-Requests) | Regulatory erasure | All | Nightly |
| | | | |

**Validation test:** Send a test to a known suppressed address. Confirm address appears in exclusion log, not sent log. [ ] Passed [ ] Failed — notes:

---

## Sendable Data Extension Deduplication Check

**DEs targeted in this send or journey:**

| DE Name | Primary Key Field | Duplicate SubscriberKeys Possible? | Pre-aggregation Applied? |
|---|---|---|---|
| | | [ ] Yes [ ] No | [ ] Yes [ ] No |

If duplicates are possible and personalization accuracy matters, apply SQL ranking before send:

```sql
SELECT
    SubscriberKey,
    EmailAddress,
    -- add personalization fields here
FROM (
    SELECT
        SubscriberKey,
        EmailAddress,
        -- personalization fields
        ROW_NUMBER() OVER (PARTITION BY SubscriberKey ORDER BY EventDate DESC) AS rn
    FROM [Source_DE_Name]
) ranked
WHERE rn = 1
```

---

## Held Subscriber Review

**Held subscriber count:** ___

**Bounce investigation query (run in Automation Studio SQL or SSJS):**

```sql
SELECT
    SubscriberKey,
    EmailAddress,
    BounceType,
    BounceSubtype,
    BouncedDate
FROM _Bounce
WHERE BounceType = 'HardBounce'
ORDER BY BouncedDate DESC
```

| SubscriberKey | EmailAddress | BounceSubtype | Action |
|---|---|---|---|
| | | | Reactivate / Keep Held |

**Reactivation evidence documented?** [ ] Yes — attached  [ ] N/A (all Held records are legitimate)

---

## Cross-BU Suppression (Enterprise 2.0 Only)

If multiple BUs are in scope:

- [ ] Cross-BU opt-out propagation mechanism is in place
  - Method: [ ] API-based propagation  [ ] Centralized Auto-Suppression List push  [ ] Other: ___
- [ ] All child BUs audited for independent All Subscribers global unsubscribes

---

## Send Pipeline Test Results

| Subscriber Category | Subscriber Key | Expected Outcome | Actual Outcome | Pass? |
|---|---|---|---|---|
| Active, no suppression | | Receives send | | [ ] |
| Globally Unsubscribed (All Subscribers) | | Excluded | | [ ] |
| Auto-Suppression List match | | Excluded | | [ ] |
| Held status | | Excluded | | [ ] |
| Publication list unsubscribed only | | Receives send (if not globally unsub) | | [ ] |

---

## Review Checklist

- [ ] Subscriber Key strategy confirmed and documented (CRM ID preferred)
- [ ] All Subscribers Held records reviewed; reactivations documented with opt-in evidence
- [ ] Global unsubscribes confirmed not overrideable by any automation or publication list
- [ ] Auto-Suppression Lists configured for all permanent/regulatory exclusions
- [ ] Sendable DEs use SubscriberKey as primary key; duplicate row behavior documented
- [ ] Cross-BU suppression acknowledged and addressed (if Enterprise 2.0)
- [ ] Compliance documentation in place (opt-in proof, unsubscribe audit trail)
- [ ] Send pipeline test passed for all subscriber status categories

---

## Notes and Deviations

(Record any departures from the standard pattern documented in SKILL.md and the reason why.)
