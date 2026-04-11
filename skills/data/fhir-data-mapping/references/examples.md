# Examples — FHIR Data Mapping

## Example 1: Mapping a FHIR Patient Resource to Person Account and Child Records

**Context:** A health system is migrating patient demographics from an EHR that exports FHIR R4 Patient bundles. The middleware team needs to load patient identity data into Health Cloud.

**Problem:** The team's first pass wrote patient name and phone number directly to `Account.FirstName`, `Account.LastName`, and `Account.Phone`. Queries using Health Cloud clinical APIs returned no results because the platform's clinical data model expects demographics in child PersonName, ContactPointPhone, and ContactPointAddress records, not the Account fields.

**Solution:**

```python
# Middleware pseudocode: transform FHIR Patient to HC records

def transform_patient(fhir_patient: dict) -> dict:
    """
    Maps FHIR Patient resource to Salesforce Person Account
    plus child PersonName, ContactPointPhone, ContactPointAddress records.
    """
    account = {
        "RecordTypeId": PERSON_ACCOUNT_RECORD_TYPE_ID,
        # Do NOT write fhir_patient["name"] here
    }

    person_names = []
    for name in fhir_patient.get("name", []):
        person_names.append({
            "GivenName": " ".join(name.get("given", [])),
            "FamilyName": name.get("family", ""),
            "NameUse": name.get("use", "official").capitalize(),
            # ParentId set after Account upsert
        })

    contact_phones = []
    for telecom in fhir_patient.get("telecom", []):
        if telecom.get("system") == "phone":
            contact_phones.append({
                "TelephoneNumber": telecom.get("value"),
                "AddressType": telecom.get("use", "home").capitalize(),
                # ParentId set after Account upsert
            })

    contact_addresses = []
    for addr in fhir_patient.get("address", []):
        contact_addresses.append({
            "Street": " ".join(addr.get("line", [])),
            "City": addr.get("city"),
            "StateCode": addr.get("state"),
            "PostalCode": addr.get("postalCode"),
            "CountryCode": addr.get("country"),
            "AddressType": addr.get("use", "home").capitalize(),
            # ParentId set after Account upsert
        })

    return {
        "account": account,
        "person_names": person_names,
        "contact_phones": contact_phones,
        "contact_addresses": contact_addresses,
    }
```

**Why it works:** Health Cloud's FHIR-aligned data model stores demographics in the PersonName, ContactPointPhone, and ContactPointAddress child objects so that multiple names (legal name, nickname, maiden name) and multiple phones can be associated with one patient. Writing to Account fields directly bypasses this model and makes the records invisible to clinical APIs.

---

## Example 2: Handling a CodeableConcept with More Than 15 Codings

**Context:** A lab results integration receives FHIR Observation resources from a reference lab. Some lab panel Observations include a CodeableConcept with 22 codings (LOINC, SNOMED CT, CPT, local lab codes, and several regional code systems). The CodeSetBundle object only supports 15 CodeSet references.

**Problem:** Loading the full 22-coding array without truncation fails at the DML layer. Silently dropping the extra 7 codings without an audit trail violates clinical governance requirements.

**Solution:**

```python
CODING_PRIORITY = {
    "http://snomed.info/sct": 1,
    "http://loinc.org": 2,
    "http://hl7.org/fhir/sid/icd-10-cm": 3,
    "http://www.ama-assn.org/go/cpt": 4,
    # Local/regional systems get lower priority
}

MAX_CODESETS = 15

def truncate_codings(codings: list, resource_id: str, audit_log: list) -> list:
    """
    Sort codings by terminology priority, keep top 15, log discards.
    """
    def priority(coding):
        return CODING_PRIORITY.get(coding.get("system", ""), 99)

    sorted_codings = sorted(codings, key=priority)
    retained = sorted_codings[:MAX_CODESETS]
    discarded = sorted_codings[MAX_CODESETS:]

    for c in discarded:
        audit_log.append({
            "resource_id": resource_id,
            "system": c.get("system"),
            "code": c.get("code"),
            "display": c.get("display"),
            "reason": "Exceeded 15-coding CodeSetBundle limit",
        })

    return retained

# Usage
audit_log = []
codings = fhir_observation["code"]["coding"]  # 22 codings
retained_codings = truncate_codings(codings, fhir_observation["id"], audit_log)

# Build CodeSetBundle record
codeset_bundle = {}
for i, coding in enumerate(retained_codings, start=1):
    codeset_id = lookup_or_create_codeset(coding)
    codeset_bundle[f"CodeSet{i}Id"] = codeset_id

# Write audit_log to CSV for clinical review
```

**Why it works:** The truncation is deterministic (same input always produces the same retained set), clinically defensible (preferred standard terminologies are retained first), and auditable (discards are logged for stakeholder review). The 15-field hard limit on CodeSetBundle is a platform constraint that cannot be configured away — middleware normalization is the only correct solution.

---

## Anti-Pattern: Loading FHIR Condition Records Without Checking for condition.code

**What practitioners do:** Middleware transforms all FHIR Condition resources and loads them to HealthCondition in bulk, without pre-filtering those that lack a `condition.code` element. This is technically valid in FHIR R4 (code is 0..1) but fails in Health Cloud.

**What goes wrong:** HealthCondition requires a code reference. Records without a code fail DML validation. In a bulk load, this often surfaces as a partial batch failure with cryptic error messages. Depending on the load tool, some code-less Conditions may be silently skipped while the rest of the batch succeeds, leaving the record set incomplete with no indication of how many were dropped.

**Correct approach:** Pre-validate the FHIR bundle before load. Separate Condition resources into two groups: those with a condition.code and those without. Load the coded group normally. Route the code-less group to a quarantine list for manual clinical coding before a second load attempt.
