# Gotchas — Volunteer Management Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: V4S Namespace Omission Causes Silent SOQL Failure

All V4S objects and fields use the `GW_Volunteers__` namespace prefix. SOQL that omits this prefix does not throw an error in anonymous Apex — it simply returns 0 rows, because the compiler resolves it to a non-existent unmanaged object name. This produces a particularly dangerous failure mode: the code appears to run successfully, data import or migration completes with exit code 0, but no volunteer records are created or updated.

**When it bites you:** During initial data load scripts, when a developer writes SOQL against `Volunteer_Hours__c` instead of `GW_Volunteers__Volunteer_Hours__c`. Also when using Salesforce Inspector browser extension, which shows objects without the namespace if you are not in the correct tab.

**Fix:** Always look up V4S API names from Setup > Object Manager with the namespace filter active, or from the installed package documentation. Never reference V4S objects by partial name.

---

## Gotcha 2: DPE-Computed `TotalVolunteerHours` is Not Real-Time

In Nonprofit Cloud, the `TotalVolunteerHours__c` field on Contact is calculated by a Data Processing Engine (DPE) batch job. The DPE runs on a configured schedule — it does not fire on record insert. This means:
- Immediately after a volunteer logs hours, `TotalVolunteerHours__c` is still the old value
- Recognition automations, threshold checks, and volunteer leaderboard displays built to trigger on the hours logging event will read a stale value
- If the DPE job fails or is paused for maintenance, the field will drift from the actual hours sum indefinitely

**Fix:** Never depend on DPE-computed fields in immediate post-insert automations. Either schedule recognitions to run after the next DPE window, or maintain a separate real-time counter using a rollup summary or Apex trigger on the source hours object.

---

## Gotcha 3: V4S Website Plugin Requires Force.com Sites — Not Experience Cloud

The V4S volunteer signup website plugin is built for Force.com Sites (legacy), not Experience Cloud LWR or Aura sites. Many teams assume that because Salesforce has "moved to Experience Cloud," the V4S plugin will work there. It does not. The plugin uses Visualforce pages and a specific Force.com Site configuration.

**Impact:** Teams that provision an Experience Cloud site and expect V4S signup forms to appear there will find blank pages. The signup and self-service volunteer management pages must be hosted on a separate Force.com Site (public access, no login required) using V4S-provided Visualforce pages.

**Fix:** Provision a Force.com Site (Setup > Sites) specifically for V4S. If the org wants to modernize to Experience Cloud, the V4S pages must be rebuilt in LWC — no automatic migration path exists.

---

## Gotcha 4: Flows Uploaded to a Released V4S Package Cannot Be Deleted from the Packaging Org

This gotcha applies to any org that maintains a customized managed package derived from V4S or creates Flow-based enhancements intended to ship as part of a package. Once a Flow version is uploaded to a released managed package (1GP), that Flow version cannot be deleted from the packaging org — only individual versions can be removed. This is a 1GP managed package constraint, not V4S-specific, but it frequently surprises teams who treat V4S as a customizable platform.

**Fix:** Keep all custom volunteer-related Flows in an unmanaged layer on top of V4S, never inside the managed package boundary, to preserve the ability to delete and replace them.

---

## Gotcha 5: NPC Volunteer Objects Are Not Available in Orgs Without the NPC License

`VolunteerInitiative__c` and `JobPositionAssignment__c` are NPC-specific objects that require the Nonprofit Cloud license. Orgs running the Nonprofit Success Pack (NPSP) managed package without an NPC license do not have these objects. Any documentation, AI-generated code, or migration plan that references these objects in an NPSP org will fail with an invalid object error.

**Fix:** Always confirm the license tier before designing the data model. Check Setup > Company Information for installed licenses, and query `PermissionSetLicense` in SOQL to confirm NPC access is provisioned.
