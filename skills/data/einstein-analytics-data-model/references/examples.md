# Examples: Einstein Analytics Data Model (XMD)

The deployable artifacts (REST calls and the `WaveXmd` metadata file with its package.xml entry) are in `metadata-examples.md`. This file walks through two real situations.

## Example 1: Renaming cryptic field labels for every dashboard user

**Context:** A dataflow extracts Opportunity and Account. Fields such as `Owner.UserRole.Name` appear in charts under their API names.

**Problem:** Business users cannot read chart axes and filter lists.

**Solution:**

1. `GET /services/data/v67.0/wave/datasets/0Fb5e000000AbCdCAI` and copy `currentVersionId` (`0Fc5e000000WxYzCAI`).
2. `GET .../wave/datasets/0Fb5e000000AbCdCAI/versions/0Fc5e000000WxYzCAI/xmds/user` and save it as `xmd-user-backup-2026-10-03.json`.
3. Edit the saved document. Add or change the two labels and keep every other entry:

```json
{
  "dimensions": [
    { "field": "Owner.UserRole.Name", "label": "Rep Role", "showInExplorer": true },
    { "field": "Account.Industry", "label": "Industry Segment", "showInExplorer": true }
  ],
  "measures": [
    { "field": "Amount", "label": "Amount (USD)", "format": { "customFormat": "[\"$#,###,###.##\",1]" } }
  ]
}
```

4. `PUT` the full edited document to the same `xmds/user` URL.
5. Open a lens on the dataset and confirm the labels.

**Why it works:** `user` is the only XMD type the REST API lets you write, and every visualization on the dataset reads it. Sending the whole document avoids losing customizations, because the XMD guide says uploads overwrite rather than append.

---

## Example 2: A field label vanished after a recipe change

**Context:** `Annual_Revenue_Band__c` disappeared from filter lists after a recipe edit.

**Problem:** The recipe dropped the column. The XMD still referenced it.

**Solution:**

1. `GET /wave/datasets/<id>` and note the new `currentVersionId`.
2. `GET .../versions/<newVersionId>/xmds/system` and confirm the field is absent from the generated schema.
3. `GET .../versions/<newVersionId>/xmds/user` and read `errorMessage`. It reports problems copying the previous version's user XMD forward.
4. Restore the column in the recipe and rerun it, or remove the stale entry from the user XMD and PUT it back.

**Why it works:** Each run creates a new version with its own system XMD. The platform copies the user XMD forward and records failures in `errorMessage` instead of raising an alert.
