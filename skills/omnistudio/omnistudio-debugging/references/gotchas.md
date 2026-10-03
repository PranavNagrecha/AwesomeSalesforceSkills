# Gotchas: OmniStudio Debugging

Non-obvious platform behaviors that cause real production problems in this domain. Each gotcha names the source it rests on, or marks the claim UNVERIFIED.

## Gotcha 1: A False Execution Conditional Formula Skips the Block Silently

**What happens:** Several Integration Procedure steps never run, and the debug output shows no error. The enclosing block's Execution Conditional Formula evaluated to false.

**When it occurs:** Blocks whose conditions reference a key that is missing or spelled differently in the input JSON.

**How to avoid:** When a step is missing from the debug output, read the enclosing block's condition first. Test with input JSON that contains every key the conditions read.

**Source:** Trailhead, "Explore the Integration Procedure Designer": "All blocks have one property in common, an Execution Conditional Formula. If this formula evaluates to true or isn't defined, the block is executed. If it evaluates to false, the block is skipped."

---

## Gotcha 2: The Response Action Trims What the Caller Receives

**What happens:** The IP debug output shows the right data, but the OmniScript's Action Debugger shows the field missing. The Response Action only sends back the node it was configured with.

**When it occurs:** A new field is added to a Data Mapper or HTTP step, but the Response Action still returns the old node.

**How to avoid:** When data exists in the IP but not in the caller, check the Response Action configuration before the Data Mapper.

**Source:** Trailhead, "Explore the Integration Procedure Designer" ("The Response Action limits what is sent back") and "Get Started with Omnistudio Integration Procedures" ("The Integration Procedure's Response Action trims the data returning to the browser from the server").

---

## Gotcha 3: Cache Blocks Hide Fixes Until They Expire

**What happens:** A fix to a Data Mapper is deployed, but users keep seeing old results. The calling IP wraps the step in a Cache Block that serves stored output from session or org cache.

**When it occurs:** IPs that use Cache Blocks, and Data Mappers with a platform cache type and time to live.

**How to avoid:** Note every Cache Block and cached Data Mapper during debugging. Test with a fresh session, or wait for the cache to expire, before concluding a fix failed.

**Source:** Trailhead, "Explore the Integration Procedure Designer" (Cache Block "saves the output of the steps within it to a session or org cache"). Trailhead, "Explore Data Mapper Features" (Platform Cache Type, Time to Live in Minutes).

---

## Gotcha 4: Previewing a DataRaptor Load Writes Real Records

**What happens:** While debugging a Load, a developer runs Preview with production-like JSON in UAT. The records are created or updated for real.

**When it occurs:** Any Load Preview.

**How to avoid:** Debug Loads in a developer sandbox or scratch org with throwaway target records, or debug them through the calling IP in a sandbox.

**Source:** Trailhead, "Build a Data Mapper Turbo Extract and Data Mapper Load": "The Objects Created panel lists the resulting objects, which are saved permanently."

---

## Gotcha 5: Named Credential Callouts Don't Need Remote Site Settings

**What happens:** An HTTP action fails in production. The team spends hours adding Remote Site Settings, which change nothing, because the endpoint is a named credential and the real problem is the production credential.

The opposite mistake also happens: an HTTP action that calls a raw URL works in a sandbox with a Remote Site Setting that was never created in production.

**When it occurs:** Environment promotion of IPs with HTTP actions.

**How to avoid:** Check how the endpoint is defined. For a named credential, verify the credential, its authentication, and its endpoint in the target org. For a raw URL, verify the Remote Site Setting; `RemoteSiteSetting` is a Metadata API type, so deploy it with the release. UNVERIFIED (2026-10-03): the fetched sources state the named-credential rule for Apex callouts; that IP HTTP actions follow the same rule is inferred from the IP runtime making Apex callouts.

**Source:** Apex Developer Guide, "Adding Remote Site Settings": "If the callout specifies a named credential as the endpoint, you don't need to configure remote site settings." Metadata API Developer Guide, RemoteSiteSetting type.

---

## Gotcha 6: A Deployment Doesn't Guarantee the Intended Version Is Active

**What happens:** A team deploys a new IP or OmniScript version. Production keeps the old behavior because the old version is still active, or the deployed file carried `isActive` false.

**When it occurs:** Any deployment of OmniStudio assets, through metadata or DataPacks.

**How to avoid:** After every deployment, open the asset in the target org and confirm the active version. In metadata, check `isActive` (OmniScript, OmniIntegrationProcedure) and `active` (OmniDataTransform) in the files you deploy.

**Source:** Industries Common Resources Developer Guide, OmniScript and OmniIntegrationProcedure `isActive`, OmniDataTransform `active`. Trailhead, "Create a Simple Omniscript" ("Only one version of an Omniscript can be active at a time").

---

## Gotcha 7: Preview Runs as the Designer, Not the End User

**What happens:** A DataRaptor Extract works in Preview for an admin and returns nothing, or fewer fields, for a portal user.

**When it occurs:** Extracts that serve users with narrower sharing or field access than the designer.

**How to avoid:** Test as a representative user in the deployed context. Turn on the Options-tab field access check for Extracts that serve restricted users, so the designer sees the same field filtering.

**Source:** Trailhead, "Explore Data Mapper Features" (Options tab: check the user's access permissions for the fields). UNVERIFIED (2026-10-03): that Preview executes with the designer's sharing and field access is consistent with the platform but not stated in the fetched sources.

---

## Gotcha 8: Navigation Doesn't Behave the Same in Preview

**What happens:** A Navigate Action seems to do nothing in the OmniScript designer Preview.

**When it occurs:** Testing end-to-end journeys only in Preview.

**How to avoid:** Use Preview to confirm the data the Navigate Action needs, and test the navigation itself in the deployed Lightning page or Experience Cloud site.

**Source:** Trailhead, "Design a Simple Omniscript" (Navigate Action sends "the user back to a previous page after the interaction is complete"). UNVERIFIED (2026-10-03): the statement that Navigate Actions are excluded from Preview is documented only in Salesforce Help.
