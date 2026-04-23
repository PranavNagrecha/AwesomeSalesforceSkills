---
name: apex-regex-and-pattern-matching
description: "Use when writing Apex that validates, extracts, or transforms strings with Pattern/Matcher or String regex methods. Covers catastrophic backtracking, 1M char input cap, anchored vs unanchored matching, and replaceAll reserved `$`/`\\` chars. NOT for SOQL LIKE queries, Flow formula REGEX, or client-side JavaScript regex."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
  - Reliability
triggers:
  - "validate an email or phone number in Apex"
  - "extract a token, order number, or ID from a free-text field"
  - "Apex regex is causing a CPU timeout or limit exception"
  - "replaceAll is inserting `$1` literal into my output"
  - "why does my Apex regex match nothing when the same pattern works in JavaScript"
tags:
  - apex-regex-and-pattern-matching
  - pattern-matcher
  - string-validation
  - redos
  - performance
inputs:
  - "the string or field being matched"
  - "the pattern the practitioner wants to enforce or extract"
  - "expected input size and shape (user input vs trusted internal data)"
outputs:
  - "correct Apex Pattern/Matcher code with anchors, escapes, and group handling"
  - "guidance on when to use `matches()` vs `find()` vs `String.replaceAll(...)`"
  - "mitigations for regex denial-of-service and the 1M character limit"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Regex And Pattern Matching

Activates when Apex code uses `Pattern`, `Matcher`, `String.replaceAll`, `String.replaceFirst`, `String.split`, or `String.matches`. Produces correct, performant, ReDoS-resistant regex with proper anchoring, escaping, and group handling.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the input user-controlled or trusted internal data? ReDoS only matters for adversarial input.
- Will the string exceed 1,000,000 characters? Apex regex throws `LimitException` past that limit.
- Is this `matches()` (whole string) or `find()` (any substring)? Anchoring behavior differs.
- Is the replacement passed to `replaceAll` or `replaceFirst`? `$` and `\` are reserved in the replacement.
- What pattern syntax is the practitioner borrowing from? Apex uses Java regex (java.util.regex), NOT JavaScript — no lookbehind in older API versions, different escape quirks.

---

## Core Concepts

### `matches()` vs `find()` — Anchored By Default Or Not

`String.matches(regex)` and `Matcher.matches()` require the pattern to match the **entire** string. `Matcher.find()` matches any substring. Practitioners coming from JavaScript often expect `matches()` to behave like `test()` and are surprised when `'abc123'.matches('\\d+')` returns `false` — it only returns `true` for `'.*\\d+.*'` or if the whole string is digits.

Use `matches()` for validation ("is this entire string a valid email?") and `find()` for extraction ("is there a token anywhere in this string?").

### Java-Flavored Regex, Double-Escaped In Apex Literals

Apex patterns are Java regex — `\d`, `\w`, `\s`, `[A-Z]`, `(?i)`, `(?m)`, `(?s)` all work. But Apex string literals require `\\` to produce a single backslash. So a digit class is written `'\\d+'`, not `'\d+'`. A literal backslash is `'\\\\'` (four chars in source, one in the pattern, zero in the matched text).

Lookbehind — supported via `(?<=...)` and `(?<!...)` — is fixed-length only in older Java versions; practitioners sometimes write variable-length lookbehind that compiles in online testers but fails in Apex.

### Replacement Strings Have Reserved Characters

`String.replaceAll(regex, replacement)` and `Matcher.replaceAll(replacement)` treat `$0`, `$1`, `$2` as backreferences to captured groups and treat `\\` as a literal backslash. This means a dollar sign or backslash in the *replacement* must be escaped with `\\$` or `\\\\`. Practitioners who want literal `$100` in output commonly get silent empty output or `IndexOutOfBoundsException`.

Use `Matcher.quoteReplacement(replacement)` to escape the replacement string safely when it's dynamic.

### Catastrophic Backtracking And The 1M Character Cap

Apex regex runs on the same engine that is vulnerable to ReDoS: patterns with nested quantifiers like `(a+)+`, `(a|a)+`, or `.*` followed by a specific suffix on a long string can cause CPU timeouts. Apex also throws `LimitException: regex too complicated` on strings over 1 million characters or on pathological patterns even on shorter inputs.

Default to atomic groups, possessive quantifiers where supported, bounded quantifiers (`{0,64}` instead of `*`), and explicit character classes (`[^@]+` instead of `.+`).

---

## Common Patterns

### Pattern 1: Validate A Whole-String Format

**When to use:** "Is this exact value a valid phone / email / Salesforce ID?"

**How it works:**

```apex
private static final Pattern E164 = Pattern.compile('^\\+[1-9]\\d{1,14}$');

public static Boolean isValidE164(String input) {
    return input != null && E164.matcher(input).matches();
}
```

**Why not the alternative:** `input.matches('...')` compiles the pattern on every call. `Pattern.compile(...)` in a static final field compiles once per transaction and is reused. For hot loops this is a measurable CPU saving.

### Pattern 2: Extract One Or More Tokens From Free Text

**When to use:** Pulling order numbers, case references, or IDs from email bodies or notes.

**How it works:**

```apex
private static final Pattern ORDER_REF = Pattern.compile('ORD-\\d{6,10}');

public static List<String> extractOrderRefs(String body) {
    List<String> hits = new List<String>();
    if (body == null) return hits;
    Matcher m = ORDER_REF.matcher(body);
    while (m.find()) hits.add(m.group());
    return hits;
}
```

**Why not the alternative:** `String.split` and manual index work is fragile and slow. `find()` in a loop handles all occurrences correctly.

### Pattern 3: Safe `replaceAll` With Dynamic Content

**When to use:** Replacing matches with content that may contain `$` or `\`.

**How it works:**

```apex
String safe = Matcher.quoteReplacement(userInput);
String result = original.replaceAll('\\{\\{token\\}\\}', safe);
```

**Why not the alternative:** Embedding `userInput` directly lets `$1` or `\\` in that input trigger backreference processing or throw `IndexOutOfBoundsException`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Validate whole-string format | `Pattern.compile(...).matcher(s).matches()` with `^` and `$` optional | Matches is already anchored; explicit anchors make intent clear |
| Extract one substring | `find()` + `group()` on first hit | Simpler and avoids unnecessary loop |
| Extract many substrings | `while (find()) hits.add(group())` | Handles overlap correctly |
| Replace with dynamic content | `Matcher.quoteReplacement(value)` | Escapes `$` and `\` in the replacement |
| Hot loop, same pattern 100+ times | `private static final Pattern P = Pattern.compile(...)` | Compile once, reuse for transaction |
| Input may be 500KB+ | Pre-truncate or chunk | 1M cap throws `LimitException` |
| Input is adversarial (portal, webhook) | Use bounded quantifiers, avoid nested `+`/`*` | Defends against ReDoS |

---

## Recommended Workflow

1. Decide whether you are validating (whole string) or extracting (substring) — this picks `matches()` vs `find()`.
2. Write the pattern and test it with 3–5 representative strings AND 2–3 adversarial strings (very long, nested repetition, empty, unicode).
3. Double-escape all backslashes when moving from a regex tester into an Apex literal.
4. If the pattern is used in a loop, move it to a `private static final Pattern`.
5. For replacements, check whether the replacement value can contain `$` or `\`. If so, wrap with `Matcher.quoteReplacement`.
6. Add a unit test with at least one string at the expected upper size (a few KB) to catch surprise CPU usage.
7. For user-supplied input, guard the length before matching (`if (s.length() > 10000) ...`).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Anchors `^` and `$` are present if whole-string validation is intended.
- [ ] Every `\d`, `\w`, `\s`, `\b`, `\.` is written as `\\d`, `\\w`, `\\s`, `\\b`, `\\.` in the Apex literal.
- [ ] Hot-path regex is compiled once in a static final `Pattern`.
- [ ] Replacement strings that could contain `$` or `\` are wrapped in `Matcher.quoteReplacement`.
- [ ] No nested quantifiers (`(a+)+`, `(.*?)*`) on user-controlled input.
- [ ] Inputs over ~1MB are truncated or rejected before hitting the engine.
- [ ] Tests cover empty string, null, whitespace-only, and one oversize string.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. See `references/gotchas.md` for the full list.

1. **`matches()` is anchored** — `'abc123'.matches('\\d+')` is `false`; use `find()` for substring matching.
2. **`$` in replacement is a backreference** — `'$9.99'.replaceAll('price', '$9.99')` throws; escape with `Matcher.quoteReplacement`.
3. **1M character hard cap** — strings over 1,000,000 chars throw `LimitException` before any match runs.
4. **Apex regex is Java, not JavaScript** — lookbehind is fixed-length, no named groups in very old API versions.
5. **Catastrophic backtracking stops the transaction** — `(a|aa)+` on adversarial input exhausts CPU.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `references/examples.md` | Realistic validation, extraction, and replacement examples |
| `references/gotchas.md` | Platform gotchas around anchors, escapes, and limits |
| `references/llm-anti-patterns.md` | Common LLM mistakes: single-backslash regex, unanchored `matches`, unsafe replace |
| `references/well-architected.md` | Performance/Security/Reliability framing |
| `scripts/check_apex_regex_and_pattern_matching.py` | Stdlib lint for Apex regex pitfalls |

---

## Related Skills

- **apex-security-patterns** — sanitizing user input before storing or rendering
- **apex-blob-and-content-version** — handling file metadata without abusing regex on bytes
- **apex-soql-basics** — prefer SOQL `LIKE` for database-side filtering over Apex regex on returned rows
