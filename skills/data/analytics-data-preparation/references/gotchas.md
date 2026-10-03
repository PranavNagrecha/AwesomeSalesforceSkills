# Gotchas: Analytics Data Preparation (XMD Metadata and External Data)

Non-obvious behaviours that erase formatting, break deployments, or drop external rows. Each gotcha names its source. "REST Guide" means the CRM Analytics REST API Developer Guide, Summer '26 (bi_dev_guide_rest.pdf). "XMD Guide" means the Analytics Extended Metadata (XMD) Developer Guide, Summer '26 (bi_dev_guide_xmd.pdf). "External Data Guide" means the Analytics External Data API Developer Guide, Summer '26 (bi_dev_guide_ext_data.pdf). "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: The XMD Resource Has No PATCH, and Only the User Type Is Writable

**What happens:** A script sends `PATCH /wave/datasets/{id}/xmds/main` with a small JSON body and gets an error, or a script built on that assumption never changes anything.

**When it occurs:** Whenever the earlier advice in this skill (PATCH main XMD as an additive merge) is followed. The REST guide lists the XMD resource as `/wave/datasets/<datasetID>/versions/<versionID>/xmds/<xmdType>` with methods "GET PUT (on Xmd User type only)," and says "The PUT request cannot be used to update System or Main Xmd types."

**How to avoid:** Read the current version ID from the Dataset resource, GET the user XMD on that version, edit it, and PUT the complete document back to `.../xmds/user`. For deployable changes, use WaveXmd (Gotcha 3).

**Source:** REST Guide, Xmd Resources table; Xmd Resource (Resource URL, HTTP Methods, PUT request note).

---

## Gotcha 2: Every Upload Overwrites the Whole XMD

**What happens:** A PUT containing only the two changed labels wipes every other label, format, color, and action on the dataset.

**When it occurs:** "Each time you upload the XMD file, CRM Analytics overwrites the current dataset customizations. Changes in the XMD aren't appended to previous customizations. Ensure that your XMD file contains all required customizations." If the uploaded XMD is invalid, "the updated XMD settings aren't applied. All formatting reverts to the defaults."

**How to avoid:** Always start from a fresh GET of the current user XMD, change only the target entries, keep everything else, and validate the JSON before sending it. Keep the pre-change copy in source control so a revert is one PUT.

**Source:** XMD Guide, Configure the XMD for a Dataset, step 5 and its notes.

---

## Gotcha 3: Version-Bound XMD Does Not Deploy; the Primary User XMD Applies Only After a Dataflow Run

**What happens:** Labels perfected in a sandbox are missing in production after deployment, or a WaveXmd deploy succeeds and the dashboards still show API names.

**When it occurs:** "The Standard User XMD file can't be used in a Salesforce package because it's tied to a dataset version that isn't packageable." The Primary User XMD "is applied to a dataset only after a dataflow that updates the dataset runs."

**How to avoid:** Put deployable formatting in WaveXmd (Primary User XMD), deploy it, then run the dataflow or recipe that updates the dataset. Add that run to the deployment runbook. Changes to the Primary User XMD don't affect the Standard User XMD until that run.

**Source:** XMD Guide, Packaging Considerations for XMD.

---

## Gotcha 4: A REST or UI Edit Makes the Next Metadata API Retrieve Return an Empty XMD

**What happens:** A developer retrieves WaveXmd to capture production formatting and gets an empty file, then deploys it and loses the labels.

**When it occurs:** "An MDAPI retrieve operation returns the Primary User XMD file only if the file was deployed using MDAPI." Updating the Primary User XMD through REST, or the Standard User XMD through the UI or REST, makes the retrieve "return an empty XMD file... even if the files were originally deployed using MDAPI."

**How to avoid:** Choose one write path per dataset. If the Metadata API owns it, forbid UI and REST edits to that dataset's XMD. Before deploying a retrieved WaveXmd, check it is not empty.

**Source:** XMD Guide, Packaging Considerations for XMD.

---

## Gotcha 5: Hidden Fields Are Still Reachable

**What happens:** A salary field is hidden from the explorer, and an analyst still pulls it with a SAQL step.

**When it occurs:** "Although hidden fields aren't available in the interface, users can still manually add them in dashboard JSON and SAQL queries. Users can also access the fields with the CRM Analytics REST API."

**How to avoid:** Treat `showInExplorer: false` as tidiness. Keep sensitive fields out of the dataset, or protect rows with a security predicate.

**Source:** XMD Guide, Hide Dataset Fields from the Explorer and Dashboard Designer (note).

---

## Gotcha 6: Renamed or Deleted Fields Leave the XMD Pointing at Nothing

**What happens:** After a dataflow change renames a field, configuring dimension actions in the UI throws errors, and the old labels disappear from the renamed field.

**When it occurs:** "If the dataset metadata changes after you configure the XMD, such as a field is deleted or renamed as a result of changes to the dataflow, you must update the associated XMD." The error also appears in the XMD's `errorMessage` field.

**How to avoid:** Review the XMD in the same change as any dataflow or recipe rename. Search the XMD for every old field name before deploying the data change.

**Source:** XMD Guide, Configure the XMD for a Dataset (closing paragraph).

---

## Gotcha 7: A CSV Without a Header Row Loses the First Row of Every Part

**What happens:** An external upload of 100 MB in ten parts is short by ten rows.

**When it occurs:** "If you are uploading a CSV file without a header row, you must set the numberOfLinesToIgnore value to 0 in the metadata file. If you don't set this value, the first row of every data part upload may be lost." Without a metadata file at all, "every field is treated as text." The metadata `fields` "must be in the same order as the CSV columns."

**How to avoid:** Always send a metadata JSON. Set `numberOfLinesToIgnore` explicitly (1 with a header, 0 without), and generate the `fields` array from the CSV header so order cannot drift.

**Source:** External Data Guide, Configure the Upload; External Data Metadata Overview; External Data Metadata Format Reference (The Fields Section note).

---

## Gotcha 8: Numeric Fields Need a Default, and Only One Text Field Can Be the Unique ID

**What happens:** An upload fails on a numeric column, or an upsert matches nothing.

**When it occurs:** "All numeric types require a default value." Precision "can be up to 18," and scale "must be less than the precision value." For `isUniqueId`: "Only 1 field can be set to be the unique ID. Only text fields can be unique IDs." It "is required for incremental extract." Field names "can contain only alphanumeric and underscore characters," must begin with a letter, can't end with an underscore, and can't contain two consecutive underscores except a trailing `__c`.

**How to avoid:** Run the skill checker on the metadata JSON before upload. Pick a text business key as the single unique ID before choosing Upsert or Incremental mode.

**Source:** External Data Guide, External Data Metadata Format Reference (defaultValue, isUniqueId, precision, scale, Field Name Restrictions).

---

## Gotcha 9: External Data Jobs Are Limited Per Dataset Per Day

**What happens:** An hourly feed stops loading in the afternoon.

**When it occurs:** The External Data Guide lists a maximum of 50 external data jobs per dataset in a rolling 24-hour period, 40 GB per upload, and 50 GB across all uploads in a rolling 24 hours. Parts must be under 10 MB; compressed data "must be compressed first and then split into 10-MB chunks. Only the gzip format is supported."

**How to avoid:** Batch the feed into fewer, larger uploads, and use `Mode` Incremental with Append for faster loads. Budget the 50 jobs across every process that writes to the dataset.

**Source:** External Data Guide, External Data API Limits; Add the Data; Update the Data.

---

## Gotcha 10: Official Samples Contain Syntax Errors

**What happens:** A WaveXmd file copied from the Metadata API guide fails to deploy, or an external metadata JSON copied from the External Data Guide fails to parse.

**When it occurs:** The Metadata API WaveXmd sample opens `<dimesions>` and closes `</dimensions>`. The External Data Guide's JSON example is missing commas after `"fieldsEscapedBy":""` and `"linesTerminatedBy":"\r\n"`, and has a trailing comma after `"scale": 2`. Separately, "XMD doesn't support empty strings."

**How to avoid:** Never paste samples verbatim. Parse every XML and JSON file before upload or deploy; the skill checker does this and flags empty strings in XMD.

**Source:** Metadata API, WaveXmd Declarative Metadata Sample Definition. External Data Guide, External Data Metadata Overview (JSON Example). XMD Guide, Basic Structure of the XMD JSON File.
