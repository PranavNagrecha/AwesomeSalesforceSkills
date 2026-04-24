# LLM Anti-Patterns — Salesforce Debug Log Analysis

Common mistakes AI assistants make when analyzing Salesforce debug logs. Each one has a detection heuristic so the consuming agent can self-check.

## Anti-Pattern 1: Reporting A Root Cause From The First 200 Lines

**What the LLM does:** Reads the first screen of the log, sees a `CODE_UNIT_STARTED|MyTrigger` followed by a `DML_BEGIN`, and concludes the trigger is the cause of the reported symptom.

**Why it happens:** LLMs optimize for producing *an* answer quickly. Salesforce logs have the real cause buried thousands of lines later — at `FLOW_ASSIGNMENT_DETAIL`, `WF_FIELD_UPDATE`, a nested `ENTERING_MANAGED_PKG`, or a `FATAL_ERROR` after the cascade.

**Correct pattern:** Always run Step 1 (triage) and Step 2 (timeline) before drawing conclusions. Then classify the user's question (Step 3) and grep for the specific events relevant to that category. For a flip-flop, the cause is almost always *after* the first 1,000 lines.

**Detection hint:** The agent's response cites evidence only from line numbers < 500 in a multi-MB log.

---

## Anti-Pattern 2: Inventing A Stack Trace That Is Not In The Log

**What the LLM does:** When asked "what caused the exception?", the agent generates a plausible-looking stack trace with made-up class names and line numbers.

**Why it happens:** The agent pattern-matches against similar-sounding incidents in training data rather than quoting actual log content.

**Correct pattern:** Every evidence citation in the report must quote a real line from the log, with either the timestamp or an approximate line offset. If the log does not contain a stack trace (e.g., `FATAL_ERROR` without frames, or a flow fault without element context), state that plainly and recommend capturing a log with higher `APEX_CODE` level.

**Detection hint:** The agent's report contains Apex class or line numbers that do not appear when the user greps the log for them.

---

## Anti-Pattern 3: Diagnosing Managed-Package Internal Logic

**What the LLM does:** Sees `ENTERING_MANAGED_PKG|SBQQ` and proceeds to explain what Salesforce CPQ is doing inside the package, citing specific method names and internal behaviors.

**Why it happens:** The agent has general knowledge of popular packages from training data and pattern-matches against the namespace. But the log deliberately hides internal package execution — any specific claim is speculation.

**Correct pattern:** Acknowledge the namespace and its likely area (e.g., "SBQQ is Salesforce CPQ, which means quote and quote line item automation is in play"). State that the log cannot show what happens inside the package, and route to `references/managed-packages.md` for known *external* behaviors. For support, direct the user to the package vendor.

**Detection hint:** The agent describes specific managed-package method calls or internal control flow without citing a `CODE_UNIT_STARTED` line that names those methods.

---

## Anti-Pattern 4: Recommending `System.debug` As The Fix

**What the LLM does:** Identifies a performance or cascade issue, then recommends "add more `System.debug` statements" or "increase the trace flag level" as the primary remediation.

**Why it happens:** The agent conflates log analysis (this skill) with instrumentation (`apex/debug-and-logging`). More debug output does not fix the underlying cascade — it makes the *next* log larger.

**Correct pattern:** Recommendations should target the mechanism: disable a legacy workflow, bulkify a helper method, move sync work to a Queueable, change a trigger's firing context. Instrumentation recommendations belong in the "stop the bleeding" section only when the next investigation is the bottleneck, not the fix.

**Detection hint:** The agent's `Recommendations` section leads with a `System.debug` or trace-flag change rather than a code or configuration change.

---

## Anti-Pattern 5: Glossing Over `What The Log Cannot Tell You`

**What the LLM does:** Produces a confident root-cause narrative for a merge failure with empty bracket list, or identifies a specific Task as the blocker without evidence, or claims a scheduled job was scheduled by Apex without querying `CronTrigger`.

**Why it happens:** The agent is trained to produce complete answers. Salesforce logs have documented silences (empty `[]` in INSUFFICIENT_ACCESS, hidden package internals, encrypted fields shown as `****`, formula "writes" with no writer). Pretending those silences do not exist produces wrong answers.

**Correct pattern:** Every report must have a `What the log cannot tell you` section with explicit limits. Give the user a concrete next step for each limit (impersonate user X, query CronTrigger for the schedule, open the field metadata to check if it's a formula).

**Detection hint:** The agent's report omits the limits section, or fills it with vague language instead of specific unanswerable questions.

---

## Anti-Pattern 6: Blaming The Running User In An Async Log

**What the LLM does:** Sees `USER_INFO|0050B00000ABCDE|IntegrationUser@org` in the header and concludes the integration user caused the incident.

**Why it happens:** The header is the most prominent user attribution in the log. But async contexts (`@future`, Queueable, Batch) run as the *enqueuing* user, not the user who caused the business action. A human click minutes earlier is often the true origin.

**Correct pattern:** For any async context (`CODE_UNIT_STARTED|[EventService..queueable]`, `BATCH_APEX_START`, `CRON_TRIGGER_`, `CODE_UNIT_STARTED|[future]`), cross-reference `AsyncApexJob.CreatedById` from Setup > Monitoring > Apex Jobs. Report both the running user and the enqueuing user.

**Detection hint:** The agent reports a user as the cause without checking whether the log context is async.

---

## Anti-Pattern 7: Treating `WF_FIELD_UPDATE` As Dead Legacy

**What the LLM does:** Sees `WF_FIELD_UPDATE` in a modern log and dismisses it because "the org has migrated to Flow."

**Why it happens:** The agent knows Workflow Rules and Process Builder are deprecated. But Salesforce still ships `WF_FIELD_UPDATE` events because many orgs have surviving rules or migrated actions that still call the legacy field-update primitive.

**Correct pattern:** Treat `WF_FIELD_UPDATE` events as authoritative evidence of a field write. Query `WorkflowRule where IsActive = true` to identify the source. If the user says they have no workflows, check `FlowDefinition` for flows that trigger legacy field-update actions as downstream effects.

**Detection hint:** The agent discounts `WF_FIELD_UPDATE` evidence by asserting "this should not be firing in a modern org."

---

## Anti-Pattern 8: Summing `DML_BEGIN.Rows` To Estimate Transaction Volume

**What the LLM does:** Adds up all `Rows` values across `DML_BEGIN` events and reports "X thousand records touched."

**Why it happens:** It looks like arithmetic. But bulk operations log multiple statements with overlapping row counts, and platform-internal DML (formula recalculation, sharing recalc) appears as `ASYNC_DML_BEGIN` and is not attributable to user code.

**Correct pattern:** For governor-limit math, cite `TESTING_LIMITS` or `LIMIT_USAGE_FOR_NS` events. For transaction volume, report the count of `DML_BEGIN` events by SObject type and note that it is an upper bound.

**Detection hint:** The agent's report has a single "records touched" number derived from `DML_BEGIN.Rows` arithmetic.

---

## Anti-Pattern 9: Assuming `VARIABLE_ASSIGNMENT` Means The Field Was Saved

**What the LLM does:** Reports that `Account.Industry` was changed to `Healthcare` based on a `VARIABLE_ASSIGNMENT` event, without checking for a corresponding successful DML.

**Why it happens:** `VARIABLE_ASSIGNMENT` looks definitive. But it only describes in-memory mutation of an SObject; if the transaction throws before `update`, or if the assignment is on a temporary copy, nothing was persisted.

**Correct pattern:** Pair every `VARIABLE_ASSIGNMENT` of interest with a subsequent `DML_BEGIN|Op:Update|Type:<SObject>` and a successful `DML_END` (no `EXCEPTION_THROWN` between them). Report only persisted changes as "the field was changed."

**Detection hint:** The agent reports a field change citing only a `VARIABLE_ASSIGNMENT` without a DML pair.

---

## Anti-Pattern 10: Loading All Reference Files Pre-emptively

**What the LLM does:** At the start of an analysis, reads all 12+ files in `references/` to "have full context."

**Why it happens:** LLMs optimize for completeness over focus. But the reference folder is structured precisely so the agent loads only the category it needs — loading everything wastes attention and leads to off-topic recommendations.

**Correct pattern:** Run Step 3 (classify the question) first. Load only the matching reference file(s). Never preload `managed-packages.md`, `specialized-topics.md`, or `legacy-automation.md` unless the user's symptom points there.

**Detection hint:** The agent reads more than two reference files before producing any extraction output or classification.
