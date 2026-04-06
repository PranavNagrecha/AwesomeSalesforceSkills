# Multi-Package Development — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `multi-package-development`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Number of packages and their names:
- Current dependency graph (draw as `A --> B --> C`):
- Mono-repo or multi-repo:
- Package types (unlocked, managed, or mix):
- CI/CD platform:

## Dependency DAG

```
(draw the current or proposed dependency graph here)
Example:
  UI --> Sales --> Base
  UI --> Service --> Base
```

## Topological Build Order

1. (first package to build — no dependencies)
2. (second package — depends only on #1)
3. (continue in order)

## Topological Install Order

Same as build order unless there are version-pinning overrides.

1.
2.
3.

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Layered Mono-Repo
- [ ] Multi-Repo with Pinned Dependencies
- [ ] Unpackaged Metadata Alongside Packages
- [ ] Other (describe)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Dependency DAG is acyclic
- [ ] Every dependency alias resolves to a valid packageAliases entry
- [ ] Exactly one packageDirectories entry has `"default": true`
- [ ] No metadata duplicated across package directories
- [ ] Unpackageable metadata in a separate unpackaged directory
- [ ] CI/CD pipeline builds and installs in topological order
- [ ] Each package's Apex tests pass independently

## Notes

Record any deviations from the standard pattern and why.
