# Gotchas — LWC Internationalization

Non-obvious platform behaviour, not advice. Line citations are into the extracted
Lightning Web Components Developer Guide (`lwc_guide`) and Metadata API Developer Guide
(`api_meta`) used to author this skill; the public URLs are listed in
`references/well-architected.md` → Official Sources Used.

## Gotcha 1: A hand-built date format reads as a different date, not a wrong-looking one

**What happens:** `03/04/2026` is 3 April to a UK user and 4 March to a US user. Nothing
errors; the number is simply understood as a different day. The guide states the split
directly: "the US uses Month, Day, Year, like 2/15/19. The United Kingdom uses Day, Month,
Year, like 15/2/19" (`lwc_guide create-i18n` L3840).

**When it occurs:** Any time a template or getter assembles a date out of parts, or pads a
`MM/DD/YYYY` string, instead of formatting it.

**How to avoid:** `<lightning-formatted-date-time>` in the template, or
`Intl.DateTimeFormat` with the imported `@salesforce/i18n/locale` where a base component
cannot go (L3841, L3843). If you need the org's own pattern strings rather than the
browser's idea of them, `dateTime.shortDateFormat` / `mediumDateFormat` / `longDateFormat`
are enumerated i18n properties (L3812–L3814).

---

## Gotcha 2: The label ceiling is 1,000 characters, but the translation ceiling is 765

**What happens:** A master label between 766 and 1,000 characters deploys cleanly. Its
translations cannot. `CustomLabel.value` is "Required. The translated custom label.
Maximum of 1000 characters" (`api_meta` L41219–L41220), and the type overview says custom
labels are "custom text values, up to 1,000 characters in length" (L41152–L41153). But
`CustomLabelTranslation.label` — the field that carries the translated text in a
`Translations` file — is "Required. The translated custom label name. Maximum of 765
characters" (`api_meta` L135934–L135935). The English paragraph fits; German, which
typically runs longer, has 235 fewer characters to work in.

**When it occurs:** Long help text, disclaimers, or an error message with an explanation,
written once in English and only discovered when the translation deployment fails.

**How to avoid:** Treat 765, not 1,000, as the working budget for anything that will be
translated. Split long help text across two labels rather than filling one to the master
ceiling. The 255-character figure that circulates for custom labels is not this limit —
`categories`, the list-view filter field on `CustomLabel`, is the field with a
255-character maximum (`api_meta` L41191–L41193).

---

## Gotcha 3: RTL breaks on the parts that are not styling, and `[dir]` selectors do not save you

**What happens:** A chevron keeps pointing right when "forward" is now left, an inline
`<svg>` refuses to mirror, and the obvious fix — a `[dir="rtl"]` CSS rule — silently does
nothing in some components. The guide is explicit: "you can't use the attribute selector
`[dir=""]` in a native shadow DOM subtree because the selector only works in synthetic
shadow DOM. Instead, see if your browser supports the `:dir()` pseudo-class in native
shadow DOM" (`lwc_guide create-components-shadow-dom` L3517).

**When it occurs:** Whenever a component sets `shadowSupportMode` to native, or lives under
a subtree that does — which the component author usually does not control.

**How to avoid:** Prefer CSS logical properties (`margin-inline-start`, `padding-inline-end`,
`text-align: start`) so no direction selector is needed at all; the guide's own RTL review
tooling describes its output as "code-level fixes for CSS logical properties, bidirectional
text, keyboard semantics, and RTL-aware SLDS class usage" (`lwc_guide mcp-testing` L12765).
Use `lightning-icon` rather than inline SVG. Where behaviour and not appearance must branch,
branch in JavaScript on `@salesforce/i18n/dir`, which returns `ltr` or `rtl` for the current
user (L3802, L3799).

---

## Gotcha 4: `CustomLabels` in `package.xml` cannot retrieve labels by name

**What happens:** You list six label names under `<name>CustomLabels</name>`, run the
retrieve, and get nothing back — no labels, and no error saying why. "`CustomLabels` doesn't
support retrieving one or more custom labels by name. To retrieve specific labels by name,
use `CustomLabel` and specify the label names as members" (`api_meta` L41225–L41227). The
plural type takes only the wildcard `*`; the singular type takes names.

**When it occurs:** Building a manifest by hand, or copying the plural type name off the
directory (`labels/`) or off the file suffix (`.labels-meta.xml`) — both of which are plural.

**How to avoid:** `<name>CustomLabel</name>` with named members, or `<name>CustomLabels</name>`
with `<members>*</members>`. Never the plural type with names.

---

## Gotcha 5: `CustomLabels` cannot be retrieved with a namespace at all

**What happens:** A retrieve against a namespaced org or a managed package returns no
labels. The guide lists this as a flat limitation of the type: "You can't retrieve the
`CustomLabels` metadata type with a namespace" (`api_meta` L41289–L41291).

**When it occurs:** Second-generation packaging work, or any org with a registered
namespace where the retrieve worked fine in the scratch org that had none.

**How to avoid:** Plan the label source of truth as files in version control rather than
something you round-trip from a namespaced org. In the component, a packaged label is still
imported the normal way — `@salesforce/label/ns.Name`, the same `namespace.labelName` format
used "in managed packages, in Visualforce, and in other Salesforce technologies"
(`lwc_guide create-labels` L3768).

---

## Gotcha 6: Deploying the labels does not deploy any translation of them

**What happens:** Every language keeps showing the English master value after a successful
deploy. They are two different metadata types in two different folders. "Master custom
label values are stored in the `CustomLabels.labels` file. Translations for custom labels
can be retrieved through `Translations` in Metadata API. Translations are stored in files
under the `translations` folder with the name format of `localeCode.translation`"
(`api_meta` L41165–L41167, L135574–L135575). Nothing fails, and nothing warns.

**When it occurs:** Every first deployment, and every time a label is added to an existing
component without a matching `<customLabels>` entry being added to each `<locale>.translation`
file.

**How to avoid:** Treat the label file and the translation files as one change set —
`package.xml` needs both `CustomLabel` and `Translations` entries. Verify by counting
`<name>` elements per language against the label file, not by looking at the component.
The count check is step 2 of `references/code-examples.md` § 11.

---

## Gotcha 7: In a Jest test, a label import is its own path, not its text

**What happens:** `expect(el.textContent).toBe('Save')` fails, and
`expect(el.textContent).toBe('c.Action_Save')` passes — which is worse, because it looks
like a green test of a translated component. "In Jest tests, we use a jest-transformer to
convert the `@salesforce/label` import statement into a variable declaration. The value is
set to the label path. By default, `myImport` is assigned a string value of
`c.specialLabel`" (`lwc_guide unit-testing-using-jest-patterns` L12650).

**When it occurs:** Any assertion on rendered label text written without a `jest.mock()`.

**How to avoid:** `jest.mock('@salesforce/label/c.X', () => ({ default: 'FIXTURE' }), { virtual: true })`
and assert against the fixture — the guide's own instruction: "You can use `jest.mock()` to
provide your own value for an import" (L12650). Do the same for
`@salesforce/i18n/locale` and `timeZone` so number and date assertions do not depend on the
machine running the suite. See `references/code-examples.md` § 7. The Jest harness itself
belongs to `lwc/lwc-testing`; this is the label- and locale-specific part of it.

---

## Gotcha 8: On an LWR site, three of the i18n properties do not work, and one comes from the browser

**What happens:** A component that reads the user's currency renders nothing sensible on an
LWR Experience Cloud site, and its times are wrong for any user whose laptop clock is not
in their Salesforce time zone. "For LWR sites, the `lang` and `locale` are mapped to the
language configured for the site, and `timeZone` is determined by the browser's timezone
rather than the user's personal settings. Additionally, `currency`,
`number.currencySymbol`, and `number.currencyFormat` are unsupported. If the site or org
language configurations are updated, you must republish the site"
(`lwc_guide create-i18n` L3836–L3838).

**When it occurs:** The same component bundle being reused from an internal Lightning page
onto an LWR site — the common and reasonable thing to do.

**How to avoid:** In an LWR-targeted component, take the currency from the record
(`CurrencyIsoCode`) rather than from `@salesforce/i18n/currency`, and do not assume
`timeZone` reflects the user record. Add "republish the site" to the runbook for any
language configuration change, because nothing else propagates it.

---

## Gotcha 9: A picklist's `label` is translated and its `value` never is

**What happens:** Code that compares, filters, or switches on the picklist string works in
English and silently stops matching the moment a translation lands, because the display
string changed and the comparison did not. "The `label` property returns the picklist label
translated into the running user's language … The `value` property always returns the
untranslated API name. Use `value` to save the user's selection back to Salesforce, and use
`label` only for display" (`lwc_guide reference-wire-adapters-picklist-values`
L14963–L14964).

**When it occurs:** `getPicklistValues` results piped into a filter, a `switch`, a CSS class
name, or a comparison with a hard-coded string.

**How to avoid:** Bind `label` to what the user reads and `value` to everything the code
does. Note also the fallback path: translation comes from the Translation Workbench, and
"Otherwise, `label` falls back to the org's default language" (L14963) — so an untranslated
picklist looks identical to a working one.

---

## Gotcha 10: A Date-only field formatted in the user's time zone loses a day

**What happens:** A `Date` field stored as `2026-03-01` renders as 28 February for every
user west of UTC. The value has no time component, so a formatter given the user's time
zone — `America/Los_Angeles` is the guide's own sample value for `@salesforce/i18n/timeZone`
(`lwc_guide create-i18n` L3835) — moves an assumed UTC midnight backwards across the date
boundary.

**When it occurs:** Any `Date` (not `DateTime`) field pulled from a wire adapter and passed
through `Intl.DateTimeFormat` or `new Date(...)` alongside `timeZone: TIME_ZONE`, which is
exactly the correct handling for the `DateTime` field two lines above it in the same
component.

**How to avoid:** Distinguish the two field types explicitly. Format a `DateTime` in the
user's `timeZone`; format a `Date` with `timeZone: 'UTC'` while still taking the *locale*
from the user (see `references/code-examples.md` § 2, `openedOn` vs `lastModifiedText`).

UNVERIFIED (2026-09-05): the UTC-midnight parse of a bare `YYYY-MM-DD` string is
ECMAScript (`Date.parse` date-time-string format), not a documented Salesforce behaviour;
neither the LWC guide nor the Metadata API guide states how a Date field's value is parsed
by a component. The observable symptom is well known but the mechanism is asserted here
from the language spec, not from Salesforce documentation.

---

## Gotcha 11: `lang` and `dir` are not stamped on your markup for you

**What happens:** Screen readers announce a German string with English pronunciation, and a
Hebrew paragraph lays out left-to-right inside an otherwise-mirrored page, because the
component's own subtree carries neither attribute. The guide describes this as work you do:
"To bind internationalization properties to HTML attributes, store them as private
properties in your component's JavaScript file. Here, `lang` determines the user's language
and `dir` specifies the direction that the text displays in HTML" (`lwc_guide create-i18n`
L3848), then "In your HTML template, reference the values with `{property}`" (L3849).

**When it occurs:** Any component that renders text without a wrapping element carrying
`lang` and `dir` — which is the default state of a component built from the skeleton.

**How to avoid:** One wrapper element, `<div lang={lang} dir={dir}>`, fed by
`@salesforce/i18n/lang` and `@salesforce/i18n/dir`. Broader language-attribute and
screen-reader concerns belong to `lwc/lwc-accessibility`; this is the i18n half of the
same wrapper.
