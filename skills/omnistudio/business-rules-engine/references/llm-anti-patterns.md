# LLM Anti-Patterns — Business Rules Engine

Common mistakes AI coding assistants make when generating or advising on Business Rules Engine.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Flow Decision Elements for Multi-Attribute Eligibility

**What the LLM generates:** Advice to use a Flow Decision element with a formula resource like `{!applicantAge} >= 18 && {!applicantState} == 'CA'` to evaluate eligibility, or a suggestion to build a Screen Flow with branching logic per product.

**Why it happens:** Flow is the dominant no-code automation tool in core Salesforce and is heavily represented in training data. LLMs pattern-match "eligibility" and "no-code" to Flow without recognizing that BRE is the purpose-built Industries Cloud tool for multi-attribute rule evaluation that must be business-analyst-managed.

**Correct pattern:**

```
Use a BRE Decision Table for flat multi-attribute eligibility (discrete combinations).
Use a BRE Expression Set for nested AND/OR boolean eligibility.
Reserve Flow Decision elements for workflow branching AFTER the BRE rule result is known
(e.g., "if IsEligible = true, navigate to the product display screen").
```

**Detection hint:** Look for suggestions containing `{!formula}` conditions inside Decision elements on topics that describe eligibility, product qualification, or discount determination in an Industries org context.

---

## Anti-Pattern 2: Assuming Metadata Deployment Activates BRE Versions

**What the LLM generates:** A deployment runbook that includes `sf project deploy start` for the BRE metadata and then immediately asserts the rules are live in production, with no post-deploy activation step.

**Why it happens:** For most Salesforce metadata types (Flows, Apex classes, Custom Objects), a metadata deployment makes the artifact active and operational immediately. LLMs generalize this pattern to BRE. However, BRE version activation is a data-layer record update, not part of the metadata deployment payload.

**Correct pattern:**

```
Step 1: Deploy BRE metadata via sf project deploy start (or Metadata API).
         Result: version arrives in production as Draft status.

Step 2: Activate the version post-deploy using one of:
  - BRE UI: open the Decision Table / Expression Set, select the version, click Activate.
  - Connect API: PATCH /connect/business-rules/decision-tables/{id}/versions/{versionId}
    with body: {"status": "Active"}

Never assume a metadata deploy activates a BRE version.
```

**Detection hint:** Look for deployment runbooks that do not include an explicit activation step for Decision Tables or Expression Sets after the deploy command.

---

## Anti-Pattern 3: Treating ExpressionSetService Return Values as Strongly Typed

**What the LLM generates:** Apex code that directly assigns the return map value to a typed variable without casting:

```apex
// Wrong — will throw TypeException
Decimal rate = result.get('DiscountRate');
Boolean eligible = result.get('IsEligible');
```

**Why it happens:** LLMs know `Map<String, Object>` is the return type but assume the `Object` value can be auto-unboxed to the declared variable type, as it can in some Java and Apex contexts. BRE's runtime typing is not guaranteed to match the column data type declaration, so direct assignment fails.

**Correct pattern:**

```apex
// Safe casting pattern
Object rateRaw = result.get('DiscountRate');
Decimal rate = rateRaw instanceof Decimal
    ? (Decimal) rateRaw
    : (rateRaw != null ? Decimal.valueOf(String.valueOf(rateRaw)) : null);

Object eligibleRaw = result.get('IsEligible');
Boolean eligible = 'true'.equalsIgnoreCase(String.valueOf(eligibleRaw));
```

**Detection hint:** Look for direct assignments from `result.get(key)` to `Decimal`, `Integer`, `Boolean`, or `Date` typed variables without explicit casting or instanceof guards.

---

## Anti-Pattern 4: Conflating BRE Decision Tables with Calculation Matrices

**What the LLM generates:** Advice to use a Calculation Matrix for eligibility rules, or to use a Decision Table for tiered pricing that changes on scheduled dates. Example wrong guidance: "Use a Calculation Matrix with condition columns for `IsEligible` determination."

**Why it happens:** Both Decision Tables and Calculation Matrices are lookup-based BRE artifacts and appear together in the OmniStudio documentation. LLMs confuse them because both accept input columns and return output columns. The critical distinction — that Calculation Matrices use date-effective version selection (automatic by timestamp) while Decision Tables use row-priority rule matching — is a platform nuance that requires deep familiarity.

**Correct pattern:**

```
Use Calculation Matrix (Decision Matrix) when:
- The lookup value changes on scheduled effective dates (e.g., regulatory rate schedules)
- Version selection should be automatic based on transaction timestamp
- The lookup is a simple tabular rate lookup (no condition operators needed)

Use Decision Table when:
- Selection is based on multi-attribute condition matching (Equals, In, Range operators)
- Business analysts need to add/remove condition rows based on eligibility logic
- Effective date is not the version selection mechanism
```

**Detection hint:** Look for suggestions that use "Calculation Matrix" and "eligibility" in the same sentence, or "Decision Table" with "effective date" as the version selection mechanism.

---

## Anti-Pattern 5: Generating BRE Metadata Without the Industries Namespace or License Guard

**What the LLM generates:** A bare `DecisionTable` metadata XML or Apex code referencing `BusinessRules.ExpressionSetService` without noting the Industries Cloud license requirement, or generating code that assumes the metadata type is available in a standard Developer Edition org.

**Why it happens:** LLMs generate syntactically plausible metadata and Apex based on documentation patterns without surfacing the license precondition. The result is a deployment that fails with `Invalid type: DecisionTable` or a runtime `TypeException: Method does not exist or incorrect signature: BusinessRules.ExpressionSetService.evaluate` in orgs without the Industries license.

**Correct pattern:**

```
Before generating or deploying any BRE metadata or Apex:
1. Confirm the target org has an Industries Cloud license (Communications Cloud,
   Financial Services Cloud, Health Cloud, Energy and Utilities Cloud, or equivalent).
2. In scratch org contexts, include the Industries feature in project-scratch-def.json:
   { "features": ["Industries"] }
3. In Apex, guard the ExpressionSetService call in a try/catch and verify
   the type exists at runtime if the code may run in non-Industries orgs:
   Type t = Type.forName('BusinessRules', 'ExpressionSetService');
   if (t == null) { /* not available — handle gracefully */ }
```

**Detection hint:** Look for BRE metadata XML generation or `ExpressionSetService` Apex code that does not include a comment or guard about the Industries Cloud license requirement.

---

## Anti-Pattern 6: Omitting the Default/Fallback Row in Decision Tables

**What the LLM generates:** A Decision Table design with condition rows for all expected input combinations but no default fallback row for unmatched inputs. The generated Integration Procedure then assumes the output attribute is always non-null.

**Why it happens:** LLMs optimize for the happy path. The common code generation pattern assumes inputs are always valid and match a defined row. The BRE platform returns null output attributes for unmatched inputs without throwing an error, which causes silent failures downstream that are hard to diagnose.

**Correct pattern:**

```
Always add a default row to every Decision Table:
- Leave all condition columns blank (matches any input combination)
- Set output columns to safe defaults (IsEligible = false, ProductCode = null)
- Assign the default row the lowest priority (highest row number)

In the Integration Procedure or Apex caller, always null-check the output
attributes before using them in downstream logic.
```

**Detection hint:** Look for Decision Table designs with no row that has all condition columns blank, or for IP/Apex code that uses BRE output attributes without a null guard.
