# Well-Architected Notes — Agent Action Error Handling

## Relevant Pillars

### Reliability

An agent's control flow is decided by a language model reading the output of
your action. That makes the response envelope a **control-plane artefact**, not a
convenience. If the envelope cannot express "stop trying", the planner's default
behaviour on an unsatisfied goal is to try again — so an under-specified error
contract does not merely produce a poor message, it produces a loop that
consumes turns, latency, and tokens until the conversation is abandoned.

Two properties make the envelope reliable:

- **Total.** Every code path returns a `Response`. Nothing throws past the
  invocable boundary, because the platform requires one output per input
  ([InvocableMethod
  Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm)).
- **Decidable.** Every field the subagent instructions (called topic
  instructions before April 2026) branch on is a stable enum
  string, never free text. Localisation, rewording, and tone edits then cannot
  change routing.

The uncatchable-exception boundary is where reliability is actually won or lost.
`LimitException` terminates the transaction regardless of your `catch`, so
bulk-safety is an error-handling requirement rather than a separate performance
concern. An action that is not bulk-safe has an error path you cannot implement.

### Security

Raw platform errors are a disclosure channel. `DmlException` messages embed
field API names, record Ids, and — when a validation rule's error text
interpolates a field — actual data values. Piped into a user-visible field, they
land in a conversation transcript that may be stored, exported, and reviewed by
people with no entitlement to the underlying record.

Sanitisation belongs at the boundary and happens exactly once: `userMessage` is
authored copy, the raw exception goes to the log. This is the same boundary
discipline as `agentforce/agentforce-pii-redaction` — data leaves the org only
through a shape you designed.

Second-order: an error taxonomy that distinguishes `NO_ACCESS` from `NOT_FOUND`
is itself an information leak in adversarial contexts. A user probing for
record existence learns from the difference. For low-trust channels (guest
Experience Cloud, public messaging) collapse the two into one code.

### Operational Excellence

`reasonCode` is the join key between three systems that are otherwise
unconnected: Apex, the subagent instructions, and the observability stack. Governing
it as data — a Custom Metadata Type rather than scattered string literals — turns
three independently-drifting artefacts into one versioned contract, and makes
"which failure mode is growing?" a groupable question rather than a log-grep.

The operational signal to watch is the **`UNKNOWN` rate**. It is the direct
measure of classification debt: every `SYSTEM_ERROR/UNKNOWN` is an error class
nobody has yet taught the agent to handle. A rising `UNKNOWN` share after a
release means an upstream contract changed. Alert on the ratio, not the count.

### Performance

Each failed turn is a full planner round-trip: model inference, action
invocation, and another inference to decide what to do with the result. A retry
loop on a terminal error is three or four of those before the user gives up. The
`retryable` flag is therefore a latency and cost control as much as a
correctness one — classifying validation failures as terminal removes the most
expensive wasted work in the system.

---

## Architectural Tradeoffs

### Typed envelope vs. plain string return

A plain `List<String>` is less code and the planner can read it. It cannot be
branched on deterministically, cannot be grouped in a dashboard, and cannot
distinguish retryable from terminal. The envelope costs about twenty lines per
action and buys the entire control plane. Take the envelope for any action that
can fail in more than one way — which is all of them.

### Reason codes in Custom Metadata vs. an Apex enum

| | Apex enum | Custom Metadata Type |
|---|---|---|
| Compile-time safety | Yes | No (test-enforced instead) |
| Readable by instruction generation | No | Yes |
| Groupable in reports | No | Yes |
| Deployable and diffable | Yes | Yes |
| Cost | Free | One object, one test |

CMDT wins because two of the three consumers are outside Apex. Recover the lost
compile-time safety with a test asserting every emitted literal is registered.

### Fine-grained codes vs. a small stable set

Too few codes and the subagent instructions cannot differentiate behaviour. Too
many and every code needs its own instruction, the instruction block becomes
unmaintainable, and the planner's adherence degrades as the rule list grows.

The workable heuristic: **a reason code earns its existence only if the agent
does something different because of it.** Two codes that produce identical agent
behaviour should be one code with two log severities.

### Retry in Apex vs. retry by the planner

Retrying inside the action (a loop with backoff around a callout) is invisible
to the planner and burns the transaction's remaining callout budget and CPU
time. Retrying at the planner level costs a full inference round-trip but keeps
the user informed and respects the conversation's own timing.

Rule of thumb: retry *once*, in Apex, for sub-second transient failures such as
a row lock. Anything with a human-perceptible wait should surface as
`retryable = true` and let the planner narrate it.

### Distinguishing NOT_FOUND from NO_ACCESS

Genuinely useful for internal users — "you can't see it" and "it doesn't exist"
lead to different next steps. Genuinely an enumeration oracle on a public
channel. Decide per channel, not per action, and record the decision in the
action's design notes so a channel expansion re-opens it.

---

## Anti-Patterns

1. **Throwing from an invocable.** Breaks the size-and-order contract for the
   entire batch, not just the failing request, and gives the planner a framework
   error it cannot reason about.

2. **`getMessage()` as `userMessage`.** A disclosure channel and a routing
   fragility in one line. Message text is localised and rewritten between
   releases; enum status codes are not.

3. **Boolean success.** Cannot express the retryable × locus-of-control matrix
   the planner needs, so the planner falls back to retrying.

4. **Per-row DML in the invocable loop.** Produces an uncatchable
   `LimitException` under bulk invocation, defeating every `catch` below it.
   Bulk-safety is a prerequisite for error handling, not an optimisation.

5. **Envelope without instructions.** A perfectly typed response that no
   instruction branches on is decoration. The contract has two halves and the
   second one is written in English.

6. **Retryable mutations without idempotency.** A retried create is a duplicate
   record; a retried timeout may be a duplicate upstream write.

---

## Related

- `templates/agentforce/AgentActionSkeleton.cls` — canonical action shape; one
  verb, bulk-safe, errors returned rather than thrown.
- `templates/agentforce/AgentTopic_Template.md` — where the per-reason-code
  instruction block lives.
- `templates/apex/ApplicationLogger.cls` — the sink for raw exceptions.
- `templates/apex/tests/MockHttpResponseGenerator.cls`,
  `templates/apex/tests/BulkTestPattern.cls` — forcing the callout and bulk
  branches.
- `agentforce/custom-agent-actions-apex` — authoring the action itself
  (schema, labels, security context).
- `agentforce/agent-action-unit-tests` — the test suite that forces each branch.
- `agentforce/agentforce-testing-strategy` — where error-path cases sit in the
  regression harness.
- `agentforce/agentforce-pii-redaction` — the same sanitisation boundary,
  applied to prompt context rather than error text.

---

## Official Sources Used

- InvocableMethod Annotation (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Create Custom Actions Using Apex InvocableMethod (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html
- Agentforce Actions (Agentforce Developer Guide) — https://developer.salesforce.com/docs/ai/agentforce/guide/get-started-actions.html
- Agentforce Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html
- Apex Actions (Actions Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_action.meta/api_action/actions_obj_apex.htm
- Design Managed Apex for Agentforce (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_manpkgs_agent.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
