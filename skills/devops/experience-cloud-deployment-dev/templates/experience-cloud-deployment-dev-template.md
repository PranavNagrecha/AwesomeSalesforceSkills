# Experience Cloud Deployment Dev — Work Template

Use this template when scripting or reviewing an Experience Cloud site deployment.

---

## Scope

**Skill:** `experience-cloud-deployment-dev`

**Request summary:** (fill in what was asked — e.g., "Deploy Customer Service Community from UAT sandbox to production")

---

## Site Identification

| Field | Value |
|---|---|
| Site name (as it appears in org) | |
| Site URL (source org) | |
| Runtime type | ☐ Aura-based (ExperienceBundle)  ☐ Enhanced LWR (DigitalExperienceBundle) |
| How runtime was confirmed | ☐ Experience Builder > Settings > Advanced > Site Runtime |
| Template used | (e.g., Customer Service, Build Your Own LWR, Help Center) |
| Source org | (sandbox alias or instance URL) |
| Target org | (production alias or instance URL) |
| Target API version | |

---

## Pre-Deployment Checks

- [ ] **Runtime type confirmed** — ExperienceBundle or DigitalExperienceBundle selected correctly
- [ ] **ExperienceBundleSettings enabled** (Aura sites only) — Settings file retrieved and confirmed `enableExperienceBundle = true`
- [ ] **CMS content assessed** — Does the site use CMS Workspace managed content? ☐ Yes  ☐ No
- [ ] **CMS migration plan documented** — If yes, plan recorded below in the CMS Content section
- [ ] **Network metadata included** — `Network:<SiteName>` is in the component list
- [ ] **ContentTypeBundle included** — If custom CMS content types are used, they are in the component list
- [ ] **Post-deployment manual steps identified** — See section below

---

## Component List and Deployment Order

Record the complete list of components to deploy and their required order.

| Order | Metadata Type | Member Name | Notes |
|---|---|---|---|
| 1 | Settings | ExperienceBundleSettings | Aura sites only — must deploy first |
| 2 | (Shared LWC, Apex, objects) | | Deploy before site bundle |
| 3 | Network | (site name) | |
| 4 | ExperienceBundle OR DigitalExperienceBundle | (site name) | Use correct type for runtime |
| 5 | ContentTypeBundle | * | If site uses custom CMS content types |

---

## Retrieve Command

```bash
# Adjust metadata types and member names for your site

# For Aura-based sites:
sf project retrieve start \
  --metadata "Settings:ExperienceBundleSettings" \
  --metadata "Network:<SITE_NAME>" \
  --metadata "ExperienceBundle:<SITE_NAME>" \
  --target-org <SOURCE_ORG_ALIAS>

# For enhanced LWR sites:
sf project retrieve start \
  --metadata "Network:<SITE_NAME>" \
  --metadata "DigitalExperienceBundle:<SITE_NAME>" \
  --target-org <SOURCE_ORG_ALIAS>
```

**Post-retrieve check:** Verify the bundle directory is non-empty before proceeding.

```bash
# Aura: check experiences/ directory
ls force-app/main/default/experiences/

# LWR: check digitalExperiences/ directory
ls force-app/main/default/digitalExperiences/site/
```

---

## Deploy Command

```bash
# Deploy in correct order — use sequential commands, not a single manifest

# Step 1: ExperienceBundleSettings (Aura only)
sf project deploy start \
  --metadata "Settings:ExperienceBundleSettings" \
  --target-org <TARGET_ORG_ALIAS>

# Step 2: Shared dependencies (LWC, Apex, custom objects)
sf project deploy start \
  --source-dir force-app/main/default/lwc \
  --source-dir force-app/main/default/classes \
  --target-org <TARGET_ORG_ALIAS>

# Step 3: Network + site bundle
sf project deploy start \
  --metadata "Network:<SITE_NAME>" \
  --metadata "ExperienceBundle:<SITE_NAME>" \  # or DigitalExperienceBundle
  --target-org <TARGET_ORG_ALIAS>
```

---

## CMS Content Migration Plan

*(Complete this section only if the site uses CMS Workspace managed content)*

| Field | Value |
|---|---|
| CMS Workspace name | |
| Content types in use | |
| Migration method | ☐ Export/Import UI  ☐ Managed Content REST API  ☐ Not applicable |
| CMS export file location | |
| Target org CMS workspace (if pre-existing) | |
| Channel assignment required? | ☐ Yes — assign workspace to Experience Cloud channel after import |

**Migration steps:**

1. Export content from source org: Setup > CMS Workspaces > (workspace) > Export
2. Import to target org: Setup > CMS Workspaces > Import
3. Assign workspace to site channel in target org: Experience Builder > CMS Content > Connect Workspace
4. Verify content appears in content zones on site pages

---

## Post-Deployment Manual Steps

These items are never captured in metadata and must be completed manually after every deployment.

| # | Step | Owner | Setup Path | Verified |
|---|---|---|---|---|
| 1 | Activate the site | | Experience Builder > All Sites > Activate | ☐ |
| 2 | Custom domain binding | | Setup > My Domain > Assign to Site | ☐ |
| 3 | SSO / Authentication provider | | Experience Builder > Administration > Login & Registration | ☐ |
| 4 | CDN configuration | | (CDN provider console) | ☐ |
| 5 | Guest user profile settings | | Setup > Profiles > (Guest User Profile) | ☐ |
| 6 | (add org-specific steps) | | | ☐ |

---

## Smoke Test

After completing all steps above, verify the site is accessible and functional.

```bash
# Check site returns HTTP 200
SITE_URL="https://<your-site-url>"
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}" "$SITE_URL")
echo "Site status: $HTTP_STATUS"
# Expected: 200

# Publish the site if not already active
sf community publish --name "<SITE_NAME>" --target-org <TARGET_ORG_ALIAS>
```

Manual checks:
- [ ] Site loads without error in a private browser window (not logged in)
- [ ] Login page appears correctly (if site requires authentication)
- [ ] At least one content zone renders expected content
- [ ] Custom domain resolves correctly

---

## Notes and Deviations

Record any deviations from the standard pattern and why:

---

## Completion Sign-Off

- [ ] All pre-deployment checks completed
- [ ] Retrieve non-empty and verified before deploy
- [ ] CMS content migrated (if applicable)
- [ ] All post-deployment manual steps completed and verified
- [ ] Smoke test passed
- [ ] Release runbook updated with completed step records
