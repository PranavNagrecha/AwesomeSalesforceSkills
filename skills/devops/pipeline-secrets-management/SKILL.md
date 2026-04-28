---
name: pipeline-secrets-management
description: "Store and inject Salesforce auth URLs, JWT keys, and API credentials into CI without leaking them. NOT for runtime secrets in Apex."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "jwt auth ci salesforce"
  - "leak sfdx auth url"
  - "github actions salesforce secret"
  - "rotate pipeline credential"
tags:
  - ci
  - secrets
  - jwt
  - sfdx-auth
inputs:
  - "CI provider (GitHub Actions / GitLab / Jenkins)"
  - "target orgs"
outputs:
  - "Secret store layout"
  - "JWT auth workflow snippet"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Pipeline Secrets Management

Salesforce CI pipelines need to authenticate to orgs (sandboxes, UAT, prod). The safest pattern is a JWT bearer flow with a Connected App per pipeline stage and the private key stored as a base64 secret in the CI provider's vault. This skill defines naming, rotation, and leak-detection procedures.

## Recommended Workflow

1. Create one Connected App per CI stage (CI-Dev, CI-UAT, CI-Prod) with JWT flow enabled; export certificate + private key.
2. Store the PEM private key as a CI secret (GitHub Actions: repository secret, base64-encoded).
3. In the pipeline, write the key to a temp file, run `sf org login jwt --client-id ... --username ... --jwt-key-file ...`, then delete the temp file.
4. Rotate the private key every 90 days via a scheduled task; invalidate the previous certificate in the Connected App.
5. Enable GitHub secret scanning and a pre-commit hook that blocks `force://` auth URL patterns.

## Key Considerations

- Never commit sfdxAuthUrl (`force://...`) — it contains a refresh token.
- JWT flow uses a cert, not a password — much safer for long-lived automation.
- Scope the Connected App to only the API scopes needed (api, refresh_token).
- Audit logs of JWT logins appear in LoginHistory — wire to SIEM.

## Worked Examples (see `references/examples.md`)

- *GitHub Actions JWT step* — Deploy workflow
- *Rotation job* — 90-day rotation SLA

## Common Gotchas (see `references/gotchas.md`)

- **Auth URL committed** — Anyone with repo read owns the org.
- **Shared Connected App** — Blast radius includes all pipelines.
- **Expired certificate** — Pipelines fail silently at midnight.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- sfdxAuthUrl in env vars
- One Connected App for all stages
- Password+security token auth

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Unlocked Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- SF CLI — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/
- DevOps Center — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Scratch Org Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_snapshots.htm
- sfdx-hardis — https://sfdx-hardis.cloudity.com/
