# LLM Anti-Patterns — Flow Interview Debugging

Mistakes AI coding assistants reliably make when asked to debug or instrument a
Salesforce Flow. Each entry states what gets generated, why the model reaches
for it, the corrected pattern, and how a reviewer spots it.

---

## Anti-Pattern 1: Fault Connector on a Get Records to Catch "No Records Found"

**What the LLM generates:** a `faultConnector` on a `recordLookups` element
pointing at a "No record found" branch, described in the explanation as
"handles the case where the query returns nothing."

**Why it happens:** in most languages a lookup that finds nothing raises — SQL
frameworks throw `NoResultException`, ORMs throw `RecordNotFound`. The model
maps Flow's fault path onto that mental model.

**Correct pattern:** zero rows is a *success*. Route the not-found case through a
Decision using the `IsNull` operator against the record variable, and set
`assignNullValuesIfNoRecordsFound` to `true` so the variable is reliably null.
Keep the fault connector for real platform exceptions and point it at a logger.

**Detection hint:** a `<faultConnector>` inside a `<recordLookups>` whose target
element's label contains "not found", "none", "missing", or "empty".

---

## Anti-Pattern 2: A Screen Element as the Universal Fault Handler

**What the LLM generates:** every fault connector routed to a Screen that
displays `{!$Flow.FaultMessage}`, regardless of the flow's `processType`.

**Why it happens:** it is the pattern in most Flow tutorials, which are almost
always written about screen flows, and it produces a satisfying-looking diagram.

**Correct pattern:** a Screen is not a valid target in record-triggered,
scheduled, autolaunched, or platform-event-triggered flows — there is no UI to
render into. Write a log record first; add a Screen only when `processType` is
`Flow`. To both message the user and block the save in a record-triggered flow,
use the **Custom Error** element, which displays your message and rolls the
transaction back.

**Detection hint:** a `<screens>` element referenced from a `<faultConnector>` in
a flow whose `<processType>` is anything other than `Flow`.

---

## Anti-Pattern 3: Inventing Debug Globals That Do Not Exist

**What the LLM generates:** references such as `$Flow.CurrentElement`,
`$Flow.ErrorElement`, `$Flow.FaultCode`, `$Flow.StackTrace`, or
`$Flow.InterviewId` in a logging assignment.

**Why it happens:** the model knows `$Flow.FaultMessage` and
`$Flow.InterviewGuid` exist and generalizes a family of siblings that would be
useful if they existed. Flow XML happily saves a bogus `elementReference` name
in some tooling paths, so the invention is not always caught at authoring time.

**Correct pattern:** pass the element name in as a literal string typed by the
author at each fault-handler call site. There is no run-time global that reports
which element faulted; only the error email carries it. Stick to globals you can
name from the documentation — `$Flow.FaultMessage` and `$Flow.InterviewGuid` are
the two this domain actually needs.

**Detection hint:** any `$Flow.` reference other than the documented set. Grep
the flow XML for `$Flow.` and check each hit against
`help.salesforce.com` → *Flow Resource: $Flow Global Variables*.

---

## Anti-Pattern 4: "Set the Flow Error Email to the Flow Owner"

**What the LLM generates:** advice to change the error-email recipient to the
flow's owner, or to add a `Send Email` action to the fault path addressed to a
hard-coded person.

**Why it happens:** "owner" is the intuitive noun and appears in most other
Salesforce contexts. The platform setting does not offer it.

**Correct pattern:** the two real options under Setup → **Process Automation
Settings** → **Send Process or Flow Error Email to** are *User Who Last Modified
the Process or Flow* (the default) and *Apex Exception Email Recipients*. Route
to the latter and manage the list under Setup → **Apex Exception Email**. A
hard-coded address in a Send Email action is people-as-configuration and breaks
on the first staff change.

**Detection hint:** the strings "flow owner", "flow creator", or a literal email
address inside flow metadata.

---

## Anti-Pattern 5: Log-and-Continue on Every Fault Path

**What the LLM generates:** each fault path writes a log row and then connects
straight back into the main path, so the interview always completes.

**Why it happens:** "handle the error, don't crash" is the correct default in
long-running services. In a Salesforce transaction it converts a loud,
observable failure into a silent partial commit.

**Correct pattern:** decide per fault path whether the business outcome can
survive the step failing. If it cannot, end the path — and in a record-triggered
flow use **Custom Error** so the transaction rolls back rather than committing a
half-finished state. Continue past a fault only when the faulted step was
genuinely optional, and log either way.

**Detection hint:** a fault path whose last element's `<connector>` targets an
element that is also on the happy path.

---

## Anti-Pattern 6: Attributing Any Limit Error to the "2,000 Element Limit"

**What the LLM generates:** a diagnosis that the flow "exceeded the 2,000
executed elements limit," followed by a refactor to reduce element count.

**Why it happens:** the number is heavily represented in pre-2023 blog content,
which dominates the training distribution for this topic.

**Correct pattern:** that cap was removed in API version 57.0 (Spring '23). Read
the actual exception. `Too many SOQL queries: 101` and `Too many DML statements:
151` are the per-transaction Apex governor limits the flow shares with every
other automation in the transaction; `Apex CPU time limit exceeded` is CPU.
None of them is an element cap, and none is fixed by deleting elements.

**Detection hint:** the string "2,000 elements" or "2000 element limit" in an
explanation, especially when paired with an error message that names SOQL, DML,
or CPU.

---

## Anti-Pattern 7: Treating a Clean Debugger Run as a Passing Test

**What the LLM generates:** a verification step that ends at "run Debug in Flow
Builder and confirm all elements are green."

**Why it happens:** the debugger is the most visible affordance in Flow Builder
and produces an unambiguous pass/fail signal, which is exactly what a test step
wants.

**Correct pattern:** name the three things the debugger does not cover — commit
and everything downstream of it (when roll-back is on), scheduled and async
paths, and the permissions of the real running user — and give a verification
step for each: a rollback-off run in a sandbox, the Setup → **Time-Based
Workflow** queue, and a run as a low-privilege persona.

**Detection hint:** a test plan whose only verification is the Flow Builder
debugger, with no mention of a running user or of the async path.

---

## Anti-Pattern 8: Recommending Apex Debug Logs as the Primary Flow Diagnostic

**What the LLM generates:** "enable a debug log on the user and set the Workflow
category to FINEST" as the first troubleshooting step, with the implication that
the log will explain the flow.

**Why it happens:** the model's strongest debugging prior is server-side logs,
and Flow does emit into the debug log.

**Correct pattern:** debug logs are the right tool for *governor* questions —
the cumulative limits section tells you who spent the SOQL and DML budget in a
shared transaction. They are a poor first stop for a functional Flow bug: the
error email already names the element, the type, the version, and the interview
GUID, and the fault-path log row already carries the record and the running
user. Reach for the debug log when you need to know what *else* was in the
transaction, not to find out which element failed.

**Detection hint:** a troubleshooting sequence that starts with a debug-log trace
flag and never mentions the flow error email or `$Flow.InterviewGuid`.
