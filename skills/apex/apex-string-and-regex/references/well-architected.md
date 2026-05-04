# Well-Architected Notes — Apex String and Regex

## Relevant Pillars

- **Operational Excellence** — `static final Pattern` is the difference
  between a trigger that runs in 50 ms and one that runs in 500 ms at
  200 records. The cost of compile-once vs compile-per-record is
  invisible until production. The `static final` discipline is also the
  highest-yield review item across this skill — easy to spot, easy to
  fix, real impact.
- **Security** — Two security touchpoints. First, `String.escapeSingleQuotes`
  for SOQL string-binding (covered in `apex/dynamic-soql`, but related —
  the wrong escape function for the wrong context is the canonical
  injection bug). Second, `Matcher.quoteReplacement` when feeding
  user-supplied data into `replaceAll` — without it, a user-controlled
  `$1` triggers regex backreference behavior the developer didn't intend.

## Architectural Tradeoffs

- **Pre-compiled Pattern vs `String.replaceAll(regex, ...)` convenience
  method.** The String instance method recompiles on every call.
  Acceptable for one-shot use, terrible in a loop. The Pattern object is
  more code; that code wins on any hot path.
- **Validation regex vs structured parsing.** A long, complex regex for
  email / phone / URL passes simple cases but fails on edge cases that
  the relevant RFC explicitly allows. For high-volume input, a regex is
  fine. For correctness-critical input (auth tokens, signed payloads),
  use a structured parser, not a regex.
- **`String.split` vs `Matcher` for tokenization.** `split` is simpler
  for fixed-delimiter cases. Use `Matcher` when you need positional
  groups or when the delimiter rules are non-trivial (quoted CSV,
  escaped delimiters). The `limit = -1` argument is non-negotiable
  whenever trailing-empty preservation matters.

## Anti-Patterns

1. **Compiling a Pattern inside a loop body.** Hoist to `static final`
   at class scope. Single most common Apex perf bug in this domain.
2. **`String.format` with printf placeholders (`%s`, `%d`).** The
   placeholders are MessageFormat-style: `{0}`, `{1}`. Wrong syntax
   produces literal output, not a substitution.
3. **Calling instance methods on potentially-null strings.** Use
   `String.isBlank` / `String.isNotBlank` (null-safe) instead of relying
   on the caller. Defensive over polite.
4. **`split(regex)` where trailing empties matter.** Use `split(regex, -1)`
   to preserve them.
5. **`group()` without a successful `find()` / `matches()` first.** Always
   gate `group()` on a match-success condition.

## Official Sources Used

- Apex String Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_string.htm
- Apex Pattern and Matcher Using Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_pattern_and_matcher_using.htm
- Apex Matcher Class Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_pattern_and_matcher_matcher_methods.htm
- Java MessageFormat (the format String.format follows) — https://docs.oracle.com/javase/8/docs/api/java/text/MessageFormat.html
- Sibling skill — `skills/apex/dynamic-soql/SKILL.md` for SOQL escaping (different rules)
