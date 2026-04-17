# LLM Anti-Patterns — Prompt Template Versioning

1. Hardcoding template DeveloperName in Flow/Apex — rollback requires redeploy.
2. Editing prompts in place — no diff, no rollback.
3. Skipping fixture tests 'because the change is small' — prompts amplify small changes.
4. Relying on author memory for what changed between versions.
5. Flipping production on Friday — allow one full working day of canary.
