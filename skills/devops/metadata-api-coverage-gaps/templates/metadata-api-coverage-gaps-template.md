# Metadata API Coverage Gaps -- Work Template

Use this template when assessing metadata coverage gaps for a project or resolving deployment failures caused by unsupported types.

## Scope

**Skill:** `metadata-api-coverage-gaps`

**Request summary:** (fill in what the user asked for)

**Target API version:** (e.g., 60.0)

**Deployment mechanism:** (source deploy / change set / unlocked package / 2GP managed package)

## Context Gathered

- Org edition and feature licenses:
- Current `sourceApiVersion` in `sfdx-project.json`:
- Deployment target(s): (sandbox names, production, subscriber orgs)
- Known problematic metadata types:

## Coverage Gap Table

| # | Metadata Type | Metadata API | Source Tracking | Unlocked Pkg | Managed Pkg | Impact | Workaround |
|---|---|---|---|---|---|---|---|
| 1 | | Supported / Partial / No | Yes / No | Yes / No | Yes / No | Critical / High / Low | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |

## Release Runbook -- Manual Steps

### Step 1: (metadata type name)

- **When to execute:** Before / After automated deployment
- **Setup path:** Setup > ...
- **Values to configure:**
- **Verification:** (SOQL query, Tooling API check, or manual confirmation)
- **Owner:** (name or role)

### Step 2: (metadata type name)

- **When to execute:**
- **Setup path:**
- **Values to configure:**
- **Verification:**
- **Owner:**

## Post-Deploy Script Requirements

| Script | Purpose | Tooling API Object | Idempotent? |
|---|---|---|---|
| | | | Yes / No |

## Exclusions Added

| File / Pattern | Added to | Reason |
|---|---|---|
| | `.forceignore` / `package.xml` / `sfdx-project.json` | |

## Checklist

- [ ] Every metadata type in the project checked against Coverage Report
- [ ] Unsupported types excluded from deployment manifest
- [ ] Release runbook entry created for each excluded type
- [ ] Each runbook step has an owner and verification method
- [ ] Post-deploy scripts are idempotent and error-handled
- [ ] Source tracking gaps mitigated with explicit retrieve steps
- [ ] Coverage gap table committed to project repository

## Notes

Record any deviations from the standard pattern and why.
