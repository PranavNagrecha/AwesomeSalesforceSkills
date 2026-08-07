# Well-Architected Mapping: Formula Fields

## Pillars Addressed

### Performance

Formula fields are easy to create and easy to overuse.

- Careful cross-object usage prevents avoidable reporting and page-load pain.
- Simple formulas reduce admin tendency to offload all logic into runtime recalculation.

### Reliability

Good formulas return the right value for real-world edge cases.

- Explicit blank handling reduces misleading outputs.
- Correct tool choice prevents formula fields from being misused as historical snapshots.

### Operational Excellence

Readable formulas are maintainable formulas.

- Documentation and simpler expressions reduce admin handoff risk.
- Review discipline prevents nested formula debt from spreading across the org.

## Pillars Not Addressed

- **Security** - formula design does not directly govern record access.
- **User Experience** - formulas can help UX, but this skill is about correctness and maintainability first.

## Official Sources Used

- Salesforce Well-Architected Overview — performance and maintainability framing for formula usage
- Object Reference — object and relationship semantics behind formula references
- Metadata API Developer Guide — formula metadata behavior during deployment
- Tips for Reducing Formula Size — Reducing the Length of Your Formula: https://developer.salesforce.com/docs/atlas.en-us.salesforce_formula_size_tipsheet.meta/salesforce_formula_size_tipsheet/reducing_formula_length.htm — "Maximum number of characters: 3,900 characters"; "Maximum formula size when saved: 4,000 bytes"
- Tips for Reducing Formula Size — Reducing Your Formula's Compile Size: https://developer.salesforce.com/docs/atlas.en-us.salesforce_formula_size_tipsheet.meta/salesforce_formula_size_tipsheet/reducing_formula_compile_size.htm — "Maximum formula size (in bytes) when compiled: 5,000 bytes"; compile size reflects the generated query, so shortening the formula text does not reduce it
- Salesforce Help — Formula Field Limits and Restrictions: https://help.salesforce.com/s/articleView?id=platform.formula_field_limits.htm&type=5 — all formula limits apply uniformly to every object; there is no object-dependent variant
