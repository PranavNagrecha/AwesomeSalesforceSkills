# Gotchas — Custom Label Management

Eleven non-obvious platform behaviors that catch teams building i18n
on top of Custom Labels. Gotchas 6-11 are quoted from the Metadata API
Developer Guide and the Apex Reference Guide with the source line beside each
claim. These compound (not duplicate) the items in
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
organization`. UNVERIFIED (2026-09-04): the per-org label cap is not in the extracted Metadata API guide or the App Limits cheat sheet; carried from a Help citation. Both ceilings are tenant-wide and include labels
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

---

## Gotcha 6: The label set is one file, so every deploy is a whole-set write

**What happens:** "Master custom label values are stored in the
CustomLabels.labels file" (`api_meta.txt:41165`) — singular, org-wide. And the
plural metadata type refuses to narrow the retrieve: "`CustomLabels` doesn't
support retrieving one or more custom labels by name" (`api_meta.txt:41224-41227`).
The consequence is that the artifact you deploy is always the complete set as
your working copy has it. A colleague's Setup edit to a label you didn't touch
is reverted by your deploy, silently, with a success status — the platform saw a
valid `CustomLabels` component and applied the values in it.

**When it occurs:** Any org where labels are edited in more than one place — a
Setup-editing admin plus a git-based pipeline, or two feature branches that each
retrieved the file at different times. It also occurs in a single-pipeline org
whenever a working copy sits on a branch for more than a day or two, which is
most branches.

**How to avoid:** Pick a single source of truth and enforce it in code review.
Either labels never get created in Setup (git owns the file, and merge conflicts
in `CustomLabels.labels-meta.xml` behave like conflicts in any other file), or
`sf project retrieve start --metadata CustomLabels` runs immediately before every
edit and the edit is deployed the same day. The singular `CustomLabel` type
narrows a *retrieve* to named members (`api_meta.txt:41261-41280`) but does not
narrow a `--source-dir .../labels` deploy, because that directory still holds the
one whole file. UNVERIFIED (2026-09-04): whether a deploy additionally *deletes*
labels absent from your file is not stated in the guide's `CustomLabels` section
(`api_meta.txt:41147-41291`); establish the answer in a scratch org rather than
assuming it.

---

## Gotcha 7: You cannot retrieve `CustomLabels` with a namespace

**What happens:** The guide carries a dedicated *CustomLabels Limitation*
section that is one sentence long: "You can't retrieve the CustomLabels metadata
type with a namespace" (`api_meta.txt:41289-41291`). A retrieve aimed at an
installed managed package's labels comes back without them. The retrieve itself
succeeds, so the failure looks like "the package has no labels" rather than
"this type cannot express that request."

**When it occurs:** Auditing an installed AppExchange package's label footprint;
trying to fork or re-point a managed package's copy; building an org-wide label
inventory that is supposed to include package-contributed labels. Also when a
team assumes the 5,000-label ceiling can be audited by retrieving everything —
it can't, because the namespaced portion never arrives.

**How to avoid:** Don't build the label inventory from a Metadata API retrieve
alone; it is structurally incomplete in any org with managed packages. Treat
package labels as a separate, non-retrievable population and count them from the
Setup list view filtered by namespace instead. In Apex, the `Label` class can
still *read* an unprotected packaged label at run time via
`Label.get('MyNamespace', 'MyLabel', 'fr')` (`apexrefguide.txt:220047`) even
though you cannot retrieve its definition.

---

## Gotcha 8: Retrieving `Translations` without also listing the label type returns no label translations

**What happens:** You add `Translations` to `package.xml`, retrieve, and get
`.translation` files that are missing the `<customLabels>` entries you expected —
or missing entirely. The guide states the rule plainly: "When you use the
`retrieve()` call to get translations, the files returned in the `.translations`
folder only include translations for the other metadata types referenced in
package.xml" (`api_meta.txt:136670-136673`). Translations are not a standalone
export; they are a projection of whatever else the manifest names.

**When it occurs:** A translation-only pipeline stage ("just pull the
translations, the labels haven't changed"), or a hand-written manifest that lists
`Translations` and the Apex/LWC consumers but omits the label type because the
labels weren't being edited. The result is a `.translation` file that deploys
cleanly and translates nothing.

**How to avoid:** Any manifest that names `Translations` must also name
`CustomLabels` (wildcard) or `CustomLabel` (named members). The guide's own
example manifest for this scenario lists six other types alongside `Translations`
for exactly this reason (`api_meta.txt:136674-136712`). Add the pairing as a
lint rule on `package.xml` rather than a review convention.

---

## Gotcha 9: A translation can be shorter than the value it translates — 765 vs 1000 characters

**What happens:** `CustomLabel.value` is "Required. The translated custom label.
Maximum of 1000 characters" (`api_meta.txt:41219-41220`). But
`CustomLabelTranslation.label` — the field that carries the translated text in a
`Translations` file — is "Required. The translated custom label name. Maximum of
765 characters" (`api_meta.txt:135933-135937`). A source value between 766 and
1,000 characters saves fine and then cannot be fully translated into any locale.
Languages that expand relative to English (German, French, Spanish routinely run
15-30% longer) hit the ceiling well before the source value does.

**When it occurs:** Long-form label content — a legal disclaimer, a multi-
sentence onboarding hint, an email body fragment — authored in English against
the 1,000-character ceiling, then handed to a translation vendor months later.
The English author has no signal that they've built something untranslatable.

**How to avoid:** Treat 765 characters, not 1,000, as the working ceiling for any
label that will ever be translated, and leave headroom below it for expansion —
roughly 600 English characters is safe. The checker in this skill flags values
over 1,000 as an ERROR; add your own threshold at 765 if the org is multilingual.
For genuinely long content, split into suffix-versioned siblings or move it to a
Custom Metadata Type LongTextArea (see Gotcha 1 and
`admin/custom-metadata-types`).

---

## Gotcha 10: `protected` is a packaging contract, and it is invisible until the package is installed

**What happens:** `protected` is a **Required** boolean on every `CustomLabel`
(`api_meta.txt:41203-41206`), and the guide defines it as: "Protected components
can't be linked to or referenced by components created in the installing
organization." The Apex `Label` class restates the runtime half: "You can't
access labels that are protected in a different namespace"
(`apexrefguide.txt:220008-220009`). In the *developing* org the flag changes
nothing observable, so it gets copy-pasted as `false` across an entire label file
and the mistake surfaces only after a subscriber installs the package and starts
referencing internals you never meant to expose — or, in the opposite direction,
after a subscriber's Apex fails to compile against a label you marked `true`.

**When it occurs:** First package upload; or the first upgrade after a label's
`protected` value is changed. Also on the consuming side: an ISV's support team
writing subscriber-org Apex against a label that turns out to be protected.

**How to avoid:** Decide `protected` per label at authoring time, from the
question "may the installing org's own components reference this?" — internal
error strings and engine diagnostics are `true`; anything a subscriber is meant
to display or override is `false`. Record the decision in the string inventory
(`templates/custom-label-management-template.md`) rather than in the XML alone,
because the XML gives a reviewer no way to tell a considered `false` from a
copy-pasted one. In an unpackaged org the flag is inert, which is exactly why it
needs a review gate rather than a runtime test.

---

## Gotcha 11: `categories` is comma-separated and capped at 255 characters, not a free-text field

**What happens:** The guide defines `categories` as "A comma-separated list of
categories for the label. This field can be used in filter criteria when creating
custom label list views. Maximum of 255 characters" (`api_meta.txt:41191-41193`).
Teams routinely write `Errors;Quote` with a semicolon, copying the multi-select
picklist convention. The value stores, the deploy succeeds, and the list-view
filter then treats `Errors;Quote` as one opaque category — so filtering on
`Errors` matches nothing, and the category taxonomy that was supposed to organise
a few hundred labels quietly does nothing.

**When it occurs:** Any org whose label conventions were written before anyone
read the field table — which is most of them, because the Setup UI accepts
whatever you type. The 255-character ceiling bites separately on labels that
accumulate categories over years of feature work, at which point the save fails
on a field nobody thinks of as size-constrained.

**How to avoid:** Commas, always: `<categories>Errors,Quote</categories>`. Fix
existing semicolon entries in one pass rather than per-feature, because a
half-migrated taxonomy is worse than a consistent wrong one — a filter on
`Errors` will match some labels and not others with no visible reason. Keep the
category vocabulary short and shared across features so the 255-character
ceiling stays irrelevant; treat "this label needs six categories" as a signal
that the categories are being used as tags for something a naming convention
should carry.
