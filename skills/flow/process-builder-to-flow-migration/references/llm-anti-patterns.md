# LLM Anti-Patterns — Process Builder to Flow Migration

Common mistakes AI coding assistants make when generating or advising on Process Builder to Flow migration.

## Anti-Pattern 1: Treating Tool Migration as a Safe 1:1 Conversion

**What the LLM generates:** "Run the Migrate to Flow tool on all your processes — it converts them automatically and the result is ready to activate."

**Why it happens:** LLMs overfit to the existence of the migration tool and underweight the tool's documented limitations and the need for post-generation review.

**Correct pattern:**
The Migrate to Flow tool creates INACTIVE flows that require manual review. It silently drops or mis-maps: ISCHANGED/ISNEW criteria, invocable Apex actions, task creation, scheduled actions, and related-record field updates. Every generated flow must be reviewed in Flow Builder against the original process before activation.

**Detection hint:** Any response that says "run the tool and activate" without mentioning review, fault paths, or unsupported action types.

---

## Anti-Pattern 2: Not Checking for ISCHANGED/ISNEW Before Running Tool

**What the LLM generates:** Instructs user to run Migrate to Flow tool on processes that include `ISCHANGED(FieldName)` or `ISNEW()` in their criteria.

**Why it happens:** LLMs don't always parse the distinction between static-value criteria (tool-eligible) and function-based criteria (not tool-eligible).

**Correct pattern:**
Before running the tool, audit every process for ISCHANGED/ISNEW criteria. These require manual rebuild using `{!$Record__Prior.FieldName} != {!$Record.FieldName}` in a Decision node. The tool cannot map these and may generate a flow that fires on every record update without restriction.

**Detection hint:** LLM response runs the tool without first listing what action types/criteria the source processes use.

---

## Anti-Pattern 3: Recommending a Parallel-Active Monitoring Period

**What the LLM generates:** "Activate the new Flow in production and leave the Process Builder process active for a week to monitor before deactivating it."

**Why it happens:** General software migration advice recommends parallel running for safety, but this is incorrect for PB+Flow because the platform doesn't define cross-system execution order.

**Correct pattern:**
Never run both an active Process Builder process and an active record-triggered flow on the same object simultaneously. Deactivate the Process Builder the moment the Flow is activated. If a rollback is needed, re-activate PB and deactivate the Flow.

**Detection hint:** Any suggestion of parallel active automation on the same object for "monitoring."

---

## Anti-Pattern 4: Ignoring Pending Scheduled Actions at Cutover

**What the LLM generates:** "Deactivate the Process Builder process and activate the replacement Flow. The scheduled actions will continue from the Flow's Scheduled Paths."

**Why it happens:** LLMs conflate logical continuity (the Flow has equivalent scheduled paths) with runtime continuity (pending queued actions transfer).

**Correct pattern:**
Pending scheduled actions queued from a Process Builder process are immediately cancelled when the process is deactivated. They do NOT transfer to the replacement Flow. Teams must account for in-flight scheduled actions: query `FlowInterview` for pending items, plan cutover timing to minimize cancellations, or communicate to stakeholders that certain scheduled actions will not fire.

**Detection hint:** Response mentions "scheduled paths" as the replacement without noting that in-flight PB scheduled actions are cancelled on deactivation.

---

## Anti-Pattern 5: Not Adding Fault Paths to Generated Flows

**What the LLM generates:** Generated flow code or instructions that activate the Migrate to Flow output without adding fault paths to DML elements.

**Why it happens:** The Migrate to Flow tool generates flows without fault paths, and LLMs assume the generated output is complete.

**Correct pattern:**
Every DML element (Update Records, Create Records, Delete Records) in a migrated flow must have a Fault Path. Without it, any DML failure produces an unhandled error that sends an email to the running user and rolls back the transaction with no custom messaging. Add fault paths before activation and route them to appropriate error handling.

**Detection hint:** Generated flow XML has DML elements with no `<faultConnector>` entries, or instructions that skip directly from "generate" to "activate."

---

## Anti-Pattern 6: Using Process Builder EOL Dates from Training Data

**What the LLM generates:** "Process Builder retirement deadline is [incorrect date from training data]" — or claims there's still time when new creation is already blocked.

**Why it happens:** Multiple retirement deadline announcements were made and revised; training data may capture an earlier date. As of Spring '25, new Process Builder creation is already blocked.

**Correct pattern:**
New Process Builder creation was blocked in Spring '25. End of support (existing processes stop being maintained) is December 31 2025. Do not recommend waiting — all active processes should be migrated now.

**Detection hint:** Any specific retirement date claim that differs from "new creation blocked Spring '25, end of support December 31 2025."
