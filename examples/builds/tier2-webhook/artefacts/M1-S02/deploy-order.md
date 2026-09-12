# Deploy order — M1-S02 (External Credential, Named Credential, permission set)

Build `tier2-webhook` · step `M1-S02` · type `access` · owner `metadata-builder`
(run under `build-step-runner`) · API version **67.0** (assumption A11) ·
`build_mode: design-only` — **nothing here has been deployed, and this agent deploys nothing.**

This step carries `human_gate: true`. Its `step:M1-S02` gate was approved at
`2026-09-12T10:01:57Z` before the build began; the access review in § 6 is a *second*,
post-build read the reviewer performs at the M1 gate against the files themselves.

## 0. Rebuild record — run 2, after mock-deploy run 1 rejected run 1's credential

This step was built once, tested clean, and **failed the operator's dry-run validation**
(`reports/MOCK-DEPLOY-M1.md` run 1 — `checkOnly`, org `sfskills-dev`, API 67.0: 23 components,
22 ok, 2 errors). The org's two errors, verbatim:

| Component | Error |
|---|---|
| `ExternalCredential OnCall_Tool_EC` | `The parameter type "AuthHeader" requires these fields: ParameterValue.` |
| `PermissionSet Tier2_Webhook_Admin` | `The OnCallToolNamedPrincipal parameter value doesn't exist or you may not have permission to access it.` |

**S2-F-02 (HIGH).** Run 1 shipped the `AuthHeader` parameter with no `parameterValue`, deliberately:
the formula grammar was UNVERIFIED in the cited skill *and* nothing in the plan, the 45
clarifications or `requirement.md` named the parameter the API key is stored under. The org has now
answered the question the build could not: `parameterValue` is **required** on an `AuthHeader`
parameter. Run 1's own § 5 item 1 flagged exactly this as an open UNVERIFIED question; the dry run
closed it.

**S2-F-03 (cascade).** The permission set's `externalCredentialPrincipalAccesses` grant names the
principal of the credential that failed in the same request, so it could not resolve. Nothing is
wrong with the permission set — it is expected to clear once the External Credential validates, and
run 2 of the dry run is where that is confirmed.

**What the requester supplied** (step `amendments[1]`, `2026-09-12T10:23:06Z`; the `step:M1-S02`
gate was **rejected and re-signed** at `2026-09-12T10:23:07Z` on the amended inputs). The clarifier
never asked either fact — driver's log 26:

| Fact | Value |
|---|---|
| Endpoint URL | `https://api.oncall.example/v1/salesforce/escalations` — production and sandbox share this host and differ only in the key |
| Principal authentication parameter | `ApiKey`, entered in Setup post-deploy, never in metadata |
| `AuthHeader` `parameterValue` | `{!$Credential.OnCall_Tool_EC.ApiKey}` |

**What changed in run 2 — two values in two files, and nothing else:**

| File | Change |
|---|---|
| `externalCredentials/OnCall_Tool_EC.externalCredential-meta.xml` | `parameterValue` added to the `X-API-Key` `AuthHeader` parameter (**fixes S2-F-02**) |
| `namedCredentials/OnCall_Tool.namedCredential-meta.xml` | `Url` `parameterValue` changed from the reserved-domain placeholder to the real endpoint |
| `permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml` | **byte-identical to run 1** — SHA-256 `9988b317…65de5a` before and after. S2-F-03 was a cascade, not a defect in this file |
| `package.xml` | **byte-identical** — SHA-256 `43c142d1…89b65d`. No member changed |

The permission set and manifest being untouched is the point: the fix belongs entirely to the
credential, and re-running the access review against an unchanged file costs the reviewer nothing.

## 1. What this step ships

| # | Component | Type | Manifest member | File |
|---|---|---|---|---|
| 1 | `OnCall_Tool_EC` | ExternalCredential | `OnCall_Tool_EC` | `externalCredentials/OnCall_Tool_EC.externalCredential-meta.xml` |
| 2 | `OnCall_Tool` | NamedCredential | `OnCall_Tool` | `namedCredentials/OnCall_Tool.namedCredential-meta.xml` |
| 3 | `Tier2_Webhook_Admin` | PermissionSet | `Tier2_Webhook_Admin` | `permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml` |

Three components, three manifest members, no member without a file and no file without a member.

## 2. Order inside this step

**ExternalCredential → NamedCredential → PermissionSet.** Each artefact names the one before it,
which is why the order is not negotiable:

1. **`OnCall_Tool_EC` before `OnCall_Tool`.** The Named Credential's Authentication parameter
   carries `<externalCredential>OnCall_Tool_EC</externalCredential>`. `externalCredential` is a
   field of `NamedCredentialParameter`, not a top-level field of `NamedCredential`
   (`apex/apex-named-credentials-patterns/references/code-examples.md` § 2, `api_meta`
   L90272–90278) — a reference to a credential that does not yet exist resolves to nothing.
2. **`OnCall_Tool_EC` before `Tier2_Webhook_Admin`.** The permission set's
   `externalCredentialPrincipal` value is built from the External Credential's file stem and the
   `parameterName` of its `NamedPrincipal` parameter. Gotcha 6 in the same skill: "the External
   Credential declares the principal and the Permission Set grants it — two files, two deploys,
   in that order."
3. **`Integration_Failure__c` and its fields (M1-S01) before `Tier2_Webhook_Admin`.** See § 3.

A single `sf project deploy start` over this manifest resolves all three; the order above is what
that request must not be split against, and what a split *must* follow if one is forced.

## 3. Order against the rest of the build

| Must precede | This step | Why |
|---|---|---|
| **M1-S01** `Integration_Failure__c` + its 12 fields + `Case.Tier2_Notified_At__c` | this step's permission set | "Permission sets referencing new fields fail if fields are not yet in the target" (`admin/change-management-and-deployment/references/llm-anti-patterns.md` Anti-Pattern 4). Every one of the 12 `fieldPermissions` rows names a field M1-S01 creates. |

| This step | Must precede | Why |
|---|---|---|
| `OnCall_Tool` | **M1-S03** Apex callout | The Apex names `callout:OnCall_Tool`. A `callout:` naming a credential not in the org fails at run time, and the step's own checker raises `NC-APEX-003` when the name does not resolve in the tree. |
| `Tier2_Webhook_Admin` | **M1-S03** / **M1-S04** first run | A principal is inert until a permission set grants it *and* that set is assigned to the running user (`api_meta` L94794–94796; gotcha 6). Without the assignment every callout returns 401. |
| — | **M1-S05** build-level `package.xml` | M1-S05 aggregates; it does not re-declare these files. |

**Do not deploy this step in the same request as M1-S01.** M1-S01's `deploy-order.md` § 3 records
why: retrieving a `CustomObject` "makes the component appear in any Profile and PermissionSet
components that are retrieved in the same package" (`api_meta` L41920–41921). Two requests,
objects first.

## 4. Decisions recorded while writing these files

| Element | Value written | Source |
|---|---|---|
| `authenticationProtocol` | `Custom` | Step input + decision **D2**. The guide's enum is `AwsSv4`, `Basic`, `Custom`, `Jwt`, `JwtExchange`, `NoAuthentication`, `Oauth`, `Password` (`api_meta` L63641–63657); `Custom` is "User-created authentication". |
| Principal | `OnCallToolNamedPrincipal`, `NamedPrincipal`, `sequenceNumber 1` | Step input (Q4) + decision **D3**. `NamedPrincipal` = "the same set of user credentials for all users" (`api_meta` L63806–63808); only the named principal works from a Queueable. |
| Auth header | `parameterName X-API-Key`, `parameterType AuthHeader`, `parameterValue {!$Credential.OnCall_Tool_EC.ApiKey}`, `sequenceNumber 1` | Step input (Q6) + requester answer (`amendments[1]`). "When using AuthHeader, the `parameterName` field must be the header name as a string, and `parameterValue` must be a formula of a header value that is evaluated at run time" (`api_meta` L63757–63764). `parameterValue` is **required** — the org said so in dry-run run 1 (§ 0, S2-F-02). |
| `namedCredentialType` | `SecuredEndpoint` | Step input + decision **D3**. Every legacy field is deprecated at API 56.0; `<endpoint>` "is valid only when NamedCredentialType is set to Legacy". |
| URL | `namedCredentialParameters` / `parameterType Url` / `https://api.oncall.example/v1/salesforce/escalations` | Gotcha 5: in a `SecuredEndpoint` credential the URL lives in a parameter, **not** in `<endpoint>` — "and the wrong one deploys cleanly". Value supplied by the requester (`amendments[1]`); **§ 5 item 2**. |
| `generateAuthorizationHeader` | `false`, written explicitly | Step input (Q5). It **defaults to true** (`api_meta` L90039–90046); left absent, the platform would add its own `Authorization` on top of the External Credential's `X-API-Key`. |
| `allowMergeFieldsInHeader` / `allowMergeFieldsInBody` | both `false`, written explicitly | Step input. Both already default to `false` (`api_meta` L89914–89940); they are written out because Q5 makes "Apex never builds the key header" a decision, not an accident. |
| `calloutStatus` | `Enabled` | Step input. `Disabled` is how you ship a credential that is not yet usable (API 59.0+, `api_meta` L90000–90007). |
| `externalCredentialPrincipal` | `OnCall_Tool_EC-OnCallToolNamedPrincipal` | Built from the two authoritative sources, not from memory: the EC file stem, a **dash**, the principal's `parameterName` (`api_meta` L94995–94999; gotcha 7). An underscore here fails silently at run time. |
| `objectPermissions` | `Integration_Failure__c`, all six flags `true` | Step input (Q19 CRUD) + decision **D12** / assumption **A3**. The chain holds: `modifyAllRecords` requires read, edit, delete and `viewAllRecords`, all present. The checker's sharing-bypass WARN on this row is **deliberate** per D12. |
| No `objectPermissions` row for `Case` | omitted | Assumption **A14**. Verified in the checker's source: the object-row rule is guarded by `if has_object_row and owner not in granted_objects`, so a `fieldPermissions` entry for a `Case` field with no `Case` object row cannot fire it. A `Case` CRUD row would grant more than any answer asked for. |
| `fieldPermissions` | 11 `Integration_Failure__c` fields + `Case.Tier2_Notified_At__c`, all `readable` **and** `editable` true | Step input (Q19 FLS) + PV-001. `editable` never ships without `readable`: `PermissionsEdit` requires `PermissionsRead` and a row without it "will be deleted". |
| `Status__c` **excluded** | omitted | Operator amendment F-S2-01 (`2026-09-12T09:41:08Z`) and decision **D-M1S01-02**. `Status__c` is `required true`, and "In API version 30.0 and later, permissions for required fields can't be retrieved or deployed" (`api_meta` L95020–95021). **Eleven fields, not twelve.** |
| `hasActivationRequired` | `false` | `admin/permission-set-architecture/references/metadata-examples.md` § 1. A session-based set loses its step-up requirement inside a PSG (gotcha 5 in that skill); nothing here is session-based. |
| `license` | **not declared** | The skill requires this to be "populated or empty by decision". D14's assignee set is every user who can escalate a Case plus the scheduling user — a population nothing in the answers pins to one license — and `license` "pins a permission set to one license". Left empty deliberately. |
| `<fullName>` | **not written** in any of the three files | Source format carries the API name in the file name. All three fenced examples in the cited skills omit it (`code-examples.md` §§ 1–3, `metadata-examples.md` §§ 1–2); only the `PermissionSetGroup` example carries one, and this step ships no PSG. |

## 5. UNVERIFIED and unbound — read before deploying

Run 1 listed four items here. **Two are now closed by the requester and the org** (§ 0); the
remaining two are unchanged. None is guessed; each is written the narrowest legal way and flagged.

1. **CLOSED — the `X-API-Key` `AuthHeader` `parameterValue` is written.**
   `{!$Credential.OnCall_Tool_EC.ApiKey}`. Both halves of run 1's open question are answered:
   - *The parameter name.* The requester named it: the principal's authentication parameter is
     `ApiKey`, entered in Setup post-deploy (`amendments[1]`, `2026-09-12T10:23:06Z`). Assumption
     **A5** is therefore closed by a human answer, not by a build-side guess — the clarifier never
     asked the question (driver's log 26).
   - *Whether the element is required.* Answered by the org, not by the guide: dry-run run 1
     returned `The parameter type "AuthHeader" requires these fields: ParameterValue.` Run 1's own
     UNVERIFIED note asked exactly this and the dry run settled it.

   **Still narrowing rather than fully proven.** What is now established is that the element is
   required and that this formula is the shape the requester intends. What the next dry run
   establishes is that the **grammar parses on deploy**; what only UAT establishes is that the
   **header arrives at the on-call tool carrying the key at run time**. The Metadata API guide still
   publishes no formula grammar for this field (`api_meta` L63760–63761) and the
   External-Credential-scoped `$Credential.<EC>.<Param>` form still appears in no guide — the cited
   skill's UNVERIFIED marker (2026-09-05) stands. Two checkpoints remain:
   **(a)** mock-deploy run 2 — proven live on deploy; **(b)** UAT — header behaviour at run time
   confirmed against the on-call tool. A clean deploy is not evidence of (b): a formula that parses
   and resolves to an empty string deploys perfectly and 401s on every callout.

2. **CLOSED — the endpoint URL is real.** `https://api.oncall.example/v1/salesforce/escalations`,
   supplied by the requester (`amendments[1]`): the on-call tool's inbound events endpoint, HTTPS,
   with production and sandbox sharing the host and differing only in the key entered in Setup. The
   reserved-domain placeholder run 1 shipped is gone. Assumption **A7**'s portability rule still
   holds and still points here: the API name is identical in every org, and this parameter is the
   one thing that may legitimately differ — so confirm the value per target org even though it is
   no longer a placeholder.

3. **UNCHANGED — the Authentication parameter's own `parameterName` (`OnCallToolAuth`) was derived,
   not supplied.** `NamedCredentialParameter` requires a `parameterName`, the plan binds only the
   `parameterType` and the `externalCredential` link, and the cited skill's fenced example names its
   equivalent `PartnerOrdersAuth`. It is a label for the parameter row, referenced by neither Apex
   nor the permission set. It validated in dry-run run 1. Rename freely.

4. **UNCHANGED — assumption A2 is still the one that decides whether this set is assigned widely
   enough, and it is `risk: high` and self-flagged UNVERIFIED.** It rests on the library's own
   hedged wording — async Apex runs as "often the user who fired the async" — and A2's own text
   says "confirm in a scratch org before go-live." Nothing in dry-run run 1 touches it: a
   `checkOnly` validation does not execute a Queueable, so this assumption cannot be closed by any
   deploy, only by a run. If it is wrong the failure is loud: every escalation returns 401 and lands
   in an `Integration_Failure__c` row.

## 6. Access review for the M1 gate

The step's `manual` acceptance test. A reviewer confirms, from `artefacts/M1-S02` alone:

- **(a)** `externalCredentialPrincipal` reads exactly `OnCall_Tool_EC-OnCallToolNamedPrincipal` —
  dash-joined, matching the EC file stem and the principal's `parameterName`. ✅ as written.
- **(b)** No credential value appears anywhere in the three files. ✅ — the `AuthHeader`
  `parameterValue` is a **merge-field reference** (`{!$Credential.OnCall_Tool_EC.ApiKey}`), not a
  key: it names where the platform reads the secret from at run time. The secret itself is entered
  in Setup (§ 7 step 2) and appears in no file here.
- **(c)** `generateAuthorizationHeader` is explicitly `false`. ✅ as written.
- **(d)** `fieldPermissions` carries `Case.Tier2_Notified_At__c` with `readable` and `editable`
  both true, and every `Integration_Failure__c` field from M1-S01 **except the required
  `Status__c`**. ✅ — 12 rows, listed in § 4. **No checker fails on the absence of a grant, so
  this clause is the check**: count the rows.
- **(e)** The assignee set in § 7 step 3 is the one decision **D14** defines — every user who can
  escalate a Case to `Tier_2_Engineering`, **plus** the user who schedules the hourly job (A13) —
  and a **named person accepts that wider list, or sends D14 back.** It is wider than Q19's three
  Support Engineering admins, and § 5 item 4 is why.
- **(f)** The `X-API-Key` `AuthHeader` `parameterValue` formula is flagged for confirmation. ✅ —
  the requester supplied the formula and the org confirmed the element is required (§ 0), so A5 is
  closed. The grammar itself is **proven on deploy at mock-deploy run 2** and its **runtime header
  behaviour confirmed at UAT** — § 5 item 1. A reviewer should read this clause as *narrowed*,
  not discharged.

## 7. What no deploy performs — the human steps, in order

The deploy of these three files does **not** make the integration work. Four steps, none of which
any agent in this loop performs:

0. **Confirm the endpoint per target org.** The `Url` `parameterValue` now carries the real
   endpoint (§ 5 item 2). It is no longer a placeholder, but it is still the one parameter designed
   to differ per org — check it rather than assume it.
1. **Enter the API key in Setup**, against the `OnCallToolNamedPrincipal` principal on
   `OnCall_Tool_EC`. Setup → Named Credentials → External Credentials → `OnCall_Tool_EC` →
   Principals → `OnCallToolNamedPrincipal` → Edit → add an authentication parameter **named
   exactly `ApiKey`** holding the key. **The name is load-bearing**: the `AuthHeader` formula
   `{!$Credential.OnCall_Tool_EC.ApiKey}` resolves by that name, so a parameter named anything else
   leaves the header empty and every callout returns 401. The value is **never** in metadata, never
   in an export, and does not survive a sandbox refresh — so this step repeats in every org.
2. **Assign the permission set.** Per D14 + A13, to every user who can escalate a Case to
   `Tier_2_Engineering` **and** to the user who will run `System.schedule` for M1-S04:

   ```bash
   sf org assign permset --name Tier2_Webhook_Admin --target-org <alias>
   ```

3. **Verify against a real user** before the first escalation, per the cited skill's workflow
   step 7.

## 8. Validate-only command — for a human to run, never for an agent

This build never deploys. When a human wants an org-side check of this step, the loop's own
dry-run wrapper is the supported route (it hard-codes `checkOnly: true`):

```bash
python3 scripts/mock_deploy.py .sfskills/builds/tier2-webhook/plan.json \
  --org-alias <alias> --milestone M1
```

The raw equivalent, if the artefacts are assembled into a DX project by hand:

```bash
sf project deploy start --manifest package.xml --target-org <alias> --dry-run
```

Run the M1-S01 objects request **before** this one (§ 3).
