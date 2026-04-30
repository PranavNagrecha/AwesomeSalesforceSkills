# Gotchas — Mass Transfer Ownership

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: User deactivation blocks while records remain

**What happens:** Admin clicks Deactivate; Salesforce returns "User is currently the default owner of records." Deactivation refuses.

**When it occurs:** The departing user owns at least one active record, or is configured as a default queue/case-owner anywhere in Setup.

**How to avoid:** Always reassign first, then deactivate. Build a pre-deactivation checklist that queries each owned-record source.

---

## Gotcha 2: Sharing recalc continues after the apparent success

**What happens:** Data Loader returns "Operation finished successfully" in 8 minutes. Forty-five minutes later, users still can't see records they own. Help desk lights up.

**When it occurs:** Whenever the org-wide default for the transferred object is Private and the volume exceeds tens of thousands of records.

**How to avoid:** Communicate the recalc lag to stakeholders. Use deferred sharing calculations for >100k. Monitor Setup → Background Jobs for "Sharing Rule Recalculation" to drain before declaring done.

---

## Gotcha 3: Data Loader updates do not cascade

**What happens:** Account.OwnerId is updated for 5,000 Accounts. Child Cases retain the old owner. Reports filtered by Case.Owner show wrong attribution.

**When it occurs:** Whenever a parent OwnerId change is done via Data Loader or API rather than the Mass Transfer Records UI.

**How to avoid:** Plan child-object passes explicitly. Build a checklist per parent that lists every child object whose OwnerId should follow.

---

## Gotcha 4: Triggers and assignment rules fire on transfer

**What happens:** A Lead reassignment triggers the Lead assignment rule, which immediately reroutes the Leads back via round-robin. Effective transfer: zero.

**When it occurs:** Any DML update where `AssignmentRuleHeader` is set (default in Data Loader UI for Lead/Case).

**How to avoid:** Uncheck "Use Assignment Rule" in Data Loader, or omit `AssignmentRuleHeader` in Apex. For triggers, gate them on a custom-setting flag your team toggles during migrations.

---

## Gotcha 5: Queue OwnerId requires the object to support queues

**What happens:** Setting `OwnerId = '00G...'` on a custom object returns `INVALID_OWNER`.

**When it occurs:** The object's "Allow Queues" setting is off in Setup.

**How to avoid:** Verify Setup → Object Manager → \[Object\] → Allow Queues is enabled before targeting Queue IDs in the transfer.
