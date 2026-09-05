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
- Metadata API Developer Guide, *CustomField* → Fields (v62 PDF, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf; api_meta.txt:43422-43426) — the `formula` and `formulaTreatBlanksAs` elements and the `BlankAsBlank` / `BlankAsZero` enum (`references/metadata-examples.md`, gotchas "One Switch For The Whole Formula")
- Metadata API Developer Guide, *CustomField* → Declarative Metadata File Suffix, Wildcard Support, and Sample Definition (api_meta.txt:43226, 43248-43252, 43934-43946, 43983-43984) — `Object.Field__c` member syntax, no `*` wildcard, FLS pulled into profiles on retrieve, and the `<fields>`-inside-`<CustomObject>` shape (`references/metadata-examples.md` "Where the file lives", "package.xml")
- Metadata API Developer Guide, *CustomField* → `precision`, `scale`, `externalId` (api_meta.txt:43401-43404, 43563-43565, 43610-43612) — numeric return-type elements and why `externalId` / `unique` are inert on a formula (`references/metadata-examples.md` "How to read it")
- Metadata API Developer Guide — `<formula>` XML escaping in the guide's own samples: `Name &amp; &quot;Updated&quot;` (api_meta.txt:140599) and `&apos;` in `errorConditionFormula` (api_meta.txt:45439-45440) (gotchas "A `<` Or `&` In The Formula Breaks The Deploy")
- Metadata API Developer Guide, *ArticleType CustomField* → `type` (api_meta.txt:22161-22178) — the one place `Formula` is a `FieldType` value, which is why a regular formula field's `<type>` is its return type instead
- Metadata API Developer Guide, *FlowSettings* → `doesFormulaGenerateHtmlOutput` (api_meta.txt:116861-116863) — `BR()`, `IMAGE()`, `HYPERLINK()` named as the HTML-generating family, evaluated by the Flow engine rather than the formula-field engine (`references/metadata-examples.md`, IMAGE example)
- Object Reference, *Calculated Field Type* (v62 PDF, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf; object_reference.txt:2207-2211) — "Calculated fields are read-only fields in the API"; "You can filter on these fields in SOQL, but you don't replicate these fields"; "The length of text calculated fields is 3,900 characters or less — anything longer is truncated" (gotchas "Read-Only In The API", "Do Not Replicate", "Truncated At 3,900 Characters")
- Tips for Reducing Formula Size — Reducing the Length of Your Formula: https://developer.salesforce.com/docs/atlas.en-us.salesforce_formula_size_tipsheet.meta/salesforce_formula_size_tipsheet/reducing_formula_length.htm — "Maximum number of characters: 3,900 characters"; "Maximum formula size when saved: 4,000 bytes"
- Tips for Reducing Formula Size — Reducing Your Formula's Compile Size: https://developer.salesforce.com/docs/atlas.en-us.salesforce_formula_size_tipsheet.meta/salesforce_formula_size_tipsheet/reducing_formula_compile_size.htm — "Maximum formula size (in bytes) when compiled: 5,000 bytes"; compile size reflects the generated query, so shortening the formula text does not reduce it
- Salesforce Help — Formula Field Limits and Restrictions: https://help.salesforce.com/s/articleView?id=platform.formula_field_limits.htm&type=5 — all formula limits apply uniformly to every object; there is no object-dependent variant
