---
name: custom-label-management
description: "Custom Labels for i18n, configuration strings, and UI text: translation workbench, Apex System.Label, LWC @salesforce/label imports, 1,000-char limit. NOT for custom settings or custom metadata types (use custom-metadata-types). NOT for platform cache (use caching-strategies)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Custom Label Management

Activate when hard-coded strings appear in Apex, LWC, validation rules, or email templates that will need to be translated, reviewed for tone, or changed without code. Custom Labels are the canonical Salesforce mechanism for externalizing text and pushing it through the Translation Workbench.

## Before Starting

- **Identify every hard-coded user-facing string.** LWC templates, Apex `addError` calls, validation rules, and email templates all accumulate string debt.
- **Know the 1,000-character limit per label.** Longer blocks need splitting or a Rich Text custom object.
- **Enable the Translation Workbench** and inventory target languages before exporting.

## Core Concepts

### Label vs Name vs Value

Every custom label has a Name (API, immutable once referenced), Short Description (required, hint for translators), Categories (free-text, used for grouping), Value (the default-language string), and per-language translations. Never rename Name — Apex references break.

### Reference patterns

- Apex: `System.Label.My_Label`
- LWC: `import LABEL from '@salesforce/label/c.My_Label';` (namespace `c` for local, custom namespace for package)
- Validation rule / formula: `$Label.My_Label`
- Visualforce: `{!$Label.My_Label}`

### Translation Workbench

Admin enables target languages; translators (or a translator profile) fill values per language. Export/import CSV/STF files for external translation services.

### Packaging impact

Labels travel with metadata. Managed-package labels are namespaced (`ns.My_Label`); unlocked packages and org-level labels are not.

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

1. Audit codebase for hard-coded strings in LWC, Apex, validation rules, email templates.
2. Create labels with meaningful Names and filled Short Descriptions.
3. Categorize labels by UI area or feature.
4. Replace hard-coded strings with `System.Label` / `@salesforce/label` / `$Label` references.
5. Enable target languages; export STF for translators; import translated STF.
6. Add CI check that flags new string literals in LWC templates and Apex error messages.
7. Document naming convention and approval workflow for label additions.

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

## Related Skills

- `admin/custom-metadata-types` — configuration data vs UI text
- `lwc/lwc-localization-i18n` — LWC-side language handling
- `devops/cicd-pipeline-design` — CI checks for new literals
