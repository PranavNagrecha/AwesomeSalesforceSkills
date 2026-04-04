# Gotchas — Calculation Procedures

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Matrix Lookup Returns Only the First Matching Row

**What happens:** When a Calculation Matrix lookup step executes, the platform returns only the first row that satisfies all input column criteria. If the matrix contains duplicate input combinations (same values across all input columns in the same active version), the second and subsequent matching rows are silently ignored.

**When it occurs:** Happens when rows are loaded from a CSV or spreadsheet without deduplication, or when a partial key is used across two rows that share the same primary input values but differ only on a column the lookup does not use. It also occurs after a matrix data migration where the source system allowed non-unique keys.

**How to avoid:** Enforce unique input column combinations for every active matrix version before loading. If range columns are used (`QuantityMin`/`QuantityMax`), verify ranges do not overlap across rows. Use the matrix test harness in the OmniStudio designer to probe boundary values before activating a version.

---

## Gotcha 2: Inactive Procedure Version Causes Runtime Error, Not Empty Result

**What happens:** Calling a Calculation Procedure whose version is not active (`IsActive = false` on `ExpressionSetVersion`) throws a runtime exception. The caller does not receive an empty result map — it receives an error. In an OmniScript context this surfaces as a failed action step, typically with an opaque "Execution failed" message that masks the activation root cause.

**When it occurs:** Most commonly after creating a new procedure version to fix a bug or update logic. Developers create and test the new version but forget to activate it before going live, or they deactivate the old version before activating the new one, creating a window where no version is active.

**How to avoid:** Follow activation order: activate the new version first, verify it is callable, then deactivate the old version. Never deactivate the current active version until the replacement is confirmed active. Include an activation check in the deployment runbook: query `ExpressionSetVersion WHERE IsActive = true` for the target procedure before declaring the release complete.

---

## Gotcha 3: Variable Data Type Mismatch With Matrix Column Produces Silent Null

**What happens:** If the Calculation Procedure declares a variable as `Decimal` but the matching Calculation Matrix output column holds `Text` values (or vice versa), the column-to-variable mapping silently assigns null to the variable. No error is thrown. Downstream Assignment steps that reference the null variable produce incorrect output (null arithmetic returns null) or throw a null-reference error later in the procedure.

**When it occurs:** Most commonly when the matrix was created with a `Text` column (easier default in the UI) and the procedure variable was later declared as `Decimal` to support arithmetic. Also occurs after a matrix column type change where the associated procedure variable type was not updated.

**How to avoid:** Before finalizing a Decision Matrix Lookup step, compare each output column data type in the matrix definition against the data type of the procedure variable it maps to. They must match exactly. Use the built-in test execution panel: after running a test, inspect the variable state after the lookup step. A null output where a numeric value was expected is the most reliable indicator of a type mismatch.

---

## Gotcha 4: Matrix Version Rank Collision Causes Non-Deterministic Selection

**What happens:** When two or more matrix versions are active at the same time for overlapping date ranges and share the same `Rank` value, the platform's version selection behavior is non-deterministic. Different executions may return results from different versions. This produces intermittent, hard-to-reproduce pricing or eligibility discrepancies.

**When it occurs:** Occurs when a new version is created by cloning an existing one without incrementing the `Rank`. It also occurs when multiple team members create versions independently without coordinating rank assignments. Date-effective versioning relies on both date range and rank; rank alone does not guarantee uniqueness.

**How to avoid:** Establish a rank convention before creating the first matrix (e.g., increment by 10 to leave room for future inserts). Document the convention. When creating a new version to replace an existing one, either assign a higher rank than the predecessor or set the predecessor's `EndDateTime` to close its window, ensuring no overlap exists at the same rank.

---

## Gotcha 5: Sub-Procedure Must Be Activated Before Parent Activation

**What happens:** A parent Calculation Procedure containing a SubExpression step that references an inactive child procedure will activate successfully but fail at runtime when the SubExpression step executes. Activation of the parent does not validate whether referenced sub-procedures are active.

**When it occurs:** When deploying a multi-procedure design in a new environment (e.g., production release) and the deployment script activates procedures in alphabetical or arbitrary order rather than dependency order. Also occurs during testing when a child procedure is temporarily deactivated for debugging.

**How to avoid:** Map the dependency tree before activation. Activate leaf-level sub-procedures first, then parent procedures last. In CI/CD pipelines, add a post-deploy step that queries `ExpressionSetVersion WHERE IsActive = true` for every procedure referenced in a SubExpression step and asserts all are active before activating the top-level procedure.
