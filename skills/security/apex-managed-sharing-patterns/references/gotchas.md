# Gotchas — Apex Managed Sharing Patterns

## Gotcha 1: Row Cause not deployed

**What happens:** Insert throws INVALID_ROW_CAUSE; you cannot use RowCause until the sharing setting is enabled.

**When it occurs:** Fresh scratch org or missing metadata deploy.

**How to avoid:** Deploy <Object>.sharingModel + sharingSettings before the Apex class; validate in scratch org CI.


---

## Gotcha 2: Forgetting to revoke

**What happens:** Users keep access after leaving the team; compliance failure.

**When it occurs:** Delete handler on the driving object is missing.

**How to avoid:** Always pair insert/update with a delete handler that removes __Share rows with the matching RowCause.


---

## Gotcha 3: 'with sharing' misconception

**What happens:** Developer assumes 'with sharing' prevents managed-sharing inserts.

**When it occurs:** Service reuse across two callers.

**How to avoid:** 'with sharing' scopes SELECT; __Share DML is governed by Modify All / ownership only.

