# LLM Anti-Patterns — DataRaptor Load and Extract

Common mistakes AI coding assistants make when generating or advising on DataRaptor Load and Extract.

## Anti-Pattern 1: Recommending Bulk Load via DataRaptor for High-Volume Operations

**What the LLM generates:** Instructions to use DataRaptor Load to insert or update hundreds or thousands of records, sometimes in a loop.

**Why it happens:** LLMs know DataRaptor Load writes to Salesforce and generalize it as a bulk-capable tool. They do not know it uses standard DML without Bulk API support.

**Correct pattern:**
- DataRaptor Load: use for single-record or small-set (< ~50 records) conversational DML only
- For bulk operations: use Bulk API 2.0, Apex Database.executeBatch(), or Data Loader outside the OmniStudio context

**Detection hint:** Any Load configuration in a loop, or any suggestion to use Load for data migration, batch sync, or large record imports.

---

## Anti-Pattern 2: Not Checking iferror After Load Steps

**What the LLM generates:** Integration Procedure configurations with a DataRaptor Load step followed immediately by a success response, with no iferror check.

**Why it happens:** LLMs model Load as a synchronous operation that throws on failure (like Apex DML). In OmniStudio, Load does not throw — it returns failure info in the output JSON.

**Correct pattern:**
After every Load step, add an explicit check:
- Set Values or Conditional step: check `<LoadStepName>:iferror` for non-empty value
- If `iferror` is present, surface the `<LoadStepName>:iferror:message` to the user or log it
- Only proceed to a success path if `iferror` is absent

**Detection hint:** Any Integration Procedure that has a Load step with no subsequent check for the `iferror` output path.

---

## Anti-Pattern 3: Using Object Label Instead of API Relationship Name in Output Mapping

**What the LLM generates:** Output mapping configurations using the object label (e.g., `Contact`) or the field label instead of the SOQL relationship API name (e.g., `Contacts`).

**Why it happens:** LLMs use the label form of object names which they see more frequently in natural language training data.

**Correct pattern:**
Use the API relationship name exactly as it appears in SOQL. For Account → Contact: `Contacts` (plural). Check in Setup > Object Manager > Relationships to confirm the SOQL relationship name.

**Detection hint:** Any output mapping path that uses a singular object name for a child relationship (e.g., `Contact`, `Case`, `Opportunity`) instead of the SOQL plural relationship name.

---

## Anti-Pattern 4: Using Turbo Extract for Cross-Object Data

**What the LLM generates:** Turbo Extract configuration for a use case that requires parent-child relationship data.

**Why it happens:** LLMs see "Turbo" as a superior option and default to it without knowing its limitations.

**Correct pattern:**
Turbo Extract supports only direct field reads on the base object. For any cross-object data (parent fields via lookup, child records via sub-select), use standard DataRaptor Extract.

**Detection hint:** Any Turbo Extract recommendation where the output mapping includes relationship fields (dot-notation to parent fields or array paths to child records).

---

## Anti-Pattern 5: Assuming Multi-Object Load Is Atomic

**What the LLM generates:** Multi-object Load configuration for a complex data entry pattern, with the assumption that if one object fails, nothing is committed.

**Why it happens:** LLMs model DML as transactional from their experience with database systems where multi-statement operations are atomic by default.

**Correct pattern:**
DataRaptor Load does not provide rollback for multi-object operations. Design Loads as single-object where possible. For complex multi-object scenarios requiring atomicity, use Apex DML in a single transaction with proper savepoint and rollback logic.

**Detection hint:** Any multi-object DataRaptor Load for a business operation that requires all-or-nothing semantics (e.g., creating an Order Header + Order Items where both must succeed).
