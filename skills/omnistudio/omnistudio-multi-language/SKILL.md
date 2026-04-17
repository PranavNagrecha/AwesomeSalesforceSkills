---
name: omnistudio-multi-language
description: "Localize OmniScripts, FlexCards, and DataRaptors using Label-based translation, multi-language JSON, and locale-aware number/date formatting. NOT for Salesforce Translation Workbench alone."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
triggers:
  - "translate omniscript"
  - "omnistudio multilingual"
  - "flexcard language"
  - "translate dataraptor labels"
tags:
  - omnistudio
  - i18n
  - translation
inputs:
  - "target languages"
  - "OmniScripts/FlexCards in scope"
outputs:
  - "language data JSON + label extraction plan"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# OmniStudio Multi-Language

OmniStudio stores UI labels inside its JSON; translation happens via a Language Data file per script. FlexCards similarly support labels via the DataRaptor data source. This skill describes the label-extraction workflow, the process for re-exporting Language Data JSONs after every script edit, layout checks for longer translated strings, RTL preview steps, and verifies that number/date formatting respects user locale so a single OmniScript works for every active language without hard-coded English leaking through.

## When to Use

Any OmniStudio deployment for a multi-locale business.

Typical trigger phrases that should route to this skill: `translate omniscript`, `omnistudio multilingual`, `flexcard language`, `translate dataraptor labels`.

## Recommended Workflow

1. Export Language Data JSON for each OmniScript/FlexCard; send to translators.
2. Import translated JSONs; verify in each language preview.
3. For DataRaptor label columns: use Translation Workbench custom labels referenced via `{$Label.Foo}` in DR maps.
4. Number/date: rely on browser/user locale via component formatting options, not inline formatting.
5. Regression test: run each script in each language and verify layout (some languages 30% longer).

## Key Considerations

- Label extraction is per-version; re-export on every script change.
- RTL languages reveal layout issues; budget QA time.
- FlexCard static text is not localized via LDJ — use labels.
- Managed-package OmniStudio assets may need vendor coordination.

## Worked Examples (see `references/examples.md`)

- *Four-language deploy* — Global retail
- *Layout regression* — German labels 40% longer

## Common Gotchas (see `references/gotchas.md`)

- **LDJ out of sync** — Missing translations after script edit.
- **Hard-coded strings in FlexCard** — Stay English after translation.
- **RTL broken** — Layout reversed wrong.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Hard-coded static text
- No RTL testing
- Stale LDJ files in source control

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/
- OmniStudio for Salesforce — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_for_salesforce_overview.htm
- OmniScript to LWC OSS — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer.meta/omnistudio_developer/os_migrate_from_vf_to_lwc.htm
