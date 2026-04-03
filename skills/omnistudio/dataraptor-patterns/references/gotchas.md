# DataRaptor Patterns — Gotchas

## 1. Turbo Extract Is A Narrow Optimization

Teams often treat Turbo Extract like a default performance upgrade.

Avoid it:
- Use it for simple single-object reads only.
- Switch back to Extract when mapping flexibility is actually needed.

## 2. Mapping Complexity Hides Asset Drift

The DataRaptor may still function while becoming impossible to maintain confidently.

Avoid it:
- Keep names and output shapes deliberate.
- Split read, transform, and write responsibilities clearly.

## 3. Load Assets Are Production Write Surfaces

Because they are declarative, teams sometimes under-review them.

Avoid it:
- Treat the input contract like any other write API.
- Remove brittle assumptions such as hardcoded record IDs.

## 4. Orchestration Logic Belongs Elsewhere

The urge to keep everything in one OmniStudio layer can turn a mapping asset into a pseudo-service layer.

Avoid it:
- Move sequencing and multi-step coordination into Integration Procedures.
- Use Apex where OmniStudio no longer fits cleanly.
