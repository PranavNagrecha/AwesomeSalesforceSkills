# Managed Package Development — Work Template

Use this template when building or maintaining a Salesforce 1GP managed package.

## Package Identity

- Package Name: ___________
- Namespace Prefix: ___________ (PERMANENT — cannot change after registration)
- Packaging Org URL: ___________
- Current Released Version: ___________

---

## Pre-Release Review Checklist (Complete Before First Released Upload)

- [ ] PostInstall class API name finalized: ___________ (PERMANENT after first Released upload)
- [ ] UninstallHandler class API name finalized: ___________
- [ ] All custom object API names reviewed and confirmed
- [ ] All Apex class API names reviewed and confirmed
- [ ] All Flows confirmed as required features (cannot delete from packaging org after release)

---

## PostInstall Script Design

```apex
global class {PostInstallClassName} implements InstallHandler {
    global void onInstall(InstallContext context) {
        if (context.previousVersion() == null) {
            // Fresh install logic
            // Keep DML minimal — offload large operations to Queueable
            System.enqueueJob(new SetupQueueable());
        } else {
            Version prev = context.previousVersion();
            if (prev.major() == 1 && prev.minor() == 0) {
                // Upgrade from v1.0 logic
            }
        }
    }
}
```

- [ ] PostInstall script tested via `Test.testInstall(new MyPostInstall(), new Version(0,0), true)`
- [ ] Large DML offloaded to Queueable to avoid subscriber org governor limits

---

## Package Upload Process (NOT CLI)

1. Navigate to packaging org Setup > Package Manager > [Package Name] > Upload
2. Set version number (Major.Minor.Patch)
3. Set release type: [ ] Beta  [ ] Released
4. Set Release Notes and Description
5. Download installation URL

**Do NOT use `sf package version create` — this is for 2GP packages only.**

---

## Patch Org Registry

| Package Version | Patch Org URL | Status | Notes |
|---|---|---|---|
| v1.0.x | | Active/Retired | |
| v2.0.x | | Active/Retired | |

---

## Push Upgrade Plan

| Target Version | Subscriber Orgs | Scheduled Date | Status |
|---|---|---|---|
| | | | |

---

## Notes

_Capture packaging decisions, component lock events, and open questions._
