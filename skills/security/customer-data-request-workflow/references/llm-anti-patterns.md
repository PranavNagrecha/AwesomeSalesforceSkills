# LLM Anti-Patterns — Customer Data Subject Request (DSR) Workflow

1. Running a hard `DELETE FROM Contact WHERE Email=…` query with no audit
2. Using the UI 'Delete' button for high-volume DSR — not repeatable, no audit
3. Ignoring analytics (CRMA) caches that retain PII in datasets
4. Skipping the sandbox dry run
5. Treating every request the same — access and deletion have different SLAs and scopes
