# Gotchas: FHIR Integration Patterns

Non-obvious Health Cloud behaviors that cause real production problems in FHIR integrations. Each one names the official source it rests on. "HC guide" is the Agentforce Health (Health Cloud) Developer Guide, release 262 (`health_cloud_dev_guide.pdf`); "Healthcare API guide" is developer.salesforce.com/docs/industries/health/guide.

## Gotcha 1: A CodeableConcept keeps at most 15 codings

**What happens:** A concept sent with SNOMED, ICD-10, and a dozen local codes loses everything past the fifteenth coding.

**When it occurs:** When middleware maps `coding[]` onto CodeSetBundle without a limit check.

**How to avoid:** Order codings by a documented priority (for example the `userSelected` coding first, then the system your reports use), keep the first 15, and log the rest.

**Source:** HC guide (262), "Considerations for Integration": "Code Set Bundle flattens this zero-to-many reference to 15 zero-to-one Code Set references ... CodeSet1Id ... until CodeSet15Id"; CodeableConcept mapping table.

---

## Gotcha 2: Salesforce does not validate FHIR codes

**What happens:** A Procedure with a wrong CPT code is stored without error, and the bad code flows into reports and care gaps.

**When it occurs:** Whenever the caller sends codes that are malformed or from the wrong system.

**How to avoid:** Validate codes in middleware against the expected code systems before writing.

**Source:** Healthcare API guide, "Considerations": "Salesforce doesn't support FHIR semantic validation (codeset validation). The system calling the API is expected to send the right FHIR codes."

---

## Gotcha 3: HealthCondition requires a code that FHIR treats as optional

**What happens:** A Condition without `code` fails to insert.

**When it occurs:** When the EHR sends problem-list entries with only text or with no coding.

**How to avoid:** Create a CodeSetBundle from `code.text` (it maps to `CodeSetBundle.Name`) or route the record to a review queue.

**Source:** HC guide (262), Condition mapping table: `HealthCondition.ConditionCodeId` is a lookup to CodeSetBundle with cardinality 1..1, "While FHIR defines condition.code as a zero-to-one resource."

---

## Gotcha 4: Several FHIR elements have no Salesforce field

**What happens:** `Condition.onsetAge`, `onsetRange`, `onsetString`, `Address.type`, `Address.text`, and `Address.district` disappear.

**When it occurs:** When the mapping assumes every element has a home.

**How to avoid:** List unsupported elements per resource from the mapping tables, and decide whether to drop them, store them in a note, or convert them (for example onsetAge to a date).

**Source:** HC guide (262), Condition and Address mapping tables ("Not supported").

---

## Gotcha 5: Packaged EHR objects are closed to new customers

**What happens:** Code that writes `HC24__EhrCondition__c` cannot create records in a new org.

**When it occurs:** When integration code follows pre-Spring '23 examples.

**How to avoid:** Target the FHIR R4-aligned standard objects (HealthCondition, ClinicalEncounter, MedicationStatement, PatientImmunization, and so on). The exact error text is UNVERIFIED (2026-10-03).

**Source:** HC guide (262), "Clinical Data Model" note: "Starting with the Spring '23 release, new customers won't be able to create records in the packaged EHR objects that have counterpart standard objects in the FHIR R4-aligned data model."

---

## Gotcha 6: SMART-style wildcard scopes are not supported

**What happens:** A SMART on FHIR client requests `patient/*.read` and authorization fails.

**When it occurs:** When a client built for other FHIR servers is pointed at the Salesforce Healthcare API.

**How to avoid:** Request the Healthcare API custom scopes per resource and method, such as `user_condition_read` or `system_all_write`, through an external client app.

**Source:** Healthcare API guide, "Considerations": "The format of SMART on FHIR scopes is not supported because Salesforce doesn't allow usage of wildcard characters in the OAuth Scopes"; "Authorization" (custom scopes table).

---

## Gotcha 7: Healthcare API concurrency and batch limits

**What happens:** Calls fail when middleware fans out dozens of parallel requests, or a Bundle with 40 entries is rejected.

**When it occurs:** During backfills and high-volume event streams.

**How to avoid:** Keep concurrent requests at five or fewer, batch Bundles at 30 entries with no more than 10 reads or searches, and expect about 3 seconds per call. Handle 424 for entries whose dependencies failed.

**Source:** Healthcare API guide, "Considerations" and "Get Started" (Bundle notes).

---

## Gotcha 8: Portal users need a separate permission set

**What happens:** Experience Cloud users can't see HealthCondition or other Clinical Data Model records on the site.

**When it occurs:** When portal users get only the internal Health Cloud permission sets.

**How to avoid:** Assign the FHIR R4 for Experience Cloud Sites permission set to community users who need clinical records. The permission set API name is UNVERIFIED (2026-10-03); check it in Setup.

**Source:** HC guide (262), "Clinical Data Model" note.

---

## Gotcha 9: CDS Hooks needs a MuleSoft service in front of Health Cloud

**What happens:** An EHR configured to call Salesforce directly as a CDS service gets no cards back.

**When it occurs:** When the design treats Salesforce as the CDS Hooks endpoint.

**How to avoid:** Use the MuleSoft CDS Hooks Direct Integration app (or another middleware service) as the CDS service, reading care gaps and alerts from Health Cloud.

**Source:** Healthcare API guide, "Explore MuleSoft Direct Integration Apps": "The MuleSoft integration enables EMR workflow integration with Clinical Decision Support services from Salesforce Health Cloud." UNVERIFIED (2026-10-03): the specific HTTP status an EHR receives when it calls a Salesforce URL that is not a CDS service.
