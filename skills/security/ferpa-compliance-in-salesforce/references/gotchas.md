# Gotchas — FERPA Compliance in Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LearnerProfile FERPA Booleans Do Not Enforce Anything

**What happens:** Administrators set `HasFerpaParentalDisclosure = true` or `HasFerpaThrdPtyDisclosure = true` on LearnerProfile and assume that Salesforce will automatically permit or restrict data access based on these flags. Nothing changes — data is still accessible or restricted based solely on profile permissions, FLS, and sharing rules.

**When it occurs:** Every initial FERPA implementation that treats these fields as enforcement controls rather than informational flags.

**How to avoid:** Build explicit automation (Flow, Apex trigger, or sharing rules) that reads these flags and takes action — restricting visibility, filtering query results, or suppressing records from Experience Cloud pages. The flags are inputs to your compliance logic, not the logic itself.

---

## Gotcha 2: FERPA Rights Transfer Is Not Age-Triggered by the Platform

**What happens:** A student turns 18 or enrolls in a postsecondary institution, but `HasParentalFerpa` remains `true` on their LearnerProfile. Parents continue to receive access to education records they should no longer see, because no automation detected the rights-transfer event.

**When it occurs:** Any org that does not have a scheduled job checking student age or enrollment status against the FERPA rights-transfer threshold.

**How to avoid:** Build a Scheduled Flow or Batch Apex job that runs daily or weekly. Query LearnerProfile records where the associated Contact's Birthdate indicates the student is now 18+ (or where enrollment status indicates postsecondary). Update `HasParentalFerpa = false` and revoke any parent-facing sharing rules or portal access that depended on parental FERPA rights.

---

## Gotcha 3: Individual.ShouldForget Triggers GDPR Erasure, Not FERPA Amendment

**What happens:** An admin processing a FERPA amendment request sets `ShouldForget = true` on the student's Individual record. If the org has GDPR automation (Privacy Center or Batch Apex responding to this flag), the student's personal data is anonymized or deleted — destroying education records that FERPA requires the institution to maintain.

**When it occurs:** Orgs that handle both GDPR and FERPA, where staff are trained on one regulation but not the other.

**How to avoid:** Never use `ShouldForget` for FERPA requests. Create a separate Case record type or custom object for FERPA amendment requests. Train staff on the distinction: GDPR Article 17 = erasure; FERPA = amendment or annotation, with mandatory record retention.

---

## Gotcha 4: Directory Information Opt-Out Must Be Honored Across All Channels

**What happens:** A student opts out of directory information disclosure. The admin updates the student's Contact record or LearnerProfile, but forgets to suppress the student from the institution's online student directory (Experience Cloud), commencement lists, or third-party integrations that export directory data.

**When it occurs:** Orgs where directory information is surfaced through multiple channels — Experience Cloud pages, external integrations, report exports, and Marketing Cloud sends — and the opt-out flag is only checked in one place.

**How to avoid:** Treat the opt-out as a data-layer filter, not a UI-layer filter. Add the opt-out check to every SOQL query, report filter, Experience Cloud component, and integration callout that surfaces directory information. Use a centralized utility class or Flow that checks the flag before any directory data is returned.

---

## Gotcha 5: ContactPointTypeConsent EffectiveTo Expiry Is Not Auto-Enforced

**What happens:** A parental disclosure consent record has `EffectiveTo = 2025-06-30`. After that date, the consent should no longer be valid, but the LearnerProfile `HasFerpaParentalDisclosure` flag remains `true` because no automation checked the expiry date.

**When it occurs:** Any implementation that creates time-bounded consent records but does not build a scheduled job to check for expired consent.

**How to avoid:** Build a Scheduled Flow or Batch Apex job that runs daily. Query ContactPointTypeConsent records where `EffectiveTo < TODAY()` and `OptInStatus = 'OptIn'`. For each expired record, update the linked LearnerProfile FERPA booleans to `false` and optionally notify the registrar that consent has lapsed and must be re-obtained.

---

## Gotcha 6: PersonAccount vs. Contact Confusion in Higher Education Orgs

**What happens:** Some Education Cloud implementations use PersonAccounts for students instead of plain Contacts. The `IndividualId` field exists on both Contact and PersonAccount, but LearnerProfile links to Contact. If the org uses PersonAccounts, the Contact portion of the PersonAccount must be the link target — not the Account portion. Queries that filter on `Account.IndividualId` will return nothing because `IndividualId` lives on the Contact side.

**When it occurs:** Orgs that adopted PersonAccounts for their student population before implementing FERPA compliance.

**How to avoid:** Always query `Contact.IndividualId` when working with FERPA consent, even in PersonAccount orgs. Verify that LearnerProfile is linked to the Contact Id (not the Account Id) of the PersonAccount.
