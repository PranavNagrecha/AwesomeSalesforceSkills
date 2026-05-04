# LLM Anti-Patterns — Lightning Experience Transition

Common mistakes AI coding assistants make when generating or advising on Lightning Experience Transition.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending The Org-Wide Switch As The First Step

**What the LLM generates:** "To migrate to Lightning Experience, navigate to Setup → Lightning Experience Transition Assistant and turn Lightning Experience on as the only experience for the org."

**Why it happens:** The model knows the org-wide setting exists and treats "enable Lightning" as a one-step action because most documentation describes the *capability*, not the *program*. Training data overweights the toggle and underweights the wave-based rollout playbook.

**Correct pattern:**

```
1. Run the Readiness Check first. Treat its output as the asset baseline.
2. Build the asset-triage matrix (Replace/Rebuild/Retain/Retire).
3. Roll out via permission set ("Lightning Experience User") to a pilot cohort.
4. Validate with telemetry (LightningExitByPageMetrics) for 7+ days.
5. Promote to subsequent waves; only flip the org-wide setting after sustained adoption.
```

**Detection hint:** If the recommendation says "turn LEX on" or "enable LEX org-wide" without first mentioning the Readiness Check, asset triage, or a wave/cohort plan, the answer is wrong.

---

## Anti-Pattern 2: Treating "Lightning Ready" As Production-Equivalent

**What the LLM generates:** "All your installed packages are Lightning Ready, so they will work the same in LEX as they did in Classic."

**Why it happens:** The model takes the AppExchange marketing label literally. The label means "renders in LEX without breaking," not "all features are parity with the Classic experience." The model has no signal for the actual feature delta.

**Correct pattern:**

```
For each managed package:
  - Confirm "Lightning Ready" status from the AppExchange listing.
  - Open the package in a LEX sandbox.
  - Walk every screen the cohort uses; document feature gaps.
  - For each gap, decide: vendor escalation, replace package, or carve-out.
```

**Detection hint:** If the answer says "Lightning Ready means the package works in LEX," it's collapsing a binary label into a multi-dimensional reality. Push back and ask which features the cohort actually uses.

---

## Anti-Pattern 3: Conflating User Preference With Profile Setting

**What the LLM generates:** "To force users into LEX, remove the 'Lightning Experience User' permission from the Classic profile and re-add it to the LEX profile."

**Why it happens:** Profile-permission manipulation is a common LLM-trained pattern for permission rollouts. The model doesn't know about `UserPreferencesLightningExperiencePreferred` — a per-user boolean that overrides profile-level rollout.

**Correct pattern:**

```
1. Assign the "Lightning Experience Hides Classic Switcher" permission set to the cohort.
   This both forces LEX and removes the switch-back link from the user menu.
2. Optionally run a one-time User-record DML to reset
   UserPreferencesLightningExperiencePreferred = true for any user with
   a sticky Classic preference.
3. Verify on next-day login: query User WHERE
   UserPreferencesLightningExperiencePreferred = false should return 0
   for the cohort.
```

**Detection hint:** If the answer talks about profile-level "Lightning Experience User" without mentioning the per-user preference flag or the "Hides Classic Switcher" permission set, the rollout will fail in production.

---

## Anti-Pattern 4: Auto-Migrating JavaScript Buttons To Quick Actions Without Re-Architecture

**What the LLM generates:** Generates an Apex `@InvocableMethod` and a Quick Action that runs the same JavaScript code path. "I converted your JavaScript button — here is the equivalent Quick Action."

**Why it happens:** The model treats the migration as a syntactic transformation: JS code → Apex action. It doesn't understand that JavaScript buttons often used `sforce.connection.query` synchronously inline with DOM manipulation, which has no Apex/Quick Action equivalent.

**Correct pattern:**

```
For each JavaScript button:
  1. Classify the action: simple field update | navigation | bulk record op | UI-driven multi-step.
  2. simple field update → Quick Action (record-level) with a header field set.
  3. navigation → standard Lightning navigation event in an LWC, or a Web Link.
  4. bulk record op → headless flow with Apex action; do NOT inline DML in the action.
  5. UI-driven multi-step → LWC + Apex action + flow if needed.
DO NOT translate JavaScript → Apex line-for-line. Re-design for Lightning primitives.
```

**Detection hint:** If the migration recipe is "I converted the JS to Apex" and the Apex method has the same control flow as the JS, the LLM did a syntactic transform and missed the design step.

---

## Anti-Pattern 5: Skipping Telemetry / "Just Run The Wave And See"

**What the LLM generates:** "Wave 1 is ready to deploy. Assign the permission set and monitor the help desk for tickets."

**Why it happens:** "Help desk tickets" is the LLM's default proxy for adoption. The model doesn't know about `LightningExitByPageMetrics`, `LightningUsageByAppTypeMetrics`, or `LightningUsageByPageMetrics` — Salesforce-specific objects that surface adoption without waiting for users to call.

**Correct pattern:**

```sql
-- Daily monitor query during a wave
SELECT
  PageType,
  AppType,
  TotalCount,
  ExitsCount,
  (ExitsCount * 100.0 / NULLIF(TotalCount, 0)) AS SwitchBackPct
FROM LightningExitByPageMetrics
WHERE MetricsDate = LAST_N_DAYS:1
ORDER BY SwitchBackPct DESC NULLS LAST
LIMIT 20
```

Pair with a threshold (e.g., switch-back rate < 5% sustained for 7 days) before promoting the next wave.

**Detection hint:** If the answer mentions "monitor the help desk" or "watch for user complaints" without naming `LightningExitByPageMetrics` or `LightningUsageByAppTypeMetrics`, the program lacks objective telemetry.
