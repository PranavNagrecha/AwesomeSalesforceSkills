# Examples — OmniStudio vs Flow Decision

Worked decisions, each shown as the routing that produced it rather than as a
verdict. The point of the format is that a reader can check the reasoning against
the trees and disagree with a specific step — which is the only kind of
architectural decision worth writing down.

Every decision below starts in
[`standards/decision-trees/automation-selection.md`](../../../../standards/decision-trees/automation-selection.md)
and, where that lands on Flow, continues into
[`standards/decision-trees/flow-pattern-selector.md`](../../../../standards/decision-trees/flow-pattern-selector.md).

---

## Example 1: The decision the trees settle before OmniStudio comes up

**Requirement:** "When an Application is submitted, stamp a risk tier on the
record and set the review-due date."

**Routing:**

```text
automation-selection.md
  Q1  What triggers the work?              → A record change            → Q2
  Q2  Under ~10s and touches only fields
      on the record itself?                → Yes
      ⇒ Before-save record-triggered Flow
```

**Decision: Flow. This skill has nothing to add.**

OmniStudio has no before-save equivalent. Before-save is the cheapest automation
on the platform — it writes the field in the save the trigger already pays for
rather than issuing a second one — and there is no OmniStudio artifact that runs
in that slot.

**Why this example is first:** the most common failure of an "OmniStudio vs Flow"
conversation is that it happens at all. On an Industry Cloud org, roughly this
requirement gets built as an Integration Procedure invoked from an after-save Flow
because the org's default is OmniStudio. That is a second save, an extra artifact,
and a deployment mechanism, in exchange for nothing.

**The general rule this illustrates:** run the automation tree first. Several of
its branches resolve to something OmniStudio cannot do, and on those branches the
comparison is not close — it is empty.

---

## Example 2: Where the trees say Flow and OmniStudio still wins

**Requirement:** a 14-step commercial insurance application. Conditional sections
by product line, save-and-resume across days, document upload at step 9,
validation that depends on answers three steps earlier, delivered to brokers
through an Experience Cloud site and to internal underwriters in a console.

**Routing:**

```text
automation-selection.md
  Q1  What triggers the work?               → A user filling a form     → Q7
  Q7  Button on a record page or list view? → Neither — a standalone journey
      (nearest branch: Q8 → "Can the action complete in under 10s
       without custom UI?" → No → LWC calling imperative Apex)

flow-pattern-selector.md
  Q1  What fires the flow?                  → A user interaction        → Q7
  Q7  Is the user PAUSING mid-flow?         → Yes, resumes later
      ⇒ Orchestration OR screen flow + pause element
```

**The baseline the trees produce:** a Screen Flow with a pause element, or an
Orchestration, or a custom LWC over imperative Apex.

**Per-layer decision:**

| Layer | Choice | Reason |
|---|---|---|
| UI | **OmniScript** | 14 steps with cross-step conditional validation is what it exists for. A Screen Flow reaches "hard to reason about" well before step 14, and the pause-element route makes resume a transaction-boundary problem — see the flow-pattern-selector transaction table |
| Orchestration | **Integration Procedure** | Rating callouts plus response shaping, reused by both surfaces |
| Data shaping | **Data Mapper** | The rating vendor dictates a nested JSON contract; a Transform makes that contract a named artifact |
| Post-submit side effects | **After-save record-triggered Flow** | `flow-pattern-selector.md` Q4–Q5: create the review task and the underwriter assignment where record-triggered work belongs |

**Note the last row.** The submit consequences stay in Flow. Pulling them into
the Integration Procedure because "the journey is OmniStudio" puts record-triggered
work in a non-record-triggered context and loses Flow Trigger Explorer, the
debugger, and every standard automation surface.

**What makes this the strong case:** two surfaces, real branching depth, an
external payload contract, and a team that already runs OmniStudio. Remove any
one of those and the answer moves.

---

## Example 3: The same requirement, an org where the answer flips

**Requirement:** identical to Example 2 — 14 steps, two surfaces, external rating
call.

**What is different:** the org bought OmniStudio nine months ago. One consultant
built two OmniScripts and has since rolled off. Nobody on the internal team has
built one. The release pipeline promotes Flows and Apex through a source-control
process that has never carried an Omnistudio artifact.

**Same routing, opposite recommendation.**

| Layer | Choice | Reason |
|---|---|---|
| UI | **Screen Flow with a pause element**, or a small LWC | The capability that cannot be maintained is worth less than a worse one that can |
| Orchestration | **Invocable Apex** | `automation-selection.md` Q6: one step needs a callout, orchestration is otherwise simple |
| Data shaping | **Apex** | The payload contract lives in a class the team can test and deploy today |

**Why this belongs in the examples rather than in a caveat:** capability
comparisons produce Example 2's answer every time. Nothing about the requirement
changed between these two examples. What changed was who maintains it and whether
it can be promoted — and those decided it.

**The honest framing to give a stakeholder:** "OmniScript is the better fit for
this shape and we should not use it here. The gap is training and pipeline, both
of which are fixable, and neither of which is fixable inside this project's
timeline."

**What to write down:** the conditions under which the decision should be
revisited — two trained builders and an Omnistudio-capable pipeline — so the next
team inherits a reversible decision rather than a precedent.

---

## Example 4: Mixed tools, and the boundary as a contract

**Requirement:** a three-screen "request a policy change" form for internal
service agents. One step must produce a nested JSON document for the policy
administration system.

**Routing:**

```text
automation-selection.md
  Q1  → A user clicking a button on a record page   → Q7 → Q8
  Q8  Completes in under 10s without custom UI?     → Yes
      ⇒ Screen Flow with a Quick Action

flow-pattern-selector.md
  Q1  → A user interaction                          → Q7
  Q7  Pausing mid-flow?                             → No
      ⇒ Standard screen flow
```

**Per-layer decision:**

| Layer | Choice | Reason |
|---|---|---|
| UI | **Screen Flow** | Three screens, admin-owned, changes monthly |
| Orchestration + shaping | **Integration Procedure + Transform Data Mapper** | The nested payload is dictated externally; expressing it in Flow formulas is genuinely worse |

This is a mixed design and it is correct. The instinct to pick one vendor per
capability is aesthetic.

**The part that actually needs writing down** is the seam:

```text
BOUNDARY CONTRACT — Screen Flow "Policy Change Request"
                 → Integration Procedure "PolicyChange_Submit"

  Direction        Screen Flow → Integration Procedure

  Input            policyNumber      Text, required
                   changeType        Text, required, one of:
                                     ADDRESS | COVERAGE | PAYMENT_METHOD
                   effectiveDate     Date, required, today or later
                   requestedBy       Text (User Id), required

  Output           confirmationId    Text — the admin system's reference
                   status            Text — ACCEPTED | REJECTED | PENDING
                   messages          List<Text> — surfaced to the agent verbatim

  Owner (Flow side)   Service Ops admin team
  Owner (IP side)     Integrations team

  Change protocol  Additive changes to Output are safe.
                   Any change to Input, or any change to the changeType
                   enumeration, requires notice to the Flow owner and a
                   regression test on both sides in the same release.

  Failure contract The IP returns status = REJECTED with messages populated.
                   It does NOT throw. The Screen Flow has no fault path that
                   can meaningfully explain an unhandled OmniStudio error to a
                   service agent.
```

**Why this is the artifact that matters:** in a mixed design, the failure will be
at the seam and the argument will be about who owns it. Two teams, one interface,
no written contract is the standard shape of a production incident. The failure
contract in particular is load-bearing: without it, the Flow's fault path shows an
agent an error string from an artifact they have never heard of.

---

## Example 5: FlexCard vs Lightning Record Page — a separate decision

**Requirement:** a policy summary panel on the Account record page.

**What usually happens:** the org "is an OmniStudio org", so it is a FlexCard.

**The two questions that actually decide it:**

1. **Is this consumed anywhere other than the Lightning record page?** An
   Experience Cloud site, an OmniScript step, a second object's page? If yes,
   FlexCard's reuse is real.
2. **Does it need a FlexCard-specific behaviour?** Actions driven from the central
   designer, an IP-powered save chain, state shared across cards? If yes, the
   Lightning Record Page cannot do it.

Two noes means Lightning Record Page:

| | Lightning Record Page | FlexCard |
|---|---|---|
| Who can change it | Any admin, in App Builder | Someone with OmniStudio skills |
| Deployment | Standard metadata pipeline | DataPacks, or Metadata API as `OmniUiCard` after enabling the Omnistudio Metadata setting |
| Reuse across surfaces | Limited | Genuine |
| Introspection | Standard tooling | `OmniUiCard` is a standard object, but the Omnistudio standard objects are documented "For internal use only" — read, don't write |

**Why this is its own example:** teams decide "OmniScript vs Screen Flow" once and
then apply the outcome to every layer, including this one. The UI-composition
layer has a different cost profile from the journey layer — a record page is
edited far more often, by far more people — and it deserves its own answer.

---

## Anti-Pattern: the migration that grew during a migration

**What happens:** an org on the managed package runtime plans its move to the
standard runtime. Mid-project, a new requirement arrives. The team is now fluent
in OmniStudio, the requirement is a good OmniScript fit, and they build it as one
on the managed package runtime.

**What goes wrong:** it is immediately in scope for the migration they are trying
to finish. The three-phase move now includes an artifact that did not exist when
it was scoped, and every hour spent building it is an hour that will be spent
again migrating it.

**The subtler cost:** it gets built on managed-package idioms — DataPacks,
`vlocity_*` Apex entry points, the managed-package extension model — all of which
have standard-runtime replacements that the team will have to learn anyway. The
new artifact teaches the team the pattern they are supposed to be leaving.

**Correct approach:** during a runtime migration, new capability goes into
something outside the migration's scope — Flow, Apex, LWC — unless it genuinely
cannot. Where OmniStudio is unavoidable, build it on the target runtime even if
that means the capability lands later. "We built it twice" is a worse outcome than
"we built it once, later".

**Detection hint:** any new OmniStudio artifact created on the managed package
runtime in an org with an active migration plan. Also: a migration scope document
whose artifact count has gone up since it was written.
