# LLM Anti-Patterns — Calculation Procedures

Common mistakes AI coding assistants make when generating or advising on OmniStudio Calculation Procedures and Calculation Matrices.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Calculation Procedures with Integration Procedures

**What the LLM generates:** "Use a Calculation Procedure to call an external API and process the response" when Calculation Procedures are for mathematical and logical computations, not for external callouts or data retrieval.

**Why it happens:** Both are OmniStudio "procedures" with similar naming. LLMs conflate their purposes because training data discusses them in the same OmniStudio context.

**Correct pattern:**

```text
Calculation Procedure vs Integration Procedure:

Calculation Procedure (Expression Set):
- Purpose: mathematical calculations, conditional logic, lookup tables
- Steps: constant, formula, lookup (from Calculation Matrix), conditional
- Use case: pricing calculations, eligibility scoring, rate determination
- Does NOT make external callouts or query Salesforce objects directly

Integration Procedure:
- Purpose: orchestrate data retrieval, transformation, and callouts
- Steps: DataRaptor, HTTP Action, Apex Remote Action, other IPs
- Use case: gather data from multiple sources, call external APIs
- CAN make callouts, query Salesforce, and transform data

For a workflow that calculates pricing from external data:
1. Integration Procedure: fetch data from API and Salesforce
2. Calculation Procedure: compute pricing from the fetched data
```

**Detection hint:** Flag Calculation Procedure recommendations that mention "API call," "HTTP," "DataRaptor," or "callout." These are Integration Procedure capabilities.

---

## Anti-Pattern 2: Not Versioning Calculation Matrices Before Updating

**What the LLM generates:** "Update the rates in the Calculation Matrix" without noting that Calculation Matrices support versioning (effective date ranges) and that directly modifying an active matrix changes results for all in-flight calculations.

**Why it happens:** LLMs treat Calculation Matrices like editable spreadsheets. The versioning mechanism (creating a new version with an effective date while keeping the old version for historical calculations) is specific to OmniStudio and underrepresented in training data.

**Correct pattern:**

```text
Calculation Matrix versioning:

1. DO NOT edit the active matrix version directly
2. Create a new version with the updated rates:
   - Clone the existing matrix version
   - Set the new effective start date
   - Update the values in the new version
   - Activate the new version

3. Version selection at runtime:
   - Calculation Procedure automatically selects the version
     whose effective date range covers the calculation date
   - Historical calculations reference the matrix version that
     was active at the time

4. Audit trail: previous versions remain accessible for audit
   and historical recalculation purposes
```

**Detection hint:** Flag Calculation Matrix update instructions that do not mention versioning or effective dates. Look for direct edits to active matrices without creating new versions.

---

## Anti-Pattern 3: Using Incorrect Step Ordering in Calculation Procedures

**What the LLM generates:** Calculation Procedure designs where a formula step references a variable that has not been set by a prior step, or where lookup steps reference input variables that are not yet available.

**Why it happens:** LLMs generate calculation steps logically but do not always enforce the strict sequential execution order of Calculation Procedures, where each step can only reference variables set by previous steps or input parameters.

**Correct pattern:**

```text
Calculation Procedure step execution:

Steps execute strictly top-to-bottom. Each step can reference:
1. Input parameters (passed from the calling OmniScript or IP)
2. Constants defined in earlier steps
3. Variables computed by earlier formula steps
4. Lookup results from earlier matrix lookup steps

Step ordering rules:
1. Constants first: define fixed values used by later formulas
2. Lookups next: retrieve rates/factors from Calculation Matrices
3. Formulas: compute using constants, lookups, and inputs
4. Conditional logic: branch based on computed values
5. Output assignment: set the variables returned to the caller

Debugging: if a step shows "null" or "0" unexpectedly,
check that the referenced variable was set by a PRIOR step.
```

**Detection hint:** Flag Calculation Procedure designs where formula steps reference variables defined in later steps. Check for circular references or forward references.

---

## Anti-Pattern 4: Ignoring Data Type Mismatches in Matrix Lookups

**What the LLM generates:** A Calculation Matrix with text column headers being queried with numeric inputs, or date comparisons against text fields, causing silent lookup failures.

**Why it happens:** Calculation Matrices are flexible and do not enforce strict data types at design time. LLMs configure lookups without validating that input data types match column data types.

**Correct pattern:**

```text
Calculation Matrix data type alignment:

Common mismatches:
- Input is a Number (42), matrix column contains Text ("42")
  Result: lookup fails silently, returns null
- Input is a Date, matrix column contains Text date strings
  Result: comparison fails or produces wrong matches
- Input has trailing spaces, matrix values do not
  Result: exact match fails

Prevention:
1. Define matrix column types explicitly (Text, Number, Date)
2. Ensure Calculation Procedure input variables match the column types
3. Test with edge cases: nulls, empty strings, boundary values
4. Use the Calculation Procedure preview to verify lookup results
5. Add a conditional step after lookup to handle null results (fallback)
```

**Detection hint:** Flag Calculation Matrix configurations where column types are not explicitly documented or where the Calculation Procedure input types are not verified against matrix column types.

---

## Anti-Pattern 5: Building Complex Business Logic in Calculation Procedures Instead of Apex

**What the LLM generates:** A Calculation Procedure with 50+ steps implementing complex conditional branching, nested lookups, and iterative calculations that would be more maintainable and testable in Apex.

**Why it happens:** LLMs try to solve everything within OmniStudio's declarative tools. Calculation Procedures are powerful for simple-to-moderate calculations but become unwieldy for complex logic that benefits from code structure, unit testing, and version control.

**Correct pattern:**

```text
When to use Calculation Procedures vs Apex:

Calculation Procedures are ideal for:
- Rate lookups from matrices (pricing tiers, tax rates, scores)
- Simple formulas with 5-15 steps
- Business-user-configurable calculations (non-developers maintain rates)
- Calculations that change frequently (matrix updates, not code deploys)

Move to Apex when:
- Logic exceeds 30-40 steps and is hard to follow visually
- Complex iteration or recursion is needed
- Unit testing is required for compliance
- The calculation references external data mid-computation
- Performance is critical (Apex is faster than declarative execution)

Hybrid approach:
- Use Calculation Procedure for rate lookups and simple formulas
- Use Integration Procedure with Apex Remote Action for complex logic
- Pass calculation inputs/outputs between the two
```

**Detection hint:** Flag Calculation Procedures with more than 40 steps or deeply nested conditional branches. Check whether the complexity warrants an Apex alternative.

---

## Anti-Pattern 6: Inventing a `ConnectApi` Apex Class to Invoke an Expression Set

**What the LLM generates:** Asked how to call a Calculation Procedure / expression set from Apex, the model produces a confident one-liner against a class that does not exist:

```apex
// DOES NOT COMPILE — ConnectApi.EvaluationService is not a real class
Map<String, Object> result =
    ConnectApi.EvaluationService.executeExpression(expressionSetName, inputs);
```

Variants swap in `ConnectApi.BusinessRulesEngine`, `ConnectApi.ExpressionSetService`, or a `.evaluate()` / `.run()` method on the same imagined class.

**Why it happens:** The `ConnectApi` namespace is a genuinely large, genuinely heterogeneous surface — dozens of `*Service`-suffixed classes covering Chatter, Communities, Commerce, Einstein and more. That makes `ConnectApi.<Domain>Service.<verb>()` a **highly productive naming template**, and the model completes it for any domain that has a Connect REST API, on the assumption that every Connect REST resource has a mirrored Apex class. It does not. Business Rules Engine has Connect *REST* APIs without a corresponding `ConnectApi` Apex class. The tell is that the surrounding explanation is usually correct — the model knows expression sets are invoked rather than queried, and knows Connect is involved — so only the symbol is confabulated, and it lands in a decision table where a developer copies it straight into a class.

**Correct pattern:**

```text
Documented invocation surfaces for Business Rules Engine expression sets:

  - Flow            : the "Evaluate Expression Set" action
  - OmniStudio      : Integration Procedure / Calculation Procedure steps
  - Connect REST API: the Business Rules Engine Connect resources under
                      /services/data/vXX.0/connect/...
                      (resolve the exact path in the Business Rules Engine
                       Connect API reference for your API version)

There is NO ConnectApi.EvaluationService class and no executeExpression()
method. Confirmed against the ConnectApi Namespace reference, whose class
list contains no EvaluationService entry.

If Apex must be the caller, call the Connect REST resource over a Named
Credential. Do not guess an Apex symbol.
```

**Detection hint:** Mechanically checkable in two ways. (1) Before accepting any `ConnectApi.<Something>` symbol in generated Apex, confirm `<Something>` appears in the ConnectApi Namespace class list — the namespace is documented exhaustively, so absence from that list is proof of non-existence, not merely absence of evidence. A compile in a scratch org settles it in seconds. (2) Treat the inference "this feature has a Connect REST API, therefore it has a `ConnectApi` Apex class" as invalid: the two surfaces are curated independently and REST coverage is much broader. Any generated code that pairs a correct REST resource with a same-named Apex class is exhibiting exactly this error.
