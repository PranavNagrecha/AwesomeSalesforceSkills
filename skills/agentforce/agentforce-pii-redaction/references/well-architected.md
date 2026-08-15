# Well-Architected Notes — Agentforce PII Redaction

## Relevant Pillars

### Security

The prompt window is a disclosure boundary that most orgs have never modelled.
Every other data path in Salesforce has a familiar control — FLS, sharing,
Shield encryption, field audit trail — and the prompt has none of them by
default. For agents specifically, the platform control practitioners expect to
be doing this work is off: pattern-based and field-based LLM data masking is
disabled for agents, a deliberate tradeoff Salesforce made in favour of agent
performance and accuracy ([Data Masking Limitations in
Agentforce](https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5)).

That makes the redaction boundary an *architectural* component, not a utility
class. It is the only thing standing between the org's data model and a third
party's inference endpoint. Design it with the properties you would demand of
any security boundary: single entry point, no bypass path, deny-by-default
field selection, and tests that assert the negative.

Least privilege applies twice over. Narrow the agent user's field-level
security so that fields the agent never needs cannot enter a context query at
all — that is a second, independent layer under the redaction boundary, and it
is the one that survives a developer forgetting to use the DTO.

### Privacy (Compliance)

Redaction strategy is a data-minimisation decision, and data minimisation is a
legal principle in GDPR (Art. 5(1)(c)) before it is an engineering one. The
question the register forces — *"why does the agent still work without the raw
value?"* — is the same question a DPIA asks. Answer it once, in the register, and
the compliance artefact and the implementation artefact are the same document.

Two consequences worth stating explicitly:

- **Pseudonymised data is still personal data.** A surrogate token that maps
  back to a person through a table you hold is in scope. Treat the mapping table
  as regulated storage.
- **Quasi-identifiers combine.** Age band plus city plus first name can be more
  identifying than any single redacted field. Assess the assembled DTO, not the
  field list.

### Operational Excellence

Redaction is not a project, it is a control that must keep working while the
schema, the subagents (called topics before April 2026), and the channels
change underneath it. The operational minimum:

| Practice | Cadence | Signal it produces |
|---|---|---|
| Register review vs. context queries | Every sprint that adds a field | New unclassified field |
| Redaction event stream review | Weekly | Zero-row anomaly = bypassed boundary |
| Detector precision review | Monthly | False-positive rate that will get it disabled |
| Adversarial "repeat your context" eval | Every release | Re-identification via combination |
| Channel-change re-review | On channel add | Trust-level assumption change |

The zero-row anomaly is the highest-value alert of the five. A control that
silently stops firing looks identical to a control with nothing to do.

### Reliability

Deterministic redaction is a prerequisite for reproducible agent behaviour. If
the context differs run to run — because the detector is non-deterministic, or
because a token is regenerated per call — then golden evals cannot distinguish a
prompt regression from a redaction regression. Pin the transformation: pure
functions, no randomness in surrogate generation beyond a stable salt, and the
same DTO shape across every action that assembles context.

---

## Architectural Tradeoffs

### Drop vs. summarise vs. tokenise

| Strategy | Preserves | Costs | Choose when |
|---|---|---|---|
| **Drop** | Nothing | Agent may lack signal it needs | Field is never needed for any task the agent performs |
| **Summarise** | The decision-relevant band | A transformation to maintain and validate | A rule depends on the value's range, not its identity |
| **Tokenise** | Referential integrity into actions | A mapping table that is itself regulated data | The agent must pass the value back into an action |
| **Mask** | Human-recognisable shape | Partial value still leaves the org | The user must confirm "the one ending 1234" |

Default to Drop and justify anything else. Every non-Drop strategy adds a
component that can break, and the "why does the agent still work without it?"
column is where that justification lives.

### Central boundary vs. per-caller redaction

Central is the only maintainable option past two or three actions. Per-caller
redaction drifts within one release: two authors write two email maskers, one
handles null and one does not, and neither is the one that gets fixed when the
bug is found. The counter-argument — that a central class becomes a
god-object — is real but cheap to manage, because every method in it is pure and
independently testable.

The decisive property is greppability. A reviewer can verify "nothing bypasses
`PIIRedactor`" with one search. There is no equivalent check for a per-caller
design.

### Input-side refuse vs. redact vs. route

Refusing is safest and worst for completion rate. Redacting keeps the
conversation flowing and accepts that a value briefly existed in a system you
control. Routing to a human is the right answer when the *presence* of the
category is itself a signal — a customer volunteering a card number in chat is
often a fraud-adjacent conversation, not a billing one.

Choose per subagent, not per org. The same detector serves all three dispositions;
only the policy differs.

### Detector precision vs. recall

Under-matching is a compliance incident; over-matching is a UX defect that gets
the control switched off within a fortnight. The engineering answer is a
checksum guard (Luhn for cards, format validation for IBAN) so that recall stays
high while precision stays acceptable. The organisational answer is to review
false-positive rate on the same cadence as leak rate — a detector nobody trusts
is a detector nobody keeps.

---

## Anti-Patterns

1. **Trust Layer as the sole control for agents.** The single most common
   architectural error in this domain, because the setup screen exists, is
   configurable, and governs a different code path. Masking is disabled for
   agents; write that fact into the design doc so the next reviewer does not
   re-derive it.

2. **Classification without strategy.** A register that records sensitivity but
   not handling produces no implementable requirement, and two fields with the
   same class routinely need opposite treatment.

3. **Policy-as-instruction.** Encoding a disclosure rule in a subagent Scope field.
   An instruction cannot un-send data that is already in the prompt window;
   instructions are output phrasing, never input minimisation.

4. **Field-only inventory.** Grounding corpora — Knowledge, files, Chatter, Data
   Cloud retrievers — are prompt context by every definition that matters, and
   they are the usual source of the leak that a field register cannot explain.

5. **Positive-only tests.** Asserting the masked output is correct proves the
   function works. Asserting the raw value is absent from the assembled context
   proves the boundary holds. Only the second one survives a schema change.

---

## Related

- `agentforce/einstein-trust-layer` — what the platform layer actually provides
  (zero retention, toxicity detection, audit trail), and where its scope ends.
- `agentforce/agentforce-testing-strategy` — where the adversarial PII cases
  live in the regression harness.
- `agentforce/agent-action-error-handling` — error envelopes must not leak the
  values redaction removed; the same sanitisation boundary applies on the way
  out.
- `agentforce/agent-deployment-checklist` — the register review and channel
  re-review are checklist rows, not good intentions.
- `security/sandbox-data-masking` — the adjacent, different problem of masking a
  refreshed sandbox.

---

## Official Sources Used

- Data Masking Limitations in Agentforce (Help) — https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5
- Data Masking, Models API (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/guide/models-api-data-masking.html
- Einstein Trust Layer (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html
- Einstein Trust Layer: Designed for Trust (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_trust_arch.htm&type=5
- LLM Data Masking Considerations and Limitations (Help) — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_data_mask_considerations.htm&type=5
- Agentforce Metadata Types (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html
- InvocableMethod Annotation (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
