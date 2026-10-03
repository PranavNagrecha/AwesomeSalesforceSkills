# Gotchas: Multi-Org Strategy

Non-obvious platform behaviours that turn a multi-org topology into integration debt. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Metadata API" means the Metadata API Developer Guide, Version 67.0; "Object Reference" means the Object Reference, Version 67.0; "Limits Quick Reference" means the Salesforce Developer Limits and Allocations Quick Reference (Summer '26 PDF).

---

## Gotcha 1: Salesforce to Salesforce Is A Connection Object With Its Own Lifecycle, Not An Integration Layer

**What happens:** Records shared through Salesforce to Salesforce (S2S) depend on a `PartnerNetworkConnection` record whose `ConnectionStatus` can be `Inactive`, `Disconnecting`, or `ConnectionSuspended`. When the connection leaves `Accepted`, sharing stops and nothing in the calling org's automation notices. UNVERIFIED (2026-10-03): this skill's earlier claims that S2S runs on SOAP API calls against both orgs' daily allocation and silently drops records once the target org's API allocation is exhausted come from Salesforce Help, which does not fetch; treat them as field reports, not documented behaviour.

**When it occurs:** In orgs that enabled S2S years ago and in orgs where someone proposes S2S as "the native option" for a new cross-org sync. The object is invisible in orgs that never enabled S2S, so an inventory query fails there rather than returning zero rows.

**How to avoid:** Inventory before designing: `SELECT ConnectionName, ConnectionStatus, ConnectionType, ReplicationRole FROM PartnerNetworkConnection`. A `ConnectionType` of `Replication` means Organization Sync, which is a business-continuity feature, not a data-sharing integration. Do not start new integrations on S2S; plan each `Accepted` connection's replacement with REST or Bulk API 2.0 behind a named credential, or the cross-org adapter for read-mostly lookups.

**Source:** Object Reference, PartnerNetworkConnection ("Represents a Salesforce to Salesforce connection between Salesforce organizations"; `ConnectionStatus` and `ConnectionType` picklist values; `ReplicationRole` "only accessible in Salesforce organizations where Organization Sync is enabled"; "If the organization does not have Salesforce to Salesforce enabled, the PartnerNetworkConnection object is not available"). PartnerNetworkRecordConnection ("Represents a record shared between Salesforce organizations").

---

## Gotcha 2: Formulas, Roll-Ups, And Master-Detail Cannot Span Orgs, Even Through External Objects

**What happens:** A design assumes a roll-up summary or formula on the hub org can total values from a spoke org's records surfaced as external objects. External objects cannot hold formula, roll-up summary, or master-detail fields, and support only lookup, external lookup, and indirect lookup relationships. A "total contract value across all orgs" field has no declarative path.

**When it occurs:** Whenever a reporting or validation requirement needs data from two orgs in one calculation.

**How to avoid:** Choose one of two paths and cost it in the design: replicate the needed values into the hub with a scheduled Bulk API 2.0 or REST job and calculate locally, or aggregate in an analytics layer that reads both orgs (CRM Analytics with the Salesforce External Connector, or a warehouse). Record which org owns each aggregate.

**Source:** Metadata API, CustomField ("These custom field types aren't available for external objects": Formula, Master-detail relationship, Roll-up summary; Auto-number, Currency, and Picklist are "available only with the cross-org adapter for Salesforce Connect"). Object Reference, Overview: "Only lookup, external lookup, and indirect lookup relationships are available for external objects." Analytics Platform Setup Guide (Spring '26), CRM Analytics Limits: the Salesforce External Connector syncs "Up to 20 million rows or 10 GB per object" per job.

---

## Gotcha 3: Each Org Has Its Own Inbound API Allocation, Computed From That Org's Licences

**What happens:** A hub org calls a spoke org every few minutes for every changed record. The calling side looks safe: at most 100 callouts per Apex transaction and 120 seconds of cumulative callout time. The receiving side runs out first, because its 24-hour inbound allocation is computed from the spoke's own licence count, which is usually small. Allocation is enforced against the aggregate of all API calls into that org, not per user.

**When it occurs:** Hub-and-spoke designs where a large hub polls or pushes into a small spoke, and M&A spokes with a few dozen licences.

**How to avoid:** Compute the receiving org's allocation before choosing the pattern. For Enterprise Edition it is 100,000 plus the number of licences multiplied by the per-licence-type calls (1,000 for a Salesforce licence), plus purchased add-ons. A 40-licence Enterprise spoke receives 140,000 calls per 24 hours for every integration combined. Move volume to Bulk API 2.0 jobs, batch changes, and set API Usage Notifications in both orgs.

**Source:** Limits Quick Reference, Total API Request Allocations ("total inbound API requests (calls) per 24-hour period for an org"; Enterprise "100,000 + (number of licenses x calls per license type)"; "Limits and allocations are enforced against the aggregate of all API calls made to the org in a 24-hour period. Limits and allocations are not on a per-user basis"; "The total number of API requests allowed is defined by the users' licenses in the org"). Apex Developer Guide, Execution Governors and Limits: "Total number of callouts (HTTP requests or web services calls) in a transaction" 100; "Maximum cumulative timeout for all callouts" 120 seconds.

---

## Gotcha 4: Single Sign-On Does Not Deprovision, And Just-in-Time Provisioning Only Acts At Login

**What happens:** Each org is a separate service provider. A leaver is disabled in the IdP and can no longer start an SSO session, but the user record in each spoke stays active with its permissions, and any username-and-password or API access that user had keeps working. Just-in-Time provisioning on the SAML configuration "creates users the first time they log in"; it does not touch users who never log in again.

**When it occurs:** Every multi-org estate that relies on SSO alone for joiner, mover, and leaver handling.

**How to avoid:** Treat deprovisioning as its own design item per org: an IdP provisioning connector that deactivates users, or a scheduled reconciliation that compares the IdP's leaver list with active users in every org. UNVERIFIED (2026-10-03): SCIM-based provisioning from Okta or Microsoft Entra ID into each Salesforce org is configured in the IdP and Salesforce Help; no fetched Salesforce PDF documents it. MFA is still required for logins that arrive through SSO, so the IdP must enforce it for every org.

**Source:** Metadata API, SamlSsoConfig (`userProvisioning`: "If true, Just-in-Time user provisioning is enabled, which creates users the first time they log in"; `samlJitHandlerId`; `executionUserId` "must have the Manage Users permission"). Salesforce Security Guide, Version 67.0, Multi-Factor Authentication: the MFA requirement "applies equally to direct logins with a Salesforce username and password and to logins via single sign-on (SSO)."

---

## Gotcha 5: External Objects Are Live Callouts With No Triggers And No Apex-Managed Sharing

**What happens:** Spoke data surfaced in the hub as external objects looks like local data in list views and SOQL. Every access is a real-time callout to the other org, and external objects support neither Apex triggers nor Apex-managed sharing. A design that expects "when the EU opportunity closes, update the hub account" from a trigger on the external object cannot be built. UNVERIFIED (2026-10-03): the earlier statement that each external object SOQL query counts against a per-transaction "external SOQL" limit was not found in a fetched source.

**When it occurs:** Hub designs that use the cross-org adapter for anything beyond display-time lookups, and batch Apex that iterates external records.

**How to avoid:** Use external objects for low-volume, on-demand reads. Drive cross-org automation from the owning org (a platform event or callout from the spoke's own trigger), not from the reader. For batch Apex over external data, note that an iterable batch stores the external records in Salesforce while the job runs; a `Database.QueryLocator` batch does not.

**Source:** Object Reference, External Objects ("access the data in real time via web service callouts"; "best used when you have a large amount of data that you can't or don't want to store in your Salesforce organization, and you need to use only a small amount of data at any one time"). Apex Developer Guide, Apex Considerations for Salesforce Connect External Objects ("These features aren't available for external objects: Apex-managed sharing; Apex triggers"; the iterable batch storage note).

---

## Gotcha 6: Environment-Specific Endpoints And Org Ids Break Every Promotion

**What happens:** An Apex class hard-codes the spoke org's My Domain URL or 18-character Organization Id. The class works in the sandbox paired with a spoke sandbox, then calls the wrong org, or fails, after deployment to production.

**When it occurs:** Any cross-org callout written before a named credential existed, and Flow or custom setting defaults that hold org-specific values.

**How to avoid:** Create a named credential with the same name in every org, each pointing at its own counterpart's URL, and reference only `callout:Name/path` in code. Keep non-authentication routing values in custom metadata records per environment. Run this skill's checker (`scripts/check_multi_org.py --project-dir force-app`) to find literal endpoints and org Ids.

**Source:** Apex Developer Guide, Named Credentials as Callout Endpoints: "If you have multiple orgs, you can create a named credential with the same name but with a different endpoint URL in each org." An Apex class that uses the shared name "can be packaged and deployed on all those orgs without programmatically checking the environment."

---

## Gotcha 7: The Cross-Org Adapter Is Its Own Data Source Type, And Writes Need API 39.0 Or Later

**What happens:** Designers configure an OData 4.0 data source against another Salesforce org, or assume external objects from another org are read-only by nature. The cross-org adapter is a separate external data source type (`SfdcOrg`) with its own configuration (`apiVersion`, `environment`, `searchEnabled`, `timeout`). Writable external objects through the cross-org adapter require `isWritable` set in API version 39.0 or later. This corrects the earlier version of this skill, which routed cross-org lookups through "OData adapter to target org REST API".

**When it occurs:** When the hub needs spoke records on demand and the team reaches for OData because it is the adapter they know.

**How to avoid:** Use `ExternalDataSource` type `SfdcOrg` for Salesforce-to-Salesforce lookups. Decide per data source whether writes are allowed; leave `isWritable` false unless the reading org is meant to edit the owning org's records. Choose `principalType` deliberately: `NamedUser` runs every request as one integration identity in the target org, `PerUser` maps each user to their own identity there.

**Source:** Metadata API, ExternalDataSource (`type` value `SfdcOrg`, listed as the cross-org adapter; the cross-org adapter's `customConfiguration` sample `{"apiVersion":"32.0","environment":"CUSTOM","searchEnabled":"true","timeout":"120"}`; `isWritable` "with the cross-org adapter for Salesforce Connect, you can set this field to true only in API version 39.0 and later"; `principalType` values).

---

## Gotcha 8: A Named-Principal Data Source Fails When One User In Another Org Changes

**What happens:** A named-principal external data source authenticates every hub user as one identity in the spoke. When that spoke user is deactivated, loses a permission set, or has its password or OAuth grant revoked, every hub page that shows spoke data fails at once, and the error appears in the hub while the cause sits in the spoke. UNVERIFIED (2026-10-03): the earlier claims that the user needs an "Integration User license or higher" and that the failure shows as zero rows rather than an error are not in a fetched source.

**When it occurs:** Offboarding sweeps in the spoke, permission clean-ups, and credential rotations done by a team that does not know the hub depends on that user.

**How to avoid:** Use a dedicated, named integration user per data source in each target org, never a person's account. List it in the spoke's runbook as a dependency of the hub. Exclude it from automated leaver processes, and monitor its active status and last login.

**Source:** Metadata API, ExternalDataSource `principalType` (`NamedUser` versus `PerUser`, "Determines whether you're using one set or multiple sets of credentials to access the external system") and `username` ("Make sure that the credentials you use have adequate privileges to access the external system").

---

## Gotcha 9: Every Org Needs Its Own Service Provider Registration At The IdP

**What happens:** Users can single sign-on into the first org but the second rejects the assertion. Each org's SAML configuration has its own `samlEntityId`, which is both the issuer in requests Salesforce sends and the expected audience of inbound responses; Salesforce recommends the org's My Domain login URL. An IdP application copied from the first org carries the wrong audience for the second.

**When it occurs:** When a second or third org is added to an existing SSO setup, and after a My Domain change.

**How to avoid:** Register one IdP application per org with that org's entity ID and login URL, map users on Federation ID consistently across orgs, and include the `SamlSsoConfig` of each org in its own release manifest.

**Source:** Metadata API, SamlSsoConfig (`samlEntityId`: "The issuer in SAML requests generated by Salesforce, and is also the expected audience of any inbound SAML Responses. Salesforce recommends that you use your My Domain login URL"; `identityMapping` `FederationId`; suffix `.samlssoconfig` in the `samlssoconfigs` folder).
