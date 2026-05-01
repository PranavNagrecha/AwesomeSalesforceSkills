# Zero-Trust Salesforce — Work Template

Use this template when designing or auditing a zero-trust posture for
a Salesforce org.

## Scope

**Skill:** `zero-trust-salesforce-patterns`

**Engagement:** (one line — what triggered this work)

## Current State Inventory

- [ ] MFA: ☐ off  ☐ on, partial  ☐ on, universal
- [ ] SSO: ☐ none  ☐ Salesforce-as-IdP  ☐ external IdP (name): _______
- [ ] Session timeout: _______ hours; HA-required for any Profile? (list)
- [ ] Shield (RTEM + Event Monitoring) licensed? ☐ yes ☐ no
- [ ] Mobile Security policies in place? ☐ yes ☐ no
- [ ] Number of Profiles with `Modify All Data` = _______ (target: 0–2)
- [ ] PSG / Muting PS in active use? ☐ yes ☐ no
- [ ] Login Flow active? ☐ yes ☐ no — what does it do?

## High-Assurance Perimeter

List the operations/objects that should require step-up MFA at access time:

| Operation / Object | High-blast permission | Owning PSG |
|---|---|---|
| | | |

## Four-Leg Coverage

| Leg | Salesforce control | Specific config | Owner |
|---|---|---|---|
| Verify explicitly (session start) | Login Flow + IdP claim | | |
| Verify explicitly (operation level) | High-Assurance Session on PSG | | |
| Least privilege | PSG + Muting PS, JIT grants | | |
| Continuous verification | RTEM + TSP | | |
| Device awareness | Mobile Security + IdP device-state claim | | |

If any row is empty, the posture is incomplete — every leg needs a
control.

## RTEM Event-Type Matrix

For each enabled event, mark whether TSP enforcement applies:

| Event | TSP supported? | Action chosen | Notes |
|---|---|---|---|
| LoginEvent | yes | | |
| ApiAnomalyEvent | yes | | |
| SessionHijackingEvent | yes | | |
| ReportEvent | yes | | |
| BulkApiEvent | yes | | |
| IdentityVerificationEvent | **no — detect only** | (Apex / Flow subscriber) | per gotcha #1 |
| MobileEmailEvent | **no — detect only** | (Apex / Flow subscriber) | per gotcha #1 |

(Re-confirm against the latest Enhanced TSP docs every release.)

## Phased Rollout

| Phase | Window | Change | Soak metric |
|---|---|---|---|
| 1 | wk 0–2 | New TSPs in **Notify** mode | false-positive rate |
| 2 | wk 2–4 | Promote to **Require MFA** | step-up tickets |
| 3 | wk 4–6 | Promote to **Block** | help-desk volume |
| 4 | wk 6+ | Add muting PSs, JIT grants | drift watch |

## Residual Risk Register

| Risk | Mitigation | Owner |
|---|---|---|
| CAEP not consumed → IdP risk-revoke does not propagate | shorter session timeouts, RTEM session-end TSP | |
| In-session device-trust polling not supported | shorter session timeouts | |
| TSP unsupported event types | detect-and-respond via Apex/Flow | |
| Profile minimization is multi-quarter work | parallel workstream | |

## Quarterly Review Cadence

- [ ] Owner assigned: _______
- [ ] Review date set: _______
- [ ] Metrics reviewed: TSP firings, JIT-PSG dwell time, mute exceptions, session-timeout drift

## Notes

(Record deviations from the patterns in SKILL.md and why.)
