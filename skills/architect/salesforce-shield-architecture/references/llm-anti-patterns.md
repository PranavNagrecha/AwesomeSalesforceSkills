# LLM Anti-Patterns — Salesforce Shield Architecture

Mistakes AI coding assistants commonly make when advising on Shield
architecture. The consuming agent should self-check against this list
before recommending a Shield design or feature setup.

---

## Anti-Pattern 1: Recommending Shield Platform Encryption setup as if it were a free feature

**What the LLM generates.** "To encrypt SSN__c, go to Setup → Platform
Encryption → Encryption Policy → New …"

**Why it happens.** Shield Platform Encryption is documented in the
public Salesforce Help center alongside free features. The LLM doesn't
internalize that it's a paid PSL with a separate purchase requirement.

**Correct pattern.** Always begin with a license-confirmation gate:

```
Before any Setup work, confirm Platform Encryption permission set
license: Setup → Company Information → Permission Set Licenses. If
absent, the design is blocked on procurement.
```

**Detection hint.** Any Shield recommendation that jumps straight into
"Setup → Platform Encryption" / "Setup → Event Monitoring" / "Setup →
Field Audit Trail" without a license check is incomplete.

---

## Anti-Pattern 2: Probabilistic encryption on a field that needs filtering

**What the LLM generates.** "Encrypt SSN__c using the default
probabilistic scheme for maximum security."

**Why it happens.** "Maximum security" sounds correct; the LLM
doesn't surface the tradeoff that probabilistic encryption blocks
filterability.

**Correct pattern.** Always ask what the field is used for in queries.
If it needs **exact-match** filtering (`=`, `IN`) → deterministic. If it
is display/audit/archival only → probabilistic. If it needs **sorting,
ranges, or wildcard search** → neither scheme helps; see Anti-Pattern 2b.
Document the choice in the design.

**Detection hint.** Any Platform Encryption recommendation with no
discussion of "what queries run against this field?" is missing the
central decision.

---

## Anti-Pattern 2b: Claiming deterministic encryption enables sorting / ORDER BY

**What the LLM generates.** A scheme-comparison table whose deterministic
row reads "equality filter YES; **sort YES**", frequently with an
invented mechanism attached — "lexicographic on ciphertext" — and a
decision rule of the form "if the field is filtered, sorted, or
grouped → deterministic."

**Why it happens.** Two things compound. First, **capability bundling**:
"filterable" and "sortable" travel together for ordinary database
columns, so once the model establishes that deterministic restores
filtering it extends the same win to sorting without separate evidence.
Second — and this is the diagnostic tell — the model *justifies* the
extension by reasoning about the mechanism and gets the reasoning
backwards. Determinism guarantees **equal plaintext → equal ciphertext**.
That is an equality property. It carries no ordering information
whatsoever: AES ciphertexts for "Adams" and "Zeller" collate in an order
unrelated to A-before-Z. "Lexicographic on ciphertext" is not a
misremembered fact; it is a fabricated mechanism invented to support a
conclusion the model already reached. Fabricated mechanisms read as
*more* authoritative than bare claims, so this survives review.

The cost is high because it is load-bearing: encryption scheme is chosen
at design time, cannot be changed on a populated field without
re-encrypting every row, and the failure surfaces only when someone tries
to sort a list view in UAT.

**Correct pattern.**

```text
Deterministic encryption restores:   = and IN  (exact match)
                                      filtering in reports and list views
                                      (case-sensitive or case-insensitive)

NO scheme restores:                   ORDER BY / sorting
                                      ranges (<, >, BETWEEN)
                                      LIKE / wildcard

Salesforce: "You can't sort records in list views by fields that contain
encrypted data." Encrypted fields also can't be referenced in filtering
or sorting contexts in flows, orchestrations, and processes.

If the business needs to sort or range-scan the value, the answer is an
unencrypted sortable surrogate (bucket, masked prefix, derived sort key)
— not a different encryption scheme.
```

**Detection hint.** Grep any encryption design for `sort` or `ORDER BY`
in the same table row, sentence, or bullet as `deterministic` — the
pairing is wrong every time. Then apply the general rule this instance
illustrates: when generated guidance supplies a *mechanism* for a
capability claim, check the mechanism actually entails the capability.
"Equal inputs give equal outputs" entails equality matching and nothing
about order; any ordering claim built on it is fabricated regardless of
how fluently it is written.

---

## Anti-Pattern 3: Suggesting encryption of formula or roll-up summary fields

**What the LLM generates.** "Add MaskedSSN__c (formula) and
TotalEncryptedSpend__c (roll-up summary) to the Encryption Policy."

**Why it happens.** "Encrypt sensitive-looking fields" is a reasonable
heuristic; the LLM doesn't surface that derived fields can't be
encrypted because their evaluation requires plaintext inputs.

**Correct pattern.** Encrypt the **source** fields. The formula /
roll-up evaluator decrypts inputs at evaluation time; the derived
output is intrinsically less sensitive (or, if it is sensitive, the
fix is to redesign the formula, not to encrypt the result).

**Detection hint.** Any Encryption Policy field list containing a
formula, roll-up summary, auto-number, or unique-indexed external ID
is wrong. Setup will reject it.

---

## Anti-Pattern 4: Treating "Shield" as one product with one license

**What the LLM generates.** "If your org has Shield, you can use
Platform Encryption, Event Monitoring, and Field Audit Trail."

**Why it happens.** Marketing materials say "Salesforce Shield" as if
it's a single SKU. It isn't — it's three separately-sold products.

**Correct pattern.** Each component has its own license: `Platform
Encryption`, `Event Monitoring`, `Field Audit Trail`. Recommend
per-component, justify each against a compliance driver.

**Detection hint.** Any sentence that uses "Shield" as a single
license check is incomplete; the LLM should always disambiguate which
of the three is in scope.

---

## Anti-Pattern 5: CCKM recommendation without availability tradeoff disclosure

**What the LLM generates.** "Use Cache-Only Key Service for the
strongest security posture."

**Why it happens.** CCKM is documented as the strongest option; the
LLM emits the recommendation without surfacing the cost.

**Correct pattern.** CCKM's tradeoff is explicit: customer HSM outage
→ Salesforce encryption operations fail until the HSM (or cache)
recovers. Always disclose this so the org can decide whether the
custody benefit outweighs the new failure mode.

**Detection hint.** Any CCKM recommendation that doesn't include the
phrase "HSM outage" or "availability tradeoff" is missing half the
decision.

---

## Anti-Pattern 6: "Configure Field Audit Trail retention in Setup"

**What the LLM generates.** "Setup → Field Audit Trail → Set
Retention to 10 years."

**Why it happens.** The LLM assumes a Setup UI exists for retention
because Setup UIs exist for almost everything else.

**Correct pattern.** Retention is set per object via the
`HistoryRetentionPolicy` element in the object's metadata XML,
deployed via Metadata API or Tooling API. There is no Setup UI for
this; the Setup page only enables / disables the feature.

**Detection hint.** Any Field Audit Trail retention recommendation
without an XML snippet (or a metadata-deploy command) is wrong.

---

## Anti-Pattern 7: Recommending Real-Time Event Monitoring via the streaming API CometD channel

**What the LLM generates.** "Subscribe to /event/SessionHijackingEvent
via CometD …"

**Why it happens.** Older training data references CometD as the
real-time monitoring channel. The platform migrated to Pub/Sub API
in stages across Spring '23 → Summer '24.

**Correct pattern.** Subscribe via Pub/Sub API (gRPC). Or use
Transaction Security Policies for declarative in-flight blocking,
which consumes the same events natively.

**Detection hint.** Any RTEM subscriber recipe that uses CometD or
the legacy `/event/` URL prefix is dated and probably broken.

---

## Anti-Pattern 8: Buying all three Shield components for "best practice"

**What the LLM generates.** "Best practice is to enable Shield —
Platform Encryption, Event Monitoring, and Field Audit Trail — for any
production org handling regulated data."

**Why it happens.** "Buy the bundle" is the simpler answer; the LLM
doesn't push back to ask which of the three actually addresses a
specific control.

**Correct pattern.** Each component must be tied to a named compliance
driver (regulator, contract clause, internal control). If the org
doesn't have a driver for one of the three, buying it is a budget
smell, not a best practice.

**Detection hint.** Any "enable all three Shield components"
recommendation without a per-component justification table is
overselling.
