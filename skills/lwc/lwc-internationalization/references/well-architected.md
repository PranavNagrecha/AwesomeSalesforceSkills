# Well-Architected Notes — LWC Internationalization

**User Experience:** the goal is not that the component is translated but that it agrees
with everything else the user sees. A date formatted from `navigator.language` and a date
in a report come from different settings and will disagree for any user whose browser and
Salesforce locale differ — which is most users in a multinational org. Reading the
platform's locale, or better, letting a base component read it, keeps one component from
being the only surface in the org that disagrees about what "03/04" means. The guide's own
framing is the same: use base components "as they adapt automatically to the language,
locale, and time zone settings of the Salesforce org they run in", and reach for the
internationalization properties only "to internationalize your own components so that they
also adapt" (`lwc_guide create-i18n` L3795–L3796).

**Operational separation:** custom labels put translation in the hands of translators
rather than deployments. A JavaScript dictionary keyed by language works on day one and
then requires a release for every wording change in every language, which is how orgs end
up with stale translations they cannot afford to fix. Labels are one of the string stores
the `Translations` metadata type covers — the same file also carries custom applications,
custom tabs, bots, and dozens of other sub-lists (`api_meta` L135600–L135612) — so the
translation of a label travels the same route as the translation of a picklist value, and
can be reviewed as one artefact per language.

**Design constraint, not a limitation:** the label *specifier* is fixed in source; the
*value* is resolved per user at runtime, because "modules scoped with `@salesforce` add
functionality to Lightning web components at runtime" (`lwc_guide
reference-salesforce-modules` L21986). That split is what lets one deployed bundle serve
every language at once. Attempting to defeat the static half with runtime name construction
does not produce a dynamic translation system; it produces a component with no translations
at all, and no error to say so.

**Two ceilings, not one:** the master value holds 1,000 characters (`api_meta`
L41219–L41220) and its translation holds 765 (L135934–L135935). Any design that treats the
larger number as the budget has already decided that some language will be truncated. This
is the kind of constraint worth encoding in the checker rather than in a review checklist,
which is why `scripts/check_lwc_internationalization.py` raises the 766–1,000 band as a
warning before it ever reaches a translator.

**Silent failure everywhere:** an untranslated label falls back to the master value, an
unenabled language falls back, a picklist with no Translation Workbench entry "falls back to
the org's default language" (`lwc_guide reference-wire-adapters-picklist-values` L14963),
and a Jest assertion on label text passes against the label's own path string
(`unit-testing-using-jest-patterns` L12650). Nothing in this system fails loudly, so "it
looks fine" is not evidence. The only reliable check is loading the component as a user
whose language is one of the target languages — including one right-to-left language, where
a class of defect exists that no amount of code review finds.

**Reliability across containers:** the same bundle behaves differently on an LWR Experience
Cloud site, where `currency`, `number.currencySymbol` and `number.currencyFormat` are
unsupported, `timeZone` comes from the browser, and a language configuration change requires
a site republish (`lwc_guide create-i18n` L3836–L3838). A component intended for both
surfaces should take currency from the record rather than from the user, so that the
degraded container is not also the wrong one.

## Official Sources Used

- Lightning Web Components Developer Guide — Labels (`create-labels`): the `@salesforce/label` scoped module, the `namespace.labelName` reference format, `{property}` binding in templates, and label files living anywhere under `force-app/main/default` — https://developer.salesforce.com/docs/platform/lwc/guide/create-labels.html
- Lightning Web Components Developer Guide — Internationalization (`create-i18n`): the full enumerated property table (`lang`, `dir`, `locale`, `currency`, `timeZone`, `firstDayOfWeek`, `dateTime.*`, `number.*`), values "returned for the current user", the base-components-first recommendation, the `Intl` fallback, the explicit `lang`/`dir` binding instruction, and the LWR-site limitations — https://developer.salesforce.com/docs/platform/lwc/guide/create-i18n.html
- Lightning Web Components Developer Guide — @salesforce Modules (`reference-salesforce-modules`): "Modules scoped with `@salesforce` add functionality to Lightning web components at runtime", and the fixed identifier set for `@salesforce/i18n` — https://developer.salesforce.com/docs/platform/lwc/guide/reference-salesforce-modules.html
- Lightning Web Components Developer Guide — Jest Test Patterns (`unit-testing-using-jest-patterns`): the label jest-transformer producing the label path as the value, `jest.mock(..., { virtual: true })` to override it, and `moduleNameMapper` for mock modules — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-patterns.html
- Lightning Web Components Developer Guide — getPicklistValues (`reference-wire-adapters-picklist-values`): `label` is translated into the running user's language and falls back to the org default, `value` is always the untranslated API name, and `@salesforce/i18n/lang` detects the running user's language — https://developer.salesforce.com/docs/platform/lwc/guide/reference-wire-adapters-picklist-values.html
- Lightning Web Components Developer Guide — Shadow DOM (`create-components-shadow-dom`): the `[dir=""]` attribute selector works only in synthetic shadow DOM; use `:dir()` in native shadow DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-shadow-dom.html
- Metadata API Developer Guide — `CustomLabels` / `CustomLabel`: field table (`fullName`, `categories` max 255, `language`, `protected`, `shortDescription`, `value` max 1000), the sample XML definition this skill's label file is shaped from, the `CustomLabels` vs `CustomLabel` manifest rule, and the no-namespace retrieval limitation — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `Translations` / `CustomLabelTranslation`: the `localeCode.translation` file-naming rule, the `translations` folder location, the `customLabels` sub-list, and the 765-character translated-label maximum — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

### Sources deliberately not treated as checked

- **Salesforce Help — Custom Labels** (`platform.cl_about`): the source of the widely quoted "5,000 labels per org, managed-package labels excluded" figure. UNVERIFIED (2026-09-05): help.salesforce.com cannot be fetched in this environment and the figure is absent from the Metadata API guide, the Object Reference and the App Limits Cheat Sheet. Cite the 1,000-character value limit, which is grounded; do not assert the org-wide count.
- **Salesforce Help — Translation Workbench**: enabling it, assigning translators, and the export/import file format. UNVERIFIED (2026-09-05): help-only. The declarative side is owned by `admin/multi-language-and-translation` and `admin/custom-label-management`.
- **Lightning Component Library** — attribute tables for `lightning-formatted-number`, `lightning-formatted-date-time` and the rest of the `lightning-formatted-*` family. UNVERIFIED (2026-09-05): the LWC Developer Guide names these components and their purposes (`data-wire-service-about` L6620–L6638) but publishes no attribute tables; `format-style`, `currency-code` and the `year`/`month`/`day` spellings used in this skill's examples come from the Component Library and should be confirmed there.
- **Salesforce DX Developer Guide** — the `-meta.xml` source-format suffix on `de.translation-meta.xml`. UNVERIFIED (2026-09-05): the Metadata API guide gives the MDAPI file name `de.translation`; the source-format variant is documented in the DX guide, which is not in the extracted set.
