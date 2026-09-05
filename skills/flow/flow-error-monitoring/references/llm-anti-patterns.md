# LLM Anti-Patterns — Flow Error Monitoring

Ten failure modes seen in generated flow-monitoring designs. The last four are specific to
this domain and are the ones a reviewer should look for first, because they produce output
that *reads* as authoritative.

---

## Anti-Pattern 1: Logging PII in message bodies

**What the LLM generates:** `message = 'Failed for user ' + user.Email + ' with SSN ' + user.SSN__c`

**Why it happens:** LLMs dump available context into error messages.

**Correct pattern:** Log Ids only — `Related_Record_Id__c` and `Running_User__c` (a lookup to
`User`). The reader can open the record; the log does not have to carry the data. An error log
is queryable by anyone with read on the object, which is a wider audience than the source
records had.

---

## Anti-Pattern 2: One generic email alert for everything

**What the LLM generates:** Every fault → Send Email to `ops@company.com`.

**Why it happens:** Default single-channel alerting; the model optimises for "something is
wired" over "someone acts".

**Correct pattern:** Severity decides the channel and aggregation decides the volume. Inline
notification only where the flow is single-record; otherwise the fault writes a row and a
separate flow on the log object applies a threshold (gotcha 14).

---

## Anti-Pattern 3: Log schema with no correlation handle

**What the LLM generates:** A flat log object with a message and a timestamp.

**Why it happens:** LLMs produce the minimum schema that satisfies the sentence they were
given.

**Correct pattern:** Reuse `templates/apex/custom_objects/Application_Log__c` — it already
carries `Request_Id__c` as an external Id, which is what groups a flow's rows with the Apex
rows from the same transaction. Inventing a second log object splits the very surface the
skill exists to unify.

---

## Anti-Pattern 4: Dashboard with no filter

**What the LLM generates:** "Show all errors from the last 30 days" over an unfiltered log
object.

**Why it happens:** LLMs default to comprehensive views.

**Correct pattern:** Filter to `ERROR`/`FATAL` for the headline view and put `WARN`/`INFO` on
demand. The report in `references/metadata-examples.md` §6 shows the `criteriaItems` shape.

---

## Anti-Pattern 5: No retention decision

**What the LLM generates:** Log forever, archive never.

**Why it happens:** Storage is invisible in the prompt.

**Correct pattern:** State a retention policy with an owner in the design, even if the answer
is "keep everything for now" — an unstated policy becomes a storage incident. Archive
mechanics belong to `data/` skills, not here.

---

## Anti-Pattern 6: Treating fault connectors as optional

**What the LLM generates:** A flow with DML and no fault connectors, relying on the default
fault email.

**Why it happens:** Fault routes are not required for a flow to save or deploy, so nothing in
the feedback loop demands them.

**Correct pattern:** Every fault-capable element routes to the org's one sink. Run
`scripts/check_flow_error_monitoring.py --manifest-dir <src> --strict`; the
`fault-sink-unreachable` rule exists for exactly this.

---

## Anti-Pattern 7: Inventing `FlowExecutionErrorEvent` field names

**What the LLM generates:** A platform-event subscriber that reads `ErrorId`,
`ElementApiName`, `FlowVersionNumber`, `ContextRecordId` and `FlowApiName` off a
`FlowExecutionErrorEvent`, presented as a native, zero-config error feed.

**Why it happens:** The name is plausible, it matches the naming convention of real event
objects, and field names can be extrapolated from `FlowInterviewLog`. The output looks like
documentation.

**Correct pattern:** **`FlowExecutionErrorEvent` appears nowhere in `object_reference.txt`,
`api_meta.txt`, `apexdev.txt` or `api_rest.txt`** (verified 2026-09-05, 0 hits in all four).
Never state a field of it as fact. If a subscriber is genuinely wanted, serialise the whole
event — `JSON.serialize(evt)` into a `LongTextArea` — so the code cannot depend on a field
name nobody has confirmed. The primary path in this skill is the fault connector writing
`Application_Log__c`, which needs no such event.

---

## Anti-Pattern 8: `SELECT ... FROM FlowVersionView` with no filter

**What the LLM generates:** An org-wide version-drift audit querying `FlowVersionView`
directly, and a conclusion — "no drift found" — drawn from the empty result.

**Why it happens:** It is the object whose name matches the question.

**Correct pattern:** "A query must be filtered by `DurableId` or `FlowDefinitionViewId` to
get results" (`object_reference.txt` L145295–L145296). Drive it from
`FlowDefinitionView.IsOutOfDate`. An empty result from an unfiltered query is not evidence
of anything, and reporting it as a clean bill of health is worse than not running it.

---

## Anti-Pattern 9: Reporting "monitoring is live" from a successful deploy

**What the LLM generates:** A summary that says monitoring is now in place because
`sf project deploy start` returned success.

**Why it happens:** The deploy result is the only feedback signal in the transcript.

**Correct pattern:** In production, `enableFlowDeployAsActiveEnabled` defaults to `false`, so
"all processes and flows are deployed as inactive" (`api_meta.txt` L116877–L116886). Verify
with `SELECT ApiName, IsActive, IsOutOfDate FROM FlowDefinitionView WHERE ApiName = '…'` and
by forcing one real fault and reading the log row back. A deploy is evidence that metadata
landed, never that a fault path runs.

---

## Anti-Pattern 10: Claiming `FlowTest` covers the log write

**What the LLM generates:** A `FlowTest` plus the sentence "this asserts that the fault path
creates the log record".

**Why it happens:** `FlowTest` is the flow-native test artefact, so the model assumes it can
assert anything a test could.

**Correct pattern:** Test points exist only at `Start` and `Finish` (`api_meta.txt`
L74141–L74148) and no `FlowTest` field inspects records the flow created. `HasError` (API
64.0+, L74203) proves the fault occurred; proving the row exists needs an Apex wrapper or a
manual scratch-org check. Say which of the two claims the artefact actually supports.
