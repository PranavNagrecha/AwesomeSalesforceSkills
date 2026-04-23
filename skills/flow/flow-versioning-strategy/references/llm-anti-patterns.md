# LLM Anti-Patterns — Flow Versioning

## Anti-Pattern 1: Breaking Change As A Version Bump

**What the LLM generates:** renames a required input, bumps version,
activates.

**Why it happens:** treats versions as generic "new revision."

**Correct pattern:** breaking changes are a new flow, not a new version.

## Anti-Pattern 2: Delete-All Old Versions

**What the LLM generates:** cleanup script deletes all non-active
versions.

**Why it happens:** "housekeeping."

**Correct pattern:** retain last 3 inactive; never delete a version
with paused interviews.

## Anti-Pattern 3: Rollback By Redeploy

**What the LLM generates:** "redeploy the previous flow metadata."

**Why it happens:** standard dev instinct.

**Correct pattern:** activate the prior inactive version. Faster and
safer.

## Anti-Pattern 4: Rename Variables Without Caller Audit

**What the LLM generates:** rename with "find/replace."

**Why it happens:** refactor instinct.

**Correct pattern:** search every caller (Apex, LWC, other Flows,
OmniScripts) before renaming; decide breaking vs non-breaking.

## Anti-Pattern 5: Ignore Paused Interview Age

**What the LLM generates:** "delete versions older than 30 days."

**Why it happens:** simple rule.

**Correct pattern:** age is measured from the drain of the last
paused interview on the version, not from the version's creation.
