# Development Documentation Standards — Work Template

Use this template when documenting Apex or defining an org-wide documentation standard.

## Scope

**Skill:** `development-documentation-standards`

**Request summary:** (fill in what the user asked for)

**Level:** code-level (ApexDoc + naming on specific classes) | org-level (written standard)

## Context Gathered

- Class(es) / area in play:
- Existing conventions or "define from scratch"?
- Public/global surfaces that MUST be documented:
- Constraints to watch: ApexDoc is unenforced by the compiler; nothing here compiles-checks.

## ApexDoc block skeleton (copy per element)

```apex
/**
 * <one-line summary: what it does, verb-first>.
 * @group <optional grouping>
 * @param <paramName> <constraint / null-handling, not just the name>
 * @return <what the caller gets> (OMIT for void methods and constructors)
 * @throws <ExceptionType> <when it fires>
 * @deprecated <reason> Use {@link <Class#member>} instead. (only if retiring)
 */
```

Rules to apply while filling it in:
- Block opens with `/**` (two asterisks) and immediately precedes the declaration.
- One `@param` per parameter, in signature order, exact parameter name.
- `@return` only on non-`void` methods.
- `@throws` for every exception the element can raise.
- Use ApexDoc tags only — `@throws`, not JavaDoc's `@exception`.

## Naming baseline (official Apex conventions)

- [ ] Classes start with a capital letter (PascalCase)
- [ ] Methods start with a lowercase verb (`createAccount`, `validateInput`)
- [ ] Variables are meaningful
- [ ] Otherwise follows Java standards

## Org-level standard (fill in for org-level scope)

```text
1. Naming conventions ......... <adopt official Apex conventions verbatim + org prefixes>
2. ApexDoc requirements ....... <required surfaces + required tags>
3. Central storage ............ <the ONE agreed location for standards + design docs>
4. Enforcement ................ <review gate + CI checker>
```

## Checklist (from SKILL.md)

- [ ] Every public/global class, method, constructor has a `/**` block immediately preceding it
- [ ] `@param` matches signature order/names; `@return` only on non-void; `@throws` per exception
- [ ] No JavaDoc-only tags (`@exception`, `@inheritDoc`, ...)
- [ ] Naming follows the official conventions
- [ ] Deprecations use `@deprecated` + `{@link}`
- [ ] Standard lives in one central location (org-level)
- [ ] No GA/Beta/Pilot maturity asserted for ApexDoc

## Validation

```bash
python3 scripts/check_development_documentation_standards.py --manifest-dir force-app/main/default
# add --require-return to also flag non-void methods missing @return
```

## Notes

(Record any deviations from the standard pattern and why.)
