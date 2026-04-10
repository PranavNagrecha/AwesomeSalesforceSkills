# Gotchas — Marketing Consent Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: MC Consent Management Integration Must Be Explicitly Enabled — It Is Not Automatic

**What happens:** After installing the Marketing Cloud Connect package and connecting MC to a Salesforce org, practitioners assume consent is flowing between the systems. It is not. The connector establishes a data sync for Contacts, Leads, and Campaigns, but the Consent Management feature — which causes MC to query CRM consent objects at send time — is a separate configuration step that must be explicitly enabled in the connector's Consent Management settings and mapped to Data Use Purpose records.

**When it occurs:** Every org that has MC connected to CRM but has not explicitly navigated to the Consent Management section of the connector setup and configured purpose mappings. This includes orgs that have been running for years with the connector active.

**How to avoid:** After enabling the connector, verify Consent Management is active by checking the Setup menu in MC for the Consent Management configuration. Confirm that at least one Data Use Purpose mapping exists. Run a test send to a subscriber with a CRM opt-out record and verify they are suppressed.

---

## Gotcha 2: HasOptedOutOfEmail on Individual vs. MC All Subscribers Are Independent Fields

**What happens:** When a subscriber unsubscribes via MC (click-to-unsubscribe, SafeUnsubscribe, REST API unsubscribe), the MC All Subscribers record `HasOptedOutOfEmail` flag is set to true. The corresponding Salesforce CRM `Individual.HasOptedOutOfEmail` field is **not** updated. The two fields are completely independent unless a writeback integration or custom process explicitly keeps them synchronized.

**When it occurs:** Any time a subscriber manages their consent preferences through MC channels (email unsubscribe link, MC preference center). Also occurs in reverse: when a CRM user updates `Individual.HasOptedOutOfEmail = true` for a Contact, the MC subscriber record is not automatically suppressed — the subscriber may continue to receive MC emails until the next sync cycle or until the Consent Management integration is active.

**How to avoid:** Treat CRM consent objects as the system of record. Configure the MC Consent Management integration to write MC unsubscribes back to CRM as ContactPointTypeConsent or ContactPointConsent records with `PrivacyConsentStatus = OptOut`. Monitor both fields in reconciliation reports weekly until the integration is validated as reliable.

---

## Gotcha 3: ContactPointTypeConsent OptOut Does Not Suppress All CRM Email Sends

**What happens:** Creating a ContactPointTypeConsent record with `ContactPointType = Email` and `PrivacyConsentStatus = OptOut` suppresses MC sends when the Consent Management integration reads it — but it does not automatically suppress emails sent directly from Salesforce CRM through other mechanisms (Apex `Messaging.sendEmail`, Flow Send Email action, Omni-Channel, or direct SMTP relay integrations). Those channels typically check `Contact.HasOptedOutOfEmail` (a legacy field) or `Individual.HasOptedOutOfEmail`, not the ContactPointTypeConsent objects.

**When it occurs:** Multi-channel orgs where email is sent from both MC and CRM-native tools. A customer opts out of marketing email and a ContactPointTypeConsent OptOut is recorded correctly, but a triggered Flow continues sending transactional emails because it checks `Contact.HasOptedOutOfEmail` which was not updated.

**How to avoid:** When a ContactPointTypeConsent record is created or updated to OptOut, use a trigger or Flow to also evaluate whether `Individual.HasOptedOutOfEmail` should be flipped — particularly for channels where coarse-grained suppression is acceptable. For orgs with strict per-purpose requirements, build custom validation into every email-sending path to query the appropriate ContactPointTypeConsent record before sending.

---

## Gotcha 4: Data Use Purpose Is Not Enforced — Records Save Without It

**What happens:** The Salesforce platform does not enforce that ContactPointTypeConsent records have a populated `DataUsePurpose` lookup. Records save successfully without it. Orgs frequently create thousands of consent records without a purpose assignment during initial data migration or rollout, making it impossible to perform purpose-scoped suppression later. MC Consent Management integration requires a purpose mapping to know which consent record to evaluate; if records lack a purpose, the integration may not suppress anyone (treating absence of a matching record as ambiguous, defaulting to send) or may suppress everyone depending on the connector configuration.

**When it occurs:** Initial bulk loads from legacy consent data where the source system had no concept of purpose, or when developers create ContactPointTypeConsent records in Apex/Flow without setting the DataUsePurpose field. Also occurs when non-architect contributors create records through standard UI without guidance.

**How to avoid:** Add a required Data Use Purpose field validation rule on ContactPointTypeConsent to prevent saving without a purpose. Pre-create Data Use Purpose records for all lawful bases before migrating consent data. Include DataUsePurpose as a mandatory field in all consent-capture Flows and Apex code.

---

## Gotcha 5: ContactPointConsent and ContactPointTypeConsent Have Different Parent Objects

**What happens:** Practitioners confuse the two consent objects. ContactPointTypeConsent has an `IndividualId` lookup — it links to an Individual record (the privacy pivot), not to a Contact or Lead directly. ContactPointConsent has a `ContactPointId` lookup — it links to a specific ContactPointEmail or ContactPointPhone record, which in turn links to an Individual. If you try to link ContactPointTypeConsent directly to a Contact's Id, the lookup will fail or store incorrectly, producing consent records that the integration cannot match to MC subscriber data.

**When it occurs:** When building consent record creation logic in Apex or Flow using Contact.Id instead of Contact.IndividualId as the parent for ContactPointTypeConsent. Also occurs during data migration when the source export contains Contact Ids and the load template incorrectly maps them to the IndividualId field.

**How to avoid:** Always resolve `Contact.IndividualId` (creating an Individual record first if it does not exist) before inserting ContactPointTypeConsent. In data migration scripts, include a pre-load step that creates Individual records for all Contacts in scope and populates the `IndividualId` field before any consent records are loaded.
