# Gotchas — Lightning Experience Transition

Non-obvious Salesforce platform behaviors that cause real production problems during a Classic-to-Lightning rollout.

## Gotcha 1: JavaScript Buttons Fail Silently In LEX

**What happens:** Click a JavaScript button on a record page in Lightning Experience and nothing happens — no error toast, no console error, no progress indicator. The button is still rendered on the page layout (so users see and click it) but the `OnClickJavaScript` is not executed in the LEX runtime.

**When it bites you:** Mid-wave. Users in the new cohort encounter a button they used yesterday, click it, see no result, click again, then eventually switch back to Classic to "make it work." Switch-back rate spikes for that page in `LightningExitByPageMetrics`.

**How to handle:** Audit `WebLink` `linkType = 'javascript'` before any wave that touches the host object. For each button, ship a Quick Action, headless flow, or LWC replacement, then **remove the JavaScript button from the page layout** so users can't click the dead control. The button can still exist as metadata for rollback safety; it just must not be on a layout the wave's users see.

---

## Gotcha 2: Profile-Level LEX Flip Doesn't Reset User Preference

**What happens:** You enable "Lightning Experience User" in a profile and disable Classic UI access. Users in that profile who had previously clicked "Switch to Salesforce Classic" land in Classic on next login anyway, hit a "your profile doesn't allow Classic" message in some cases, or — depending on the org config — silently work in Classic with the per-user preference still dominant.

**When it bites you:** Adoption dashboards lie. `LightningUsageByAppTypeMetrics` shows the rollout completed; spot checks show users in Classic.

**How to handle:** Use the **Lightning Experience Hides Classic Switcher** permission set (or its equivalent) for the cohort. It overrides the per-user preference. Alternatively, run a one-time User-record DML to set `UserPreferencesLightningExperiencePreferred = true` for the cohort; the permission-set approach is auditable and reversible.

---

## Gotcha 3: Console Apps Don't Auto-Translate

**What happens:** A Classic Service Console with primary tabs and subtabs is migrated to LEX. The Lightning Console app is enabled but the layout is empty — no console-specific behavior, no utility bar, no pinned tabs. Service reps lose case-handling productivity overnight.

**When it bites you:** Service teams that depend on console muscle memory. The Readiness Check flags Console-based assets but does not migrate them. The team assumes "Lightning Console" is just "Console with new chrome" — it is not. It is a separately configured app with its own metadata.

**How to handle:** Treat Console rebuild as its own asset-triage track. For each Classic Console app, define a Lightning Console app with primary tabs (record-driven), subtabs (record-relationship-driven), utility bar items (Open CTI, Macros, History), and a CSS-tweaked compact layout. Pilot with 2–3 reps before rolling to the full team.

---

## Gotcha 4: AppExchange "Lightning Ready" Is Not "Lightning-Equivalent"

**What happens:** A managed package's listing shows "Lightning Ready" but in production the LEX experience is degraded — a Visualforce-based settings page, a Classic-only related list, or a feature that's only available in Classic.

**When it bites you:** Users who relied on the package's Classic-specific feature complain mid-wave. The vendor's "Lightning Ready" badge means "renders without breaking in LEX," not "every feature is available in LEX."

**How to handle:** During the package-compatibility audit, validate **the actual workflows your users execute**, not the marketing badge. Open the package in a sandbox with LEX enabled; walk every screen the cohort uses. Document any feature gaps and either (a) escalate to the vendor for a roadmap commitment, (b) replace the package, or (c) carve out the gap-affected workflow into Classic-only profiles for the duration.

---

## Gotcha 5: VF Pages Render Inside An iframe With Different Domain

**What happens:** A Visualforce page that uses `window.parent`, manipulates the URL hash, or relies on cross-origin DOM access works in Classic but breaks in LEX. The page itself loads, but a JS-driven button on it does nothing, or the page can't read a query string set by the parent.

**When it bites you:** Power users with complex VF pages (record-flow wizards, custom dashboards). The Readiness Check flags the VF page as "review needed" but doesn't tell you which JS calls are broken; testing finds it post-cutover.

**How to handle:** For each VF page in the Replace or Rebuild bucket, test inside LEX **before** the wave that exposes it. Specifically test (a) `window.parent` access — blocked by same-origin policy, (b) URL hash manipulation, and (c) cross-frame messaging. The fix is usually `parent.postMessage` or moving logic into an LWC; either is a Rebuild, not a Retain.

---

## Gotcha 6: The Readiness Check Doesn't Find New Assets Added Mid-Program

**What happens:** A 6-month transition program runs. Wave 2 surfaces a "wait, this VF page exists?" — an asset the Readiness Check at program start missed because someone shipped it in week 8.

**When it bites you:** Active orgs ship new metadata weekly. A baseline-only Readiness Check captures month-zero state.

**How to handle:** Re-run the Readiness Check before each wave, not just at the start. Diff the report against the baseline; the new flags are by definition assets shipped during the program that no one queued for triage. Hold the wave if the new assets affect the cohort's apps.

---

## Gotcha 7: Some Standard Salesforce Features Behave Differently In LEX

**What happens:** Standard List Views, related-list configurations, and report formatters can render slightly differently in LEX vs Classic — pixel-level layout shifts, different default sort, related-list row counts capped at 6 by default in LEX whereas Classic showed 5 with "View All."

**When it bites you:** Power users who memorized "the third row" of a related list lose their muscle memory. Reports embedded in dashboards may show different default chart types.

**How to handle:** Don't promise "pixel-identical" — that's not what Lightning is for. Communicate the expected delta in training materials. Tune the LEX-side: set "Related Records" component to show 10 rows; verify list-view default sort matches Classic; configure dashboards explicitly rather than relying on defaults.
