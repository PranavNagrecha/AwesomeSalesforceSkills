# Gotchas — Flow Error Notification Patterns

Non-obvious behaviors of Flow fault handling that cause real
production silent-failure incidents.

---

## Gotcha 1: A "do-nothing" Fault path silently succeeds the flow

**What happens.** Admin adds a Fault connector to satisfy a code-review
rule but doesn't connect it to anything meaningful — Fault → end. The
platform considers the flow successful (the Fault path didn't itself
fail). No unhandled-fault email fires. Failures are silent.

**When it occurs.** Adding fault paths "for safety" without
implementing the recovery / log step.

**How to avoid.** A Fault path must do *something* observable. Insert
a `Flow_Error_Log__c` record, publish a Platform Event, or display
the error to the user. "End" alone is the failure mode.

---

## Gotcha 2: Default unhandled-fault email contains the entire interview state

**What happens.** When the flow has no Fault path, the platform sends
a plain-text email to "Apex Exception Email Recipient" containing
every variable's value at the moment of failure. For complex flows,
this is hundreds of lines, mostly irrelevant.

**When it occurs.** Default org behavior; affects every flow without
explicit Fault paths.

**How to avoid.** Pattern A — replace the default with a custom
`Flow_Error_Log__c` object + reusable sub-flow. Reports on the log
object give grouping, severity, retention. The default email still
goes to the org-default recipient as a fallback for flows you haven't
covered yet.

---

## Gotcha 3: `$Flow.FaultMessage` may be empty or generic depending on context

**What happens.** Fault path captures `$Flow.FaultMessage` and finds
it empty or just `"An error occurred"`. The actionable detail isn't
there.

**When it occurs.**
- Fault paths attached to elements that don't produce a structured
  error (e.g. deeply nested sub-flow whose own fault was caught).
- Some Apex-invoked-action errors that the action class doesn't
  surface as a typed exception.

**How to avoid.** Test fault paths with intentionally-broken inputs;
verify `$Flow.FaultMessage` is populated. If it isn't, capture
additional context (the input record, the user, the timestamp) so
the log has something to work with even when the message is
uninformative.

---

## Gotcha 4: Screen flow Fault paths that don't display anything = blank screen

**What happens.** Fault path on a screen-flow element ends without
showing the user anything. The screen appears blank or transitions
to nothing. User thinks the application broke.

**When it occurs.** Copy-paste of a non-screen-flow Fault pattern
into a screen flow.

**How to avoid.** Every screen-flow Fault path ends with either:
- A Display Text showing the error / friendly message.
- A Screen element that lets the user retry.
- An explicit "End interview with confirmation" screen.

Never end a screen-flow Fault path with a bare End. The user has no
context.

---

## Gotcha 5: Email sends inside record-triggered before-save Fault paths hit governor risk

**What happens.** Admin attaches a Send Email Action to the Fault
path of a before-save flow. On any failure, the email-send itself
counts against the same transaction's email-send governor. Bulk DML
that triggers many before-save fault paths can exceed the email
governor and itself fail.

**When it occurs.** Bulk imports, mass-update buttons, or any DML
that touches many records and fires the before-save trigger flow on
each.

**How to avoid.** Use Pattern C — publish to a Platform Event. The
email-send happens later, in a separate transaction (the Apex
subscriber). The flow's transaction stays clean.

---

## Gotcha 6: Send Email Action inside a Fault path can throw its own fault — unhandled

**What happens.** Fault → Send Email Action → if the email-send
itself fails (governor, missing template, malformed address), there's
no further Fault path. The secondary failure is unhandled. The flow's
unhandled-fault email fires (with the original fault context plus
the new email-send failure layered on top).

**When it occurs.** Any time an action in a Fault path can itself
fault. Not just email — any callout, DML, or sub-flow invocation.

**How to avoid.** The minimum-risk Fault path action is a single
Create Records on `Flow_Error_Log__c`. DML on a custom log object
rarely fails. If it does, that's a deeper org problem worth the
unhandled-fault email.

---

## Gotcha 7: Validation rule errors and DML faults are indistinguishable to the platform

**What happens.** Both produce a fault. Both populate
`$Flow.FaultMessage`. The platform doesn't tag the message with
severity or category. Without a decision branch, both flow into the
same Fault path treatment.

**When it occurs.** Any flow that does DML on objects with validation
rules.

**How to avoid.** Decision element inside the Fault path that
inspects `$Flow.FaultMessage`. Validation messages typically contain
`FIELD_CUSTOM_VALIDATION_EXCEPTION` or the rule's error text
verbatim. Branch: validation → user-display, no log; other → log.

---

## Gotcha 8: Sub-flow Fault paths don't propagate to the parent

**What happens.** A sub-flow has its own Fault paths that handle
errors silently. The parent flow has no Fault path on its Subflow
action. Errors caught by the sub-flow never surface to the parent
— and the parent admin's monitoring is blind.

**When it occurs.** Reusable sub-flows whose authors thought
"I'll handle errors here so callers don't have to".

**How to avoid.** Decide explicitly: either the sub-flow handles its
own errors (and produces a structured success/failure return value
for the parent to read) OR the sub-flow lets errors propagate
(parent attaches a Fault path to the Subflow action). Mixed — sub-flow
silently swallows AND parent expects errors to surface — produces
silent failures.

---

## Gotcha 9: Fault path on Loop element catches faults inside the loop body, not the Loop itself

**What happens.** Admin expects a Fault path on a Loop to catch
errors thrown by elements inside the loop. It does — but the loop
*continues* to the next iteration after the fault, unless the fault
path is wired to redirect outside the loop.

**When it occurs.** Loop-with-DML flows where one record's failure
should stop the whole loop.

**How to avoid.** Inside the Fault path, set a `hasError` boolean
variable. After the loop, check the variable and branch. Or, if you
want fail-fast: the Fault path connects to a path *outside* the
loop, which exits early and skips remaining iterations.
