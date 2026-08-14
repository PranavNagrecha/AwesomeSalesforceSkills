# Gotchas — Business Rules Engine

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: BRE Version Activation Is a Data Change, Not a Metadata Change

**What happens:** A team deploys a new Decision Table version through a metadata deployment to production. They expect the new rules to take effect immediately. Runtime continues to return results from the old version. The new version arrives in production as Draft and is never evaluated.

**When it occurs:** Every time a team uses `sf project deploy start` or the Metadata API `deploy()` to push a new BRE version. Metadata deployments transfer the version definition records but do not flip the `Status` field from Draft to Active. This is because BRE version activation is a data-layer record update (`PATCH` on the version record), not a metadata-layer operation. The Salesforce metadata model treats activation as a post-deploy step.

**How to avoid:** Build a post-deployment activation step into every release that touches BRE artifacts. Options:
1. Use the BRE UI in production to manually activate the new version immediately after deploy.
2. Script activation via the Connect API: `PATCH /connect/business-rules/decision-tables/{decisionTableId}/versions/{versionId}` with `{"status": "Active"}`.
3. Include the Connect API activation call in a post-deploy script or a CI/CD pipeline step.
Document the activation step explicitly in the release checklist so it cannot be missed.

---

## Gotcha 2: Input Attribute Name Mismatches Are Silent — No Runtime Error

**What happens:** A practitioner configures a Decision Table with column API name `CreditTier` (capital C, capital T). The Integration Procedure action element passes `creditTier` (lowercase c). At runtime the table receives `null` for the `CreditTier` input and matches the default row — returning `IsEligible = false` for all customers. No error is thrown; the IP succeeds and returns a result, just the wrong one.

**When it occurs:** Any time the input attribute names in the calling context (Integration Procedure JSON, Apex `Map` key, or OmniScript context variable) do not exactly match the column API names in the BRE artifact. Names are case-sensitive and whitespace-sensitive. This mismatch is not caught by the BRE designer, the IP designer, or any validation rule.

**How to avoid:**
- Establish a naming convention for all BRE column API names before authoring (e.g., PascalCase) and apply it consistently.
- After building an Integration Procedure action that calls a BRE artifact, use the BRE Test tab to confirm expected outputs with the exact input keys the IP will pass.
- In Apex, define input key constants in a utility class rather than inline string literals to catch typos at compile time.

---

## Gotcha 3: Decision Table Row Evaluation Stops at First Match — Overlapping Rows Return Wrong Results

**What happens:** A Decision Table has two rows:
- Row 1 (priority 1): `CreditTier = 'Gold'`, `Region = 'West'` → `DiscountRate = 15`
- Row 2 (priority 2): `CreditTier = 'Gold'`, `Region = 'West'` → `DiscountRate = 10`

Row 2 was intended as a lower-priority fallback for a different region but was accidentally duplicated with the same condition values. At runtime, customers matching Gold/West always receive `DiscountRate = 15` from Row 1 and Row 2 is never evaluated. There is no warning or error.

**When it occurs:** When rows have overlapping or duplicate condition values and different outputs. Also occurs when the `In` operator is used on two rows that share a value in their set — for example, Row A uses `Region IN ['West', 'Central']` and Row B uses `Region IN ['Central', 'East']`: any input with `Region = 'Central'` will always match whichever row has higher priority, regardless of which was intended.

**How to avoid:**
- Audit the Decision Table for overlapping rows before activation. Export the table to CSV (BRE supports CSV-based export) and sort by condition columns to identify duplicates.
- Use mutually exclusive condition values across rows (e.g., use `Equals` instead of `In` on columns where exclusivity is required).
- Test all boundary inputs explicitly in the BRE Test tab to confirm the expected row is being selected.

---

## Gotcha 4: ExpressionSetService Returns Untyped Object — Casting Errors at Runtime

**What happens:** An Apex developer calls `BusinessRules.ExpressionSetService.evaluate()`, retrieves the output value from the return map, and tries to assign it directly to a typed variable: `Decimal rate = result.get('DiscountRate')`. A `System.TypeException: Invalid conversion from runtime type Integer to Decimal` is thrown. Alternatively, the developer casts to `String` when the output is Boolean, causing a `TypeException` on the first matching record.

**When it occurs:** `ExpressionSetService.evaluate()` returns `Map<String, Object>`. All values in the map are typed as `Object`. The actual runtime type depends on how the output attribute was configured in the Expression Set or Decision Table — a numeric output may come back as `Integer`, `Long`, or `Decimal` depending on the value. Salesforce does not document a guaranteed return type per column data type.

**How to avoid:**
- Always cast defensively using string conversion as the safest path for display values: `String.valueOf(result.get('DiscountRate'))`.
- For numeric values used in math, use: `Decimal rate = result.get('DiscountRate') instanceof Decimal ? (Decimal)result.get('DiscountRate') : Decimal.valueOf(String.valueOf(result.get('DiscountRate')))`.
- For booleans: `Boolean isEligible = 'true'.equalsIgnoreCase(String.valueOf(result.get('IsEligible')))`.
- Write Apex unit tests that cover the actual return type from the BRE artifact in a test org, not just mock the map.

---

## Gotcha 5: BRE Is Not Available in Developer Edition Orgs Without Industries License

**What happens:** A developer sets up a Developer Edition org to build and test a BRE-based solution. The Business Rules Engine menu item is absent from Setup. Metadata deployments of `DecisionTable` or `ExpressionSet` types fail with `Invalid type: DecisionTable` or a similar metadata type not found error.

**When it occurs:** BRE is part of the OmniStudio Industries Cloud feature set and requires an Industries-specific license (Communications Cloud, Energy and Utilities Cloud, Financial Services Cloud, Health Cloud, or similar). Standard Developer Edition orgs and Enterprise Edition orgs without an Industries add-on do not have BRE available.

**How to avoid:**
- Use a dedicated Industries Cloud scratch org or partner developer org that has the Industries license feature enabled.
- In `project-scratch-def.json`, include the relevant Industries feature flag (e.g., `"features": ["Industries"]`) and confirm the feature is available in your Dev Hub.
- Confirm license availability in a target org before including BRE artifacts in a deployment package: run `SELECT Id, Label FROM PermissionSet WHERE Label IN ('Rule Engine Runtime', 'Rule Engine Designer')` — these are the permission sets that ship with the Business Rules Engine permission set licenses, so their absence means the feature is not provisioned.

---

## Gotcha 6: BRE Access Comes from Permission Set Licenses, Not the Profile

**What happens:** An admin builds and activates an Expression Set, tests it successfully from the BRE UI, then wires it into an Integration Procedure for service agents. Every agent invocation returns no result. The org has the Industries license; the users do not have the permission sets that come with it. The admin's own success proves nothing — the admin is the only user who can run the rule.

**When it occurs:** Whenever a non-author identity executes a rule. BRE access is granted through the permission sets associated with the Business Rules Engine permission set licenses, not through the profile and not through the org's Industries license alone. The two core sets are:

- **Rule Engine Runtime** — run expression sets and lookup tables, Read access to Business Rules Engine objects, read decision tables. This is what every executing identity needs: agents, Experience Cloud users, and the integration user behind an Integration Procedure.
- **Rule Engine Designer** — all of the above plus Create, Update, Delete access to Business Rules Engine objects and decision tables, and use of context definition tags as list variables in expression sets.

Three more are separately required and are the usual omission:

- **Context Service Admin** — create and activate context definitions for use as list variables.
- **Context Service Runtime** — execute expression sets that use context definition tags as list variables. Rule Engine Runtime alone does not cover this path.
- **Decision Explainer Service Access** — configure explanations for expression set steps and capture action logs for each run.

**How to avoid:**
- Assign Rule Engine Runtime to every identity that executes rules and Rule Engine Designer only to authors. Do not grant Designer as a shortcut to make runtime work.
- If any expression set uses context tags as list variables, pair Rule Engine Runtime with Context Service Runtime for runtime users, and Context Service Admin for authors.
- Test as a runtime user, not as the author. The BRE Test tab runs under the author's permissions and will not reproduce a runtime access failure.
- The five names above are the documented sets — there is no generic `Business Rules Engine User` or `BRE Admin`. Confirm the exact labels in Setup → Permission Sets before writing them into an access design.
