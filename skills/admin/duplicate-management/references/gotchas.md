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

---

## Matching Rules Silently Degrade Without Field-Level Access

**What happens:** Salesforce documents this directly: if a user who updates a record doesn't have access to one or more fields referenced in a matching rule, the duplicate rule doesn't work as expected. Nothing surfaces the mismatch — Setup still shows the rule as active, and the user saves a duplicate without an alert.

**When it bites you:** The classic report is "duplicate rules work for admins but not for reps." The admin has full field access and sees correct behavior every time they test. The rep is missing FLS on one field in the matching rule — often a phone or an email variant added later — and detection is off for that user on that object.

**How to avoid it:** Treat the matching rule's field list as a permission dependency. When you add a field to a matching rule, audit FLS for every profile and permission set that creates or edits the object. Reproduce reported failures as the affected user, not as an admin. This is also why a matching rule with a wide field list is operationally more fragile than a narrow one, independent of match quality.

---

## Named Create Paths That Never Evaluate Duplicate Rules

**What happens:** A duplicate rule is active, correct, and thoroughly tested, and duplicates keep arriving. The records are being created through paths that do not run duplicate rules at all.

**When it bites you:** The documented list includes Quick Create, Community Self-Registration, Lightning Sync, Einstein Activity Capture, manual merge, undelete from the Recycle Bin, and lead conversion when "Use Apex Lead Convert" isn't enabled. An org with a self-registering community can have its single largest duplicate source sitting entirely outside the control it believes is protecting it. Undelete is the quietest of these: restoring a record you deleted as a duplicate re-creates the duplicate without re-evaluation.

**How to avoid it:** Inventory create paths per object before trusting a rule. For paths on the skip list, move the control upstream — an External ID with an idempotent upsert, or an explicit pre-insert check inside the integration. Do not report duplicate coverage as a percentage of rules active; report it as a percentage of create paths covered.

---

## Match Keys Cap the Comparison Set at 100 Candidates

**What happens:** Match keys run a preliminary comparison that narrows evaluation to the 100 most likely duplicate records before the matching rule's algorithms run. A true duplicate outside that window is never scored.

**When it bites you:** High-collision values. Ten thousand Contacts named "John Smith", an Account named "Consulting", a shared corporate switchboard number. The rule is not wrong; the candidate set never contained the record.

**How to avoid it:** Design matching rules whose leading fields have high selectivity. When a common value is unavoidable, pair it with a discriminating field so the match key narrows on something real. Do not conclude from a single missed match that fuzzy thresholds need loosening — loosening thresholds does not widen the candidate set, it only adds false positives inside it.

---

## Standard Fuzzy Methods Are Tuned for North American Data

**What happens:** Salesforce states that Fuzzy: Phone and Fuzzy: Street work best with North American data. Fuzzy: Last Name leans on Metaphone 3, a phonetic algorithm built around English pronunciation. Fuzzy: Company Name strips terms like "Inc" and "Corp" before comparing.

**When it bites you:** International rollouts. Non-NANP phone numbers, addresses whose street type does not precede or follow the name in the expected position, surnames whose phonetics English-language Metaphone was never designed for, and companies suffixed GmbH, S.A., Pty Ltd, or 株式会社 rather than Inc. Detection rates drop by region without any signal that a region is the variable.

**How to avoid it:** Normalize before matching — E.164 for phone, a consistent address standard for street. Measure detection rate per country rather than per object; an org-wide match rate can hide a near-total failure in one geography. Where standard fuzzy methods underperform, reach for an exact match on a normalized field instead of a fuzzy match on a raw one.

---

## Bypass Sharing Changes What "Detection" Means

**What happens:** A duplicate rule set to bypass sharing rules operates on all potential duplicates regardless of ownership. When a rep creates a record matching one they cannot access, Salesforce alerts or blocks according to the rule's settings but does not display the record the rep lacks access to.

**When it bites you:** Two ways, in opposite directions. Leave it off in a private-OWD org and reps create duplicates of records they cannot see — the rule is doing exactly what you told it to. Turn it on without warning anyone and a rep hits a block on a record that, as far as they can tell, does not exist. Support tickets follow.

**How to avoid it:** Decide this deliberately per rule and write the decision into the governance template. If you bypass sharing, the alert text has to carry the weight the record itself cannot: tell the user a match exists, who to contact, and what to do next. For Apex-initiated DML, `Database.DMLOptions.DuplicateRuleHeader.runAsCurrentUser` is the per-transaction equivalent of this decision.
