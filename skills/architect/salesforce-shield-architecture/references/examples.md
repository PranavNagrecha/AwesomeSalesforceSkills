# Examples — Salesforce Shield Architecture

## Example 1 — "Encrypt SSN, but reps still need to search by it"

**Context.** Healthcare org bringing PHI into Salesforce. Patient SSN
must be encrypted at rest. Service agents need to look up a patient by
SSN.

**Wrong instinct.** Probabilistic encryption on the SSN field.

**Why it's wrong.** Probabilistic = random IV per encryption, so the
same SSN encrypts to a different ciphertext every time. SOQL `WHERE
SSN__c = '123-45-6789'` cannot find anything because the search value
is encrypted to a different ciphertext than the stored one.

**Right answer.** **Deterministic case-sensitive** encryption on
SSN__c. Same plaintext → same ciphertext, so equality filter works.
Document the trade in the Shield Architecture Decision Document:
"Deterministic encryption is weaker than probabilistic against
ciphertext-frequency analysis; we accept this for SSN because the
business need for searchability outweighs the marginal additional
strength of probabilistic against an adversary with database-level
read."

---

## Example 2 — "Encrypt the formula field that displays masked SSN"

**Context.** Same org as Example 1. There's a formula field
`Patient__c.MaskedSSN__c` that returns `XXX-XX-` + LEFT(SSN__c, 4) for
display. Author wants to encrypt the formula field "for safety".

**Wrong instinct.** Add MaskedSSN__c to the encryption candidate list.

**Why it's wrong.** Formula fields cannot be encrypted — encryption
would prevent the formula evaluation engine from reading inputs and
producing outputs. Adding MaskedSSN__c to the encryption list will
fail validation in Setup.

**Right answer.** Encrypt the *underlying* SSN__c field. The formula
evaluator reads the decrypted value at evaluation time; the masked
output is intrinsically less sensitive (only the last 4 digits, plus
the `XXX-XX-` prefix is publicly known). If the masked field's display
in Reports is itself a leak, the right answer is to remove the field
from those reports — encrypting it isn't possible.

---

## Example 3 — "Healthcare org with regulator-audited key custody"

**Context.** Hospital network bound by HIPAA + state-level regulator
that requires the encryption keys to be in customer-controlled HSM
infrastructure. Auditor wants annual proof that Salesforce never
holds the keys.

**Right answer.** **Cache-Only Key Service (CCKM)** with the customer's
existing AWS CloudHSM. Salesforce fetches the key just-in-time when
encryption / decryption is needed; never persists it.

**Tradeoff documented.** A CloudHSM outage causes Salesforce
encryption operations to fail. The architecture review accepts this:
"For our compliance posture, key custody outranks availability. An
HSM outage that lasts long enough to impact Salesforce write
availability would also block our other systems that share the HSM —
the failure is correlated, not multiplicative."

**Operational runbook.** HSM availability target: 99.95 %. Salesforce
write availability during HSM outage: 0 % (expected). Recovery: HSM
restoration restores Salesforce immediately as the cache repopulates.

---

## Example 4 — "Audit retention required to be 7 years"

**Context.** SOX-bound finance org needs 7-year retention on changes to
contract financial fields (Amount, CloseDate, Probability on
Opportunity).

**Right answer.** **Field Audit Trail license** + per-object
`HistoryRetentionPolicy`:

```xml
<!-- Opportunity.object-meta.xml -->
<HistoryRetentionPolicy>
    <archiveAfterMonths>18</archiveAfterMonths>
    <archiveRetentionYears>7</archiveRetentionYears>
    <description>SOX retention on contract financial fields</description>
</HistoryRetentionPolicy>
```

After 18 months, history rows move from `OpportunityHistory` (queryable
in Reports) to `FieldHistoryArchive` (queryable via SOQL). After 7
years they're deleted.

**Storage projection.** Estimate based on history-row-per-edit volume.
History rows in `FieldHistoryArchive` are billed differently from
standard data storage — confirm with Salesforce account team before
finalizing.

---

## Example 5 — "Block out-of-policy session via real-time monitoring"

**Context.** Enterprise wants to terminate user sessions that are
flagged as suspicious (geolocation anomaly, impossible-travel,
high-volume API export) in real time, not just log them.

**Right answer.** **Event Monitoring** license + **Real-Time Event
Monitoring** subscription on the Pub/Sub API + a **Transaction Security
Policy** that consumes the SessionHijackingEvent / ApiAnomalyEvent
streams and triggers a block action.

**Wrong instinct.** Build a custom Apex trigger that polls Login
History every 5 minutes and disables suspicious users.

**Why it's wrong.** Polling cannot react in real time; blocks happen
after the damaging API export already completed. TSP is the only
in-flight block mechanism.

---

## Anti-Pattern: Recommending Shield without confirming licenses

```
User: "How do I encrypt the Patient__c.SSN__c field?"
Wrong: "Setup → Platform Encryption → Encryption Policy → New …"
```

**What goes wrong.** The org doesn't have the Platform Encryption PSL.
The user clicks through Setup, finds no Encryption Policy menu item,
files a support ticket, and three weeks later procurement realizes a
Shield license has to be bought. The design depended on a feature
that wasn't licensed.

**Correct.**

```
"Before any Setup work, confirm Platform Encryption PSL: Setup →
Company Information → Permission Set Licenses. If absent, the design
is blocked on procurement; let me know once it's confirmed and we'll
continue."
```
