---
name: cicd-for-experience-cloud
description: "CI/CD pipeline patterns for Experience Cloud sites — the layer between sfdx-project metadata deploys and a working production site. Covers GitHub Actions / Jenkins / GitLab pipeline shapes for ExperienceBundle / DigitalExperienceBundle deploys, BrandingSet + ExperiencePropertyTypeBundle promotion, guest-user permission-set automation, custom-domain / CDN binding scripts, and the ordering rules that make the difference between a clean deploy and a half-applied site. NOT for the metadata-shape details (use devops/experience-cloud-deployment-dev), NOT for generic SFDX CI/CD (use devops/sfdx-cicd-pipeline)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "experience cloud cicd github actions pipeline"
  - "experiencebundle digitalexperiencebundle deploy ordering"
  - "experience cloud theme branding set deployment"
  - "experience cloud guest user permission set automation"
  - "experience cloud custom domain cdn pipeline"
  - "experience cloud cms content promotion pipeline"
tags:
  - experience-cloud
  - cicd
  - github-actions
  - jenkins
  - branding-set
  - guest-user
  - custom-domain
inputs:
  - "Pipeline tooling (GitHub Actions / Jenkins / GitLab CI / Azure DevOps / Copado / Gearset)"
  - "Site type (LWR vs Aura vs classic Visualforce site)"
  - "Branding model (single site vs multi-site theme reuse)"
  - "Custom domain / CDN setup (Salesforce-managed domain vs CNAME to a CDN)"
  - "Guest-user model (anonymous browse / login required / hybrid)"
outputs:
  - "Pipeline job definitions (`.github/workflows/*.yml`, Jenkinsfile, etc.) for the deploy"
  - "Metadata-type ordering plan (Network → ExperienceBundle → BrandingSet → guest-user permission set)"
  - "Custom-domain / CDN binding script that runs post-deploy"
  - "Guest-user permission-set automation that survives every promotion"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# CI/CD for Experience Cloud

The pipeline layer that turns a versioned ExperienceBundle into a working
production site. Generic SFDX CI/CD gets you 80 % of the way there; the
last 20 % is Experience-Cloud-specific — metadata ordering rules, theme
promotion, guest-user permission-set automation, and the custom-domain
binding that lives outside Metadata API entirely.

What this skill is NOT. The shape of `ExperienceBundle` /
`DigitalExperienceBundle` metadata, the CMS Managed Content exclusion,
and the per-bundle deploy mechanics live in
`devops/experience-cloud-deployment-dev`. Generic SFDX CI/CD patterns
(scratch org strategy, source tracking, package versioning) live in
`devops/sfdx-cicd-pipeline`. This skill is the Experience-Cloud-specific
*pipeline-tooling* layer between them.

---

## Before Starting

- **Confirm the metadata API version.** `ExperienceBundle` is the older
  shape; `DigitalExperienceBundle` is the v58+ shape for LWR sites.
  Older sites may still ship as `ExperienceBundle`. The pipeline must
  match the source-org's bundle type.
- **Decide who owns CMS content promotion.** Salesforce CMS Managed
  Content is *not* fully covered by the SFDX CLI / Metadata API.
  Pipelines that assume "deploy bundles, content goes with them" will
  ship broken sites. Either treat CMS content as runtime-config
  (admins promote separately) or build a custom CMS-content-export
  step.
- **Identify every dependency the bundle deploy needs in place first.**
  Custom objects, fields, profiles, permission sets, the Network
  metadata that defines the site itself — all must exist in the
  target before the bundle deploys. Order matters.
- **Decide the guest-user model.** Permission-set assignment to the
  guest user is a one-time-per-org operation that bundle deploys do
  NOT redo. If the pipeline doesn't include explicit guest-user
  reconciliation, the first guest after a fresh deploy will see "no
  access" errors that nobody knows how to debug.

---

## Core Concepts

### The four metadata-ordering rules

Experience Cloud deploys are non-trivially ordered. The pipeline must
sequence:

1. **Foundation metadata first.** Custom objects, custom fields,
   permission sets, profiles, profile field-level security. The
   ExperienceBundle references these; if missing, the deploy fails.
2. **`Network` metadata.** Defines the Site / Community itself
   (URL prefix, login behavior, accessibility). Required before any
   ExperienceBundle that targets it.
3. **`ExperienceBundle` / `DigitalExperienceBundle`.** The bundle
   itself — pages, components, properties, navigation menus.
4. **`BrandingSet` and `ExperiencePropertyTypeBundle`.** Theme
   tokens (colors, fonts, logos), component property types. Often
   shared across multiple sites — promote *after* the bundles that
   reference them, but the BrandingSet metadata itself can deploy in
   the same package.

CMS Managed Content (articles, images, video assets) is **outside this
ordering** — handled separately because it doesn't ship via SFDX.

### Guest-user permission-set automation

Every Experience Cloud site has a guest-user profile auto-provisioned
when the site is created. Permissions on the guest user control what
anonymous visitors can read. The pipeline must:

- Assign required permission sets to the guest user (most common:
  read-access to lookup objects the site queries).
- Re-apply permission sets after any production refresh / sandbox
  copy that resets the guest user.
- Validate guest-user permissions match a known baseline before
  promoting through environments.

Salesforce CLI does not have a single "set up the guest user" command.
The automation pattern is a small sf-cli wrapper script (or Apex
anonymous block) that assigns the relevant permission sets to the
site's guest user, idempotent on re-run.

### Custom-domain / CDN binding

Production Experience Cloud sites usually live on a custom domain
(`portal.example.com`, not `example.my.site.com`). Two pieces:

1. **Salesforce-side:** Setup → Domains → register the custom domain
   → bind to the site. Metadata-deployable via `CustomDomain` /
   `CustomSite` types but with caveats — the domain registration
   step requires DNS verification that's not pipeline-automatable on
   the Salesforce side.
2. **DNS-side:** CNAME the custom domain at the Salesforce-supplied
   target (or a CDN that fronts it). Owned by the DNS team, not
   Salesforce.

The pipeline coordinates these: deploy the Salesforce-side metadata,
emit the DNS targets to a known location, the DNS team applies them.
Many pipelines stop at "metadata deployed" and miss that the site
isn't reachable until DNS propagates — explicit DNS-confirmation gate
prevents that.

### Theme reuse via BrandingSet

`BrandingSet` defines tokens (primary color, font family, logo
references) that themes consume. A single BrandingSet referenced from
multiple sites is the right pattern for multi-site brand consistency.
Pipeline implication: BrandingSet promotion is a separate concern from
bundle promotion — same metadata package can carry both, but the
theme team's promotion cadence often differs from the
site-feature-team's cadence.

---

## Common Patterns

### Pattern A — GitHub Actions pipeline for a single LWR site

```yaml
# .github/workflows/experience-cloud-deploy.yml
name: deploy-experience-cloud-site

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: install sf cli
        run: npm install -g @salesforce/cli

      - name: authenticate
        env:
          SFDX_AUTH_URL: ${{ secrets.SFDX_AUTH_URL }}
        run: |
          echo "$SFDX_AUTH_URL" > ./auth.txt
          sf org login sfdx-url --sfdx-url-file ./auth.txt --alias prod
          rm ./auth.txt

      # 1. Foundation: objects/fields/permission-sets the bundle depends on.
      - name: deploy foundation metadata
        run: sf project deploy start
              --source-dir force-app/main/default/objects
              --source-dir force-app/main/default/permissionsets
              --target-org prod

      # 2. Network metadata (defines the site itself).
      - name: deploy network metadata
        run: sf project deploy start --source-dir force-app/main/default/networks --target-org prod

      # 3. The ExperienceBundle / DigitalExperienceBundle itself.
      - name: deploy experience bundle
        run: sf project deploy start --source-dir force-app/main/default/experiences --target-org prod

      # 4. BrandingSets last — they reference bundle artifacts.
      - name: deploy branding sets
        run: sf project deploy start --source-dir force-app/main/default/brandingSets --target-org prod

      # 5. Guest-user permission reconciliation.
      - name: assign guest-user permsets
        run: bash scripts/assign-guest-permsets.sh prod

      # 6. Smoke test — confirm site loads, anonymous read works.
      - name: smoke test
        run: bash scripts/smoke-test-site.sh prod

      # 7. Emit DNS targets for the DNS team (if domain not yet bound).
      - name: emit DNS targets
        run: bash scripts/emit-dns-targets.sh prod > dns-targets.txt
      - uses: actions/upload-artifact@v4
        with:
          name: dns-targets
          path: dns-targets.txt
```

The seven-step shape: foundation → Network → bundle → BrandingSet →
guest-user → smoke → DNS-emit. Drop or reorder a step and the deploy
either fails noisily (good) or appears to succeed but leaves the site
broken (bad — see Gotchas).

### Pattern B — Multi-site theme promotion

**When to use.** A BrandingSet shared by 4+ sites (corporate brand),
promoted on its own cadence (theme team owns it) separate from the
per-site feature releases.

**Approach.** Two pipelines, one repository:

- `branding-pipeline.yml` — deploys `force-app/main/default/brandingSets/`
  alone. Triggers on changes to that directory. Runs against all
  consuming orgs.
- `site-pipelines/<site>.yml` — deploys per-site bundles. Trigger on
  per-site directory changes.

The pipelines are independent; site bundles reference the BrandingSet
by API name. Coordination happens via the API name being stable —
renaming a BrandingSet is a coordinated migration across every site
that consumes it.

### Pattern C — Guest-user permission-set baseline validator

**When to use.** Production refreshes / sandbox copies that reset
guest-user permissions. Without a validator, you discover the
regression when a customer reports "site says no access".

```bash
#!/bin/bash
# scripts/validate-guest-permsets.sh
set -eu
TARGET=$1
EXPECTED_PERMSETS="Site_Public_Read,Site_Lookup_Access"

# Find the site's guest user.
GUEST_USER=$(sf data query --query \
    "SELECT Username FROM User WHERE Profile.Name LIKE '%Site Profile%' AND IsActive = TRUE LIMIT 1" \
    --target-org "$TARGET" --json | jq -r '.result.records[0].Username')

# Check assigned permission sets.
ASSIGNED=$(sf data query --query \
    "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE Assignee.Username = '$GUEST_USER'" \
    --target-org "$TARGET" --json | jq -r '.result.records[].PermissionSet.Name' | sort | tr '\n' ',')

# Compare against baseline.
for ps in ${EXPECTED_PERMSETS//,/ }; do
    if ! echo "$ASSIGNED" | grep -q "$ps"; then
        echo "MISSING guest permset: $ps"
        exit 1
    fi
done
echo "OK: guest user has all expected permsets"
```

Run as a CI gate on every promotion. Cheap; catches the regression
before customers do.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| First Experience Cloud pipeline for a new site | **Pattern A** (single-site 7-step pipeline) | Standard shape; covers ordering, guest user, DNS coordination |
| Multi-site brand consistency | **Pattern B** (theme pipeline + per-site pipelines) | BrandingSet promotion has a different cadence than site features |
| Refreshed sandbox loses guest permissions | **Pattern C validator** as CI gate | Catches the regression automatically |
| LWR site (modern, post-API v58) | `DigitalExperienceBundle` deploys | LWR-specific bundle type |
| Aura-based site | `ExperienceBundle` deploys | Older bundle type |
| Hybrid Aura + LWR site (uncommon) | Both bundle types in the package | Each component lives in its own bundle |
| Custom domain not yet DNS-bound | Pipeline emits DNS targets; gate on confirmation | Don't promote past "metadata deployed" until the site is reachable |
| CMS Managed Content needed in target | Separate CMS-content-export step (NOT SFDX) | CMS isn't covered by Metadata API |
| Generic SFDX CI/CD without Experience-Cloud specifics | **Use `devops/sfdx-cicd-pipeline`** | Don't reinvent the SFDX layer |
| Bundle metadata details / shape | **Use `devops/experience-cloud-deployment-dev`** | This skill is pipelines, not bundle internals |

---

## Recommended Workflow

1. **Identify bundle type** (Aura `ExperienceBundle` vs LWR `DigitalExperienceBundle`). Pipeline source paths and deploy commands differ.
2. **Inventory dependencies** (objects, fields, profiles, permission sets, Network metadata) and order them as foundation → network → bundle → branding.
3. **Build the pipeline** following Pattern A's seven-step shape.
4. **Add guest-user reconciliation** as an explicit step. Don't assume it's automatic.
5. **Add the guest-user permset validator** (Pattern C) as a CI gate.
6. **Coordinate DNS** with the DNS team — pipeline emits targets, DNS team applies, gate the next promotion on DNS-confirmation.
7. **Plan CMS-content promotion separately** if the site uses CMS Managed Content.

---

## Review Checklist

- [ ] Bundle type matches the source-org's site (ExperienceBundle vs DigitalExperienceBundle).
- [ ] Foundation metadata (objects, fields, permission sets) deploys *before* the bundle.
- [ ] Network metadata deploys before the ExperienceBundle that targets it.
- [ ] BrandingSet promotion is sequenced with the bundles that reference it.
- [ ] Guest-user permission-set assignment is an explicit pipeline step.
- [ ] Guest-user permset validator runs as a CI gate post-deploy.
- [ ] CMS Managed Content promotion is handled (or explicitly excluded with rationale).
- [ ] Custom-domain DNS targets are emitted and the DNS team has a known follow-up.
- [ ] Smoke test validates the site loads and anonymous read works.

---

## Salesforce-Specific Gotchas

1. **CMS Managed Content is not covered by SFDX.** Pipelines that assume "deploy and the content comes too" ship broken sites. (See `references/gotchas.md` § 1.)
2. **Guest-user permission sets reset on sandbox refresh.** Without a CI step that re-applies them, the first guest after refresh sees access errors. (See `references/gotchas.md` § 2.)
3. **Network metadata must deploy before the ExperienceBundle** that targets it. Reverse order produces a deploy that succeeds-but-doesn't-work. (See `references/gotchas.md` § 3.)
4. **`ExperienceBundle` (Aura) and `DigitalExperienceBundle` (LWR) are different metadata types.** Pipeline source paths differ; mixing them in a single deploy is fine but the paths and target sites must match. (See `references/gotchas.md` § 4.)
5. **Custom-domain registration requires DNS verification** that's not pipeline-automatable on the Salesforce side. The pipeline must coordinate with the DNS team. (See `references/gotchas.md` § 5.)
6. **`ExperienceBundleSettings` must be enabled in the target org** before any ExperienceBundle deploys. First-time setup catches this once. (See `references/gotchas.md` § 6.)
7. **Renaming a BrandingSet API name breaks every site that references it.** Treat as a coordinated migration. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pipeline definition | `.github/workflows/*.yml`, Jenkinsfile, GitLab CI YAML, etc. — the seven-step shape |
| Guest-user assignment script | sf-cli wrapper that assigns permission sets to the site guest user |
| Guest-user validator | CI gate that confirms the guest user has the expected permission sets |
| DNS-target emitter | Post-deploy script that surfaces the Salesforce-supplied CNAME target for the DNS team |
| Smoke-test script | Confirms the site URL responds 200 and the homepage renders for an anonymous visitor |

---

## Related Skills

- `devops/experience-cloud-deployment-dev` — bundle metadata internals (this skill ends where that one starts).
- `devops/sfdx-cicd-pipeline` — generic SFDX CI/CD; this skill assumes those primitives are in place.
- `admin/experience-cloud-admin-designer` — site design / configuration; this skill is the deploy half.
- `security/guest-user-security` — what permissions the guest user *should* have (vs this skill which is about how the pipeline applies them).
- `architect/experience-cloud-licensing-model` — license-model decisions upstream of the pipeline.
