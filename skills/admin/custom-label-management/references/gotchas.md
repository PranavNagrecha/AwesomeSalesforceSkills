# Gotchas — Custom Label Management

Five non-obvious platform behaviors that catch teams building i18n
on top of Custom Labels. These compound (not duplicate) the items in
SKILL.md's Salesforce-Specific Gotchas section — these are the
issues that surface in CI, scratch-org dev, or production weeks
after the initial label rollout.

---

## Gotcha 1: Per-org allocations — 1,000 characters per label value, 5,000 labels per org

**What happens:** Setup rejects any label whose `Value` (or any
language translation) exceeds 1,000 characters with the error
`Value: data value too large` on save. Hit the 5,000-label org
allocation and `New Custom Label` returns
`You've exceeded the maximum number of custom labels for your
organization`. Both ceilings are tenant-wide and include labels
shipped by installed managed packages.

**When it occurs:** Long-form email body content gets pasted into a
label (typical: legal disclaimer, multi-paragraph notification),
sometimes by an admin who pre-rendered HTML into the value. The
5,000-label ceiling bites later — orgs that have run for a decade
or installed several AppExchange packages can be at 3,000+ labels
before the team even starts a new i18n initiative.

**How to avoid:** For values over ~800 characters, split into
suffix-versioned siblings (`Disclaimer_Part1`, `Disclaimer_Part2`)
and concatenate in a helper class, or move the long-form content
into a Custom Metadata Type record with a `LongTextArea` field
(32,768 chars) — see SKILL.md's "Long-text overflow" pattern. For
the 5,000-label ceiling, periodically audit unused labels with the
Metadata Dependency API (`/services/data/vXX.0/tooling/sobjects/MetadataComponentDependency`)
and delete dead entries; track installed-package contribution
separately because you can't delete those.

---

## Gotcha 2: Apex `System.Label.X` is resolved at compile time — label must already exist

**What happens:** A developer adds `System.Label.New_Welcome_Banner`
to an Apex class and pushes the class via Metadata API. The
deployment fails with `Variable does not exist: New_Welcome_Banner`
because the label metadata was not deployed in the same deployment
package (or was deployed after the class). The reverse also fails:
deploying a destructive-changes that removes a referenced label
without first removing the Apex reference causes the dependent
class to compile-fail and the entire org's Apex to revert to its
last-saved state until the missing label is restored.

**When it occurs:** The mismatch surfaces during deployment
ordering errors, package version splits where labels live in one
unlocked package and Apex in another, and during destructive-
changes cleanups. CI pipelines that deploy classes before
`CustomLabels.labels` are particularly vulnerable.

**How to avoid:** Always ship Apex and the labels it references in
the same deployment artifact. In `package.xml` order doesn't fix
this — the entire deployment is validated together, so the labels
must be present in the same payload. For destructive-changes,
remove Apex references first, deploy, then remove the labels in a
separate later deployment. If you use `Label.get('New_Welcome_Banner')`
dynamic access instead, the compiler can't verify existence —
references resolve at runtime to an empty string when missing,
which trades the compile-time safety for silent failure (rarely
worth it).

---

## Gotcha 3: Missing translations fall back silently to the source-language value

**What happens:** A user with `LanguageLocaleKey = es` opens a page
that references `System.Label.Quote_Save_Button`. The label has
French and Japanese translations but not Spanish. The UI shows the
English source-language value (e.g., "Save Quote") with no warning,
no flag in the debug log, no entry in any Setup audit log. Users
see partial translation — buttons in English, page headers in
Spanish — and assume the app is half-broken.

**When it occurs:** Any rollout where new labels ship faster than
the translation vendor returns work, or where a new language is
added late and existing labels were not back-translated. Common
trigger: a sprint adds 15 labels for a new feature and the team
forgets to commission Spanish translations because the existing
feature was already translated.

**How to avoid:** Add a CI check that runs after deployment — query
`CustomLabel` via the Tooling API and join against
`CustomLabelLocalization` per supported language; flag any label
missing a translation in any active language. Fail the build (or
post a Slack alert) so the gap is visible before users see it.
There is no platform-level "missing translation" warning, so the
discipline has to live in CI. The known LWC/Aura issue
(`a028c00000p5gv6AAA`) where some component contexts incorrectly
fall back to English instead of the org default language is a
related trap — verify both in the user's locale and in the org
default.

---

## Gotcha 4: LWC label imports are bundled at compile time — value changes need a component rebuild

**What happens:** An admin changes the `Value` of
`Quote_Save_Button` from "Save Quote" to "Save and Submit" via
Setup. Apex picks up the new value on the next transaction (Apex
`System.Label.X` re-resolves per request). LWC components keep
showing the old text — sometimes for hours, sometimes until the
component is redeployed. The reason: LWC `@salesforce/label/c.X`
imports are baked into the compiled component bundle at deploy
time; the platform re-bundles only when the component metadata is
itself re-touched.

**When it occurs:** Any Setup edit to a label `Value` (not the
language translations) where the label is consumed by LWC. Also
hits when a managed package upgrade swaps a label value but the
consuming LWC doesn't re-deploy because its source hash didn't
change.

**How to avoid:** Re-deploy the consuming LWC after any label
`Value` change — a no-op `touch` and `sf project deploy start
--source-dir force-app/main/default/lwc/quoteForm` is enough. For
managed-package upgrades, the package install should re-bundle
automatically, but verify in a sandbox first. For high-velocity
copy iteration, push the translation change rather than the source
`Value` and Apex picks it up immediately; reserve `Value` edits
for batched releases. Document the rule in your release runbook —
ops teams routinely change a Value, refresh the browser, and file
a "label not updating" bug.

---

## Gotcha 5: Scratch orgs don't auto-sync label changes — `sf project deploy start` is required

**What happens:** A developer edits a label in their scratch org
via Setup UI, then makes an LWC change locally that references the
new label, and runs `sf project deploy start` (or the older
`sfdx force:source:push`). The deploy succeeds but the new label
isn't included because the developer never ran `sf project retrieve
start` to pull the Setup-side edit into the local project. The LWC
deploys, fails to find `c.New_Label` at runtime, and the component
breaks. Conversely, editing the label file locally and pushing
sometimes appears to "work" but the scratch org's compiled LWC
bundle still references the previous value — see Gotcha 4 — until
the LWC source is also pushed.

**When it occurs:** Mixed workflows where some changes happen in
Setup UI (admin-style) and some happen in local files (developer-
style), without a discipline of `retrieve` before `deploy`. Also
hits when multiple developers share a scratch org and edits
collide.

**How to avoid:** Standardize the rule: labels are managed in
source. Either always edit `force-app/main/default/labels/CustomLabels.labels-meta.xml`
locally and `sf project deploy start --source-dir force-app/main/default/labels`,
or always edit in Setup and run `sf project retrieve start --metadata
CustomLabel` before any deploy that references the changes. Pick
one and enforce in code review. For shared scratch orgs, prefer
per-developer scratch orgs entirely — label-edit race conditions
are one of many reasons. Add a pre-deploy git hook that runs
`sf project retrieve start --metadata CustomLabel` automatically
if your team can't agree on the discipline.
