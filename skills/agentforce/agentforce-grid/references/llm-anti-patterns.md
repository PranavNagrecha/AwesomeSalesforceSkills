# LLM Anti-Patterns — Agentforce Grid

Common mistakes AI coding assistants make when generating or advising on Agentforce Grid. These
patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Apex/Flow/metadata for a no-code tool

**What the LLM generates:** an Apex batch class, a Flow, or a `package.xml` "to implement the
Agentforce Grid worksheet."

**Why it happens:** the model reaches for deployable Salesforce automation it has seen far more
often than Grid, which is a no-code Studio surface with no Metadata API type.

**Correct pattern:** describe the worksheet as an ordered set of Data / AI / Action columns
built in the Grid UI (a design spec, not deployable metadata). If the user actually needs
deployable, repeatable automation, say so and route them to Flow or Apex.

**Detection hint:** any `.cls`, `@InvocableMethod`, `Database.Batchable`, or `<Package>` output
presented as "the Grid implementation."

---

## Anti-Pattern 2: Ignoring metering / claiming runs are free

**What the LLM generates:** "just run it across all your records to test" with no mention of
cost, or an assertion that testing/experimentation doesn't consume anything.

**Why it happens:** the model treats a spreadsheet-like tool as free local computation.

**Correct pattern:** state that Grid is metered — "Agentforce Grid usage is metered regardless
of the AI lifecycle phase in which it's used" — draws on Flex Credits, and that cost scales with
rows × AI/action columns. Recommend reviewing the Billing Calculator estimate and bounding rows
before a wide run.

**Detection hint:** guidance to run a large row set without a cost caveat or a Max Results /
filter recommendation.

---

## Anti-Pattern 3: Building a forward or unresolvable column reference

**What the LLM generates:** a worksheet where an action or AI column references a column placed
to its right, or an Update Record column ahead of the AI column it should write.

**Why it happens:** the model treats columns as independent cells rather than a left-to-right
pipeline where a column can only consume earlier columns.

**Correct pattern:** order columns data → AI → action so every reference points to a column to
its left; the `@` picker only resolves earlier columns.

**Detection hint:** a `references` entry naming a column that appears at an equal or higher index
than the column that references it.

---

## Anti-Pattern 4: Confusing Grid with the prompt builder or a single agent turn

**What the LLM generates:** advice to "use Agentforce Grid" for a single-record summary or one
interactive chat response.

**Why it happens:** the model conflates any AI-over-CRM-data task with Grid.

**Correct pattern:** Grid's value is *bulk* — rows are jobs. For one record or one conversational
turn, use the prompt-builder / agent surfaces. Reserve Grid for running the same chain across
many rows.

**Detection hint:** a Grid recommendation where the workload is a single row / single response.

---

## Anti-Pattern 5: Asserting GA status or inventing limits

**What the LLM generates:** "Agentforce Grid, generally available since Winter '26, supports up
to N rows per worksheet…" with a fabricated cap or a GA claim.

**Why it happens:** models pattern-fill maturity labels and numeric limits that read as
authoritative.

**Correct pattern:** describe Grid as introduced in Winter '26 with **Beta** setup documentation;
do not assert GA, and do not state row/column limits the official docs don't give.

**Detection hint:** the words "generally available"/"GA" for Grid, or any specific numeric limit
presented without a documentation citation.

---

## Anti-Pattern 6: Reaching for an Update Record column on a read-only task

**What the LLM generates:** an action column that writes back results even when the user only
asked to *review* AI-generated insights.

**Why it happens:** the model assumes a complete pipeline always ends in a write.

**Correct pattern:** for insight-only runs, stop at the AI column and read the Output Preview —
omit the action column entirely. Write-backs mutate live data and spend credits on writes that
weren't requested.

**Detection hint:** an `update-record` action column in a worksheet whose stated goal is review,
analysis, or exploration rather than data change.
