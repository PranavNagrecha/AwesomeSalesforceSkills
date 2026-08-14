# Examples — Education Cloud EDA Setup

## Example 1: Establishing Which Model the Org Actually Runs

**Scenario:** A new engagement. The client says "we're on Education Cloud." The statement of work assumes Program Plans and Course Connections.

**Problem:** Both models are called Education Cloud in conversation, and they share almost no API names. Designing against the wrong one is discovered at build, after sign-off.

**Solution:** Determine it from the org, not the conversation. The standard model's objects exist without any package installed:

```apex
// Run as anonymous Apex. String lookups, not type tokens -- a type token
// for an object that is absent would not compile at all, which is the
// opposite of what a detection script needs.
Map<String, Schema.SObjectType> g = Schema.getGlobalDescribe();

// Lower-case both sides before comparing; do not depend on the case the
// map happens to key on.
Set<String> present = new Set<String>();
for (String k : g.keySet()) {
    present.add(k.toLowerCase());
}

Boolean hasStandardEducationCloud =
    present.contains('academicterm')
    && present.contains('courseofferingparticipant')
    && present.contains('learningprogramplan');

// EDA present? Its objects are managed-package custom objects, so match
// on the suffix and read the ACTUAL prefixed name -- never assume it.
for (String apiName : g.keySet()) {
    String lower = apiName.toLowerCase();
    if (lower.endsWith('affiliation__c') || lower.endsWith('program_plan__c')) {
        System.debug('EDA object found, exact API name: '
            + g.get(apiName).getDescribe().getName());
    }
}
System.debug('Standard Education Cloud objects present: ' + hasStandardEducationCloud);
```

**Why it works:** `Schema.getGlobalDescribe()` reports what is installed rather than what the project brief claims. The loop prints the exact prefixed API name, which is the value every subsequent Flow, data-load mapping, and class needs — reconstructing it from the object's label is the single most common failure in EDA work.

---

## Example 2: Mapping the Four-Level Academic Structure Across Both Models

**Scenario:** A reporting requirement written against EDA ("students enrolled in offerings of course X in term Y") has to be satisfied in an org running the standard Education Cloud model.

**Problem:** The concepts survive the translation; the objects do not. Every field, every relationship, and every API name is different, and the resemblance tempts teams into assuming a mechanical migration exists.

**Solution:** Map concept to concept, then rebuild against the target model's objects:

```
Concept                     EDA (managed package)   Education Cloud (standard)
--------------------------  ----------------------  ---------------------------------
Academic period             Term                    AcademicTerm
                                                    "Defines an academic period which may
                                                     hold other more defined time periods"
Catalogue-level course      Course                  Learning / LearningCourse
Instance of a course        Course Offering         CourseOfferingSchedule
  in a period                                       AcademicSession ("Records course
                                                     offering period")
Student in an offering      Course Connection       CourseOfferingParticipant
                                                    "information about a student's
                                                     enrollment in a Course Offering"
Grade / outcome             Course Connection       CourseOfferingPtcpResult
                              (fields on it)        CourseOfrPtcpActvtyGrd
Enrolment status per term   Affiliation status      AcademicTermEnrollment
Programme definition        Program Plan            LearningProgramPlan
Programme requirements      Plan Requirement        LearningProgramPlanRqmt
Learner's programme         Program Enrollment      LearnerProgram
```

On the standard model, the requirement becomes an ordinary relationship query:

```sql
SELECT Id, CourseOfferingScheduleId
FROM CourseOfferingParticipant
WHERE CourseOfferingSchedule.AcademicTermId = :termId
```

**Why it works:** The four-level split — period, catalogue course, offering, participant — is the same idea in both models, which is what makes the requirement portable. The API names, fields, and relationship names are not, which is what makes a copy-paste migration fail. Confirm every field API name against the developer guide for whichever model the org runs; the concept mapping above is what carries across.

---

## Anti-Pattern: Bulk-Loading Contacts Without Handling EDA's Trigger Layer

**What practitioners do:** Load 40,000 student Contacts with Data Loader, straight in, as they would on any Sales Cloud org.

**What goes wrong:** EDA's automation runs on Contact insert — Household creation, affiliation defaulting, relationship auto-create. At load volume this either exhausts limits mid-batch or completes with a fraction of the records correctly affiliated. Failures land in EDA's own **Error** object rather than in the Data Loader error file, so the load reports success and the gap is discovered by an advisor who cannot see their students.

**Correct approach:** Stage the load, control the trigger layer, and verify against the Error object:

```
1. Load Academic Program Accounts and Program Plans first.
   Every Contact needs a valid affiliation target at insert.

2. Deactivate the relevant handlers in EDA's Trigger Handler object.
   Record which ones -- reactivation is a required step, not a cleanup task.

3. Load Contacts in batches, then Affiliations explicitly rather than
   letting auto-create infer them at volume.

4. Reactivate the handlers.

5. Query EDA's Error object for the load window BEFORE declaring success:
```

```sql
-- Substitute the installed package's namespace prefix.
SELECT Id, CreatedDate, /* error text field */ Name
FROM <namespace>__Error__c
WHERE CreatedDate = TODAY
ORDER BY CreatedDate DESC
```

```
6. Spot-check a sample: pick 20 Contacts across batches and confirm each
   has the expected Primary Academic affiliation and Household.
```

The Trigger Handler and Error objects are EDA configuration and telemetry held as records, which means they do not travel with a metadata deploy and can differ between a refreshed sandbox and production. Verify both in the target org before the load, not after.
