# Gotchas: Einstein Analytics Data Model (XMD)

Non-obvious CRM Analytics behaviors that cause real production problems in this domain. Each one names the official source it rests on.

## Gotcha 1: Only the user XMD type is writable through REST

**What happens:** A PUT to `xmds/main` or `xmds/system` is rejected. There is no PATCH method on the Xmd resource at all.

**When it occurs:** When a script follows older advice to "PATCH main XMD" for org-wide labels.

**How to avoid:** Write to `PUT /wave/datasets/<datasetID>/versions/<versionID>/xmds/user`. Read system and main for reference only.

**Source:** CRM Analytics REST API Developer Guide (262), "Xmd Resource": HTTP methods "GET PUT (on Xmd User type only)" and "The PUT request cannot be used to update System or Main Xmd types." The HTTP status code returned for a rejected write is UNVERIFIED (2026-10-03).

---

## Gotcha 2: XMD belongs to a dataset version, not to the dataset

**What happens:** A script that cached a version ID edits a version that dashboards no longer read. The change looks successful and nothing changes on screen.

**When it occurs:** After any dataflow or recipe run creates a new version between the time the ID was captured and the PUT.

**How to avoid:** Read `currentVersionId` from `GET /wave/datasets/<datasetIdOrApiName>` immediately before every XMD call.

**Source:** CRM Analytics REST API Developer Guide (262), "Xmd Resources" (all URLs include `/versions/<versionId>/`) and the Dataset response body (`currentVersionId`).

---

## Gotcha 3: An upload replaces the XMD, and an invalid one wipes all formatting

**What happens:** Customizations missing from the uploaded file disappear. If the file fails validation, the guide says the updated settings are not applied and all formatting reverts to the defaults.

**When it occurs:** When someone uploads a partial file or a file with a JSON or validation error on the Edit Dataset page.

**How to avoid:** Always start from a GET of the current user XMD, edit the whole document, validate the JSON, and keep the pre-change copy. XMD has no version history to roll back to.

**Source:** Analytics Extended Metadata (XMD) Developer Guide (262), "Configure the XMD for a Dataset": "Each time you upload the XMD file, CRM Analytics overwrites the current dataset customizations. Changes in the XMD aren't appended to previous customizations." UNVERIFIED (2026-10-03): whether a partial body sent through the REST PUT behaves the same way.

---

## Gotcha 4: The version-bound user XMD cannot be packaged

**What happens:** Formatting built in a sandbox does not arrive in production with the release.

**When it occurs:** When the team relies on the Standard User XMD and expects a change set or package to carry it.

**How to avoid:** Deploy the `WaveXmd` metadata type, which sets the Primary User XMD on the dataset container. Then run the dataflow, because the Primary User XMD applies only after a dataflow that updates the dataset runs.

**Source:** XMD Developer Guide (262), "Packaging Considerations for XMD"; Metadata API Developer Guide (262), "WaveXmd" (suffix `.xmd`, `wave` folder, API 39.0 and later).

---

## Gotcha 5: MDAPI retrieve returns an empty WaveXmd after a UI or REST edit

**What happens:** A retrieve of `WaveXmd` brings back an empty file, and the next deploy from source control erases formatting.

**When it occurs:** When anyone updates the Primary User XMD through REST, or the Standard User XMD through the UI or REST, even if the file was first deployed with MDAPI.

**How to avoid:** Pick one owner for each dataset's XMD. If source control owns it, make all changes in the `WaveXmd` file and deploy. Never treat an empty retrieve as the truth.

**Source:** XMD Developer Guide (262), "Packaging Considerations for XMD."

---

## Gotcha 6: Hidden fields are still queryable

**What happens:** A field set to `showInExplorer: false` disappears from the explorer and dashboard designer, but a user can still add it in dashboard JSON or SAQL, or read it through the REST API.

**When it occurs:** When an admin hides a salary or margin field to keep it from viewers.

**How to avoid:** Build a dataset without the column, or restrict who can open the dataset. A security predicate filters rows, not columns. Use `showInExplorer` only to declutter.

**Source:** XMD Developer Guide (262), "Hide Dataset Fields from the Explorer and Dashboard Designer" and "Measures and Derived Measures in XMD."

---

## Gotcha 7: A multi-dataset query uses only the first dataset's XMD

**What happens:** Labels and number formats defined on the second dataset do not appear on a widget that blends two datasets.

**When it occurs:** On SAQL steps that `load` more than one dataset, for example with `cogroup`.

**How to avoid:** Put the formatting on the dataset loaded first, or copy the relevant XMD entries to it.

**Source:** XMD Developer Guide (262), "Format the Results of a Query with Multiple Datasets."

---

## Gotcha 8: Downloads ignore some formatting

**What happens:** Custom thousands and decimal delimiters do not appear in CSV downloads. A measure with a multiplier of 0 downloads every value as 0.

**When it occurs:** When users export a table to CSV or .xls.

**How to avoid:** Avoid a 0 multiplier. Tell users that exported numbers use default delimiters.

**Source:** XMD Developer Guide (262), "Measures and Derived Measures in XMD" (delimiters) and "Multiply Measures by a Fixed Amount" (0 multiplier note).

---

## Gotcha 9: Schema changes break XMD entries, and the signal is a field, not an alert

**What happens:** After a dataflow renames or drops a field, XMD entries refer to a field that no longer exists. Configuring actions in the UI fails, and the error text sits in the `errorMessage` property of the XMD.

**When it occurs:** On the first run after a recipe or dataflow schema change.

**How to avoid:** After schema-changing runs, GET the new version's user XMD and check `errorMessage`. Remove or rename the stale entries.

**Source:** XMD Developer Guide (262), "Configure the XMD for a Dataset" (final paragraph); CRM Analytics REST API Developer Guide (262), Xmd response body, `errorMessage`.

---

## Gotcha 10: Some date settings are no longer read from XMD

**What happens:** `firstDayOfWeek` and `fiscalMonthOffset` set in the XMD `dates` section have no effect.

**When it occurs:** When a team tries to fix a fiscal calendar through XMD.

**How to avoid:** Set them in the sfdcDigest transformation for Salesforce data, or in the metadata (schema) file for CSV uploads.

**Source:** XMD Developer Guide (262), "Dates in XMD": both parameters are "deprecated at the dataset level."
