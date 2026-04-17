# LLM Anti-Patterns — Apex Managed Sharing Patterns

1. Inserting __Share rows in a before-trigger (record may not be committed → ghost shares)
2. Using RowCause='Manual' from Apex (platform may recalc and remove the row)
3. Per-record callouts inside a trigger to fetch the user list — always bulkify
4. Using 'All' access level when 'Read' suffices
5. Forgetting to write a negative test with runAs confirming revocation
