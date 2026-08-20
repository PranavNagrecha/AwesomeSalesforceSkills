# Local commit and tag plan

Cursor must make local commits only. It must not push, publish, create a pull request, submit a marketplace package, or alter remote configuration.

Suggested commit groups:

```text
chore(v2): preserve baseline and import SFAEF specification
feat(v2-core): add schemas, definitions, run state, context and evidence contracts
feat(v2-policy): add authority broker, target pinning and run bundles
feat(cursor): add native SfSkills plugin and local installer
feat(product): add deployment failure triage
feat(product): add Apex test failure triage
feat(qa): add context and evidence regression suites
feat(product): add access path explainer
feat(qa): add disposable scratch-org behavioral lab
feat(product): add flagship change, automation and release products
feat(product): add beta product portfolio
feat(adapters): add portability adapters and release package
chore(release): generate traceability, quality report and review bundle
```

Rules:

- no history rewriting after a review tag;
- no squashing evidence-bearing milestone commits before external review;
- generated artifacts in their own commit when useful for drift review;
- every tag resolves to a clean tree;
- preserve prior user work before cleanup or refactoring;
- commit messages do not claim live tests that were not run.
