# Business Rules Engine — Work Template

Use this template when working on BRE design, review, or troubleshooting tasks.

## Scope

**Skill:** `omnistudio/business-rules-engine`

**Request summary:** (fill in what the user asked for — e.g., "Design eligibility rules for the Gold Broadband product", "Troubleshoot why the Decision Table is returning null", "Migrate hard-coded Apex eligibility logic to BRE")

---

## Context Gathered

Answer these before starting work:

- **Industries Cloud license confirmed?** (Yes / No / Unknown — BRE is not available without it)
- **Artifact type selected:** (Decision Table / Expression Set / Both — justify the choice)
- **Input attributes:** (list names, data types, and valid values — these become column API names)
- **Output attributes:** (list names and data types returned by the rule)
- **Caller context:** (Integration Procedure / Apex `ExpressionSetService.evaluate()` / both)
- **Versioning requirements:** (single active version / future-effective draft / parallel rule sets)
- **Current org API version:** (must be 55.0+ for full BRE Decision Table support)

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Product Eligibility Decision Table — flat row-based lookup, discrete conditions
- [ ] Pattern 2: Complex Eligibility with Expression Set — nested AND/OR boolean logic
- [ ] Pattern 3: Versioned Rule Rollout with Parallel Draft — future-effective rule staging

Justify the choice: ___

---

## Artifact Design

### Decision Table / Expression Set: `<ArtifactName>`

**Column / Condition Schema:**

| Name (API) | Type | Role | Operator | Notes |
|------------|------|------|----------|-------|
| `InputAttribute1` | Text | Input | Equals | |
| `InputAttribute2` | Decimal | Input | Range | |
| `OutputAttribute` | Boolean | Output | — | |

**Default/Fallback Row defined?** (Yes / No — must be Yes)

**Versioning plan:**
- Version 1 status: (Draft / Active)
- Planned activation date: ___
- Rollback procedure: ___

---

## Integration Wiring

**If calling from Integration Procedure:**

```
Action type: BusinessRules / DecisionTable
Input mapping:
  <ColumnApiName> ← %ipContextVariable%
Output mapping:
  %ipOutputVariable% ← <OutputColumnApiName>
```

**If calling from Apex:**

```apex
Map<String, Object> inputs = new Map<String, Object>{
    '<InputAttribute1>' => value1,
    '<InputAttribute2>' => value2
};
Map<String, Object> result = BusinessRules.ExpressionSetService.evaluate('<ArtifactApiName>', inputs);

// Always cast defensively
Object rawOutput = result.get('<OutputAttribute>');
// Cast to appropriate type — see gotchas.md for safe casting patterns
```

---

## Checklist

Run through before marking complete:

- [ ] Industries Cloud license confirmed on target org
- [ ] Artifact type justified (Decision Table vs. Expression Set)
- [ ] All input attribute names confirmed case-sensitive match with caller context
- [ ] Default/fallback row added to Decision Table
- [ ] BRE Test tab validated with happy path, boundary values, and unmatched inputs
- [ ] Version activated post-deploy (not assumed from metadata deploy)
- [ ] Only one version in Active status
- [ ] Output attribute null-check present in IP or Apex caller
- [ ] Versioning plan documented

---

## Notes

Record any deviations from the standard pattern and why:

- ___
