# Deployment Error Diagnosis — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `deployment-error-diagnosis`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Full error text (every line, not the first):
- Package contents (`package.xml` or source paths) and API version:
- Source and target environments; test level used (`RunLocalTests`, `RunSpecifiedTests`, ...):
- CLI flags in the pipeline (`--ignore-errors`, `--ignore-warnings`):

## Approach

Error pattern from the Core Concepts table that matches, and why:

## Checklist

- [ ] Full deploy error message captured (not just first line).
- [ ] Package contents reviewed.
- [ ] Test-coverage status (ran / didn't run / failed) and test level noted.
- [ ] Fix applied in source control, not the target org.
- [ ] Dependent metadata included in the package.

## Notes

Deviations from the standard pattern and why:
