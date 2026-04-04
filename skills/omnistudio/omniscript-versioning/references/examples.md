# Examples — OmniScript Versioning

## Example 1: Activating a New OmniScript Version After a Form Change

**Scenario:** A telecommunications company has a `NewService / Residential / English` OmniScript at version 3 that customers use to order new service. The product team has built version 4 with an additional step for equipment selection.

**Problem:** Version 4 has been tested in the UAT sandbox. The team needs to activate it in production without disrupting customers currently using version 3.

**Solution:**
1. The admin exports a DataPack backup of version 3 from production and stores it in the project's DataPacks backup folder.
2. Schedules the activation for 11pm (low traffic window) on a weekday.
3. In production, navigates to OmniStudio > OmniScripts, filters by `NewService / Residential / English`.
4. Clicks Activate on version 4. Version 3 automatically deactivates.
5. Opens the live site in an incognito browser and completes the OmniScript through the new equipment selection step to confirm version 4 is live and correct.
6. Documents the activation in the release log: "NewService/Residential/English v3 → v4, [timestamp], equipment selection step added."

**Why it works:** The DataPack backup ensures version 3 can be restored in under 5 minutes if a defect is discovered. The low-traffic window minimizes disruption to in-flight sessions. The immediate smoke test confirms activation before the support team goes to sleep.

---

## Example 2: Rolling Back After a Broken Activation

**Scenario:** A healthcare company activates version 6 of a `PatientIntake / Default / English` OmniScript. Within 10 minutes, the help desk receives 4 calls from patients unable to complete the intake form — the new version has a broken Remote Action reference.

**Problem:** Version 6 is active in production and failing for all users. Version 5 must be restored immediately.

**Solution:**
1. The admin navigates to OmniStudio > OmniScripts and filters by `PatientIntake / Default / English`.
2. Clicks on version 5 row (Status = Inactive).
3. Clicks Activate on version 5.
4. Version 6 immediately deactivates; version 5 is now live.
5. Confirms in the browser that the intake form loads correctly.
6. Total recovery time: 4 minutes.

**Why it works:** Version 5 was never deleted — inactive versions persist. No deployment was needed, no DataPack import was required. The rollback is a UI action that takes seconds.

**Post-incident action:** The broken Remote Action reference in version 6 is fixed in a new version 7, tested in UAT, and re-promoted during the next maintenance window.
