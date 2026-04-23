# Apex Regex And Pattern Matching — Work Template

Use this template when writing or reviewing any Apex that uses `Pattern`, `Matcher`, `String.matches`, `String.split`, `String.replaceAll`, or `String.replaceFirst`.

## Scope

**Skill:** `apex-regex-and-pattern-matching`

**Request summary:** (fill in what the user asked for — validation? extraction? replacement?)

## Context Gathered

- **Input source:** (LWC form, portal submission, Lead source, email handler, Flow input, trusted internal?)
- **Input size:** (max expected characters; flag anything over 50K)
- **Input trust:** (user-controlled = defend against ReDoS; trusted = relaxed rules)
- **Semantic intent:** (whole-string validation, substring extraction, dynamic replacement)
- **Hot path:** (called per record in a loop? once per transaction? per request?)

## Approach

Pick the pattern from SKILL.md:

- [ ] Whole-string validation → `matches()` with `Pattern.compile` in a static final field
- [ ] Single extraction → `find()` + `group()` once
- [ ] Multiple extraction → `while (find()) { hits.add(group()); }`
- [ ] Dynamic replace → `Matcher.quoteReplacement(value)`
- [ ] Literal-only search → `Pattern.quote(userInput)` or `String.contains`

## Pattern

```apex
// Paste the actual pattern here.
Pattern P = Pattern.compile('...');
```

## Checklist

- [ ] Every `\d`, `\w`, `\s`, `\b`, `\.` is written `\\d`, `\\w`, `\\s`, `\\b`, `\\.` in the source.
- [ ] `Pattern.compile` is in a `private static final` field if called more than once per transaction.
- [ ] Anchors match the semantic intent (`matches()` is already anchored).
- [ ] User input is either `Pattern.quote`-wrapped (going into pattern) or `Matcher.quoteReplacement`-wrapped (going into replacement).
- [ ] No nested quantifiers on user input.
- [ ] Input size is guarded if the field could exceed ~100KB.
- [ ] Unit tests include: null, empty, oversize, one adversarial example.

## Notes

Record any deviations from the standard pattern and why.
