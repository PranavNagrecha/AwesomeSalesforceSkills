# Gotchas — Custom Metadata Types And Settings

Eleven platform behaviours that change what you ship. Line citations are to the Summer '26 / v62 PDF text of the Apex Developer Guide (`apexdev`), Apex Reference Guide (`apexrefguide`), Metadata API Developer Guide (`api_meta`), and Object Reference (`object_reference`).

## Custom Setting Records Do Not Deploy

**What happens:** An admin or developer deploys a Custom Setting field definition through a change set or SFDX push. The field definition arrives in the target org correctly, but all values — org default, profile-level records, and user-level records — are blank. The feature behaves as if the setting does not exist.

**When it occurs:** Every time a Custom Setting is included in a deployment for the first time in a new org, or when a new environment (sandbox, scratch org) is provisioned. Teams that do this step manually forget it during high-pressure release windows.

**How to avoid:** Document a post-deploy data-setup script that upserts the org-default record using `SetupOwnerId = UserInfo.getOrganizationId()`. Run this script as a deployment step. Never rely on Custom Setting records being present unless they were explicitly created in that org. Grounded for packaging: "Only custom settings definitions are included in packages, not data. To include data, you must populate the custom settings using Apex code run by the subscribing organization after they've installed the package" (apexdev.txt:13561–13562). Note the asymmetry — "custom settings data is included in sandbox copies" (apexdev.txt:13514), so a refreshed full sandbox has the rows and a fresh scratch org does not.

---

## `getInstance()` Never Returns Null — It Returns An Empty Record

**What happens:** Code written defensively as `if (settings == null) { useFallback(); }` never takes the fallback branch, because the platform hands back a real object. "If no custom setting data is defined for the user, this method returns a new custom setting object. The new custom setting object contains an ID set to null and merged fields from higher in the hierarchy. … If no custom setting data is defined in the hierarchy, the returned custom setting has empty fields, except for the `SetupOwnerId` field" (apexrefguide.txt:205095–205105). `getOrgDefaults()` behaves the same way: "If no custom setting data is defined for the organization, this method returns an empty custom setting object" (apexrefguide.txt:205212–205214).

**When it occurs:** In any org where the seeding script has not run — a fresh scratch org, a new developer sandbox, a subscriber org right after package install. The failure is not a NullPointerException on the record; it is a silently null **field** flowing into a threshold comparison or a `(Integer)` cast.

**How to avoid:** Guard the field, not the record: `Integer threshold = cfg.Alert_Threshold__c == null ? 20 : (Integer) cfg.Alert_Threshold__c;`. The record-level null check is only correct for Apex saved using API version 21.0 or earlier, where the guide notes the method did return null (apexrefguide.txt:205106–205108) — modern code that relies on it is testing a condition that cannot occur.

---

## `getValues(userId)` Does Not Merge The Hierarchy; `getInstance()` Does

**What happens:** A developer swaps `getInstance(uid)` for `getValues(uid)` believing them interchangeable and every field that was only set at the org level suddenly reads null. The guide's own worked example is unambiguous: with `OverrideMe` set at org/profile/user and `DontOverrideMe` set only at the org level, `getInstance()` returns `Fluffy` / `World`, while `getValues(RobertId)` returns `Fluffy` / **null** — "Note how this value is null, because you are returning data specific for the user" (apexrefguide.txt:204786–204800). For a **list** custom setting the two are genuinely identical: "`getInstance(dataSetName)` … returns the exact same object as `getValues(dataSetName)`" (apexrefguide.txt:204968–204974).

**When it occurs:** During refactors, and whenever an LLM completes `getValues(` because it saw the list-setting form first. It is invisible in a well-seeded developer org where all three levels happen to carry values.

**How to avoid:** Use `getInstance()` / `getInstance(id)` for anything that consumes a resolved value at runtime. Reserve `getValues(id)` for the narrow case where you deliberately want to know whether a row exists **at that exact level** — which is what makes it the right call inside a seeding or migration script.

---

## Custom Settings Methods Cost No SOQL; A SOQL Query Against The Same Object Does

**What happens:** Two lines that look equivalent have different governor-limit behaviour. "All custom settings data is exposed in the application cache … **However, querying custom settings data using Standard Object Query Language (SOQL) doesn't use the application cache and is similar to querying a custom object.** To benefit from caching, use other methods for accessing custom settings data such as the Apex Custom Settings methods" (apexrefguide.txt:204705–204709). The cached path is explicitly free: "Because the data is cached, access is low-cost and efficient: you don't have to use SOQL queries that count against your governor limits" (apexdev.txt:13521–13522).

**When it occurs:** In helper methods that were written as `[SELECT ... FROM My_Setting__c WHERE SetupOwnerId = :uid]` because that is how every other sObject is read, and in code that "optimises" `getInstance()` into a bulk query inside a trigger handler.

**How to avoid:** Never SOQL a custom setting in runtime code. Reach for SOQL only in a verification script or a data-migration job, where the query cost is irrelevant and you actually need to see all `SetupOwnerId` rows at once.

---

## Inserting A Hierarchy Setting In Both `@TestSetup` And A Test Method Throws `DUPLICATE_VALUE`

**What happens:** A test class seeds the org default in `@TestSetup` and a later test method inserts a row for the same `SetupOwnerId` to exercise an override. In API version 42.0 and later that second insert throws `DUPLICATE_VALUE`; in API 41.0 and earlier both inserts succeeded (apexdev.txt:44803–44807, apexrefguide.txt:205046–205052).

**When it occurs:** When a test class is bumped to a modern API version, or when someone adds a `@TestSetup` block to a class whose methods were already inserting settings individually. The class compiled fine and passed for years.

**How to avoid:** Pick one owner of each `SetupOwnerId`. Seed the org default (`UserInfo.getOrganizationId()`) once in `@TestSetup`, and have test methods insert only *different* owners — a profile Id or a user Id — to build overrides on top of it. To change the org-default value inside a method, query and `update` it rather than inserting a second row.

---

## Apex Tests Cannot See Existing Custom Settings Data

**What happens:** Code that reads `getInstance()` works in the org, then the test for it fails with a null field. "While custom settings data is included in sandbox copies, it is treated as data for the purposes of Apex test isolation. Apex tests must use `SeeAllData=true` to see existing custom settings data in the organization. As a best practice, create the required custom settings data in your test setup" (apexdev.txt:13514–13516).

**When it occurs:** Immediately, for any test on a class that reads a custom setting, and only ever in the test — never in the org where the developer manually verified the feature. This is exactly opposite to the Custom Metadata Type behaviour developers are used to, which makes the failure read as a platform bug rather than as isolation working correctly.

**How to avoid:** Insert the rows in `@TestSetup` and assert against known values. Do not reach for `@IsTest(SeeAllData=true)` to make the failure go away — that couples the test to whatever the org happens to contain and turns a deterministic test into an environment-dependent one.

---

## `Protected` Visibility Does Nothing Outside A Managed Package

**What happens:** A team sets `<visibility>Protected</visibility>` on a custom setting, treating it as a security control, and puts an internal endpoint or a token in a field. The setting is not in a managed package, so nothing is protected: "Protection only applies to custom settings that are marked protected and installed to a subscriber organization as part of a managed package. Otherwise, they are treated as public custom settings and are **readable for all profiles, including the guest user**" (apexdev.txt:13508–13513).

**When it occurs:** In any org building for itself rather than for AppExchange — which is most orgs. The `Protected` label in Setup and in the XML reads like an access control and behaves like a packaging attribute.

**How to avoid:** Treat `visibility` as a packaging switch only. The guide's own instruction for secrets is explicit: "Outside of a managed package, use named credentials or encrypted custom fields to store secrets like OAuth tokens, passwords, and other confidential material" (apexdev.txt:13511–13513). Inside a managed package the flip side bites too: when Privacy is Protected, "the subscribing organization can't edit the values or access them using Apex" (apexdev.txt:13565–13567) — so a protected setting the subscriber is expected to configure is a support ticket waiting to happen.

---

## `customSettingsVisibility` Was Superseded At API 34.0 And Still Round-Trips

**What happens:** A retrieved `.object` file from an old org, or an LLM trained on pre-34.0 examples, writes `<customSettingsVisibility>Protected</customSettingsVisibility>`. That element "is available in API versions 17.0 through 33.0. In versions 34.0 and later, use the `visibility` field instead of this field" (api_meta.txt:41986–41988, restated at 42296–42298). Meanwhile `visibility` "default value is `Public`" (api_meta.txt:42294), so a file carrying only the old element deploys as a Public setting.

**When it occurs:** On migrations off legacy metadata, and whenever a package.xml pins a `<version>` below 34.0 for unrelated reasons.

**How to avoid:** Grep the manifest for `customSettingsVisibility` before every deploy and replace it with `visibility`. The checker in this skill's `scripts/` does this. Also remember `customSettingsType` itself defaults to `Hierarchy` when the element is absent (api_meta.txt:41974–41975) — a definition missing the element is a hierarchy setting, not an error.

---

## Custom Setting Values Are Exposed Through The SOAP API By Default

**What happens:** A setting holding internal configuration is readable by any integration user with object read, because the org-level lock is off unless someone turned it on. `SchemaSettings.enableAdvancedCSSecurity` "indicates whether custom settings type values are available only to Apex, flow, and formula operations (true) or exposed in other contexts such as through the Enterprise WSDL or SOAP API (false). **This field has a default value of false**" (api_meta.txt:125511–125515). The sibling switch `enableSOSLOnCustomSettings` (default false) controls whether the values surface in SOSL results (api_meta.txt:125520–125523).

**When it occurs:** Silently, from the day the setting is created. Nothing in the custom setting's own definition reveals it — the switch lives in `settings/Schema.settings-meta.xml`, which most repos never retrieve.

**How to avoid:** Retrieve `Settings:Schema`, decide both switches deliberately, and commit the file. Turning `enableAdvancedCSSecurity` on is the right default for internal configuration, but it will break any integration that was reading the values over SOAP — inventory those readers first.

---

## Non-Admins Need The Setting Granted, And Describe Lies About It Before API 54.0

**What happens:** A feature works for the admin who built it and returns empty values for everyone else, because read access to a custom setting is a permission that has to be granted. `PermissionSetCustomSettingAccesses` — `enabled`, "indicates whether the records for this custom setting are readable" — is available in API version 47.0 and later (api_meta.txt:94956–94964); `ProfileCustomSettingAccesses` is the profile form (api_meta.txt:97974–97989). Detection code makes it worse on older API versions: "API version 54.0 and later: For custom settings and custom metadata type objects, `DescribeSObjectResult.isAccessible()` returns false if the user doesn't have permissions to access the queried objects. In API version 53.0 and earlier, the method returns **true** even if the user doesn't have the required permissions" (apexdev.txt:44634–44639).

**When it occurs:** At the first non-admin test of the feature, and in any pre-54.0 class whose access guard is `isAccessible()`.

**How to avoid:** Ship a permission set carrying `customSettingAccesses` alongside the setting definition — see `references/metadata-examples.md`. Raise the API version of any class that gates behaviour on `isAccessible()` for a `__c` setting or an `__mdt` type to 54.0 or later.

---

## Geolocation Fields Are Not Available, And List Settings May Be Blocked Org-Wide

**What happens:** A design that stores a service-area centre point or a warehouse coordinate on a custom setting fails at field creation: "Geolocation fields aren't supported in custom settings" (object_reference.txt:2953). Separately, a team that plans a List custom setting may find they cannot create one: `SchemaSettings.enableListCustomSettingCreation` "indicates whether you can create custom settings when using application-level data definitions (true) or not (false). This field has a **default value of false**" (api_meta.txt:125516–125518).

**When it occurs:** Late — after the storage decision is made and the fields are designed, when someone opens Setup and the option is not there.

**How to avoid:** Store latitude and longitude as two Number fields on the setting, or move the data to a Custom Metadata Type or custom object. For flat key-value lookups, plan on a Custom Metadata Type as the primary option and treat List custom settings as available only where the org has explicitly enabled their creation. UNVERIFIED (2026-09-05): the widely repeated claim that List custom settings are formally *deprecated* in Lightning Experience does not appear in the extracted Metadata API, Apex Developer, Apex Reference, or Object Reference guides, which describe list settings as a current feature; the grounded fact is the creation switch above, not a deprecation.
