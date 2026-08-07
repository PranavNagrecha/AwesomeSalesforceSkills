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

---

## Anti-Pattern 6: Justifying the Bulk Warning With Fabricated Governor Arithmetic

**What the LLM generates:** The right conclusion ("don't use Data Mapper Load for bulk") supported by numbers that do not add up:

> "Data Mapper Load uses standard DML — one DML statement per record iteration. For 500 records, this consumes 500 DML statements in a single transaction, quickly hitting governor limits. The Integration Procedure fails with `Too many DML statements`."

**Why it happens:** The model reaches a correct recommendation and then **back-fills a mechanism to justify it**, because a bare "don't do this" reads as weaker than a causal explanation. The back-fill is never checked against the limit it invokes: the DML **statement** limit is 150, so a run that genuinely issued one statement per record would fail at iteration 151 and never reach 500. The "500" is picked as a round illustrative volume, not derived. A second confusion feeds it — the DML **rows** limit is 10,000, and models routinely blur "statements" and "rows" into a single "DML limit", which makes 500 feel comfortably inside a ceiling it is not being measured against.

This matters beyond pedantry. A reader who trusts the arithmetic concludes the safe threshold is somewhere near 500 and builds a 300-record loop that fails in production. Fabricated supporting detail attached to correct advice is more dangerous than no detail, because it converts a directional warning into a false quantitative permission.

**Correct pattern:**

```text
Per-transaction limits (Apex Developer Guide, sync and async alike):
  Total number of DML statements issued                    : 150
  Total records processed as a result of DML statements    : 10,000

A LOOP-DRIVEN Load therefore dies at the 151st iteration, on statements
— not on rows, which are nowhere near their ceiling.

The claim that is safe to make without further checking:
  "Data Mapper Load writes via platform DML, not the Bulk API, so the
   entire write is bounded by the calling transaction's governor limits.
   It is unsuitable for high-volume writes."

The claim that needs a source before you make it:
  any statement about how many DML statements Load issues internally for
  a SINGLE invocation carrying an N-element array. A bulkified 500-row
  write sits well inside both limits. Verify against the Omnistudio Data
  Mapper Load documentation; do not infer it from the loop case.
```

**Detection hint:** Whenever generated guidance pairs a record count with `Too many DML statements`, check the count against 150 — any figure above it that is described as "consuming N DML statements" before failing is fabricated arithmetic. Second, mechanical and general: grep for the phrase `DML limit` / `DML limits` used without the word `statements` or `rows`. Salesforce has two distinct DML ceilings that differ by a factor of ~67, and guidance that does not name which one it means has not checked either.
