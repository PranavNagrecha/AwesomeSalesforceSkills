# Experience Cloud Deployment Admin — Work Template

Use this template when deploying an Experience Cloud site between Salesforce orgs.

## Scope

**Skill:** `experience-cloud-deployment-admin`

**Request summary:** (fill in what the user asked for — e.g., "deploy CustomerPortal site from UAT sandbox to production")

---

## Pre-Deployment Context

Record answers to the Before Starting questions from SKILL.md:

| Question | Answer |
|---|---|
| Source org type | Sandbox / Scratch Org / Production |
| Target org type | Sandbox / Production |
| Site name (exact) | |
| Site template type | LWR / Aura / Salesforce Tabs + Visualforce |
| Deployment mechanism | Change Set / Salesforce CLI / Metadata API |
| Enable Experience Bundle Metadata API — Source org | Enabled / Not checked / Unknown |
| Enable Experience Bundle Metadata API — Target org | Enabled / Not checked / Unknown |
| Network record exists in target org | Yes / No / Unknown |
| CustomSite record exists in target org | Yes / No / Unknown |
| SiteDotCom present in retrieved package | Yes (must remove) / No |
| Guest User Profile included in deploy plan | Yes / No — justify |

---

## Dependency Inventory

List all metadata components the site depends on. These must be deployed before ExperienceBundle.

| Component Type | Component Name | Status in Target Org |
|---|---|---|
| ApexClass | | Exists / Needs Deploy |
| ApexClass | | Exists / Needs Deploy |
| CustomObject | | Exists / Needs Deploy |
| Profile (Guest User) | [SiteName] Profile | Exists / Needs Deploy |
| PermissionSet | | Exists / Needs Deploy |
| Network | [SiteName] | Exists / Needs Deploy |
| CustomSite | [SiteName] | Exists / Needs Deploy |

---

## Deployment Plan

### Step 1 — Deploy Dependencies (Apex, Objects, Profiles, Network, CustomSite)

**Mechanism:** Change Set named _________________ / CLI manifest: _________________

**Components included:**
- [ ] Apex classes and triggers
- [ ] Custom objects and fields
- [ ] Profiles (including Guest User Profile)
- [ ] Permission sets
- [ ] Network
- [ ] CustomSite

**Deploy command (if CLI):**
```bash
sf project deploy start --manifest package-deps.xml --target-org <alias> --wait 30
```

**Expected outcome:** Deployment status = Succeeded. Network record visible in Setup > All Sites in target org.

---

### Step 2 — Deploy ExperienceBundle

**Prerequisite confirmed:** Network and CustomSite exist in target org: Yes / No

**Mechanism:** Change Set named _________________ / CLI manifest: package-site.xml

**Components included:**
- [ ] ExperienceBundle: [SiteName]
- [ ] SiteDotCom: ABSENT (confirmed removed)

**Deploy command (if CLI):**
```bash
sf project deploy start --manifest package-site.xml --target-org <alias> --wait 30
```

**Expected outcome:** Deployment status = Succeeded.

---

### Step 3 — Publish the Site

**Method:** Experience Builder UI / Connect REST API

**Option A — Experience Builder UI:**
1. Log in to target org
2. Navigate to Setup > Digital Experiences > All Sites
3. Click Builder next to [SiteName]
4. Click Publish in Experience Builder
5. Confirm status changes to Active

**Option B — Connect REST API (for automated pipelines):**
```bash
# Get Community Id
COMMUNITY_ID=$(sf data query \
  --query "SELECT Id FROM Network WHERE Name = '[SiteName]'" \
  --target-org <alias> \
  --json | jq -r '.result.records[0].Id')

# Get access token
ACCESS_TOKEN=$(sf org display --target-org <alias> --json | jq -r '.result.accessToken')
INSTANCE_URL=$(sf org display --target-org <alias> --json | jq -r '.result.instanceUrl')

# Publish
curl -X POST \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  "${INSTANCE_URL}/services/data/v63.0/connect/communities/${COMMUNITY_ID}/publish"
```

---

## Post-Deployment Validation Checklist

- [ ] Enable Experience Bundle Metadata API confirmed active in target org
- [ ] SiteDotCom absent from deployment package (not deployed)
- [ ] All Apex/LWC dependencies deployed and confirmed present in target
- [ ] Network and CustomSite records confirmed present in target before ExperienceBundle deploy
- [ ] ExperienceBundle deployment completed without errors
- [ ] Site published (Status = Active) — verified in Setup > All Sites
- [ ] Site URL reachable from browser: ___________________
- [ ] Guest User Profile permissions reviewed in target org
  - [ ] Apex class access matches source
  - [ ] Object and field-level security reviewed
  - [ ] Guest user record access / sharing settings verified
- [ ] Authenticated user login tested (if applicable)
- [ ] Key site pages load without errors

---

## Notes and Deviations

Record any deviations from the standard pattern and the reason:

| Deviation | Reason | Mitigation |
|---|---|---|
| | | |
