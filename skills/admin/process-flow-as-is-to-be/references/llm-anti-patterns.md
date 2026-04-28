# LLM Anti-Patterns — Process Flow As-Is To-Be

Mistakes AI assistants commonly make when generating As-Is / To-Be process maps. Each entry: what the LLM produces wrong, why it happens, the correct pattern, and how to detect it.

---

## Anti-Pattern 1: Producing a To-Be without an As-Is

**What the LLM generates:** When asked to "map the process", the LLM produces a clean, idealised To-Be diagram with no As-Is at all. Pain points are missing because there is nothing to compare against. The To-Be reads like a brochure.

**Why it happens:** LLMs are biased toward producing "good" outputs. The As-Is is messy by definition; the To-Be is aspirational and easier to write. The LLM defaults to the easier task.

**Correct pattern:**

```
1. Capture As-Is first with pain-point annotations per step.
2. Derive To-Be steps from As-Is pain points (each pain point should
   correspond to at least one To-Be improvement).
3. Tag To-Be steps with automation tiers AFTER the As-Is is complete.
```

**Detection hint:** If the map has no `as_is_steps[]` or the array is empty, the As-Is was skipped. If To-Be steps lack a corresponding pain point in the As-Is, the To-Be is unanchored.

---

## Anti-Pattern 2: Hallucinating actors

**What the LLM generates:** Swim lanes labelled with generic role names that do not exist in the actual organization ("Process Owner", "Stakeholder", "End User"). When the practitioner actually has an SDR, an AE, a Sales Manager, a Deal Desk Analyst, the LLM collapses them into one "Sales User" lane.

**Why it happens:** Generic role labels are the path of least resistance when the LLM does not have specific role information. Without prompting for actor names, the LLM invents plausible-sounding generic roles.

**Correct pattern:**

```
Before drawing lanes, list every actor by their actual title or system
name. Confirm with the practitioner. Each unique actor gets its own lane.
Generic labels like "User" are only acceptable when the process truly
does not differentiate by role.
```

**Detection hint:** If lane labels include "User", "Stakeholder", "Process Owner" and the org has named roles available, the LLM hallucinated the labels. Re-prompt for actual role names.

---

## Anti-Pattern 3: Treating Flow as the answer for every step

**What the LLM generates:** A To-Be where every automated step is tagged `[FLOW]`. Steps that need callouts, batch processing, complex orchestration, or approvals are all labelled `[FLOW]` because the LLM has been trained on "Flow first" guidance.

**Why it happens:** The Salesforce documentation strongly recommends Flow as the default. LLMs internalize this as "always Flow". The decision tree's escalation criteria (callouts, > 10s logic, > 50k records, custom exception handling) are not consistently honored.

**Correct pattern:**

```
For every automated step, walk standards/decision-trees/automation-selection.md
top-to-bottom. Stop at the first branch that resolves the technology choice.
Cite the branch in the annotation: e.g.,
  "Validate credit limit [FLOW] — automation-selection.md Q2"
  "Process 100k orders nightly [APEX] — automation-selection.md Q10"
  "Manager sign-off [APPROVAL] — automation-selection.md cheat sheet"
```

**Detection hint:** A To-Be where 100% of steps are `[FLOW]` is suspicious. Real processes typically have a mix of `[FLOW]`, `[APEX]`, `[APPROVAL]`, `[INTEGRATION]`, and `[MANUAL]` tiers. Re-prompt to walk the decision tree per step.

---

## Anti-Pattern 4: Missing approval-process candidates

**What the LLM generates:** Approval steps are buried inside a `[FLOW]` annotation as a "decision element". The Approval Process tier is never used. The map loses the auditability and approver-history features.

**Why it happens:** LLMs treat approvals as a logical branch (if/else) rather than a distinct platform feature. The Approval Process is a dedicated tool with its own metadata type (`ApprovalProcess`) and its own UX (the Approval History related list, mass approval, recall).

**Correct pattern:**

```
Tag approval steps as [APPROVAL] when:
  - There is a defined approver (manager, deal desk, finance)
  - The step requires audit trail (regulatory, financial threshold)
  - The step needs recall or rejection-with-reason
  - The step is the gate before another action proceeds

Reserve [FLOW] for the orchestration around the approval, not the
approval itself.
```

**Detection hint:** A To-Be with no `[APPROVAL]` tier in a process that mentions "manager sign-off", "approval needed", "review before proceeding", or financial thresholds is missing the Approval Process candidate. Re-prompt to identify approval steps.

---

## Anti-Pattern 5: Conflating swim lanes with phases

**What the LLM generates:** Lanes labelled "Discovery", "Qualification", "Proposal", "Close" instead of actor names. The mapper has confused stage progression (which is a sales-process-mapping concern) with actor responsibility (the process flow concern).

**Why it happens:** LLMs have stronger pattern recognition for sales stages than for generic processes. When asked to map any process, the LLM reaches for the sales-stage template.

**Correct pattern:**

```
Lanes are actors (vertical axis). Time / sequence is the horizontal axis.
A swim lane labelled "Negotiation" is a phase, not an actor — re-frame.
For sales-stage processes, use the sales-process-mapping skill instead.
```

**Detection hint:** If lane labels are stage names (Prospecting, Discovery, Negotiation, Closed Won) the LLM produced a sales stage map, not a process flow map. Either switch skills or re-prompt with actor names.

---

## Anti-Pattern 6: Omitting integration handshake steps

**What the LLM generates:** A step like "Send order to NetSuite" with no exception path, no acknowledgement step, no fallback. The integration is treated as an instant, infallible operation.

**Why it happens:** LLMs simplify integrations into "send / receive" arrows. The reality of timeouts, retry policies, idempotency, dead-letter queues, and confirmation handshakes is not represented.

**Correct pattern:**

```
For every integration step:
  1. Tag with [INTEGRATION:<pattern>] from integration-pattern-selection.md
  2. Add an exception path for timeout (e.g., "if no ack within 30s,
     route to fallback queue")
  3. Add an acknowledgement / confirmation step on the receiving side
  4. Document the retry policy and idempotency key
```

**Detection hint:** Any `[INTEGRATION]` step without a timeout / fallback exception path is incomplete. The `check_process_map.py` checker flags this.

---

## Anti-Pattern 7: Single-tier annotations on multi-action steps

**What the LLM generates:** A step like "Validate credit and create payment authorization [FLOW]" — two distinct actions collapsed into one step with one tier. Validation is a Flow concern; payment authorization is a `[INTEGRATION]` callout. Tagging both as `[FLOW]` misroutes the build.

**Why it happens:** LLMs concatenate related actions into a single descriptive step rather than decomposing into atomic units. The single tier annotation seems sufficient because there is a single step.

**Correct pattern:**

```
Decompose multi-action steps into atomic units, one tier per unit:
  Step A: Validate credit [FLOW] — automation-selection.md Q2
  Step B: Create payment authorization in Stripe [INTEGRATION:REST]
          — integration-pattern-selection.md REST callout branch
  Step C: Update Order with auth result [FLOW] — automation-selection.md Q4
```

**Detection hint:** A step description with "and" linking two distinct actions (validate AND create, send AND log, route AND notify) is a candidate for decomposition. Re-prompt to split.

---

## Anti-Pattern 8: Generating decision-tree citations without checking

**What the LLM generates:** A To-Be step annotated with a confident-sounding citation like "automation-selection.md Q4 → after-save Flow" when the actual tree has Q4 routing to a different answer, or no Q4 at all.

**Why it happens:** LLMs hallucinate plausible citations to satisfy the requirement that every automated step cite a tree branch. The citation looks correct but does not match the actual tree.

**Correct pattern:**

```
Read standards/decision-trees/automation-selection.md before producing
citations. Quote the actual question text:
  "Q2. Does the logic run in under ~10s and touch only fields on the
   record itself? Yes → Before-save record-triggered Flow"
If the citation cannot be matched verbatim to the tree, do not produce it.
```

**Detection hint:** Cross-check every citation against the actual file content. If the question number does not exist in the tree, the citation was hallucinated.
