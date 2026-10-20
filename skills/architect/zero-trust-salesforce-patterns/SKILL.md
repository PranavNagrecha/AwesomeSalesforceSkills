---
name: zero-trust-salesforce-patterns
description: "Architecture pattern for assembling a zero-trust posture in Salesforce — there is no single zero-trust toggle. The pattern composes High-Assurance Sessions, Real-Time Event Monitoring (RTEM) Transaction Security Policies, Login Flows for conditional access, Event Monitoring for continuous verification, Mobile Security for device compliance, and a Permission Set Group strategy that defaults-deny. Covers the gotcha that not all RTEM event types support TSP enforcement (IdentityVerificationEvent and MobileEmailEvent do NOT). NOT for the LLM-side Einstein Trust Layer, an unrelated concept despite the shared word — use agentforce/einstein-trust-layer. NOT for MFA-only rollouts — use security/mfa-enforcement-strategy. NOT for Apex CRUD/FLS enforcement — use apex/apex-stripinaccessible-and-fls-enforcement."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do we implement zero trust in salesforce"
  - "salesforce continuous verification session policy"
  - "device trust conditional access salesforce architecture"
  - "transaction security policy versus session high assurance"
  - "continuous risk assessment after login salesforce"
  - "zero trust beyond mfa salesforce"
tags:
  - zero-trust
  - rtem
  - transaction-security
  - high-assurance-session
  - login-flow
  - event-monitoring
  - device-compliance
inputs:
  - "Org's current MFA, SSO, and session-management posture"
  - "Whether Shield (Event Monitoring + Real-Time Event Monitoring) is licensed"
  - "Mobile Security / MDM tooling currently in use, if any"
  - "List of high-assurance objects/operations to gate behind step-up auth"
outputs:
  - "Layered control map: which Salesforce control covers which zero-trust principle"
  - "RTEM event-type → Transaction Security Policy enforcement matrix (with the unsupported event types called out)"
  - "Phased rollout plan from current state to layered zero trust"
  - "Risk register: gaps Salesforce cannot close natively (CAEP, third-party device-trust signals)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Zero-Trust Salesforce Patterns

"Zero trust" in Salesforce is not a feature you turn on — it is an
architecture pattern you assemble out of multiple existing controls.
There is no single setting labeled "Enable Zero Trust" and there is no
short version of the pattern that gets the same coverage. Teams that
treat MFA as the whole answer ship something that auditors will
correctly call MFA, not zero trust.

This skill catalogues the controls Salesforce ships, maps each to the
zero-trust principle it covers (verify explicitly, least privilege,
assume breach), and documents the operational gotchas — most importantly
that Real-Time Event Monitoring's Transaction Security Policy enforcement
does not cover every RTEM event type. The output is a layered control
map and a phased rollout, not a single recommendation.

It does **not** cover MFA rollouts (covered separately by
`security/mfa-enforcement-strategy`), the Einstein Trust Layer (a
different concept — LLM trust), or per-Apex CRUD/FLS enforcement.

---

## Before Starting

- Confirm **licensing**. Transaction Security policies "require Salesforce Shield or Salesforce Event Monitoring add-on subscriptions" (secguide 262 L6063-6066) and Enhanced Transaction Security "is included in Real-Time Event Monitoring" (secguide 262 L5920). Legacy Transaction Security is "a retired feature in all Salesforce orgs" as of Summer '20 (api_meta 264 L138821-138822), so there is no smaller non-RTEM policy tier to fall back on; without RTEM the "continuous verification" leg has no enforcement layer. UNVERIFIED (2026-10-20): that the Event Monitoring Analytics App is part of the same licence is not in the corpus.
- Inventory the **current posture**. Most orgs already have MFA, an SSO IdP, and some session-timeout configuration. Zero trust adds *layers*; it does not replace what exists. Write down what is there before deciding what to add.
- Identify the **high-assurance perimeter**. Which objects, fields, or operations should require fresh, strong authentication? Examples: viewing customer SSN/PII, exporting reports, running anonymous Apex, modifying Permission Set Groups, deleting records in regulated objects. The high-assurance list shapes the Transaction Security Policy and Login Flow design.
- Note the **device-trust source of truth**. Salesforce alone cannot prove device compliance. Mobile Security covers Salesforce mobile (Enhanced Mobile Security events are published by the Mobile Security SDK, platform_events 264 L24528-24535, L24681-24684); for desktop, the source of truth is the IdP (Azure AD Conditional Access, Okta Device Trust, Ping). The IdP must pass a device-state claim through SAML/OIDC, and Salesforce must consume it via Login Flow. UNVERIFIED (2026-10-20): the vendor names, the claim-passing design and "Salesforce alone cannot prove device compliance" are architecture judgement, not corpus facts.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is Shield or the Event Monitoring add-on licensed? | Gotcha 1: Transaction Security policies need it (secguide 262 L6063-6066) | Whether the continuous-verification leg exists at all |
| Which events must be enforced, and are they valid policy `eventName` values? | Gotcha 1: `IdentityVerificationEvent` and `MobileEmailEvent` are not (api_meta 264 L138737-138798) | A TSP event matrix with detect-only rows marked |
| Which action does each event allow? | Gotcha 1: anomaly, credential stuffing and session hijacking policies are Notifications only (secguide 262 L6144, L6194, L6470, L6492) | An action per event that the platform will accept |
| Does the user work in Lightning, where MFA actions become Block? | Example 1: MFA is not supported for list view and report events in Lightning and is upgraded to Block (api_meta 264 L138715-138717) | A realistic expectation of what users will see |
| Where does device state come from, and is it passed to a Login Flow? | Gotcha 3 and 5: Login Flow runs at login; desktop trust is an IdP concern | A named IdP claim and owner |
| Do Profiles still hold Modify All Data or View All Data? | Gotcha 4 and Pattern D: muting works through permission set groups; the Profile limit is UNVERIFIED | A Profile inventory and a muting test in a sandbox |
| Who reviews policy firings and JIT grants each quarter? | Gotcha 7: JIT grants need a scheduled revoke | A named owner and calendar slot |

A proper configuration adds an event-by-action matrix the platform accepts, a tested Lightning behaviour for each MFA action, and a revocation owner for every temporary grant, instead of a diagram of controls that cannot all be enforced.

---

## Core Concepts

### The four zero-trust legs in Salesforce

Map each NIST zero-trust principle to a Salesforce control set.

1. **Verify explicitly (every transaction, not just every login).**
   - High-Assurance Sessions: a session "level" that step-up MFA produces. Grounded in the corpus: a connected app can apply the High Assurance level with `policyAction` `RaiseSessionLevel` or `Block` and `sessionLevel` `HIGH_ASSURANCE` (api_meta 264 L37959-37970, L38135-38136), an external client app uses `requiredSessionLevel` (api_meta 264 L67866-67871), a profile requires it with `ProfileSessionSetting` `requiredSessionLevel` `HIGH_ASSURANCE` (api_meta 264 L101471, L101529; MFA meets HIGH_ASSURANCE, L101498-101499), and policy conditions can test `Session Level` (secguide 262 L5981, L6005). UNVERIFIED (2026-10-20): a Permission Set Group session-level setting, and everything in this skill that depends on it (Pattern A, Gotcha 2, Examples 1 and 2), is Help-level and not in the corpus. A PSG can require an active session (`hasActivationRequired`, api_meta 264 L98032-98034; `SessionPermSetActivation`, object_reference 264 L10752-10754), which is the documented session-bound grant.
   - Login Flows: "After Salesforce authenticates a user, the login flow directs the user through a process such as enforcing strong authentication or collecting user information" before they reach the org (secguide 262 L366-370, L447-450); the flow can log the user out if unsuccessful. Checking an IdP device-state claim in it is UNVERIFIED (2026-10-20): a design choice, not a documented capability.
   - Connected App OAuth Policies: `ipRelaxation` and `refreshTokenPolicy` on the connected app (api_meta 264 L37789, L37818).
2. **Least privilege (no standing high access).**
   - Permission Set Groups + Muting Permission Sets: assign default permissions via groups and mute selected permissions for users in the group ("use muting permission sets in permission set groups to mute selected permissions", secguide 262 L857-859; `MutingPermissionSet` is "used in conjunction with PermissionSetGroup", api_meta 264 L92410-92411). Time-boxing grants via Just-in-Time PSG assignment is a design pattern, UNVERIFIED (2026-10-20): not described in the corpus.
   - Profile minimization: Profiles hold only the truly-static permissions; everything dynamic moves to PSGs.
3. **Assume breach (continuous verification + audit).**
   - Real-Time Event Monitoring (RTEM): subscribe to `LoginEvent`, `ApiAnomalyEvent`, `SessionHijackingEvent`, `CredentialStuffingEvent`, `ReportEvent`, etc., to enforce real-time policy. (For a policy, the same events are named `ApiAnomalyEventStore`, `SessionHijackingEventStore`, `CredentialStuffingEventStore`, with `ReportEvent` unchanged.)
   - Transaction Security Policies (TSPs): "The actions are Block, Multi-Factor Authentication, and Notifications" (secguide 262 L5218-5220). **Critical gotcha: not every RTEM event type supports TSP enforcement.** the `eventName` values a policy can monitor are AdminSetupEvent, ApiAnomalyEventStore, ApiEvent, BulkApiResultEventStore, CredentialStuffingEventStore, FileEventStore, GuestUserAnomalyEventStore, ListViewEvent, LoginAnomalyEventStore, LoginAsEvent, LoginEvent, PermissionSetEventStore, ReportAnomalyEventStore, ReportEvent, SessionHijackingEventStore and UniversalAnomalyEventStore (api_meta 264 L138737-138798). `IdentityVerificationEvent` and `MobileEmailEvent` are not in that list; `IdentityVerificationEvent` is a big object that supports only `describeSObjects()` and `query()` (platform_events 264 L20250-20256), and `MobileEmailEvent` is published by the Mobile Security SDK (platform_events 264 L24528-24535). The events `LogoutEvent`, `UriEvent`, `LightningUriEvent`, `IdentityProviderEventStore` and the other `Mobile*` events are absent from the list too. **Per event the actions differ:** `ApiAnomalyEventStore`, `CredentialStuffingEventStore`, `ReportAnomalyEventStore` and `SessionHijackingEventStore` policies allow Notifications only (secguide 262 L6144, L6194, L6470, L6492); `ApiEvent`, `BulkApiResultEventStore` and `FileEventStore` allow Block and Notifications, not MFA (secguide 262 L5943, L5953, L5969). `endSession` and `freezeUser` are Legacy Transaction Security only, a retired feature (api_meta 264 L138877-138880); an earlier version of this skill listed "end session" as a current action. Confirm against the current Enhanced Transaction Security docs before relying on policy enforcement.
   - Event Monitoring (file-based): log files for forensics and SIEM ingestion (`EventLogFile`, object_reference 264 L113207). UNVERIFIED (2026-10-20): the hourly / daily cadence is not in the corpus.
4. **Device & network awareness.**
   - Mobile Security (Enhanced Mobile Security for the Salesforce mobile app; policy-enforcement events `MobileEnforcedPolicyEvent` and others, platform_events 264 L24681-24684). UNVERIFIED (2026-10-20): jailbreak detection, app integrity and geolocation policy are not named in the corpus.
   - Login IP Ranges + IP Relaxation: still useful as a coarse filter; do not let "we have IP ranges" become the whole pattern.
   - IdP-side device-state claim → Login Flow consumer: the desktop counterpart to Mobile Security.

### What Salesforce does NOT cover natively

UNVERIFIED (2026-10-20) (all three bullets): negative claims; the corpus never mentions CAEP (grep of both directories finds no hit), so "not natively consumed" is an architecture judgement to confirm with Salesforce.
- **CAEP (Continuous Access Evaluation Profile)**. The IETF / Microsoft standard for cross-vendor continuous risk signals is not natively consumed by Salesforce session policy. Risk signals must currently arrive via Login Flow (at session start) or RTEM (at event time), not in-flight.
- **Third-party device-trust signal in-session.** Once a session is open, Salesforce will not poll the IdP for ongoing device compliance. The Login Flow checks at session start; an RTEM event at event time is the next opportunity.
- **A unified policy language.** Each control (Profile session settings, PSG, Login Flow Apex, TSP, Mobile Security) configures separately. The architect's job is to keep the layers aligned.

### The composition rule

A defensible zero-trust posture in Salesforce composes **at least one
control from each of the four legs above** with explicit traceability
between them. Single-leg postures (MFA only, IP allowlist only, Shield
only) all fail the audit on the same line: "show me the continuous
verification".

---

## Common Patterns

### Pattern A — High-assurance perimeter

**When to use:** Some operations (Modify All Data, exporting reports
with PII, running anonymous Apex) should require fresh strong auth even
inside an authenticated session.

**How it works (UNVERIFIED (2026-10-20): the PSG-level session setting is Help-level, see Core Concepts leg 1; the grounded levers are the connected-app `sessionLevel` and a PSG with `hasActivationRequired`):** Configure session settings on the **Permission Set
Group** that grants the high-blast-radius permissions to require
**High Assurance** session level. Users hit a step-up MFA when they
exercise the permission, regardless of how long ago they logged in.

**Why not the alternative:** Setting session level at the Profile level
forces step-up too aggressively. Setting it on individual Permission
Sets fragments policy. The PSG layer is where high-blast-radius rights
already sit; co-locate the session policy with the rights.

### Pattern B — Conditional access via Login Flow

**When to use:** The IdP holds risk signal (device compliance, IP
reputation, impossible-travel) that Salesforce should refuse to admit
into a session.

**How it works:** Configure SAML/OIDC to pass the IdP's risk claim as a
SAML attribute or OIDC claim. The Login Flow (built with Flow Builder or Visualforce, secguide 262 L453-454; `Auth.SessionManagement` is an Apex class, not a login-flow type) reads the attribute and either
admits, denies, requires step-up, or routes to a remediation page.

**Why not the alternative:** "We have MFA on the IdP" is not enough —
the IdP can grant a session even when its own conditional access raised
a risk flag, because Salesforce never saw the flag. Force the signal
through Login Flow.

### Pattern C — Continuous verification via RTEM + TSP

**When to use:** Detect and act on anomalous behavior inside an
authenticated session: report exfiltration, anomalous API access,
session-token theft, mass record export.

**How it works:** Enable RTEM event types relevant to the org. Build
**Transaction Security Policies** that subscribe to those events and
fire actions (block, require MFA, notify; end session is legacy-only, api_meta 264 L138877-138880). Anomaly, credential stuffing and session hijacking events allow notify only (secguide 262 L6144, L6194, L6470, L6492), so for those the TSP is an alert, not a gate. For event types
that do NOT support TSP (`IdentityVerificationEvent`,
`MobileEmailEvent`), subscribe via Apex / Flow on the underlying
PlatformEvent and take action manually — but recognize that TSP's
synchronous-block capability is not available there.

**Why not the alternative:** File-based Event Monitoring catches the
event 6+ hours later (UNVERIFIED (2026-10-20): the delay figure is not in the corpus) when forensics matters but exfiltration has
already happened. RTEM + TSP is the in-flight enforcement layer.

### Pattern D — Default-deny via PSG + muting

**When to use:** The Profile + Permission Set sprawl of a long-lived
org has produced "everyone has Modify All Data" through accumulated
grants. The audit asks for least-privilege.

**How it works:** Create a baseline PSG that grants common rights;
create Muting Permission Sets that explicitly remove Modify All Data,
View All, anonymous-Apex, and similar high-blast permissions for users
who do not need them. Assign Muting PSs to the baseline PSG.
Time-box exception grants via JIT PSG assignment (Apex / Flow / external
provisioning).

**Why not the alternative:** Profiles cannot mute permissions (UNVERIFIED (2026-10-20): not stated in the corpus; muting is documented only for permission set groups). Trying
to least-privilege via Profile rewriting is multi-quarter work that
breaks every adjacent integration. Muting at the PSG layer is reversible
and does not touch Profiles.

---

## Decision Guidance

| Need | Recommended layer | Why |
|---|---|---|
| Step-up auth for sensitive operation | High-Assurance Session on the right PSG | Co-located with rights |
| Risk-aware session admission | Login Flow consuming IdP risk claim | The only synchronous insertion point |
| Block / step-up / notify in-session | RTEM + Transaction Security Policy | The only synchronous-block layer for events |
| TSP-unsupported RTEM events (IdentityVerificationEvent, MobileEmailEvent) | Apex/Flow subscriber + manual action | TSP is not available; treat as detect-and-respond |
| Forensics / SIEM | File-based Event Monitoring + RTEM as platform events | Volume + retention; SIEM is the system of record |
| Salesforce mobile device trust | Mobile Security policies | The only Salesforce-native MDM signal |
| Desktop device trust | IdP Conditional Access → claim → Login Flow | Salesforce has no desktop MDM |
| Default-deny least privilege | PSG + Muting Permission Sets + JIT grant | Profiles cannot mute |
| Cross-vendor continuous risk (CAEP) | Not natively supported — design around it | Architect-level limitation |

---

## Recommended Workflow

1. **Inventory current state.** Document MFA, SSO, session timeouts, current Profiles + PSGs, Shield licensing. The zero-trust target is a delta from this, not a greenfield.
2. **Define the high-assurance perimeter.** List the operations and objects that warrant step-up. Translate to PSGs.
3. **Stand up the four legs.** One control from each: High-Assurance Session (verify explicitly), Login Flow with IdP claim (verify explicitly + device awareness), PSG + Muting (least privilege), RTEM + TSP (continuous verification). Document which control covers which principle.
4. **Map the RTEM event types.** Build the matrix of which event types are valid policy `eventName` values (api_meta 264 L138737-138798), the actions each allows, and which require Apex/Flow subscription. Mark `IdentityVerificationEvent` and `MobileEmailEvent` as detect-only explicitly, and anomaly events as notify-only. `scripts/check_zero_trust_salesforce_patterns.py --src-root <source>` checks policy XML for these.
5. **Stage the rollout.** Enforcement gates a real workflow, so flip TSPs from "Notify" to "Require MFA" to "Block" in stages with a 2-week soak each — only on events that allow those actions (the anomaly, credential stuffing and session hijacking stores stay Notify).
6. **Document the residual risk.** CAEP, in-session device-trust polling, and unified policy management are gaps Salesforce does not close natively. Write them in the risk register so the next architect does not assume the pattern is more comprehensive than it is.
7. **Schedule the review cadence.** Zero trust is not a one-time stand-up. Plan a quarterly review of TSP findings, muted-permission exceptions, and Login Flow remediation rates.

---

## Review Checklist

- [ ] All four legs have at least one control assigned, with explicit traceability to the zero-trust principle.
- [ ] High-Assurance Session is set on the PSGs holding high-blast-radius permissions, not on Profiles (UNVERIFIED (2026-10-20): the PSG-level setting is Help-level; the Profile-level one is `ProfileSessionSetting`, api_meta 264 L101471).
- [ ] Login Flow consumes at least one IdP risk claim (device compliance, MFA strength, IP risk) and acts on it.
- [ ] RTEM is enabled for the required event types and TSPs are configured for the events that support enforcement.
- [ ] `IdentityVerificationEvent` and `MobileEmailEvent` are recognized as **detect-only** in the design — no TSP relies on them.
- [ ] PSG + Muting are used; Profile rewrites are not the least-privilege strategy.
- [ ] Enhanced Mobile Security policies cover the Salesforce mobile app (platform_events 264 L24681-24684; UNVERIFIED (2026-10-20): jailbreak / app integrity / geolocation are not named in the corpus).
- [ ] Risk register lists CAEP and in-session device-trust polling as known gaps.
- [ ] TSP rollout is phased (Notify → Require MFA → Block, only for events whose policy allows that action) with soak intervals.
- [ ] Quarterly review cadence is on someone's calendar.

---

## Salesforce-Specific Gotchas

1. **Not every RTEM event type supports Transaction Security Policy enforcement.** `IdentityVerificationEvent` and `MobileEmailEvent` are not valid policy `eventName` values (api_meta 264 L138737-138798) — a TSP cannot monitor them at all, let alone block or require MFA. Even for valid events the allowed actions differ (notify only for the anomaly, credential stuffing and session hijacking stores). Confirm the current support matrix in the Enhanced Transaction Security Policy docs every release; the list changes.
2. **High-Assurance Session set on a Profile is too aggressive** (the Profile lever is `ProfileSessionSetting` `requiredSessionLevel`, api_meta 264 L101471; UNVERIFIED (2026-10-20): the PSG-level setting and the every-page step-up behaviour are Help-level, not in the corpus). It forces step-up on routine operations because the Profile-level setting applies to every page. Set it on the PSG that holds the high-blast permission instead.
3. **Login Flow runs once, at session start.** It cannot re-evaluate IdP risk mid-session. For continuous verification you need RTEM + TSP, not Login Flow. Treating Login Flow as the whole "device trust" answer is the most common architecture mistake.
4. **Muting Permission Sets do not remove permissions granted by Profile** (UNVERIFIED (2026-10-20): the corpus describes muting as aggregating the permissions granted by the permission set and those muted by the muting set, object_reference 264 L138485-138488, and says nothing about Profiles). They only mute permissions granted via Permission Sets. If "Modify All Data" lives on the Profile, muting it from a PSG does not strip it. Move the right out of the Profile first, then mute.
5. **Mobile Security policies do not apply to the desktop browser** (UNVERIFIED (2026-10-20): Help-level; the corpus describes Enhanced Mobile Security only for the Salesforce mobile app). Teams that read "Salesforce Mobile Security" assume it covers all Salesforce access. It only covers the Salesforce mobile app. Desktop device trust is an IdP problem.
6. **CAEP is not natively consumed** (UNVERIFIED (2026-10-20): CAEP appears nowhere in the corpus). Microsoft's Continuous Access Evaluation works between Azure AD and M365 but not between Azure AD and Salesforce. If the IdP revokes a session for risk, Salesforce does not know until the next Login Flow firing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Layered control map | Which Salesforce control covers each of the four zero-trust legs, with traceability matrix |
| RTEM event matrix | Event type × TSP-supported? × current org coverage; explicit `IdentityVerificationEvent` and `MobileEmailEvent` annotation |
| Phased rollout plan | Quarter-by-quarter sequencing of new TSPs, muting PSs, Login Flow updates |
| Residual risk register | CAEP gap, in-session device-trust gap, unified-policy gap, with mitigation owners |

---

## Related Skills

- `security/transaction-security-policies` — implementation skill for TSP rules.
- `security/event-monitoring` — implementation skill for the file-based + RTEM stream.
- `security/session-management-and-timeout` — High-Assurance Session mechanics.
- `security/login-forensics` — log + Login Forensics review process.
- `security/mfa-enforcement-strategy` — MFA rollout (a leg of, not all of, zero trust).
- `admin/permission-set-architecture` — PSG + Muting design that this pattern relies on.
- `security/ip-relaxation-and-restriction` — coarse-grained network filter, one input to Login Flow.
- `architect/ai-governance-architecture` — sibling architect-tier composition skill.

See also `standards/decision-trees/sharing-selection.md` for least-privilege at the data-access layer (sharing rules, OWD), which complements least-privilege at the permission layer.
