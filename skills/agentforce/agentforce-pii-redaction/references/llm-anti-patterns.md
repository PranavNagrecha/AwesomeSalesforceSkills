# LLM Anti-Patterns — Agentforce PII Redaction

Mistakes AI coding assistants reliably make when asked to "handle PII in an
Agentforce agent." Each entry: what gets generated, why the model produces it,
the corrected pattern, and how a reviewer spots it.

---

## Anti-Pattern 1: "The Einstein Trust Layer masks PII for you"

**What the LLM generates:** an architecture answer that ends at *"Salesforce's
Einstein Trust Layer automatically masks PII before prompts reach the LLM, so no
application-level redaction is required."* Often with a confident citation to
the Trust Layer overview page.

**Why it happens:** the Trust Layer marketing and overview documentation
describes masking as a core pillar, and it is — for embedded generative AI
features. The exception for agents lives on a separate limitations page that is
far less represented in training data than the overview. The model reproduces
the headline and misses the carve-out.

**Correct pattern:** for **agents**, pattern-based and field-based LLM data
masking is disabled ([Data Masking Limitations in
Agentforce](https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5)).
State what the Trust Layer *does* give agents — zero retention at the provider,
protection in transit, audit trail — and then design application-level redaction
for prompt content.

**Detection hint:** any answer that mentions Trust Layer masking and Agentforce
agents in the same breath without the word "disabled" or "not applied to
agents." Grep generated design docs for "Trust Layer" and check the sentence
around it.

---

## Anti-Pattern 2: `JSON.serialize(sObjectRecord)` as prompt context

**What the LLM generates:**

```apex
Contact c = [SELECT Id, Name, Email, Phone, SSN__c FROM Contact WHERE Id = :cid];
res.context = JSON.serialize(c);
```

**Why it happens:** it is the shortest correct-looking Apex that produces a
string for a prompt, and it appears throughout integration examples where
shipping the whole record is the point. The model optimises for "produce
serialisable context" and does not model the prompt as a disclosure boundary.

**Correct pattern:** serialise a purpose-built DTO whose fields are all
individually safe:

```apex
res.context = JSON.serialize(PIIRedactor.toContext(c));
```

The DTO makes field addition a deliberate act. Adding a field to the SOQL no
longer changes what the model sees.

**Detection hint:** `JSON.serialize(` applied to anything typed as an SObject or
`List<SObject>` inside a class that is registered as an agent action. This is a
one-line grep and belongs in CI.

---

## Anti-Pattern 3: Enforcing PII policy through subagent instructions

**What the LLM generates:** a subagent Scope or instruction (subagents were
called topics before April 2026) such as *"Never reveal the customer's social
security number, credit card number, or full address."* Presented as the
redaction control.

**Why it happens:** the model has strong priors that LLM behaviour is steered by
instructions, and Agentforce genuinely does use natural-language instructions for
routing and behaviour. It generalises "instructions control behaviour" into
"instructions control data exposure."

**Correct pattern:** an instruction cannot un-send data that is already in the
prompt window. If the SSN is in context, it has already left your org. Redaction
must happen upstream, in the context provider. Instructions are a *defence in
depth* layer for output phrasing, never the primary control.

**Detection hint:** the design has no code-level redaction and the compliance
control is a quoted string from a Scope field. Ask: "if the model ignores this
sentence once, what breaks?" If the answer is "we disclose an SSN," it is not a
control.

---

## Anti-Pattern 4: Ad-hoc regex per call site

**What the LLM generates:** each generated action gets its own inline pattern:

```apex
if (input.matches('.*\\d{3}-\\d{2}-\\d{4}.*')) { /* ... */ }
```

repeated, slightly differently, in four classes.

**Why it happens:** the model generates each file in isolation and has no
representation of "the rest of this codebase." Locality wins over consistency in
single-file generation.

**Correct pattern:** one detector class, tested, with the patterns as named
constants — plus a checksum guard for categories with high false-positive rates
(Luhn for card numbers). Call sites call the detector; they do not own patterns.

**Detection hint:** count distinct regex literals containing `\d{3}` or
`{13,19}` across the repo. More than one means the patterns will diverge.

---

## Anti-Pattern 5: Logging the raw value next to the masked one

**What the LLM generates:**

```apex
System.debug('Original: ' + c.Email + ' | Masked: ' + masked);
```

nearly always as part of the same response that implements the masking, framed
as helpful debugging.

**Why it happens:** "show your work" is a strong instinct in generated code, and
`System.debug` before/after is the canonical way to demonstrate a
transformation. The model is optimising for demonstrability, not for the fact
that debug logs are a durable store with its own access model.

**Correct pattern:** demonstrate correctness in a unit test asserting on the
transformed value only. Never place the raw value in a log line. Audit logging
records the field API name and the strategy, never the datum
(`references/examples.md` Example 5).

**Detection hint:** `System.debug` anywhere in the redaction package. Make it a
CI failure, not a review comment — this is introduced by the person who best
understands the control, at the moment they are most focused on something else.

---

## Anti-Pattern 6: Deterministic, permanent tokens presented as anonymisation

**What the LLM generates:**

```apex
String token = 'CONTACT_' + EncodingUtil.convertToHex(
    Crypto.generateDigest('SHA-256', Blob.valueOf(c.Email)));
```

described as "anonymising the contact."

**Why it happens:** hashing reads as anonymisation in most engineering contexts,
and the model has seen this shape in password and cache-key code where
determinism is the goal.

**Correct pattern:** an unsalted hash of a low-entropy identifier is
*pseudonymisation at best and reversible at worst* — the space of valid email
addresses in your org is small enough to enumerate, and the space of SSNs is
under a billion. Salt with a per-session or per-org secret held in Protected
Custom Metadata or a named credential, and scope the token's lifetime
deliberately (see gotcha 8).

**Detection hint:** `Crypto.generateDigest` whose input is only the raw value,
with no salt concatenated, in a class that describes itself as anonymising.

---

## Anti-Pattern 7: Classifying fields but not the grounding corpus

**What the LLM generates:** a thorough field-classification register for
`Contact`, `Account`, and `Case`, and no mention of Knowledge articles, files,
Chatter, or Data Cloud retrievers.

**Why it happens:** "classify PII fields" maps cleanly onto the object/field
model the assistant already reasons about. Retrieval corpora are a different
mental model and are not part of the schema, so they fall outside the frame.

**Correct pattern:** every retrievable source is prompt context. Inventory the
retrievers alongside the objects, scan the corpus, and gate at publish time
(`references/examples.md` Example 4).

**Detection hint:** the register has zero rows that are not `Object.Field`. If
the agent has any grounding or retrieval configured, that is an incomplete
inventory.

---

## Anti-Pattern 8: Treating `WITH USER_MODE` as the redaction control

**What the LLM generates:** a context query annotated `WITH USER_MODE` (or
`Security.stripInaccessible`) accompanied by a comment such as *"enforces FLS so
sensitive fields are automatically excluded."*

**Why it happens:** both are genuinely the right answer to the adjacent
question — Salesforce security guidance emphasises them heavily, and the model
has a strong association between "Apex + sensitive data" and "enforce FLS." It
substitutes the well-covered control for the poorly-covered one.

**Correct pattern:** keep `WITH USER_MODE` — it is correct and required — and
add DTO projection on top. FLS answers "may this user read it"; redaction
answers "does it belong in a prompt." The agent's running user usually passes
the first test on every field you care about.

**Detection hint:** the only PII-related construct in a context provider is a
security annotation, with no DTO or field allow-list.

---

## Anti-Pattern 9: Inventing masking configuration that does not exist

**What the LLM generates:** confident, well-formed configuration that is not
real — a `<dataMaskingPolicy>` element inside `GenAiPlannerBundle`, a
`maskingProfile` attribute on a subagent, a `@PIIRedacted` Apex annotation, or an
`EinsteinTrustLayer.mask()` Apex method.

**Why it happens:** this is the highest-risk failure in the Agentforce domain
generally. The product has been renamed repeatedly (Einstein Copilot →
Agentforce), the metadata types changed shape (`GenAiPlanner` →
`GenAiPlannerBundle`), and plausible-looking names interpolate cleanly from
neighbouring APIs. The model produces syntactically valid metadata for an API
that was never shipped.

**Correct pattern:** verify every metadata type and Apex symbol against the
[Agentforce metadata type
list](https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html)
or the Metadata Coverage Report before writing it down. The real types for an
agent are `AiAuthoringBundle`, `Bot`, `BotVersion`, `ConversationVariable`,
`GenAiFunction`, `GenAiPlannerBundle`, and `GenAiPlugin`. There is no
agent-scoped masking metadata, which is consistent with masking being disabled
for agents in the first place.

**Detection hint:** any masking configuration expressed as agent metadata. If
the control lives in metadata rather than in your Apex, it is almost certainly
invented — deploy it to a scratch org before it reaches a design doc.

---

## Anti-Pattern 10: A "redaction complete" claim with no negative test

**What the LLM generates:** a redaction class plus a test that asserts the
masked output is correct — `assertEquals('j***@acme.com', masked)` — and calls
the work done.

**Why it happens:** the positive assertion is the natural unit test for a pure
function, and it does prove the transformation. It does not prove the raw value
cannot reach the prompt by another route.

**Correct pattern:** pair every positive test with a negative one at the
boundary, asserting the raw value does not appear in the serialised context:

```apex
String ctx = CustomerContextProvider.run(reqs)[0].contextJson;
Assert.isFalse(ctx.contains('123-45-6789'), 'SSN must never reach prompt context');
Assert.isFalse(ctx.contains('jordan@acme.com'), 'full email must never reach prompt context');
```

The negative test is what survives someone adding a field to the SOQL two
sprints later.

**Detection hint:** the test class contains no `isFalse`/`contains` assertion
over the assembled context string. Positive-only test coverage on a redaction
boundary is coverage of the happy path only.
