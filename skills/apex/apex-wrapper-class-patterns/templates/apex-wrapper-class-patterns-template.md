# Apex Wrapper Class Patterns: Work Template

Use this template when designing a wrapper class.

## Scope

**Skill:** `apex-wrapper-class-patterns`

**Request summary:** (what the user asked for)

## Consumer and Direction

| Question | Answer |
|---|---|
| Consumer (Lightning web component, Aura component, Apex REST, internal Apex) | |
| Return value, parameter, or both | |
| Properties the client reads | |
| Properties the client sends back (need `{ get; set; }`) | |
| Another namespace or package serializes it? (`@JsonAccess` only if yes) | |
| Sort orders needed and the null rule for each | |
| Does any class in the design query or write records? Its sharing keyword | |

## Placement

- [ ] Component-facing wrapper is a top-level class (no inner class, no inheritance)
- [ ] Controller and wrapper are separate classes
- [ ] Comparators: inner classes of a helper class are fine (Apex-only)

## Checklist

- [ ] `@AuraEnabled` on every property the template reads
- [ ] `compareTo()` and `compare()` handle null arguments and null keys
- [ ] No SOQL or DML in wrapper constructors
- [ ] Tests cover 200 rows, null keys, null entries, empty list
- [ ] `python3 scripts/check_apex_wrapper_class_patterns.py --manifest-dir force-app/main/default/classes` exits 0

## Notes

(Record any deviation from the standard pattern and why.)
