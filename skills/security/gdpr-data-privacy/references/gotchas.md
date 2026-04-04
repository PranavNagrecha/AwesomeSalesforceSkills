# Gotchas — GDPR Data Privacy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ShouldForget=true Is a Flag, Not an Action

**What happens:** A developer sets `Individual.ShouldForget = true` on the Individual record linked to a data subject who submitted an erasure request. They then close the DSR ticket, assuming Salesforce has handled the deletion. Personal data remains fully intact in Contact, Lead, and all related objects.

**When it occurs:** Any time `ShouldForget` is set without a corresponding automation. This is especially common in orgs that read about the Individual object in Salesforce documentation and assume the platform responds to the flag natively.

**How to avoid:** Treat `ShouldForget = true` as a queue entry, not an execution. Always pair the flag with either a Privacy Center Erasure Policy (which monitors the flag and runs the policy) or a scheduled/triggered Batch Apex class that queries `Individual WHERE ShouldForget = true` and anonymizes linked records. Verify that the automation runs in a sandbox before relying on it in production.

---

## Gotcha 2: IndividualId Is Not Populated by Default

**What happens:** An org implements the RTBF batch but finds it affects zero records. Querying `Contact WHERE IndividualId != null` returns an empty set even though thousands of Contacts exist. The Individual object was never populated, and the linkage field was never set.

**When it occurs:** New Contacts created after GDPR adoption may have Individual records if an automation was built, but Contacts created before the rollout have `IndividualId = null`. The erasure batch uses `WHERE IndividualId IN :individualIds`, so it silently skips all pre-existing Contacts with no linkage.

**How to avoid:** After implementing Individual linkage, run a one-time data migration: for each Contact without an `IndividualId`, create an Individual record and set the field. For high volumes, use a Batch Apex migration job rather than a data loader, to stay within DML limits. After migration, verify coverage with: `SELECT COUNT() FROM Contact WHERE IndividualId = null`.

---

## Gotcha 3: Hard-Deleting Contacts Breaks Opportunity and Case Foreign Keys

**What happens:** An erasure implementation deletes Contact records directly. Opportunities with `ContactId` set to the deleted Contact now display "(deleted)" or null in the Contact field. In some configurations, the delete fails with a `CHILD_RECORD_FOUND` exception if any related object has a Master-Detail relationship to Contact.

**When it occurs:** Any time hard delete is used without first checking for related records. Leads linked via converted lead records, Tasks with `WhoId` pointing to the Contact, and Email Message associations are also affected.

**How to avoid:** Anonymize personal data fields on Contact rather than deleting the record. Replace `FirstName`, `LastName`, `Email`, `Phone`, `Birthdate`, and address fields with a non-identifying token (e.g., `ANON-<timestamp>`). Delete the record only if a pre-check query confirms zero related records across Opportunity, Case, Task, Event, EmailMessage, and any custom objects with Contact lookups. Use `Database.delete(contact, false)` (allOrNone=false) to capture partial failures rather than letting unhandled exceptions abort the batch.

---

## Gotcha 4: Consent Records Are Not Checked Automatically at Send Time

**What happens:** A team creates `ContactPointTypeConsent` records with `OptInStatus = OptOut` for a group of data subjects. They then send a Marketing Cloud journey or a mass email via Salesforce campaigns. The send proceeds regardless; the consent records have no native enforcement at send time.

**When it occurs:** Any time the consent model is built without integration with the email-sending channel. Salesforce consent objects record intent but do not automatically suppress sends in Salesforce campaigns, Marketing Cloud journeys, or third-party ESPs unless explicit suppression logic is built.

**How to avoid:** Build suppression into the send workflow. For Salesforce campaigns, filter the campaign member list using a SOQL join against `ContactPointTypeConsent WHERE OptInStatus = 'OptOut'`. For Marketing Cloud, sync the consent objects to Marketing Cloud via Connected App or Data Cloud and configure suppression lists. Never assume the consent record silently enforces suppression.

---

## Gotcha 5: EffectiveFrom and EffectiveTo Are Not Validated by the Platform

**What happens:** A developer populates `EffectiveFrom` and `EffectiveTo` on `ContactPointTypeConsent` with arbitrary dates — sometimes defaulting to null, sometimes using `CreatedDate`, sometimes using future dates that represent the next re-consent deadline. Downstream analytics and audits produce inconsistent results because the fields are not normalized.

**When it occurs:** Any time consent records are created programmatically without enforcing a convention. The platform does not validate that `EffectiveFrom <= EffectiveTo`, does not reject null `EffectiveFrom`, and does not alert when a consent record's `EffectiveTo` is in the past (i.e., the consent has expired).

**How to avoid:** Enforce field population in a validation rule or trigger: `EffectiveFrom` must be non-null and must be the actual consent capture date (not `TODAY()` as a default placeholder). If consent is bounded, set `EffectiveTo` explicitly. Build a scheduled report or flow that flags `ContactPointTypeConsent` records where `EffectiveTo < TODAY()` and `OptInStatus = 'OptIn'` — these represent expired consent that may still be silently treating the subject as opted in.
