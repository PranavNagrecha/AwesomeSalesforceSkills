# LLM Anti-Patterns — DataRaptor Patterns

Common mistakes AI coding assistants make when generating or advising on OmniStudio DataRaptor design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using DataRaptor Extract When Turbo Extract Is Sufficient

**What the LLM generates:** "Use a DataRaptor Extract to retrieve Account data" for simple single-object queries without filters or transformations, when Turbo Extract is faster and requires no field mapping configuration.

**Why it happens:** DataRaptor Extract is the more commonly documented component. Turbo Extract is newer and has less training data. LLMs default to the more familiar option.

**Correct pattern:**

```text
DataRaptor Extract vs Turbo Extract:

Turbo Extract:
- Single object, no mapping required
- Faster execution (no transformation overhead)
- Supports basic WHERE clauses
- Best for: simple record retrieval, prefill scenarios
- Cannot transform or reshape data

DataRaptor Extract:
- Multi-object support with relationship queries
- Full field mapping and transformation
- Formula fields in mapping
- Best for: complex data retrieval with reshaping
- More configuration overhead

Decision: if you just need fields from one object with a simple
filter, use Turbo Extract. If you need joins, transformations,
or formula-based mappings, use DataRaptor Extract.
```

**Detection hint:** Flag DataRaptor Extract recommendations for simple single-object queries. Check whether Turbo Extract would be simpler and faster.

---

## Anti-Pattern 2: Putting Business Logic in DataRaptor Transform Instead of Integration Procedure

**What the LLM generates:** Complex DataRaptor Transform configurations with conditional logic, multi-step transformations, and formula-heavy mappings that should be orchestrated in an Integration Procedure.

**Why it happens:** DataRaptor Transform is flexible and can reshape data, but LLMs overload it with logic that belongs in the orchestration layer (Integration Procedure) or in Apex.

**Correct pattern:**

```text
DataRaptor Transform scope:

Appropriate for Transform:
- Field renaming (API names to display names)
- Simple formula mappings (concatenation, date formatting)
- Flattening nested JSON structures
- Filtering out unnecessary fields from a payload

Move to Integration Procedure or Apex when:
- Conditional branching based on data values
- Iterating over collections with different processing per item
- Calling external services based on transform results
- Error handling with different paths
- Logic that would be described as "business rules"

The Transform should TRANSFORM data shape.
The Integration Procedure should ORCHESTRATE data flow.
```

**Detection hint:** Flag DataRaptor Transforms with more than 20 formula mappings or conditional logic. Check whether an Integration Procedure with simpler DataRaptors would be clearer.

---

## Anti-Pattern 3: Not Setting Extract Filter Criteria Correctly

**What the LLM generates:** DataRaptor Extract configurations with hardcoded filter values instead of using input parameters, or with filters that do not match the expected data types.

**Why it happens:** LLMs configure filters with literal values from examples rather than parameterizing them. The input parameter syntax (using merge fields from the calling OmniScript or Integration Procedure) is specific to OmniStudio.

**Correct pattern:**

```text
DataRaptor Extract filter patterns:

Hardcoded (avoid in most cases):
  WHERE: Status__c = 'Active'
  Problem: not reusable, cannot be parameterized

Parameterized (recommended):
  WHERE: AccountId = %AccountId%
  The %AccountId% is replaced at runtime with the value from the
  calling OmniScript or Integration Procedure input

Multiple filters:
  WHERE: AccountId = %AccountId% AND Status__c = %Status%

Input parameter passing:
  OmniScript -> Integration Procedure -> DataRaptor Extract
  Each level passes parameters via the JSON data structure

Common mistake: using %ContextId% when the OmniScript passes
the value under a different key name. Verify the exact key name
in the OmniScript's data JSON.
```

**Detection hint:** Flag DataRaptor Extract configurations with hardcoded filter values instead of parameterized `%variable%` syntax. Check that parameter names match the calling context's data keys.

---

## Anti-Pattern 4: Creating Separate DataRaptors for Each Object Instead of Multi-Object Extract

**What the LLM generates:** Three separate DataRaptor Extracts (one for Account, one for Contacts, one for Opportunities) called sequentially in an Integration Procedure, when a single multi-object DataRaptor Extract could retrieve all related data in one operation.

**Why it happens:** LLMs break problems into single-concern components. While separation is generally good, OmniStudio's DataRaptor Extract supports multi-object extraction with relationship queries, reducing the number of operations.

**Correct pattern:**

```text
Single vs multiple DataRaptor Extracts:

Multiple (when appropriate):
- Objects are unrelated or in different contexts
- Each extraction needs different error handling
- Extractions can run in parallel (Integration Procedure parallel block)

Single multi-object Extract (when appropriate):
- Objects are related (Account -> Contacts, Opportunities)
- Data is needed together in the same step
- Reduces the number of Salesforce queries (SOQL efficiency)
- Simpler Integration Procedure flow

Multi-object Extract configuration:
1. Primary object: Account
2. Related objects: Contact (child relationship), Opportunity (child)
3. Map fields from all objects in a single Extract
4. Output: nested JSON with parent and child data
```

**Detection hint:** Flag Integration Procedures that call 3+ sequential DataRaptor Extracts on related objects. Check whether a single multi-object Extract would be more efficient.

---

## Anti-Pattern 5: Not Handling Null Values in DataRaptor Load Mappings

**What the LLM generates:** DataRaptor Load configurations that map input fields directly to Salesforce fields without handling null or empty values, which can accidentally blank out existing field values during updates.

**Why it happens:** LLMs configure field mappings for the happy path (all values present). The scenario where an input field is null or empty and the Load overwrites an existing value with null is not commonly addressed.

**Correct pattern:**

```text
DataRaptor Load null handling:

Default behavior:
- If an input field is null/empty, the mapped Salesforce field is set to null
- This can accidentally erase existing data during updates

Prevention strategies:
1. Use "Default Value" in mapping to provide a fallback
2. Use formula mapping with IF() to check for null:
   IF(%InputField% != null, %InputField%, %ExistingValue%)
3. Filter null values in the Integration Procedure BEFORE passing to Load
4. Use separate Load configurations for required vs optional fields
5. Set "Upsert Key" to External ID to control update scope

For partial updates:
- Only map the fields that should be updated
- Do NOT map fields that should retain their existing values
- Consider separate DataRaptor Loads for create vs update scenarios
```

**Detection hint:** Flag DataRaptor Load configurations that map 10+ fields to Salesforce without null handling. Check for update scenarios where null input could overwrite existing data.
