# LLM Anti-Patterns — OAuth Redirect / Domain

## Anti-Pattern 1: Wildcard Callback

**What the LLM generates:** `https://*.app.acme.com/callback`.

**Why it happens:** "save on env-specific config."

**Correct pattern:** exact match, one per env. Wildcards are not
supported.

## Anti-Pattern 2: login.salesforce.com For Sandbox

**What the LLM generates:** sandbox client points to
`login.salesforce.com`.

**Why it happens:** copy-paste from prod config.

**Correct pattern:** sandboxes use `test.salesforce.com` or,
preferably, the sandbox's own My Domain.

## Anti-Pattern 3: Trailing Slash Drift

**What the LLM generates:** Connected App has `/callback`; client posts
`/callback/`.

**Why it happens:** cosmetic variance.

**Correct pattern:** match exactly — including trailing slash and
query-string absence.

## Anti-Pattern 4: Hardcoded Visualforce URL

**What the LLM generates:** Apex builds links with
`https://c.na123.visual.force.com/...`.

**Why it happens:** trained on pre-Enhanced-Domains patterns.

**Correct pattern:** derive base URL from `URL.getOrgDomainUrl()` or
similar. No hardcoded instance names.

## Anti-Pattern 5: No Post-Refresh Reconfigure

**What the LLM generates:** "Connected App is deployed, done."

**Why it happens:** unaware of refresh reset.

**Correct pattern:** runbook to reapply sandbox callbacks after every
sandbox refresh.
