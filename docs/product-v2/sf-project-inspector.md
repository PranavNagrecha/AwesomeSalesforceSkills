# SfSkills V2: Optional Salesforce Project Inspector

## Problem

SfSkills is a skill library. It may be opened directly in Cursor, installed as a local plugin, or used while the user is working in a separate Salesforce repository. A deployment or Apex-test product must therefore never assume that the SfSkills checkout is the Salesforce DX project to inspect.

## Contract

Project discovery has four statuses:

| Status | Meaning | Parent workflow behavior |
|---|---|---|
| `found` | One valid `sfdx-project.json` and its package directories were found | Enrich evidence with exact local paths |
| `standalone` | No local Salesforce project was found | Continue using fixture/org/SfSkills evidence |
| `ambiguous` | More than one workspace project was found | Ask for an explicit project path; do not guess |
| `invalid` | The explicit path or descriptor is invalid | Report the problem; do not silently select another project |

Discovery order:

1. Explicit `project_path` (aliases `repo_path`, `source_path`) or a file inside that project.
2. Nearest usable `sfdx-project.json` at or above the active working directory, stopping at the user home directory. The SfSkills library checkout and the bundled empty DX fixture are never selected.
3. Bounded scan of explicit workspace roots.
4. Standalone mode.

## Usage

```bash
python3 scripts/sf_project_inspector.py --json
```

Explicit external Salesforce project:

```bash
python3 scripts/sf_project_inspector.py \
  --project /work/client-salesforce \
  --component-type ApexClass \
  --full-name AccountService \
  --line 42 \
  --column 9 \
  --json
```

Workspace discovery:

```bash
python3 scripts/sf_project_inspector.py \
  --workspace /work/client-projects \
  --json
```

## Safety and performance

- Read-only; no Salesforce CLI call or file modification.
- Explicit paths never silently fall back to another project.
- Multiple projects never cause arbitrary selection.
- Workspace recursion is bounded and skips dependency/generated directories.
- Package-directory paths that escape the project root are rejected.
- Metadata mapping uses deterministic standard Salesforce source paths rather than an unbounded recursive search.
- A missing local project is a valid standalone result.

## Deployment triage integration

`/triage-deployment` should invoke the inspector only as optional enrichment. The deployment diagnosis remains functional without local metadata. Replace any mandatory `sf-repo-mapper` stage with conditional `sf-project-inspector` behavior.
