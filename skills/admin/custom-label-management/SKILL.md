---
name: custom-label-management
description: "Custom Labels for i18n, configuration strings, and UI text: translation workbench, Apex System.Label, LWC @salesforce/label imports, 1,000-char limit. NOT for translating picklist values, field labels or layouts — use admin/multi-language-and-translation. NOT for config values in custom metadata or custom settings — use admin/custom-metadata-types."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Scalability
tags:
  - custom-labels
  - i18n
  - translation
  - lwc
  - apex
triggers:
  - "how do i add a translatable string to a lightning web component"
  - "custom label versus custom metadata for configuration text"
  - "translation workbench custom label workflow for multi-language rollout"
  - "apex system.label reference fails after rename"
  - "1000 character limit on custom labels workaround"
  - "custom label deployment and packaging best practices"
  - "deploying custom labels wiped the labels already in the org"
  - "retrieve only two custom labels by name instead of every label"
  - "custom label translations missing after retrieving the translations folder"
  - "value data value too large error when saving a custom label"
  - "where do custom label translations live in the metadata"
inputs:
  - Text strings used in UI, Apex, or validation messages
  - Target languages and localization requirements
  - Packaging model (unlocked, managed, org-level)
outputs:
  - Custom Label catalog with categories
  - Translation workflow and translator handoff
  - Apex/LWC reference patterns
  - Deployment and packaging plan
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Custom Label Management

Activate when hard-coded strings appear in Apex, LWC, validation rules, or email templates that will need to be translated, reviewed for tone, or changed without code. Custom Labels are the canonical Salesforce mechanism for externalizing text and pushing it through the Translation Workbench.

## Before Starting

- **Identify every hard-coded user-facing string.** LWC templates, Apex `addError` calls, validation rules, and email templates all accumulate string debt.
- **Know the 1,000-character limit per label.** Longer blocks need splitting or a Rich Text custom object.
- **Enable the Translation Workbench** and inventory target languages before exporting.

## Questions to Ask Before Configuring

Ask these before the first `<labels>` element is written. Every row maps to a
`CustomLabel` field that Metadata API marks **Required** or to a documented
platform behaviour — skip a row and the file still deploys, then misbehaves.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is this string shown to a user verbatim, or is it a value code branches on?" | Only the first kind belongs in a label; endpoints, toggles and thresholds belong in a Custom Metadata Type | A per-string disposition: label, CMDT, or stays inline |
| "What is the org's default language, and which locales are already enabled?" | `language` is a Required field on every `CustomLabel`, and translations are separate metadata under `translations/` | The `<language>` value for the source file plus the list of `<locale>.translation` files to author |
| "Will these labels ship inside a managed package, and may the installing org reference them?" | `protected` is Required; protected components can't be linked to or referenced by components created in the installing org | An explicit `true`/`false` per label instead of a copy-pasted `false` |
| "How does the pipeline retrieve labels — wildcard `CustomLabels` or named `CustomLabel` members?" | `CustomLabels` doesn't support retrieving labels by name; the singular `CustomLabel` type does | A manifest that touches only the labels this change owns |
| "How long is the longest value, and will it be translated?" | Source `value` caps at 1,000 characters but a `CustomLabelTranslation.label` caps at 765 | Either a split-label plan or a decision to move the long text to a CMDT LongTextArea |
| "Which categories already exist, and who filters on them?" | `categories` is a comma-separated string, max 255 characters, used as list-view filter criteria | A category vocabulary reused rather than reinvented per feature |
| "Which surfaces consume each label — Apex, LWC, Flow, validation rule?" | Apex resolves `System.Label.X` at compile time, so the label must be in the same deployment payload as the class | The deployment artifact contents and the order of any destructive change |

What a proper configuration adds over just creating the labels: the file deploys
alongside the code that references it, every label carries the translator context
and packaging flag the platform requires, and the translation files exist per
locale instead of silently falling back to the source language.

---

## Core Concepts

### Label vs Name vs Value

Every custom label has a Name (API, immutable once referenced), Short Description (required, hint for translators), Categories (a comma-separated grouping string — see the field table below), Value (the default-language string), and per-language translations. Never rename Name — Apex references break.

### The `CustomLabel` fields Metadata API actually defines

| Field | Type | Required? | Constraint the guide states |
|---|---|---|---|
| `fullName` | string | Required | The name of the custom label; must be specified when creating, updating, or deleting |
| `value` | string | Required | The translated custom label. **Maximum of 1000 characters** |
| `language` | string | Required | The language of the translated custom label |
| `protected` | boolean | Required | Protected components can't be linked to or referenced by components created in the installing organization |
| `shortDescription` | string | Required | An easily recognizable term to identify this label; used in merge fields |
| `categories` | string | Optional | A comma-separated list; usable as list-view filter criteria. **Maximum of 255 characters** |

Source: Metadata API Developer Guide, *CustomLabels* → *CustomLabel* field table
(`api_meta.txt:41187-41221`). Note `categories` is **comma**-separated per the
guide, not semicolon-separated.

### Where the metadata lives

- Master values: a single `CustomLabels.labels` file — every label in the org
  shares it (`api_meta.txt:41165`).
- Translations: `translations/<localeCode>.translation`, one file per locale,
  containing `<customLabels>` entries with `<name>` and `<label>`
  (`api_meta.txt:135574-135577`, `api_meta.txt:135930-135937`).
- Packaged translations use `pkgNamespace__localeCode.translation`
  (`api_meta.txt:135576-135577`).

### Reference patterns

- Apex: `System.Label.My_Label`
- LWC: `import LABEL from '@salesforce/label/c.My_Label';` (namespace `c` for local, custom namespace for package)
- Validation rule / formula: `$Label.My_Label`
- Visualforce: `{!$Label.My_Label}`
- Apex, dynamic: `Label.get(namespace, label, language)` and
  `Label.translationExists(namespace, label, language)` — resolved at run time,
  so a missing label is silence rather than a compile error
  (`apexrefguide.txt:220031-220034`)

UNVERIFIED (2026-09-04): only the Apex forms above are grounded in the sources
used for this revision (`apexdev.txt:7246-7250`, `apexrefguide.txt:220031-220037`).
The LWC `@salesforce/label/c.<Name>` import specifier is not re-grounded because
the LWC Developer Guide is not in the extracted corpus, and the corpus shows the
`$Label` merge field only in its namespaced form inside a Gift Entry template
(`api_meta.txt:78590`) — never in a validation-rule or formula context. Confirm
both against their own guides before shipping; the full markers and what they
rest on are in `references/metadata-examples.md`.

### Translation Workbench

Admin enables target languages; translators (or a translator profile) fill values per language. Export/import CSV/STF files for external translation services. The
Workbench side — enabling locales, the picklist and field-label surfaces, and
`toLabel()` in SOQL — belongs to `admin/multi-language-and-translation`; this
skill owns the label's own lifecycle and the `Translations` metadata that
carries its translated value.

### Packaging impact

Labels travel with metadata. Managed-package labels are namespaced (`ns.My_Label`); unlocked packages and org-level labels are not. The `protected` flag is the packaging contract: protected labels "can't be linked to or referenced by components created in the installing organization" (`api_meta.txt:41203-41206`), and Apex "can't access labels that are protected in a different namespace" (`apexrefguide.txt:220008-220009`). It is inert in an unpackaged org, which is why it gets set wrong — see `references/gotchas.md` Gotcha 10.

## Common Patterns

### Pattern: Category-based organization

Use categories like `Errors`, `UIButtons`, `Toast`, `EmailBody`. Filter the setup list during audits; Apex tools can scan by category prefix.

### Pattern: LWC label import with local `labels` object

```
import greeting from '@salesforce/label/c.Greeting';
import farewell from '@salesforce/label/c.Farewell';
export default class Hello extends LightningElement {
    labels = { greeting, farewell };
}
```

Template: `{labels.greeting}`. Clean and renameable.

### Pattern: Long-text overflow

For strings over 1,000 chars (complex email body), split into `My_Long_Text_Part1`, `My_Long_Text_Part2` and concatenate. Alternatively, store in a Custom Metadata Type Rich Text field.

## Decision Guidance

| Need | Mechanism |
|---|---|
| User-facing UI string, translatable | Custom Label |
| Configuration value (URL, toggle) | Custom Metadata Type |
| Long dynamic email body | Email Template or CMDT rich text |
| Runtime mutable string by admin | Custom Setting or CMDT |
| Label over 1,000 chars | Split or use CMDT |

## Recommended Workflow

1. **Inventory and disposition.** Fill
   `templates/custom-label-management-template.md` with the answers to
   *Questions to Ask Before Configuring* and one row per hard-coded string
   found in `.cls`, `.trigger`, LWC `.html`/`.js`, `.flow-meta.xml` and
   validation rules. Anything code branches on leaves for
   `admin/custom-metadata-types`.
2. **Retrieve the current label set before editing.** `CustomLabels` is one
   file for the whole org, so every deploy is a whole-set write and a stale
   copy silently reverts other people's values. Use the retrieve command and
   manifest in `references/metadata-examples.md` ("Retrieve, lint, deploy"),
   and note the categories already in use.
3. **Author the `<labels>` entries.** Copy the shape from
   `references/metadata-examples.md` — `fullName`, `value`, `language`,
   `protected`, `shortDescription`, `categories` on every label, not just the
   Required minimum.
4. **Wire the consumers in the same change.** Apex `System.Label.X`, LWC
   `@salesforce/label/c.X`, Flow and formula `$Label.X`. Read
   `references/gotchas.md` Gotchas 2 and 6 first — the compile-time binding and
   the whole-file replacement rule decide the deployment shape.
5. **Lint before deploying.** Run
   `python3 scripts/check_custom_label_management.py --manifest-dir force-app/main/default`.
   Clear every `ERROR` (duplicate `fullName`, over-length `value`); triage
   `WARN` (missing `shortDescription`, undefined label reference) and `INFO`
   (uncategorised label, label referenced nowhere).
6. **Deploy labels and consumers as one payload**, then author
   `translations/<locale>.translation-meta.xml` per enabled locale — see
   `references/metadata-examples.md` and `admin/multi-language-and-translation`
   for the Translation Workbench side.
7. **Verify per locale.** Follow the verification step in
   `references/metadata-examples.md`: log in as a user whose
   `LanguageLocaleKey` is the target locale and confirm each consumer surface,
   because a missing translation renders the source value with no error.

## Review Checklist

- [ ] No user-facing hard-coded strings in LWC templates
- [ ] No hard-coded strings in Apex `addError` calls or `System.debug`
- [ ] Short Description filled on every new label (translator context)
- [ ] Categories consistent across labels
- [ ] Translation Workbench enabled; STFs imported for each language
- [ ] Package/deployment plan includes labels
- [ ] Naming convention documented

## Salesforce-Specific Gotchas

1. **Renaming the label Name breaks Apex.** References compile-fail. Always add a new label and deprecate.
2. **Labels are cached per session.** Changing a value may not reflect until session reload; bust cache or test with a new session.
3. **STF export can omit new labels if not saved first.** Save the label list before exporting.

## Output Artifacts

| Artifact | Description |
|---|---|
| Label catalog | Name, value, category, languages, owner |
| Reference audit | Files referencing each label |
| Translation plan | Languages, translators, turnaround |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing `CustomLabels.labels-meta.xml`, the `<locale>.translation-meta.xml` companion, the consumer snippets (Apex / LWC / Flow / validation rule), `package.xml`, the retrieve-deploy commands, or the post-deploy verification |
| `references/gotchas.md` | The labels deployed cleanly and something is still wrong — labels vanished, a class won't compile, a translation is blank, an LWC shows stale text, or a namespaced retrieve returns nothing |
| `references/examples.md` | Two end-to-end walkthroughs — one label consumed by both Apex and LWC, and a vendor translation round-trip — plus the i18n-debt anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing label guidance or label-bearing code an AI assistant produced |
| `references/well-architected.md` | Choosing between Custom Label, CMDT, Custom Setting and Static Resource, or chasing the official source behind a claim here |
| `templates/custom-label-management-template.md` | Workflow step 1 — the string inventory and per-string disposition, before any XML exists |
| `scripts/check_custom_label_management.py` | Workflow step 5, before every deploy that touches `labels/` |

---

## Related Skills

- `admin/custom-metadata-types` — configuration data vs UI text; where a value code branches on belongs
- `admin/multi-language-and-translation` — the Translation Workbench side: enabling locales, picklist and field-label translation, `toLabel()` in SOQL
- `devops/metadata-api-retrieve-deploy` — retrieve/deploy mechanics for the single-file `CustomLabels` type
- `devops/destructive-changes-deployment` — removing a label after its references are gone
