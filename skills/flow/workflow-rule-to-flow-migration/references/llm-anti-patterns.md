# LLM Anti-Patterns — Workflow Rule to Flow Migration

Common mistakes AI coding assistants make when generating or advising on Workflow Rule to Flow migration.

## Anti-Pattern 1: Confusing Workflow Rule Migration with Process Builder Migration

**What the LLM generates:** "Use the Migrate to Flow tool to convert both your Workflow Rules and Process Builder processes to flows."

**Why it happens:** Workflow Rules and Process Builder share the same retirement timeline, so LLMs group them and give identical guidance. But the migration approaches differ: Workflow Rules use field update mapping and Core Actions for outbound messages; Process Builder uses scheduled actions and invocable Apex patterns.

**Correct pattern:**
Workflow Rules and Process Builder are migrated via the same tool path (Setup > Migrate to Flow) but require separate triage. A Workflow Rule with time-based actions maps to Scheduled Paths; a Process Builder with scheduled actions also maps to Scheduled Paths — but the unsupported action lists differ. Do not mix guidance between the two.

**Detection hint:** Response treats "workflow rules" and "process builder" as interchangeable in migration guidance.

---

## Anti-Pattern 2: Assuming Outbound Message Definitions Transfer Automatically

**What the LLM generates:** "The Migrate to Flow tool will automatically convert your Outbound Message action to a Flow Core Action."

**Why it happens:** LLMs know the tool converts Outbound Messages but don't flag the pre-condition: the Outbound Message definition must already exist in Setup.

**Correct pattern:**
The tool creates a Core Action reference pointing to the existing Outbound Message definition. If the definition doesn't exist, the tool fails or generates a broken action. Always verify the definition exists before running the tool for outbound message rules.

**Detection hint:** Migration guidance for outbound messages that doesn't mention verifying the definition exists first.

---

## Anti-Pattern 3: Treating Time-Based Actions as Tool-Convertible

**What the LLM generates:** "The Migrate to Flow tool will convert your time-based workflow actions to Flow Scheduled Paths."

**Why it happens:** LLMs know Scheduled Paths can replace time-based actions, and infer (incorrectly) that the tool automates this.

**Correct pattern:**
The Migrate to Flow tool cannot convert time-based workflow actions. These must be manually rebuilt as Scheduled Paths on record-triggered flows. Set the path's time source field to match the original time trigger offset.

**Detection hint:** Any claim that the tool handles time-based actions.

---

## Anti-Pattern 4: Not Flagging ISCHANGED/ISNEW Criteria Before Running Tool

**What the LLM generates:** Runs the Migrate to Flow tool on Workflow Rules without first checking whether they use ISCHANGED() or ISNEW() in criteria.

**Why it happens:** LLMs focus on the tool's capabilities, not its documented exclusions.

**Correct pattern:**
Before running the tool, audit every Workflow Rule's entry criteria for ISCHANGED() or ISNEW() usage. These require manual rebuild using `{!$Record__Prior.FieldName}` comparisons. The tool may silently drop or incorrectly map these conditions.

**Detection hint:** Migration plan that starts with "run the tool" without an audit step.

---

## Anti-Pattern 5: Not Accounting for In-Flight Time-Based Actions at Cutover

**What the LLM generates:** "Deactivate the Workflow Rule and activate the replacement Flow. Users won't notice the difference."

**Why it happens:** LLMs treat deactivation as a clean switchover, missing the platform behavior that pending queue entries are cancelled immediately.

**Correct pattern:**
Pending time-based workflow actions are cancelled the moment the rule is deactivated. Communicate to stakeholders before cutover. Query the time-based workflow queue (via Tooling API or `ProcessInstanceStep`) to identify and document in-flight actions that will not fire.

**Detection hint:** Any cutover instruction that doesn't mention pending time-based actions.

---

## Anti-Pattern 6: Generating Task Creation Logic That Mirrors Workflow Rule Structure

**What the LLM generates:** An Apex trigger or Flow that tries to replicate Workflow Rule Task actions by calling `Database.insert(new Task(...))` inside a trigger without bulk-safe collection handling.

**Why it happens:** LLMs pattern-match on "create task when record changes" and generate single-record Apex or Flow logic.

**Correct pattern:**
In a record-triggered flow, use a Create Records element with subject, owner, activity date, and WhoId set from flow merge fields. Ensure the flow is bulk-safe (no per-record SOQL). The Create Records element handles the collection correctly when the flow fires on 200+ records.

**Detection hint:** Code or flow logic that creates tasks with single-record assumptions rather than collection-based Create Records.
