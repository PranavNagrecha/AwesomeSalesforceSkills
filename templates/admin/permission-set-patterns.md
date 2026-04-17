# Permission Set Patterns — canonical patterns

Used primarily by `permission-set-architect` and consulted by `sharing-audit-agent`, `integration-catalog-builder`, `field-impact-analyzer`, `data-loader-pre-flight`.

This template encodes the **profile-less, additive** model that is the accepted post-Spring '26 posture for Salesforce access. Profiles are treated as minimum-configuration login shells; *everything persona-specific ships as Permission Sets or Permission Set Groups with muting*.

---

## The model

```
User ─► Profile (Minimum_Access_Salesforce)
         │
         ├── PermissionSetLicenseAssignment (license-scoped entitlements)
         │
         └── PermissionSetGroup (persona bundle)
               │
               ├── PermissionSet_A (feature access)
               ├── PermissionSet_B (object access)
               ├── PermissionSet_C (tab/app access)
               └── MutingPermissionSet (persona-specific removals)
```

Rules:
- **Profile = login shell.** Default to `Minimum Access - Salesforce` or the license minimum. No custom profiles unless forced by features that still require profile-level configuration (e.g. Login Hours, IP Ranges, certain record-type defaults).
- **Persona = Permission Set Group.** Each human persona (SDR, Support Agent Tier 1, Billing Specialist, Integration Service User) gets exactly one PSG.
- **Feature = Permission Set.** Each logically cohesive feature/surface gets one PS that can be composed into any PSG.
- **Exceptions = Muting Permission Set.** When a persona bundle grants too much by transitive inclusion, mute rather than fork the feature PS.
- **Integration User = dedicated Salesforce Integration license user + dedicated PSG.** Never reuse a human's permissions for integration work.

---

## PS taxonomy (composition pattern)

Every PSG is composed of these categories of PS. An agent designing or auditing permissions maps each requested entitlement to exactly one category:

| Category | Pattern | Contents |
|---|---|---|
| **App Access** | `App_<AppName>` | Tabs, app launcher, default apps. Never object or record-level access. |
| **Object Access** | `Obj_<Object>_<CRUD_Profile>` | CRUD + FLS. One PS per (object, access-level) pair. `Obj_Opportunity_Full`, `Obj_Opportunity_ReadOnly`. |
| **Feature Access** | `Feat_<Feature>` | System Permissions + Custom Permissions for a feature. `Feat_Manage_Forecasts`, `Feat_Run_Bulk_Dedup`. |
| **Setup Access** | `Setup_<Scope>` | Setup-level permissions (Manage Users, Author Apex, View Setup and Configuration). Rarely used; gated to a named short-list. |
| **Session-Based** | `Session_<Sensitive_Action>` | Requires Session Activation via Flow or step-up auth. `Session_Export_Customer_List`, `Session_Mass_Transfer`. |
| **Time-Limited** | `Temp_<Purpose>` | Assigned with expiration date. `Temp_QuarterClose_BillingReview`. |

---

## Design principles the agent enforces

1. **Least privilege, always additive.** A PSG must include the minimum set of Feature + Object PSes to do the persona's job, then a Muting PS for anything granted transitively but not needed.
2. **One concern per PS.** If you're tempted to name a PS `..._Plus_Extra_Object_Read`, split it into two PSes and compose.
3. **Never grant Modify All Data / View All Data from a persona PS.** Those live only in a named admin-override PS that is not composable into personas. The `security/permission-set-groups-and-muting` skill's refusal-pattern applies.
4. **Integration users get a PSG built from the Integration licenses' entitlements — nothing more.** Named in the pattern `Integration_<System>_Bundle` (e.g. `Integration_NetSuite_Bundle`).
5. **Session-based PSes are used for any action that, if triggered in bulk, would qualify as an exfiltration event.** Mass transfer, data export, impersonation, bulk delete.
6. **Time-limited assignments are used for anything that should not be "on" during steady-state operations.** Quarter-close access, audit windows, war-room incidents.
7. **Deployment order matters.** Object-access PS → Feature PS → PSG → Muting PS → assignment. See `skills/devops/permission-set-deployment-ordering`.

---

## Decision tree: PS vs PSG vs Muting PS

```
is this grant persona-specific?
├── yes  → add to the persona's PSG (or compose a new feature PS into it)
└── no
    ├── is it a reusable feature?       → new PS, compose into PSGs
    ├── is it a *subtraction* from a PSG? → Muting PS attached to that PSG
    └── is it a one-off, short-lived grant? → Temp_<Purpose> PS with expiration
```

Cross-check against:
- `skills/admin/permission-set-architecture`
- `skills/admin/permission-sets-vs-profiles`
- `skills/security/permission-set-groups-and-muting`

---

## Common mistakes the audit agent flags

| Pattern | Why it's wrong | Suggested refactor |
|---|---|---|
| Custom Profile with 200+ permissions | Profile sprawl, upgrade-unsafe | Convert to `Minimum Access` + PSG |
| One PS per user (e.g. `PS_John_Smith`) | Unmaintainable, review-hostile | Re-bucket into a persona PSG; person-specific grants become Time-Limited PSes |
| Modify All Data on persona PSG | Blast radius, SOC-2 finding | Move to break-glass admin PS with session-based + logging |
| Integration user on Admin profile | Standard finding in every Health Check | Dedicated Integration license + `Integration_<System>_Bundle` PSG |
| "Super" PSG that includes 40 feature PSes | No actual persona maps to it; becomes default | Split into persona PSGs; `Super` goes away |
| Muting PS mutes permissions that aren't in the parent PSG | Dead mute | Delete or re-attach |
| PSG contains both object-access AND setup-access PSes | Setup access is cross-cutting | Extract Setup PS to an admin-only PSG |

---

## What the agent should do with this file

**When designing a persona's access (`permission-set-architect`):**

1. Read the persona requirements (job functions, objects touched, features used, sensitivity level).
2. Classify each entitlement into the 6 PS categories above.
3. Propose composition: which existing Feature PSes map, which new ones are needed.
4. Name everything per `templates/admin/naming-conventions.md`.
5. Produce the PSG composition recipe, the list of new PSes to create, the Muting PS if any, and the deployment order (per `skills/devops/permission-set-deployment-ordering`).
6. Identify session-based and time-limited candidates — explicitly flag them.

**When auditing existing access (`sharing-audit-agent` or `permission-set-architect --audit`):**

1. Probe the org via `list_permission_sets` + `describe_permission_set` (MCP tools added in Wave 0).
2. Classify each PS into the taxonomy.
3. Detect the anti-patterns in the table above.
4. Report in severity order (P0: `Modify All Data` on persona; P1: custom profile sprawl; P2: naming drift).
5. In Process Observations: note the org-level score (% of users on minimum-access profiles, ratio of persona PSGs to total users, presence/absence of muting PSes).

---

## Source skills

- `skills/admin/permission-set-architecture`
- `skills/admin/permission-sets-vs-profiles`
- `skills/admin/custom-permissions`
- `skills/admin/delegated-administration`
- `skills/admin/user-access-policies`
- `skills/admin/user-management`
- `skills/admin/integration-user-management`
- `skills/security/permission-set-groups-and-muting`
- `skills/devops/permission-set-deployment-ordering`
