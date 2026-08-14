# OmniStudio Security — Gotchas

## 1. OmniStudio Outputs Are Still Data Exposure Surfaces

Because they are configured declaratively, teams sometimes under-review what they return.

Avoid it:
- Review response contracts like any other application API.
- Return only what the caller needs.

## 2. Apex Behind OmniStudio Keeps Its Own Security Risk

The OmniStudio layer does not compensate for weak `@AuraEnabled` or invocable Apex.

Avoid it:
- Check sharing and CRUD/FLS enforcement explicitly.
- Treat custom Apex as a first-class security boundary.

## 3. Guest-User Scope Should Be Smaller Than Internal Scope

Reusing internal assets externally is the fastest way to overexpose data.

Avoid it:
- Build narrow guest or portal variants.
- Remove unnecessary fields and actions from the external path.

## 4. External Callouts Need Contract Review Too

Authentication is only one part of the security story.

Avoid it:
- Review which Salesforce data leaves the org.
- Keep HTTP responses and failure messages business-safe.

## 5. Standard Runtime Enforces FLS More Strictly Than The Managed Package Runtime

Disabling **Managed Package Runtime** in Omnistudio Settings moves components onto the standard runtime, which needs field-level security granted explicitly on three Omnistudio objects. The symptom of missing it is not an access error: it is a blank FlexCard, an Omniscript that never loads, or an LWC compilation error, which teams misdiagnose as a caching or component defect. The prerequisite is stated on *Disable the Managed Package Runtime and Deploy Custom Lightning Web Components*: "Ensure that field-level security (FLS) is explicitly set for Omni Process Compilation (Read, Edit), Omni Data Transformation (Read), and Omniscript Saved Sessions (Read, Edit) on all user profiles that run Omnistudio components."

The gate is the runtime setting, not the org's release — an org that still runs the managed package runtime does not see this.

Avoid it:
- Grant all three — Omni Process Compilation (Read, Edit), Omni Data Transformation (Read), Omniscript Saved Sessions (Read, Edit) — to every profile that *runs* Omnistudio components, guest and portal profiles included, not only to builders.
- Do not treat the Omnistudio permission sets as covering this. Permission-set assignment and field-level security are separate grants.
- Plan the switch as one-way: "After you disable the managed package runtime setting, you shouldn't re-enable it."

---

## 6. Nested Integration Procedures Skip the Caller's Permission Check

**What happens:** The parent IP has a Required Permission. A guest (or a crafted Aura `GenericInvoke2NoCont` call) still reaches child IPs and Data Mappers that the guest cannot execute directly. Salesforce documents that a parent IP can invoke children the user is not entitled to run. Scale Cache (on by default) makes a **cached** Data Mapper executable regardless of Required Permission.

**When it occurs:** Guest OmniScripts that "pass the token on every LWC call" — that is a client convention, not a boundary. Inactive IP versions with hardcoded URLs stay callable and leak credentials in debug.

**How to avoid:**
- No independently-invocable guest DataRaptor or IP. Named Credentials only; `Allowed Namespaces for Callouts` scoped to `omnistudio`.
- Turn **TurnOffScaleCache** on for guest-reachable Data Mappers; **CheckCachedMetadataRecordSecurity** on IPs.
- Delete inactive IP versions — they still disclose leftover endpoints.
- Treat `global without sharing` classes that implement `omnistudio.VlocityOpenInterface` / `Callable` as a **named unreachable** from every guest entry point. A helper that concatenates a WHERE clause from a map is a SOQL oracle.
- Assert **denial** in tests: guest cannot invoke the helper, cannot run the child IP directly. Zero denial assertions means the boundary was never proven.

---

## 7. `%ContextId%` / `{Params.contactId}` Is Attacker-Controlled

**What happens:** OmniScripts pass `%ContextId%` as `targetId`. FlexCards bind `{Params.contactId}` into an IP `inputMap`. An LWC wrapper reads `contactId` from the query string. Remote Action Apex then loads that Id. Sharing on the parent object may already be wide (guest sharing rule, View All). USER_MODE only helps if the guest cannot already see the row.

**When it occurs:** Experience Cloud guest or portal Omni; "the card is on the record page so ContextId is safe."

**How to avoid:**
- Resolve the subject from `UserInfo.getUserId()` / a server-minted session token, not from the URL.
- Treat ContextId as a display hint. Authorize in Apex/IP against the session, then load.
- Never take `sobjectName` + records from the client into a `without sharing` upsert.

---

## 8. Unsigned IPs Plus Guest Read on All Active Processes

**What happens:** `isIntegProcdSignatureAvl` is false on every IP. Guest OmniProcess sharing is Read where `IsActive = true`. The call path is Aura `GenericInvoke2NoCont` — the OmniScript UI is not a gate. Any active unsigned IP the guest can see is invocable.

**When it occurs:** Public pre-screener / portal orgs that share Omni metadata so the script can run.

**How to avoid:**
- Enable IP signatures. Share OmniProcess by Type/SubType allowlist, not "all active."
- FlexCard guest sharing is often **by Name**, not IsActive — inactive versions of a shared Name stay readable. Share the specific active uniqueName.
- Treat GenericInvoke as the attack surface. Server-check every guest-reachable IP/Apex entry.

---

## 9. Response Action Over-Returns — `returnFullDataJSON` Is a Dump

**What happens:** Response Action with empty `sendJSONPath`, `returnFullDataJSON: true`, or `includeAllActionsInResponse: true` ships the whole IP JSON to the browser — extracts, HTTP bodies, household fields, tokens. Designer preview `customJavaScript` with identifier-shaped fixtures also sits in metadata.

**When it occurs:** "Just send everything so the FlexCard can pick." Guest-reachable IPs.

**How to avoid:** Scope the Response Action to the nodes the UI needs. Never return the HTTP request body. Do not commit preview fixtures that look like real identifiers. Review the IP response like an API contract.

---

## 10. `EnforceDMFLSAndDataEncryption=false` Is an Opt-Out of Data Mapper FLS

**What happens:** Sibling Omni Interaction Config flags (`AdvancedOmnistudioAccessCheck`, `ApexClassCheck`, `EnableQueryWithFLS`) can be true while `EnforceDMFLSAndDataEncryption` is **false**. Data Mappers then run without user-context FLS/encryption. Shield on the field does not stop a DM from merging plaintext into the Omni JSON.

**When it occurs:** Orgs that "turned on the new access checks" but left the DM encryption flag at an old default. Salesforce began defaulting this **true** in Feb 2026 — verify the stored value.

**How to avoid:** Version-control every `OmniInteractionConfig`. Set EnforceDMFLS true and regression-test DM reads. Do not book Shield as IDOR protection on a guest Omni path.

---

## 11. `global without sharing` Callable Is an OmniStudio SOQL/DML Gateway

**What happens:** An IP Remote Action invokes `omnistudio.VlocityOpenInterface` / `Callable` implemented `global without sharing`. Any IP that can see the class can run dynamic queries/DML with sharing and FLS off. A WHERE clause concatenated from IP input is a SOQL oracle.

**When it occurs:** "Helper for portal queries" reused from many IPs; Generic upsert that takes `sobjectName` from the client.

**How to avoid:** `with sharing` + USER_MODE. Hard allowlist of objects and methods. Bind variables only. Named unreachable from guest. Classes with no sharing keyword inherit the IP runtime (system).
