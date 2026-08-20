# First fifteen minutes

## Target experience

### Minute 0–3: install

Run one local helper or symlink a generated plugin into the current Cursor local-plugin directory. The installer refuses unrelated overwrite and prints reload/uninstall commands.

### Minute 3–5: verify

Reload Cursor and run `/sfskills-doctor`. The user sees plugin/runtime/definitions/MCP/Salesforce CLI/index/host capability status without secrets.

### Minute 5–10: fixture product

Invoke `/triage-deployment` on an included fixture. No org or Salesforce project is required. The result shows target mode, grouped causes, evidence IDs, safe next steps, unknowns, and independent review.

### Minute 10–15: inspect trust

Open the run bundle, evidence index, context manifest, and replay command. The user can see what the system loaded and why.

## Optional enrichment after first value

- provide an explicit external Salesforce project path;
- select an explicit authorized org alias;
- provide an existing deployment or Apex test run ID;
- compare with vanilla host/raw evidence.

## Failure UX

Every failed onboarding step gives a concrete command and state. Missing index is `index_missing`, not zero results. Missing Salesforce CLI does not block fixture mode. No org produces standalone mode. Multiple projects/orgs produce ambiguity, not guessing.
