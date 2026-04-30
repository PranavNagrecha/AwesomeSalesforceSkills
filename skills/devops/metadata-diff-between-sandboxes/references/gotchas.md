# Gotchas — Metadata Diff Between Sandboxes

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Profile XML drifts on every Setup UI visit

**What happens:** A diff between two stable orgs shows hundreds of differences in every profile, even though no one knowingly edited them.

**When it occurs:** Salesforce Setup auto-rewrites profile XML when an admin opens the Profile UI — adding implicit per-field permissions, reordering nodes, etc.

**How to avoid:** Add profiles to the diff-ignore list. Use a profile-aware diff tool (sfdx-hardis `org:diff:profile`) when profile drift is the actual subject.

---

## Gotcha 2: Some metadata types are not retrievable

**What happens:** The diff shows zero differences for a type you know diverges (e.g., `WaveDataset`, `OmniscriptDefinition`, `BusinessProcess` parts).

**When it occurs:** The Metadata API does not cover every metadata type uniformly. Some types are Tooling-API-only or partially retrievable.

**How to avoid:** Consult the Metadata API Coverage report (Salesforce help) before declaring "no drift." Treat absence of diff in unsupported types as "unknown," not "identical."

---

## Gotcha 3: Folder-bound types miss items in unenumerated folders

**What happens:** `Report:*` retrieves only items at the root and in folders explicitly named in the package.xml. Items in nested or unlisted folders are silently skipped.

**When it occurs:** Reports, Dashboards, EmailTemplates, Documents.

**How to avoid:** First retrieve folder lists, then retrieve items in each folder. Use `sf project list metadata` to enumerate before manifest-building.

---

## Gotcha 4: API-token expiry mid-retrieve

**What happens:** A 25-minute retrieve fails at minute 23 with `INVALID_SESSION_ID`.

**When it occurs:** The auth token's session timeout (often 2 hours) is fine, but a forced password change or admin's session-locked policy cancels mid-flight.

**How to avoid:** Use a long-lived integration user with API-only profile, no IP login restrictions, and a session policy aligned with retrieve duration.

---

## Gotcha 5: Custom labels are translation-aware

**What happens:** Two orgs both set the English version of `MyLabel__c` identically, but one has a French translation file. The diff reports the label as "changed."

**When it occurs:** Multi-language orgs.

**How to avoid:** Normalize on the source language when comparing custom labels, or split the diff into source-language and translation-language passes.
