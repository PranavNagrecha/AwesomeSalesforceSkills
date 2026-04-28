# Template — LWC Locker → LWS Migration Runbook

Use this template to plan and execute the Locker → LWS cutover for one Salesforce org. Fill in each section as you progress.

---

## 1. Org snapshot

| Field | Value |
|---|---|
| Org name / instance | `<myOrg / NA123>` |
| Edition | `<Enterprise / Unlimited / etc.>` |
| Current state of "Use Lightning Web Security for LWC" | `<on / off>` |
| Current state of "Use Lightning Web Security for Aura" | `<on / off / not yet GA in this instance>` |
| Active release version | `<Spring 'YY>` |
| Number of custom LWC bundles | `<n>` |
| Number of static resources used by LWCs | `<n>` |
| Date of intended production flip | `<YYYY-MM-DD>` |

---

## 2. Component inventory

For every custom LWC bundle, classify into one of three buckets:

| Bundle path | Loads third-party library? | Touches `window` / `document`? | References `SecureElement` / `SecureWindow`? | Classification |
|---|---|---|---|---|
| `force-app/main/default/lwc/myChart` | yes (Chart.js patched fork) | yes (canvas) | no | `manual-test-required` + `needs-shim-removal` |
| `force-app/main/default/lwc/signaturePad` | no | yes | yes (`instanceof SecureElement` guard) | `needs-shim-removal` |
| `force-app/main/default/lwc/recordHeader` | no | no | no | `safe` |
| ... | | | | |

Classification rules:
- **`safe`** — no third-party library, no `window`/`document` reach-around, no Locker-only references.
- **`needs-shim-removal`** — references `SecureElement` / `SecureWindow` / `unwrap()` / `getRawNode()`, OR has a deep-clone-on-input shim into a third-party lib.
- **`manual-test-required`** — loads any third-party library via `loadScript` / `loadStyle`, OR touches `window` / `document` directly. (May also be `needs-shim-removal`.)

---

## 3. Static checker run

Run the checker against every LWC bundle:

```bash
python3 skills/lwc/lwc-locker-to-lws-migration/scripts/check_lwc_locker_to_lws_migration.py force-app/main/default/lwc
```

Record findings here. Any P0 must be resolved (or explicitly accepted with a documented reason) before the production flip.

| File | Severity | Finding | Resolution |
|---|---|---|---|
| `lwc/myChart/myChart.js` | P0 | References `getRawNode()` (Locker-only) | Removed in commit `<hash>` |
| `lwc/signaturePad/signaturePad.js` | P0 | `typeof SecureElement !== 'undefined'` guard | Branch deleted |
| ... | | | |

---

## 4. Sandbox enablement plan

| Sandbox | Type | Purpose | Enable LWS on (date) | Owner |
|---|---|---|---|---|
| `<dev1>` | Developer | First contact — early-warning regressions | `<date>` | `<name>` |
| `<qa>` | Partial Copy | Manual exercise + Jest run | `<date>` | `<name>` |
| `<staging>` | Full | Production-shaped final rehearsal | `<date>` | `<name>` |

Production flip happens **only** after `<staging>` has run for at least `<n>` days with no LWS-related regression.

---

## 5. Manual test matrix

For every page that hosts a `manual-test-required` LWC, exercise the third-party-library hot path under LWS in a sandbox:

| Page (App Page / Record Page / Quick Action / Utility Bar) | LWC | Library exercised | Browser | DevTools console clean? | Pass / Fail | Notes |
|---|---|---|---|---|---|---|
| Account record page | `myChart` | Chart.js bar render | Chrome 120 | yes | pass | Tooltip callbacks fire |
| Case record page | `signatureCapture` | signature_pad 4.x | Chrome 120 | yes | pass | |
| Opportunity quick action | `pdfExport` | jsPDF 2.x | Safari 17 | yes | pass | Download initiated |
| ... | | | | | | |

A failed row blocks the production flip. Triage in `<dev1>`, fix, re-run.

---

## 6. Workaround removal diff

List Locker-era workarounds removed during this migration. Each row is one PR / change-set entry:

| File | Removed | Reason |
|---|---|---|
| `lwc/myChart/myChart.js` | `JSON.parse(JSON.stringify(this.chartData))` deep-clone | Was for Locker proxy escape; now strips `tooltip.callbacks.label` functions |
| `lwc/signaturePad/signaturePad.js` | `typeof SecureElement !== 'undefined'` branch | Locker-only probe; dead under LWS |
| `staticresources/chartjs_locker_fork.zip` | Replaced with `staticresources/chartjs.zip` (upstream Chart.js 4.x) | Fork no longer needed |
| `jest.config.js` | `setupFiles: ['jest-canvas-mock']` (if no longer needed) | Originally added because Locker proxy broke canvas tests |
| `jest.config.js` | `setupFilesAfterEach: ['./test-utils/secure-window-stub.js']` | SecureWindow no longer exists |

---

## 7. Production cutover runbook

Pre-flight (T-7 days):
- [ ] All sandboxes green; manual test matrix complete; static checker clean.
- [ ] Comms drafted for end-users explaining "you may be asked to refresh your browser tab on `<date>` at `<time>`."
- [ ] Rollback owner identified and on call.

Cutover (T-0):
- [ ] Verify production has the same workaround-removal diffs deployed as `<staging>` (or that workarounds are deferred to a separate post-flip change — **not both**).
- [ ] Toggle **Setup → Session Settings → Use Lightning Web Security for Lightning web components** to **On**.
- [ ] Save. Confirm metadata diff via `sf project deploy preview` or equivalent for change-tracking.
- [ ] Open one Lightning page as a regular user; confirm DevTools shows real DOM (no `Proxy {}` wrappers in component logs).
- [ ] Send post-flip comms.

Monitor (T+0 to T+48h):
- [ ] Watch the org's `LightningUsage` / `LightningExperienceConfiguration` reports for error spikes.
- [ ] Watch user-support inbox for "page is broken" reports.
- [ ] Have a rollback decision ready by T+24h: stay on LWS or revert to Locker.

Rollback steps (only if needed):
- [ ] Toggle the setting back **off** in production.
- [ ] All users see Locker again on next page load.
- [ ] **Do not** revert workaround-removal commits in the same step — debugging is easier with a stable code baseline.
- [ ] Triage the regression in a sandbox; re-plan the flip.

---

## 8. Post-flip clean-up (separate PRs)

These changes ride **after** the production flip stabilises. Do **not** bundle into the cutover PR.

- [ ] Retire `force:hasRecordId` Aura wrappers that exist only to forward `recordId` to an LWC. Place the LWC directly on the page.
- [ ] Migrate any remaining Locker-era patched library forks to upstream builds.
- [ ] Audit cross-namespace `@api` properties for function-typed values; refactor to event-based or string-based interchange.
- [ ] Remove now-unused Jest mocks (`jest-canvas-mock`, custom SecureWindow stubs) where confirmed unnecessary.
- [ ] Update internal docs / onboarding to reference LWS, not Locker.

---

## 9. Verification

Confirm before considering the migration complete:

- [ ] Production toggle is **On** for "Use Lightning Web Security for Lightning web components."
- [ ] Static checker run against `force-app/main/default/lwc` exits 0.
- [ ] Manual test matrix is 100% pass.
- [ ] No `SecureElement` / `SecureWindow` references remain in the LWC source tree.
- [ ] Jest suite green; obsolete mocks removed.
- [ ] Rollback runbook exercised at least once in a sandbox (toggle off → back on) so the team knows the steps cold.
- [ ] Aura LWS toggle state explicitly documented (on / off / not-yet-GA), even if unchanged by this migration.
