# Formula Field Design Template

Use this before creating or rewriting a complex formula field.

---

## Overview

| Property | Value |
|----------|-------|
| Field label | TODO |
| API name | TODO |
| Return type | Text / Number / Currency / Percent / Checkbox / Date / URL |
| Object | TODO |
| Business purpose | TODO |

## Design Checks

| Question | Answer |
|----------|--------|
| Is a formula field the right tool? | TODO |
| If not a formula, what should store the value? | TODO |
| Cross-object references used? | TODO |
| Null / blank scenarios handled? | TODO |
| Reporting impact considered? | TODO |

## Formula Draft

```text
TODO
```

## Test Cases

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Happy path | TODO | TODO |
| Blank value | TODO | TODO |
| Zero or false value | TODO | TODO |
| Cross-object missing parent data | TODO | TODO |

## Documentation

- [ ] Field description updated with business rule
- [ ] Any helper formulas or dependencies documented
- [ ] Decision recorded if formula replaced a stored field or vice versa
