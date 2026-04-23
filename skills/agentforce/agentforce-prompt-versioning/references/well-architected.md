# Well-Architected Notes — Prompt Versioning

## Relevant Pillars

- **Reliability** — reproducible prompt behaviour requires pinned model +
  versioned template + retained rollback path.
- **Operational Excellence** — source control, changelog, and A/B
  turn prompt changes into ordinary software ops.

## Architectural Tradeoffs

- **Pin model vs auto-update:** pin for reliability, auto for feature
  velocity. Critical topics pin; exploratory topics auto.
- **Suffix-per-version vs revision-bump:** suffix is explicit and
  rollback-friendly but multiplies metadata; revision bump is
  lightweight but loses history.
- **Embedded rules vs injected data:** embedded is simpler, injected
  keeps policy changes out of prompt changelog.

## Hygiene

- UI edits retrieved within 24h.
- Quarterly model re-evaluation.
- Prior 2-3 versions retained.

## Official Sources Used

- Prompt Templates —
  https://help.salesforce.com/s/articleView?id=sf.prompt_builder_overview.htm
- Model Configuration —
  https://help.salesforce.com/s/articleView?id=sf.generative_ai_models.htm
