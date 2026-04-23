# Well-Architected Notes — Apex Regex And Pattern Matching

## Relevant Pillars

### Performance

Regex is a tempting generic hammer. In Apex, it competes with the 10-second sync CPU limit and a 60-second async limit. A pattern that takes 2ms per record becomes a 400ms trigger on 200 records — fine. A pattern with catastrophic backtracking on a single 50KB string can exhaust the entire transaction.

Tag findings as Performance when:
- `Pattern.compile(...)` is called inside a loop with the same literal
- nested quantifiers appear on user-controlled input
- a regex runs on strings that routinely exceed 100KB
- `replaceAll` on a large string rebuilds it when `replaceFirst` would do

### Security

Regex sits at the input-validation boundary. Getting it wrong either lets malformed data through (too permissive) or rejects valid data (too strict, frustration, shadow workarounds). The classic case: an email regex that accepts `a@b` or rejects `user+tag@domain.co.uk`.

Tag findings as Security when:
- user input is concatenated into a pattern without `Pattern.quote`
- a validation regex is unanchored when it should be whole-string
- an allowlist pattern is permissive by default (`.*`)
- the pattern is used for authentication / authorization decisions

### Reliability

Apex regex has a 1,000,000-character cap and will throw `LimitException` on large inputs. Reliable code guards input size before matching. Silent failures happen when `matches()` is used where `find()` was meant; downstream code receives wrong answers without error.

Tag findings as Reliability when:
- input size is not checked before regex is applied
- the choice between `matches()` and `find()` is wrong for the semantic intent
- `split` is used with an unescaped metacharacter

## Architectural Tradeoffs

- **Apex regex vs SOQL `LIKE`:** SOQL `LIKE` runs at the database and is cheaper for simple wildcards. Apex regex is more expressive but applies only to already-loaded records. Use `LIKE` to filter rows; use regex to validate or extract within rows.
- **Apex regex vs Flow formula `REGEX()`:** Flow formulas run on single records at a time and are fine for admin-owned validation. Apex regex is the right fit for bulk or callout transformation.
- **Regex vs purpose-built API:** for JSON, use `JSON.deserialize`; for XML, use `Dom.Document`; for CSV, use a parser library. Regex on structured data is fragile.

## Anti-Patterns

1. **Regex-as-parser** — using a pattern to split JSON or XML. The formats have escaping and nesting that regex cannot handle correctly. Use the structured API instead.
2. **Unbounded greedy match on user input** — `.*` on a portal-submitted field invites ReDoS. Use bounded classes like `[^<]{0,500}`.
3. **Hardcoding locale-specific patterns** — `\\d{5}` for US ZIP codes on a global org misses Canadian postal codes, UK codes, etc. Validate per-country or use platform features.

## Official Sources Used

- Apex Reference — Pattern class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Pattern.htm
- Apex Reference — Matcher class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Matcher.htm
- Apex Reference — String class methods: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_String.htm
- Apex Governor Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
