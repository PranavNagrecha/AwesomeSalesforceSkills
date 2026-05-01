---
name: zero-trust-salesforce-patterns
description: "Architecture pattern for assembling a zero-trust posture in Salesforce — there is no single zero-trust toggle. The pattern composes High-Assurance Sessions, Real-Time Event Monitoring (RTEM) Transaction Security Policies, Login Flows for conditional access, Event Monitoring for continuous verification, Mobile Security for device compliance, and a Permission Set Group strategy that defaults-deny. Covers the gotcha that not all RTEM event types support TSP enforcement (IdentityVerificationEvent and MobileEmailEvent do NOT). NOT for MFA-only rollouts (see security/mfa-enforcement-strategy), NOT for the LLM-side Einstein Trust Layer (different concept), NOT for Apex CRUD/FLS enforcement patterns (see apex/apex-stripinaccessible-and-fls-enforcement)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-01
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

- Confirm **licensing**. Real-Time Event Monitoring (RTEM) and the broader Event Monitoring Analytics App are part of Salesforce Shield (or an Event Monitoring add-on). Without RTEM, Transaction Security Policies are limited to a smaller event set and the "continuous verification" leg of zero trust is much thinner.
- Inventory the **current posture**. Most orgs already have MFA, an SSO IdP, and some session-timeout configuration. Zero trust adds *layers*; it does not replace what exists. Write down what is there before deciding what to add.
- Identify the **high-assurance perimeter**. Which objects, fields, or operations should require fresh, strong authentication? Examples: viewing customer SSN/PII, exporting reports, running anonymous Apex, modifying Permission Set Groups, deleting records in regulated objects. The high-assurance list shapes the Transaction Security Policy and Login Flow design.
- Note the **device-trust source of truth**. Salesforce alone cannot prove device compliance. Mobile Security covers Salesforce mobile; for desktop, the source of truth is the IdP (Azure AD Conditional Access, Okta Device Trust, Ping). The IdP must pass a device-state claim through SAML/OIDC, and Salesforce must consume it via Login Flow.

---

## Core Concepts

### The four zero-trust legs in Salesforce

Map each NIST zero-trust principle to a Salesforce control set.

1. **Verify explicitly (every transaction, not just every login).**
   - High-Assurance Sessions: a session "level" that step-up MFA produces. Set Profile or Permission Set Session Settings to require High Assurance for sensitive operations. The user is forced to re-authenticate when accessing them.
   - Login Flows: post-authentication interstitial that can require MFA, accept additional consent, or check IdP claims (e.g., device-state claim from Azure AD CA) before granting the session.
   - Connected App OAuth Policies: per-app refresh-token revocation, session policies, and IP relaxation overrides.
2. **Least privilege (no standing high access).**
   - Permission Set Groups + Muting Permission Sets: assign default permissions via groups, mute high-blast-radius permissions (Modify All Data, View All) by default, and time-box grants via Just-in-Time PSG assignment.
   - Profile minimization: Profiles hold only the truly-static permissions; everything dynamic moves to PSGs.
3. **Assume breach (continuous verification + audit).**
   - Real-Time Event Monitoring (RTEM): subscribe to `LoginEvent`, `ApiAnomalyEvent`, `SessionHijackingEvent`, `CredentialStuffingEventStore`, `ReportEvent`, etc., to enforce real-time policy.
   - Transaction Security Policies (TSPs): block / require MFA / notify on RTEM events. **Critical gotcha: not every RTEM event type supports TSP enforcement.** `IdentityVerificationEvent` and `MobileEmailEvent` are read-only event types — TSPs do NOT apply. Confirm against the latest Enhanced TSP docs before relying on policy enforcement.
   - Event Monitoring (file-based): hourly / daily log files for forensics and SIEM ingestion.
4. **Device & network awareness.**
   - Mobile Security (Salesforce-supplied MDM signals for the Salesforce mobile app): jailbreak detection, app integrity, geolocation policy.
   - Login IP Ranges + IP Relaxation: still useful as a coarse filter; do not let "we have IP ranges" become the whole pattern.
   - IdP-side device-state claim → Login Flow consumer: the desktop counterpart to Mobile Security.

### What Salesforce does NOT cover natively

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

**How it works:** Configure session settings on the **Permission Set
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
SAML attribute or OIDC claim. The Login Flow (an Apex `Auth.SessionManagement`
flow or a Flow declarative login flow) reads the attribute and either
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
fire actions (block, require MFA, notify, end session). For event types
that do NOT support TSP (`IdentityVerificationEvent`,
`MobileEmailEvent`), subscribe via Apex / Flow on the underlying
PlatformEvent and take action manually — but recognize that TSP's
synchronous-block capability is not available there.

**Why not the alternative:** File-based Event Monitoring catches the
event 6+ hours later when forensics matters but exfiltration has
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

**Why not the alternative:** Profiles cannot mute permissions. Trying
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
4. **Map the RTEM event types.** Build the matrix of which event types support TSP enforcement vs which require Apex/Flow subscription. Mark `IdentityVerificationEvent` and `MobileEmailEvent` as detect-only explicitly.
5. **Stage the rollout.** Enforcement gates a real workflow, so flip TSPs from "Notify" to "Require MFA" to "Block" in stages with a 2-week soak each.
6. **Document the residual risk.** CAEP, in-session device-trust polling, and unified policy management are gaps Salesforce does not close natively. Write them in the risk register so the next architect does not assume the pattern is more comprehensive than it is.
7. **Schedule the review cadence.** Zero trust is not a one-time stand-up. Plan a quarterly review of TSP findings, muted-permission exceptions, and Login Flow remediation rates.

---

## Review Checklist

- [ ] All four legs have at least one control assigned, with explicit traceability to the zero-trust principle.
- [ ] High-Assurance Session is set on the PSGs holding high-blast-radius permissions, not on Profiles.
- [ ] Login Flow consumes at least one IdP risk claim (device compliance, MFA strength, IP risk) and acts on it.
- [ ] RTEM is enabled for the required event types and TSPs are configured for the events that support enforcement.
- [ ] `IdentityVerificationEvent` and `MobileEmailEvent` are recognized as **detect-only** in the design — no TSP relies on them.
- [ ] PSG + Muting are used; Profile rewrites are not the least-privilege strategy.
- [ ] Mobile Security policies cover the Salesforce mobile app (jailbreak / app integrity / geolocation).
- [ ] Risk register lists CAEP and in-session device-trust polling as known gaps.
- [ ] TSP rollout is phased (Notify → Require MFA → Block) with soak intervals.
- [ ] Quarterly review cadence is on someone's calendar.

---

## Salesforce-Specific Gotchas

1. **Not every RTEM event type supports Transaction Security Policy enforcement.** `IdentityVerificationEvent` and `MobileEmailEvent` are read-only / notification-only event types — TSPs cannot block or require MFA on them. Confirm the current support matrix in the Enhanced Transaction Security Policy docs every release; the list changes.
2. **High-Assurance Session set on a Profile is too aggressive.** It forces step-up on routine operations because the Profile-level setting applies to every page. Set it on the PSG that holds the high-blast permission instead.
3. **Login Flow runs once, at session start.** It cannot re-evaluate IdP risk mid-session. For continuous verification you need RTEM + TSP, not Login Flow. Treating Login Flow as the whole "device trust" answer is the most common architecture mistake.
4. **Muting Permission Sets do not remove permissions granted by Profile.** They only mute permissions granted via Permission Sets. If "Modify All Data" lives on the Profile, muting it from a PSG does not strip it. Move the right out of the Profile first, then mute.
5. **Mobile Security policies do not apply to the desktop browser.** Teams that read "Salesforce Mobile Security" assume it covers all Salesforce access. It only covers the Salesforce mobile app. Desktop device trust is an IdP problem.
6. **CAEP is not natively consumed.** Microsoft's Continuous Access Evaluation works between Azure AD and M365 but not between Azure AD and Salesforce. If the IdP revokes a session for risk, Salesforce does not know until the next Login Flow firing.

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
- `security/permission-set-architecture` — PSG + Muting design that this pattern relies on.
- `security/ip-relaxation-and-restriction` — coarse-grained network filter, one input to Login Flow.
- `architect/ai-governance-architecture` — sibling architect-tier composition skill.

See also `standards/decision-trees/sharing-selection.md` for least-privilege at the data-access layer (sharing rules, OWD), which complements least-privilege at the permission layer.
