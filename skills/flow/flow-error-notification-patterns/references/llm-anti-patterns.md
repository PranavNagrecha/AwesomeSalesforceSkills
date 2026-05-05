# LLM Anti-Patterns — Flow Error Notification Patterns

Mistakes AI coding assistants commonly make when advising on Flow
fault paths. The consuming agent should self-check against this list
before suggesting a Flow design.

---

## Anti-Pattern 1: "Just add a Fault path" with no implementation

**What the LLM generates.** "Add a Fault connector to the element to
catch errors."

**Why it happens.** The mechanic is simple, the LLM stops there.
Doesn't surface that an unconnected / do-nothing Fault path silently
succeeds the flow.

**Correct pattern.** Always prescribe what the Fault path *does* —
log, publish event, display to user. Never "add a fault path" as a
standalone recommendation.

**Detection hint.** Any "add a Fault path" advice without a follow-up
about what the path's destination should do is incomplete.

---

## Anti-Pattern 2: Recommending Send Email Action in every Fault path

**What the LLM generates.** "In the Fault path, send an email to the
admin so they're notified."

**Why it happens.** Email is the obvious notification channel.
Doesn't surface that:
- High-volume flows hit the email-send governor.
- Email-send itself can fault, and the secondary fault has no
  further fault path.
- Per-event email is noisy; admins train to ignore.

**Correct pattern.** Recommend Platform Event publish or custom
log object insert. Email comes from a downstream Apex subscriber
or a scheduled report digest, not directly from the flow.

**Detection hint.** Any flow design with "Send Email Action" inside
a Fault path is suspect — propose Platform Event or log instead.

---

## Anti-Pattern 3: Generic "an error occurred" user-facing message

**What the LLM generates.** Screen flow Fault path with Display Text
saying "Sorry, an error occurred. Please try again."

**Why it happens.** Generic friendly-sounding messages are the
default. Doesn't surface that throwing away `$Flow.FaultMessage`
loses both user-actionability AND admin-debuggability.

**Correct pattern.** Show `$Flow.FaultMessage` to the user *if* it's
a friendly business message (validation rules typically are). For
technical errors, show a brief generic message to the user AND
publish the full message to the admin channel.

**Detection hint.** Any Fault-path Display Text that doesn't
reference `{!$Flow.FaultMessage}` or call out why the message is
being suppressed is throwing away signal.

---

## Anti-Pattern 4: One Fault path treatment for all error types

**What the LLM generates.** Fault path that goes straight to
"publish event + display generic message" with no decision branch
distinguishing validation from technical errors.

**Why it happens.** Branching is more work; the LLM emits the
simplest version.

**Correct pattern.** Decision element inside the Fault path that
checks `$Flow.FaultMessage` for known business-rejection patterns
(`FIELD_CUSTOM_VALIDATION_EXCEPTION`, validation rule wording).
Validation → user display, no log. Other → log + display generic.

**Detection hint.** Flow Fault paths with no Decision element are
likely treating validation rejections and programmer errors the same
way.

---

## Anti-Pattern 5: Hardcoding the alert channel inside the flow

**What the LLM generates.** Flow Fault path that calls a specific
Slack-webhook action or specific email template.

**Why it happens.** The LLM matches "alert" to a single channel.
Doesn't surface that production orgs have multiple alert channels
that should be configurable.

**Correct pattern.** Flow publishes to a Platform Event. Apex
subscriber routes based on custom-metadata-driven rules. Flow
doesn't know which channel the alert lands in.

**Detection hint.** Any Fault path with a Slack-specific or
email-specific Action call directly is too tightly coupled.

---

## Anti-Pattern 6: "Use the org-default exception email recipient"

**What the LLM generates.** "Configure the apex exception email
recipient in Setup → Process Automation Settings."

**Why it happens.** That's the documented platform default. The LLM
treats it as the answer.

**Correct pattern.** Default email recipient is a *fallback* for
flows you haven't wired Fault paths into. The primary error-notification
design is custom log object + Platform Event. The default catches
oversights, doesn't drive ongoing operations.

**Detection hint.** Any "Flow error handling" recommendation that
ends with "set the org-default recipient" is using the default as
the design, not the fallback.

---

## Anti-Pattern 7: Fault path that re-runs the failing element

**What the LLM generates.**

```
Update_Records → Fault → Update_Records (retry)
```

**Why it happens.** Retry-on-fault is a reasonable instinct from
other runtimes (HTTP retry, queue retry). Doesn't surface that:
- The same record is locked for the rest of the transaction.
- The same validation will reject the same input.
- An infinite loop is one transient-fault away.

**Correct pattern.** Retry is appropriate for genuinely transient
failures (callouts, deadlock recovery). For Flow, transient retry
belongs in an Apex subscriber on the Platform Event, not in the flow
itself. The flow's job is to capture and surface the error, not
recover from it.

**Detection hint.** Any Fault path that loops back to the same
element is likely missing a transient-vs-permanent distinction.

---

## Anti-Pattern 8: Sub-flow that "handles errors silently for the caller's convenience"

**What the LLM generates.** Sub-flow with internal Fault paths that
log and end. Parent flow has no Fault path on its Subflow action;
the sub-flow's docs say "errors handled internally".

**Why it happens.** "Encapsulate the error handling so callers don't
have to" sounds like good design.

**Correct pattern.** Either:
- Sub-flow handles errors AND returns a structured success/failure
  via output variables that the parent must check, OR
- Sub-flow propagates errors and the parent must attach a Fault path.

The "silent" middle ground means parent admins are blind to sub-flow
failures.

**Detection hint.** Any reusable sub-flow that has internal Fault
paths AND no output variable indicating success/failure is producing
silent failures upstream.
