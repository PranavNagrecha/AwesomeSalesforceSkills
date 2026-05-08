# Examples — ISV License Management and Trialforce

## Example 1: Wiring a 2GP managed package to the LMA for the first paid release

**Context:** A 4-person ISV team has shipped their AnalyticsPro 2GP managed package through the AppExchange security review and has the listing live as a free install. They've signed their first paid pilot customer and need to flip from "free install" to "paid, license-enforced" in time for the next release. They have a dedicated production org as the candidate License Management Org (LMO) but have never installed the LMA.

**Problem:** The partner does not know whether to install the LMA in the existing PBO or a separate LMO; how to register the existing released package version with the LMA after the fact; or what to do about the ~30 existing free-install subscriber orgs that don't have License records.

**Solution:**

```text
1. Install the LMA managed package
   - URL: production-AppExchange listing of the LMA (free)
   - Target org: dedicated production org (NOT the PBO — partners with multiple
     packages should keep LMA distinct from listing management)
   - After install, confirm sfLma__License__c, sfLma__Package__c, and
     sfLma__Package_Version__c objects are present

2. Register the existing released package version with the LMA
   - In the AppExchange Publishing Console, open the package row
   - Set License Management Org → the LMO from step 1 (must be E+ edition)
   - Salesforce verifies LMO connectivity; reject with error if LMO is sandbox

3. Set Default License Type and Default Seats on sfLma__Package__c
   - For paid release: Default Type = "Trial", Default Seats = 5,
     Default Expiration = 30 days from install
   - This ensures every NEW install starts as a trial, not a permanent free install

4. Reconcile existing free installs
   - Salesforce does NOT auto-create License records for installs that pre-date
     LMA registration
   - File a Partner Community case: "Reconcile pre-LMA installs for package 04t..."
   - Salesforce backfills sfLma__License__c records for the ~30 existing orgs
     with Status = "Active" and no expiration (grandfathered)

5. Add suspension-monitoring scheduled job in the LMO
   - Apex schedulable that queries sfLma__License__c WHERE Status = 'Suspended'
     OR ExpirationDate__c < TODAY+7
   - Posts to a Slack channel via Named Credential — the LMA itself sends no alerts

6. Verify with a test install
   - Spin up a Developer Edition org
   - Install the package via the production install URL
   - Within ~3 minutes, confirm a new sfLma__License__c row appears in the LMO
     with Status = 'Trial' and the correct expiration
```

**Why it works:** The reconciliation case is the only supported path for backfilling Licenses on pre-registration installs — direct DML against `sfLma__License__c` for a non-existent install is rejected by the platform. Pinning Default License Type to "Trial" with a non-null expiration prevents the silent-permanent-license gotcha (every install gets a clock). The Slack alert closes the LMA's missing-notification gap; without it, suspended licenses go unnoticed until customers call support.

---

## Example 2: Adding a SubscriberToLmo Feature Parameter for usage telemetry

**Context:** The partner ships the AnalyticsPro package with a "Generate Forecast" feature. Sales wants to know how many subscriber orgs are actively using the feature so they can target a paid AI-add-on upsell.

**Problem:** There is no cross-org telemetry surface in the package today. The partner is considering: (a) a callout from the package back to a partner-owned API, (b) a Custom Setting in the subscriber, or (c) a Feature Parameter. The team is unsure which is supported and which is appropriate.

**Solution:**

```xml
<!-- force-app/main/default/featureParameters/Forecast_Used_In_Last_30_Days.featureParameterBoolean-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<FeatureParameterBoolean xmlns="http://soap.sforce.com/2006/04/metadata">
  <description>True if the subscriber org has invoked Generate Forecast in the last 30 days.</description>
  <masterLabel>Forecast Used In Last 30 Days</masterLabel>
  <dataflowDirection>SubscriberToLmo</dataflowDirection>
  <defaultValue>false</defaultValue>
</FeatureParameterBoolean>
```

```apex
// In the package: invoked by the Generate Forecast button handler.
public with sharing class ForecastUsageRecorder {
    public static void markUsed() {
        // Set the FP — the platform schedules propagation to the LMA.
        System.FeatureManagement.setPackageBooleanValue(
            'Forecast_Used_In_Last_30_Days',
            true
        );
    }
}
```

```apex
// In the package: nightly scheduled job that resets the flag if the rolling
// 30-day window has lapsed since the last forecast run.
public with sharing class ForecastUsageReset implements Schedulable {
    public void execute(SchedulableContext sc) {
        DateTime cutoff = DateTime.now().addDays(-30);
        Integer recent = [
            SELECT COUNT()
            FROM Forecast_Run__c
            WHERE CreatedDate >= :cutoff
            LIMIT 1
        ];
        if (recent == 0) {
            System.FeatureManagement.setPackageBooleanValue(
                'Forecast_Used_In_Last_30_Days',
                false
            );
        }
    }
}
```

In the LMO, the partner's RevOps team builds a report on `sfLma__License__c` joined to the auto-created Feature Parameter records, filtered to `Forecast_Used_In_Last_30_Days__c = true`. That report becomes the upsell target list.

**Why it works:** Option (a) requires Remote Site Settings and is rejected during AppExchange security review when the partner cannot justify outbound traffic from a managed package. Option (b) is invisible to the partner without manual login as a subscriber. Only the `SubscriberToLmo` Feature Parameter ships data cross-org through a Salesforce-managed channel that's pre-blessed by the security review.

---

## Example 3: Trialforce template re-snapshot after a UI change

**Context:** AnalyticsPro v2.4 ships a redesigned Forecast tab. Existing trials provisioned from the v2.3-era Trialforce template still show the old tab.

**Problem:** Prospects landing in trials see the old UI; sales demos against the trial org diverge from the live release. The partner's first instinct is to "update the template" via Setup, but the Setup UI offers no in-place template update.

**Solution:**

```text
1. Open the existing Trialforce Source Org (TSO) in the partner's TMO.
2. From the package's AppExchange listing, push-upgrade the TSO to v2.4
   (or install v2.4 manually if the TSO is not auto-upgradable).
3. Re-stage sample data: data may not survive the package upgrade if v2.4
   schema changes affect demo records — verify and reseed.
4. From the TMO, run "Create Trialforce Template" against the TSO.
   This creates a NEW template; the old template is not modified in place.
5. Submit the new template for Salesforce approval (log a case via partner portal).
   Approval typically takes 5–10 business days.
6. Once approved, in the AppExchange Partner Console, edit the listing's
   trial method to point at the new template ID.
7. Old trials in flight remain on v2.3; new signups land on v2.4.
8. Optionally: leave the old template active for 30 days as a rollback target,
   then archive.
```

**Why it works:** Trialforce templates are immutable post-approval — there is no in-place mutation API. The new-template + listing-flip pattern is how Salesforce intends partners to ship trial-UX changes. Skipping the approval step (linking an unapproved template to the listing) results in trial signups failing silently with no indication to the prospect.

---

## Anti-Pattern: Building a custom license-check object instead of using the LMA

**What practitioners do:** A partner who skipped the AppExchange security review (selling the package as a free unmanaged distribution to direct customers) adds license enforcement via a Custom Setting:

```apex
// Anti-pattern: hand-rolled license enforcement
public class LicenseGuard {
    public static void enforce() {
        License_Config__c cfg = License_Config__c.getOrgDefaults();
        if (cfg == null || cfg.Expires_On__c < Date.today()) {
            throw new LicenseException('License expired');
        }
    }
}
```

**What goes wrong:** The `License_Config__c` Custom Setting is owned by the subscriber org. Any subscriber admin can edit `Expires_On__c` to a future date and bypass enforcement. There is no cross-org channel, no audit trail visible to the partner, and no AppExchange Checkout integration path. The partner has no way to suspend a non-paying customer except by emailing them a request to please not use the software.

**Correct approach:** Convert to a 1GP or 2GP managed package, register with an LMA, and use Salesforce's automatic `sfLma__License__c.Status` enforcement. License records in the LMO are not editable by the subscriber, and Salesforce-published license enforcement deactivates package components automatically when `Status` flips to `Suspended` or `Uninstalled` — without a single line of partner Apex.
