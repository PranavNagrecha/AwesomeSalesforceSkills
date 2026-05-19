# Well-Architected Notes — Custom Label Management

## Relevant Pillars

Custom Labels look like a simple admin convenience but they sit on
the critical path of two pillars and have second-order impact on a
third. Treat label hygiene as a long-term investment that pays off
the moment a second language, a rebrand, or a vendor-translation
workflow shows up — none of which are predictable on day one.

- **Operational Excellence** — Labels are the only Salesforce-
  native mechanism that lets a non-developer change user-facing
  copy without a deploy. Every Apex `addError` literal and LWC
  `<p>` tag with English text is operational debt: it requires a
  developer, a code review, a test cycle, and a deploy to update.
  Externalize early and the marketing team can iterate copy at
  their own pace, which directly compresses the time-to-revision
  cycle that ops cares about.
- **Scalability** — The 5,000-label-per-org allocation forces
  intentional naming and lifecycle hygiene (see `gotchas.md`
  Gotcha 1). Orgs that grow organically without label-management
  discipline routinely hit 3,000+ labels by year five — at which
  point a new initiative (a vertical product launch, an
  acquisition's data merge) blocks because there's no headroom.
  Audit and prune cadence (quarterly is reasonable) keeps the
  ceiling from becoming a project blocker.
- **Reliability** — Hard-coded strings in Apex `addError` cannot
  be A/B-tested, cannot be hotfixed by an admin, and cannot be
  translated without a developer. When a customer-facing error
  message has a typo or accidentally exposes internal detail, the
  fix is a code deploy if the string is inline and a Setup edit
  if it's a label. The label version reaches users in minutes; the
  code version takes a release window.

## Architectural Tradeoffs

The defining decision is **where the string should live**. Custom
Labels are the right answer for most user-facing copy, but the
edges of that envelope matter — pick the wrong storage and you
pay later.

| Storage | Translatable | Per-record? | Limit | Best for |
|---|---|---|---|---|
| Custom Label | Yes (Translation Workbench) | No (org-singleton) | 1,000 chars / 5,000 per org | User-facing copy: buttons, errors, toasts, modal text, validation messages, email body fragments |
| Custom Metadata Type | No (manual per-record) | Yes (record set) | 32,768 chars on LongTextArea field | Configuration values (URLs, API tokens, feature flags), long-form text the platform won't translate (large legal disclaimers), per-region rule data |
| Custom Setting (Hierarchy or List) | No | Yes | 300 chars per Text field, 32K per LongText | Runtime-mutable values per-user / per-profile / per-org; rarely the right answer in 2026 — CMDT replaces nearly all use cases |
| Hardcoded string in code | No | n/a | n/a | Internal logging only (`System.debug`, exception class names, developer-facing error codes that never reach a user) |
| Static Resource (locale-suffixed) | Manual per-file | n/a | 5MB per file, 250MB per org | Localized images (currency-marked screenshots, region-specific marketing graphics), per-locale CSS, downloadable PDFs |

The most common confusion: **Custom Label vs Custom Metadata Type**
for a configuration string. Rule of thumb — if the value will be
shown to a user verbatim and might one day need translation, it's
a Custom Label. If it's a configuration switch read by code (an
endpoint URL, a feature toggle, a numeric threshold), it's a CMDT.
The translation litmus test resolves 95% of the cases.

A second tradeoff: **one label per use vs shared labels across
features**. Sharing reduces label count (helpful for the 5,000
ceiling) but creates coupling — a copy change for the Quotes
feature ripples into the Cases feature if they share
`Common_Save_Button`. The pragmatic rule: share atomic UI labels
("Save", "Cancel", "Close") because they should remain identical
for UX consistency, but never share feature-specific phrasing
even when the English value happens to match. Two labels with
identical English values can diverge in French.

A third tradeoff: **inline value entry vs Translation Workbench
export/import workflow**. Inline entry (the "New Local
Translations/Overrides" button per label) is fine for under ~20
labels in 1–2 languages — Setup clicks are cheap at that volume.
Past that, the export/import workflow with a `.stf` file pays off
because it's diff-able, vendor-friendly, and reversible. Teams
that try to scale inline entry past 100 labels routinely lose
translations to mid-air collisions when two admins edit the
Workbench at the same time.

## Anti-Patterns

1. **Treating the label `Name` as a display string.** Renaming
   `Error_Msg` to `Error_Amount_Negative` to better describe its
   purpose compile-fails every Apex class referencing it and breaks
   every LWC import path. `Name` is an immutable API handle.
   Change the `Short Description` or the `Value`; never the
   `Name`. To rename a concept, create a new label, migrate
   references in a deploy, then delete the old label.

2. **Building a parallel `Map<String,String>` "i18n" mechanism in
   Apex.** Reinventing labels with a Custom Setting or hard-coded
   Map loses the Translation Workbench integration, breaks the
   Setup audit trail, and is invisible to Metadata Dependency
   tooling so refactors can't find references. `System.Label.X`
   exists for a reason; use it.

3. **Skipping the `Short Description` field.** It's the only
   context the translator has when they see your label in a `.stf`
   file. "Save" without context could mean a button label, a verb
   in a sentence ("I'll save it"), or a noun ("the savings
   account"). French translators need disambiguation and English-
   only label `Value` doesn't provide it. The 4-second cost of
   filling `Short Description` saves multi-hour vendor back-and-
   forth on every export.

4. **Hard-coding strings inside validation rule formulas.** A
   validation rule's `errorMessage` field accepts a literal string
   or a `$Label.X` reference; many admins use the literal because
   it's faster. The literal is invisible to Translation Workbench
   and can never be translated — meaning a non-English user gets
   an English error toast inside an otherwise-translated UI.
   Always use `$Label.X` for validation rule errors, even in
   English-only orgs.

5. **Letting installed managed-package labels count silently
   against the 5,000 ceiling.** An org that installs three large
   AppExchange packages can absorb 2,000+ namespaced labels
   without realizing it — those labels are invisible in the
   default Setup label list (filter by namespace to see them).
   Track them in your audit; a new initiative that needs 500
   labels will fail with "limit reached" and the team will spend
   a day diagnosing why.

## Official Sources Used

- Salesforce Help — Custom Labels:
  https://help.salesforce.com/s/articleView?id=sf.cl_about.htm
- Salesforce Help — Create and Edit Custom Labels:
  https://help.salesforce.com/s/articleView?id=sf.cl_create_define.htm
- Salesforce Help — Translation Workbench:
  https://help.salesforce.com/s/articleView?id=sf.cl_translation_workbench.htm
- Apex Reference Guide — Label class (System.Label):
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_System_Label.htm
- Lightning Web Components Developer Guide — Labels:
  https://developer.salesforce.com/docs/platform/lwc/guide/create-labels.html
- Salesforce Well-Architected — Operationally Excellent:
  https://architect.salesforce.com/well-architected/operationally-excellent/overview
