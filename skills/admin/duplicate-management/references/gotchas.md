# Gotchas: Duplicate Management

---

## Alert Fatigue Kills Good Rules

**What happens:** Users see duplicate alerts constantly and learn to ignore them. Duplicates still enter the org, but leadership thinks there is protection because banners exist.

**When it bites you:** Contact creation, lead intake, and call-center processes with high record volume.

**How to avoid it:** Reserve alerts for cases with a clear review path, and block obvious duplicates when confidence is high.

---

## Matching on a Field Users Can Change

**What happens:** A field like email or account name is treated as the primary identity key even though users edit it freely or leave it blank.

**When it bites you:** Imports, integrations, and sales-data cleanup.

**How to avoid it:** Use stronger identifiers where possible and understand where fuzzy matching is helping versus hiding identity weakness.

---

## Merging Without Survivorship Rules

**What happens:** Different admins merge records differently. The "winner" changes based on who did the merge.

**When it bites you:** Historical cleanup projects and steward queues.

**How to avoid it:** Define record and field survivorship before bulk remediation starts.

---

## Duplicate Rules Ignore System-Created Data

**What happens:** UI entry is fairly clean, but integrations and bulk loads still create duplicate Accounts and Contacts.

**When it bites you:** Middleware retries, migration reruns, and batch imports.

**How to avoid it:** Coordinate duplicate management with integration keys, External IDs, and migration controls.
