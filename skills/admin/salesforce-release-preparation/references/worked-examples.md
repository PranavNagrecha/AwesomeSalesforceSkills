# Worked Example — One Seasonal Release, Prepared End to End

One release worked through completely: **preparing a 900-user Sales + Service org on instance `NA231` for Winter '27**, from the day the preview release notes drop to the production sign-off.

Two things are true about this skill at the same time, and this file carries both:

- Most of release preparation is a **practice** — a run sheet, owners, dates, a triage table, a regression pass. Sections 1–3 and 7–8.
- Part of it is **deployable metadata**. Many Release Updates are exposed as a boolean on a `Settings` metadata type whose description in the Metadata API guide literally says it "Corresponds to the *&lt;X&gt;* release update." Those toggles can be retrieved, reviewed in a pull request, and deployed. Sections 4–6.

Everything below is filled in, not templated. Copy and edit.

Deployment mechanics for the *fixes* you find are not this skill's job — see `admin/change-management-and-deployment`. The train those fixes ride is `devops/release-management`. Which sandbox to use and when it may be refreshed is `admin/sandbox-strategy`.

---

## 1. The run sheet artefact

This is the machine-checkable record for the cycle. Save it as `release-run-sheet.yaml` in the project repo and lint it with `scripts/check_salesforce_release_preparation.py --file release-run-sheet.yaml`.

```yaml
release_run_sheet:
  id: RRP-2026-WINTER27
  release: "Winter '27"
  org_instance: NA231
  production_upgrade_date: "2026-10-16"
  owner: "platform-lead@example.com"
  status: in-progress
  notes: "Upgrade date read from trust.salesforce.com Planned Maintenance for NA231, not from the release calendar headline."

preview_sandbox:
  name: RELPREVIEW
  type: DeveloperPro
  opt_in: true
  opt_in_decision: "Opted in. RELPREVIEW carries no sprint work and its only job is release validation."
  last_refresh_date: "2026-08-20"
  refresh_freeze_from: "2026-08-25"
  refresh_rule: "No refresh of RELPREVIEW between the preview cutover and the production upgrade. A refresh after the preview upgrade returns the sandbox to whatever release the source org is on, which discards the preview. Developer Pro can be refreshed daily (admin/sandbox-strategy, Type Capacities and Refresh Windows), so the freeze is a process control, not a platform one."
  owner: "release-manager@example.com"
  status: complete

release_updates:
  - id: RU-FLOW-CPU
    name: "Accurately Measure the CPU Time Consumption of Flows and Processes"
    metadata_backed: true
    settings_type: FlowSettings
    settings_field: doesEnforceApexCpuTimeLimit
    source: "api_meta.txt L116849-116853 - 'Corresponds to the Accurately Measure the CPU Time Consumption of Flows and Processes release update. Available in API version 51.0 and later.'"
    enforcement_release: "read from Setup > Release Updates in NA231 this cycle"
    test_owner: "automation-lead@example.com"
    reads: "skills/flow/flow-governor-limits-deep-dive/SKILL.md"
    status: tested-in-sandbox
    evidence: "RELPREVIEW: 6 record-triggered flows re-run under a 200-record load; peak CPU 8.4s vs 3.1s measured before the toggle."

  - id: RU-FLOW-RESUME-CTX
    name: "Make Paused Flow Interviews Resume in the Same Context with the Same User Access"
    metadata_backed: true
    settings_type: FlowSettings
    settings_field: isTimeResumedInSameRunContext
    source: "api_meta.txt L117048-117054 - 'Corresponds to the Make Paused Flow Interviews Resume in the Same Context with the Same User Access release update. This field is available in API version 57.0 and later.'"
    enforcement_release: "read from Setup > Release Updates in NA231 this cycle"
    test_owner: "automation-lead@example.com"
    reads: "skills/flow/pause-elements-and-wait-events/SKILL.md"
    status: tested-in-sandbox
    evidence: "Two approval flows with Pause elements resumed by a delegate user; both still resolved the original running user's record access."

  - id: RU-LWC-STACKED-MODALS
    name: "Enable LWC Stacked Modals"
    metadata_backed: true
    settings_type: LightningExperienceSettings
    settings_field: enableStackedModalManagerEnabled
    source: "api_meta.txt L121509-121514 - 'Indicates whether the Enable LWC Stacked Modals release update is enabled (true) or not (false). For orgs created before Summer 24, the default value is false.'"
    enforcement_release: "read from Setup > Release Updates in NA231 this cycle"
    test_owner: "ui-lead@example.com"
    reads: "skills/lwc/lwc-performance/SKILL.md"
    status: in-sandbox
    evidence: "Org predates Summer '24, so the field defaults to false here. Quote wizard opens a modal from inside a modal - the exact shape this update changes."

  - id: RU-APEX-AURA-GUEST
    name: "Restrict Access to @AuraEnabled Apex Methods for Guest and Portal Users Based on User Profile"
    metadata_backed: true
    settings_type: ApexSettings
    settings_field: enableAuraApexCtrlGuestUserAccessCheckPref
    source: "api_meta.txt L110753-110758 - 'Indicates whether the Restrict Access to @AuraEnabled Apex Methods for Guest and Portal Users Based on User Profile critical update is activated (true) or not (false).'"
    enforcement_release: "read from Setup > Release Updates in NA231 this cycle"
    test_owner: "security-lead@example.com"
    reads: "skills/security/guest-user-security/SKILL.md"
    status: activated-in-production
    evidence: "Guest profile on the Support Community granted the 4 @AuraEnabled classes the public case form calls; activated in production 2026-09-29."

  - id: RU-SHARING-RECALC
    name: "Update Apex Code and Flows for Changed Sharing Recalculation Behavior"
    metadata_backed: false
    not_in_metadata_reason: "No Settings boolean in the Metadata API Developer Guide corresponds to this update; grep -i 'release update' api_meta.txt returns no match for sharing recalculation. It is toggled only in Setup > Release Updates, and the surrounding platform change shipped with no toggle at all - see gotchas.md Gotcha 7."
    enforcement_release: "read from Setup > Release Updates in NA231 this cycle"
    test_owner: "integration-lead@example.com"
    reads: "skills/security/dynamic-sharing-recalculation/SKILL.md"
    status: in-sandbox
    evidence: "Two Apex classes reassign account owners in bulk and then immediately query AccountShare. Both are on the regression list."

  - id: RU-EXEC-ANON-PKG
    name: "Block Execute Anonymous from Managed Packages"
    metadata_backed: false
    not_in_metadata_reason: "Enforced through the packaging platform, not a Settings field. Apex Developer Guide: the restriction 'applies to new managed packages with namespaces created in Summer 26 and later. For existing managed packages with namespaces created in Spring 26 and earlier, this restriction is enforced as a release update' (apexdev.txt L14817-14822)."
    enforcement_release: "available to subscribers Summer '26, enforced Summer '27 (apexdev.txt L14820-14821)"
    test_owner: "integration-lead@example.com"
    status: planned
    evidence: "Two installed managed packages call executeAnonymous during their post-install setup. Vendor tickets raised."

  - id: RU-MYDOMAIN-SANDBOX-HOST
    name: "Stabilize the Hostname for My Domain URLs in Sandboxes"
    metadata_backed: true
    settings_type: MyDomainSettings
    settings_field: useStabilizedSandboxMyDomainHostnames
    source: "api_meta.txt L122427-122440 - enforced in Summer '20; 'As of API version 49.0, this field's value is always true, regardless of the value that you set.'"
    enforcement_release: "already enforced (Summer '20)"
    test_owner: "release-manager@example.com"
    status: enforced
    evidence: "Row kept deliberately. The field is inert - see gotchas.md Gotcha 10 - so nobody re-opens it next cycle after seeing false in a retrieved file."
```

### How to read the run sheet

- **`metadata_backed` is the fork in the road.** `true` means the update's on/off state lives in a `Settings` file you can retrieve, diff, review and deploy. `false` means Setup is the only surface, so the row is tracked but never appears in §4–6.
- **`source` is a line citation, not a URL.** Every metadata-backed row must quote the guide sentence that ties the field to the named update. If you cannot produce that sentence, the row is not metadata-backed.
- **`enforcement_release` is deliberately not a hard-coded date in most rows.** Enforcement releases move (`gotchas.md` Gotcha 6), so the run sheet records *where to read it this cycle*, not what it said last cycle.
- **`status` is a closed set** the checker enforces: `planned`, `in-sandbox`, `tested-in-sandbox`, `activated-in-production`, `enforced`, `postponed`, `not-applicable`. There is no `done` — an update is either activated by you, enforced by Salesforce, or still moving.
- **`reads` points at the skill that owns the regression.** Release preparation routes work; it does not do the flow, LWC or sharing analysis itself.
- **An enforced row stays in the sheet.** Deleting it is how the same inert field gets re-investigated every October.

---

## 2. Release-notes triage table — area routes to the skill that owns it

Filter the release notes by Feature Impact first, then route each surviving item by area. The right-hand column is what the owner reads before they touch anything; it is also what the run sheet's `reads` field should hold.

| Release-notes area | What a change here typically breaks | Skill that owns the regression |
|---|---|---|
| Flow and Process Automation | Bulkification, fault paths, formula null handling, CPU accounting | `flow/flow-bulkification`, `flow/flow-governor-limits-deep-dive` |
| Apex runtime and API versions | Sharing default, user-mode default, deprecated syntax at a pinned version | `apex/governor-limits`, `integration/api-versioning-strategy` |
| Lightning Experience / LWC | Modal stacking, base-component property removal, render timing | `lwc/lwc-performance`, `lwc/lwc-performance-budgets` |
| Sharing and record access | Recalculation timing, group and role processing, share-record availability | `admin/sharing-rules`, `security/dynamic-sharing-recalculation` |
| Guest and Experience Cloud users | `@AuraEnabled` access checks, guest sharing, site hardening | `security/guest-user-security`, `admin/experience-cloud-guest-access` |
| Permissions and profiles | A permission newly required to do something that used to be implicit | `admin/permission-set-architecture` |
| APIs, Bulk and integrations | Retired API versions, changed payload or limit behaviour | `data/bulk-api-patterns`, `integration/api-versioning-strategy` |
| Sandboxes and environments | Preview eligibility, refresh behaviour, post-copy automation | `admin/sandbox-strategy`, `devops/sandbox-refresh-and-templates` |
| Agentforce and prompt templates | Grounding, guardrail and evaluation behaviour | `agentforce/agentforce-testing-strategy` |
| OmniStudio | Standard runtime vs managed package calendar divergence | `omnistudio/omnistudio-deployment-datapacks` |

Rows with no owning skill are the interesting ones. Assign a human, not a skill, and record why in the run sheet `notes`.

---

## 3. Preview opt-in decision, worked

| Sandbox | Type | Active work? | Refresh floor | Opt in? | Why |
|---|---|---|---|---|---|
| `RELPREVIEW` | Developer Pro | none — exists for this | 1 day (`admin/sandbox-strategy`) | **Yes** | Nothing to strand. Freeze refreshes from the cutover so the preview upgrade survives. |
| `UAT` | Full | Q4 UAT running | 29 days (`admin/sandbox-strategy`) | No | Opt-in cannot be undone for the cycle (`gotchas.md` Gotcha 1); the Q4 project would be stranded on the next release. |
| `INTEG` | Partial Copy | shared with 3 vendors | 5 days (`admin/sandbox-strategy`) | No | Vendors would upgrade without warning. |
| `DEV1`–`DEV6` | Developer | daily sprint work | 1 day | No | Sprint work. |

The refresh floor is the constraint that decides this, not the sandbox's name. A Full sandbox you refresh to escape a bad preview cannot be refreshed again for 29 days — so a Full sandbox is the *worst* candidate for a decision that cannot be reversed. Developer and Developer Pro sandboxes refresh daily, which makes them the cheapest place to be wrong.

> UNVERIFIED (2026-09-04): the preview enrollment window length, the preview cutover date, and the interval between the preview upgrade and the production upgrade are not stated in any of the Metadata API, Object Reference or Apex Developer guides. Read them from the Sandbox Preview Knowledge Article and trust.salesforce.com each cycle; do not carry the numbers forward.

---

## 4. Settings XML — three metadata-backed Release Updates, deployable

Each block is a complete `.settings` file, wrapped in the root element the Metadata API guide names for that type. Deploy only the fields you intend to move; a settings file is not a full-org snapshot obligation.

### `force-app/main/default/settings/Flow.settings-meta.xml`

`FlowSettings` values live in `Flow.settings` in the `settings` directory (api_meta.txt L116823). Sample definition and root element: api_meta.txt L117060–117076.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Corresponds to the "Accurately Measure the CPU Time Consumption of
         Flows and Processes" release update (api_meta.txt L116849-116853).
         API 51.0 and later. -->
    <doesEnforceApexCpuTimeLimit>true</doesEnforceApexCpuTimeLimit>

    <!-- Corresponds to the "Make Paused Flow Interviews Resume in the Same
         Context with the Same User Access" release update
         (api_meta.txt L117048-117054). API 57.0 and later. -->
    <isTimeResumedInSameRunContext>true</isTimeResumedInSameRunContext>

    <!-- Corresponds to the "Enforce Data Access in Flow Formulas" critical
         update (api_meta.txt L116855-116858). API 48.0 and later.
         Already true here; carried so the file shows intent, not drift. -->
    <doesFormulaEnforceDataAccess>true</doesFormulaEnforceDataAccess>
</FlowSettings>
```

### `force-app/main/default/settings/LightningExperience.settings-meta.xml`

A `LightningExperienceSettings` component has the suffix `.settings` and is stored in the `settings` folder (api_meta.txt L121340–121343). The guide does not spell the filename out for this type; `LightningExperience` is derived from the two documented rules — the manifest member is the type name without the `Settings` suffix (api_meta.txt L108368–108370) and the filename is `<feature>.settings` (api_meta.txt L108374–108378).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningExperienceSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Corresponds to the "Enable LWC Stacked Modals" release update
         (api_meta.txt L121509-121514). Orgs created before Summer '24
         default to false; orgs created Summer '24 or later default to true.
         API 61.0 and later. -->
    <enableStackedModalManagerEnabled>true</enableStackedModalManagerEnabled>

    <!-- Corresponds to the "Enable Secure Static Resources for Lightning
         Components" release update (api_meta.txt L121395-121401). Serves
         static resources from the visualforce domain instead of the
         lightning domain. API 50.0 and later. -->
    <enableAuraSecStaticResCRUCPref>true</enableAuraSecStaticResCRUCPref>
</LightningExperienceSettings>
```

### `force-app/main/default/settings/Apex.settings-meta.xml`

`ApexSettings` values live in `Apex.settings` in the settings directory of the package directory (api_meta.txt L110701). Sample definition and root element: api_meta.txt L110843–110846.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- "Restrict Access to @AuraEnabled Apex Methods for Guest and Portal
         Users Based on User Profile" critical update
         (api_meta.txt L110753-110758). -->
    <enableAuraApexCtrlGuestUserAccessCheckPref>true</enableAuraApexCtrlGuestUserAccessCheckPref>

    <!-- "Restrict Access to @AuraEnabled Apex Methods for Authenticated
         Users Based on User Profile" critical update
         (api_meta.txt L110747-110752). -->
    <enableAuraApexCtrlAuthUserAccessCheckPref>true</enableAuraApexCtrlAuthUserAccessCheckPref>

    <!-- "Use with sharing for @AuraEnabled Apex Controllers with Implicit
         Sharing" critical update (api_meta.txt L110736-110741). -->
    <enableApexCtrlImplicitWithSharingPref>true</enableApexCtrlImplicitWithSharingPref>
</ApexSettings>
```

`MyDomainSettings.useStabilizedSandboxMyDomainHostnames` is deliberately **not** in this set. It corresponds to a release update enforced in Summer '20, and "As of API version 49.0, this field's value is always true, regardless of the value that you set. Changing its value has no effect on Salesforce, even if it reads false" (api_meta.txt L122427–122440). Deploying it is a no-op that looks like a change. See `gotchas.md` Gotcha 10.

---

## 5. `manifest/release-updates-package.xml`

All org settings types are addressed through the single `Settings` name, with the member being the type name minus the `Settings` suffix (api_meta.txt L108361–108370).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Apex</members>
        <members>Flow</members>
        <members>LightningExperience</members>
        <members>MyDomain</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Do not reach for `<members>*</members>` to shorten this. The wildcard "applies only when retrieving all settings, not for an individual setting" (api_meta.txt L110860–110864), so a wildcard here pulls every settings type in the org into the diff and buries the four you care about.

---

## 6. Snapshot the org's current release-update posture

Retrieve first, review the diff, then decide. The point of source-controlling these files is that a change to a release-update boolean becomes a reviewable line in a pull request instead of a checkbox someone clicked.

```bash
# 1. Snapshot production's current posture into a scratch directory.
sf project retrieve start \
  --manifest manifest/release-updates-package.xml \
  --target-org prod \
  --output-dir snapshots/winter27-preflight

# 2. Same snapshot from the preview sandbox, after the preview upgrade ran.
sf project retrieve start \
  --manifest manifest/release-updates-package.xml \
  --target-org RELPREVIEW \
  --output-dir snapshots/winter27-preview

# 3. The diff IS the release-update posture report.
diff -ru snapshots/winter27-preflight/settings \
         snapshots/winter27-preview/settings

# 4. Lint the run sheet before the go/no-go meeting.
python3 skills/admin/salesforce-release-preparation/scripts/\
check_salesforce_release_preparation.py \
  --file release-run-sheet.yaml --repo-root .

# 5. Validate the intended change without committing it.
sf project deploy start \
  --manifest manifest/release-updates-package.xml \
  --target-org RELPREVIEW --dry-run

# 6. Deploy for real, to the preview sandbox only.
sf project deploy start \
  --manifest manifest/release-updates-package.xml \
  --target-org RELPREVIEW
```

**Verification step.** After step 6, re-run step 2 into a fresh directory and confirm each field you deployed reads back with the value you set:

```bash
sf project retrieve start --manifest manifest/release-updates-package.xml \
  --target-org RELPREVIEW --output-dir snapshots/winter27-verify

grep -H -E 'doesEnforceApexCpuTimeLimit|isTimeResumedInSameRunContext|enableStackedModalManagerEnabled' \
  snapshots/winter27-verify/settings/*.settings-meta.xml
```

A field that reads back with the opposite value is not a failed deploy — it is usually an already-enforced update whose field is inert (Gotcha 10). Cross-check Setup > Release Updates before filing a bug.

---

## 7. Regression checklist

Run this in the preview sandbox after the preview upgrade and again in production after the production upgrade. Sandbox facts are cited to the siblings rather than restated.

- [ ] `RELPREVIEW` confirmed on the preview release and **not refreshed since the cutover** — a refresh returns it to the source org's release. Refresh floors per type: `admin/sandbox-strategy` › Type Capacities and Refresh Windows.
- [ ] Post-copy automation re-verified if any sandbox was refreshed this cycle — endpoints and scheduled jobs survive a refresh still aimed at production (`devops/sandbox-refresh-and-templates`; `admin/sandbox-strategy` › Questions to Ask).
- [ ] Full Apex test run green in the preview sandbox, compared against the pre-upgrade baseline run, not against zero.
- [ ] Every Apex class pinned below the current API version listed, with the versioned behaviour changes for the versions it skips read from the Apex Developer Guide's *Apex Versioned Behavior Changes* appendix (apexdev.txt L44482+). See `gotchas.md` Gotcha 12.
- [ ] Each metadata-backed Release Update in §1 activated in the preview sandbox and its owning skill's regression run (`reads` column).
- [ ] Scheduled jobs and their next fire times checked after the upgrade — they run unattended and are the least-watched surface.
- [ ] Integration users exercised: at least one inbound API call and one outbound callout per integration, at the API version those integrations actually pin.
- [ ] Guest and Experience Cloud paths exercised with an actual guest session, not an internal user (`security/guest-user-security`).
- [ ] Settings diff from §6 reviewed by a second person and merged, so the org's release-update posture is in source control.
- [ ] Stakeholder brief sent, with the instance-specific production upgrade date, before the upgrade weekend.
- [ ] Post-upgrade monitoring owner named and on call for the window after the production upgrade.

---

## 8. What feeds this into the rest of the repo

| Artefact from this file | Consumed by |
|---|---|
| `release-run-sheet.yaml` | `agents/release-readiness-reviewer/AGENT.md` — evidence for the readiness verdict |
| Settings XML (§4) + `package.xml` (§5) | `admin/change-management-and-deployment` for promotion; `devops/release-management` for the train |
| Triage table (§2) `reads` column | The owning skill each row names, read before that regression is attempted |
| Preview opt-in decision (§3) | `admin/sandbox-strategy` for topology; `devops/sandbox-refresh-and-templates` for post-copy |
| Stakeholder brief line in §7 | `admin/change-management-and-training` for the people-side plan |
