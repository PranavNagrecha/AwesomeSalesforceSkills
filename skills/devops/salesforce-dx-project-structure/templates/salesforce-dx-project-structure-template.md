# Salesforce DX Project Structure — Work Template

Use this template when setting up or restructuring a Salesforce DX project.

## Scope

**Skill:** `salesforce-dx-project-structure`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Is this a new project or restructure of existing?
- How many teams/packages will share the repo?
- Target org API version:
- Namespace needed (managed package)?
- Are there unpackaged org-specific configs alongside packages?

## Current State

Paste the current `sfdx-project.json` here (if it exists):

```json

```

## Approach

Which pattern from SKILL.md applies?

- [ ] Single-package project
- [ ] Multi-package mono-repo
- [ ] Mixed packaged and unpackaged metadata

## Proposed sfdx-project.json

```json

```

## Directory Layout

```
project-root/
  sfdx-project.json
  .gitignore

```

## Checklist

- [ ] `sfdx-project.json` exists at repo root and is valid JSON
- [ ] `packageDirectories` has at least one entry with a valid `path`
- [ ] Exactly one packageDirectory has `"default": true`
- [ ] `sourceApiVersion` is set and matches target org
- [ ] All `path` values point to existing directories
- [ ] Package dependencies use correct names and version numbers
- [ ] `versionNumber` uses `MAJOR.MINOR.PATCH.NEXT` format
- [ ] `.gitignore` excludes `.sfdx/`, `.sf/`, and auth files
- [ ] No credentials stored in `sfdx-project.json`

## Notes

Record any deviations from the standard pattern and why.
