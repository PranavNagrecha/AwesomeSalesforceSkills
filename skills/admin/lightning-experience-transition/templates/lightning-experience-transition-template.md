# Lightning Experience Transition — Work Template

Use this template when scoping or running a Classic-to-Lightning transition program. Fill it in collaboratively with the customer's program owner; archive the completed copy in the program folder.

---

## Scope

**Skill:** `lightning-experience-transition`

**Customer / Org:**
**Program owner:**
**Target cutover date:**
**Active Classic users at program start:** _(query: `SELECT COUNT() FROM User WHERE UserPreferencesLightningExperiencePreferred = false AND IsActive = true`)_

---

## Phase 0 — Discover

- [ ] Lightning Experience Transition Assistant Readiness Check has been run
- [ ] Readiness Check PDF archived to: ____________________
- [ ] Asset counts captured (baseline):
  - Visualforce pages: ___
  - JavaScript buttons (`WebLink linkType=javascript`): ___
  - S-Controls: ___
  - Classic email templates: ___
  - Classic Knowledge articles: ___
  - Installed managed packages: ___ (of which not Lightning-Ready: ___)
- [ ] User segmentation captured (by profile / role / business unit)

---

## Phase 1 — Asset Triage Matrix

For every asset surfaced by the Readiness Check, fill in:

| Asset | Type | Last Used | Bucket | Owner | Replacement Skill | Target Wave | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
|  | VF / JSButton / SControl / Knowledge / EmailTemplate / Console / Package |  | Replace / Rebuild / Retain / Retire |  | e.g. `lwc/visualforce-to-lwc-migration` |  |  |

**Triage rules:**
- Bucket = Retire if Last Used > 12 months and not in any active workflow.
- Bucket = Replace when there is a 1:1 Lightning-native counterpart (most JavaScript buttons → Quick Actions).
- Bucket = Rebuild when re-architecture is required (Classic Console layouts, complex VF wizards).
- Bucket = Retain only if asset already renders correctly in LEX (Readiness Check confirms).

---

## Phase 2 — Wave Plan

| Wave | Cohort (count) | Permission Set | In-Scope Triage Items | Telemetry Threshold | Hold/Promote Decision Date |
|---|---|---|---|---|---|
| 0 — Pilot |  | `LEX_W0_Pilot` |  | Switch-back rate < 10%, 0 Sev-1 in 7 days |  |
| 1 |  | `LEX_W1_*` |  | Switch-back rate < 5% |  |
| 2 |  | `LEX_W2_*` |  | Switch-back rate < 5% |  |
| 3 |  | `LEX_W3_*` |  | Switch-back rate < 5% |  |
| Cutover | All users | `LEX_HideClassic` | All assets retired/replaced | LEX adoption > 95% sustained 14 days |  |

**Per-wave gates:**
- [ ] All in-scope triage items shipped to production
- [ ] Permission set deployed and validated
- [ ] Help-desk on standby with macros for top expected questions
- [ ] Rollback plan tested (un-assign permission set; verify user lands in Classic)

---

## Phase 3 — Adoption Telemetry

Daily monitor query during each active wave:

```sql
SELECT
  PageType, AppType, TotalCount, ExitsCount,
  (ExitsCount * 100.0 / NULLIF(TotalCount, 0)) AS SwitchBackPct
FROM LightningExitByPageMetrics
WHERE MetricsDate = LAST_N_DAYS:1
ORDER BY SwitchBackPct DESC NULLS LAST
LIMIT 20
```

- [ ] Daily monitor running for the active wave
- [ ] Threshold-breach alert routed to: ____________________
- [ ] Investigation playbook for high switch-back pages: identify the page, find the offending asset (use this skill's checker), schedule a fix

---

## Phase 4 — Cutover

- [ ] All waves are at telemetry green for 14+ days
- [ ] "Hides Classic Switcher" permission set assigned to all production users
- [ ] User-record DML run (or permission set covers it): `UserPreferencesLightningExperiencePreferred = true` for the cohort
- [ ] Optional: org-wide "Make Lightning Experience the only experience" toggle flipped (one-way)
- [ ] Audit-log evidence captured (LoginHistory + Setup audit trail) for compliance
- [ ] Program artifacts archived to: ____________________

---

## Notes

Record deviations from the standard pattern and why:
