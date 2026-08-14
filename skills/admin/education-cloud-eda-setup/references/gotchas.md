# Gotchas — Education Cloud EDA Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: "Education Cloud" and "EDA" Are Two Different Data Models

**What happens:** A design is written against EDA's Contact-centric custom objects and handed to an org running the standard Education Cloud model — or the reverse. Nothing in the design resolves, because the two models share almost no API names. EDA is "a community-driven data architecture that supports the entire K-20 student journey for educational institutions," delivered as a managed package of custom objects (Affiliation, Program Plan, Plan Requirement, Term, Course, Course Offering, Course Connection, Hierarchy Settings). Education Cloud ships standard objects instead: `AcademicTerm`, `AcademicTermEnrollment`, `CourseOfferingSchedule`, `CourseOfferingParticipant`, `Learning`, `LearningProgram`, `LearningProgramPlan`, `LearnerProgram`.

**When it occurs:** In every requirements conversation, because institutions and consultants use "Education Cloud" to mean whichever one they have. It is discovered at build time, after the design has been signed off.

**How to avoid:** Establish which model is installed before writing a single API name — look for the EDA managed package in Installed Packages, and for `AcademicTerm` in Object Manager. Write the design against the one that is actually there. Where a mapping is genuinely needed, the concepts line up roughly as Term → `AcademicTerm`, Course Offering → `CourseOfferingSchedule`, Course Connection → `CourseOfferingParticipant`, Program Plan → `LearningProgramPlan`, Plan Requirement → `LearningProgramPlanRqmt`, Program Enrollment → `LearnerProgram` — but they are not field-compatible and no migration is implied by the resemblance.

---

## Gotcha 2: EDA API Names Carry a Namespace Prefix; The Label Form Does Not Resolve

**What happens:** Apex, a Flow, or a data-load mapping references `Affiliation__c`, `Program_Plan__c`, or `Course_Connection__c` and fails. EDA objects live in a managed package, so every one of them carries the package's namespace prefix ahead of the object name. The unprefixed form is a plausible reconstruction of the label, not the API name.

**When it occurs:** Whenever a name is derived from the object's label rather than copied from the installed package — which is exactly what a person or a model does when working from a data-model diagram, because the published EDA entity diagrams label objects by their display name.

**How to avoid:** Read the API name from Object Manager or from the package's own metadata in the target org and copy it. In Apex, reference the type token rather than a string so a wrong name fails at compile time. Never carry an object name between orgs on the assumption that the namespace is the same — it depends on which EDA package variant is installed.

---

## Gotcha 3: EDA's Behaviour Is Configuration Records, Not Setup Screens

**What happens:** An admin looks for the switch that controls Household auto-creation or which affiliation types populate the primary fields, and cannot find it in Setup. EDA holds its own configuration in objects: **Hierarchy Settings**, **Affiliation Mappings**, **Relationship Auto-Create**, **Relationship Lookup**, and **Trigger Handler**. Changing behaviour means editing records, and those records deploy and drift like any other data.

**When it occurs:** During sandbox refreshes and org-to-org moves, where configuration held in records does not travel with metadata. A refreshed sandbox can behave differently from production with no metadata difference to point at.

**How to avoid:** Treat these objects as deployable configuration with an owner and a change log, and diff them between orgs as part of release verification. The **Trigger Handler** object is the one to know before a bulk load: EDA's automation runs from it, so a large Contact or Affiliation import needs the relevant handlers deactivated and — critically — reactivated afterwards. The **Error** object is where EDA records its own failures; check it after any bulk operation, because a silent trigger failure surfaces there and nowhere else.

---

## Gotcha 4: Grades Live on the Enrollment Record, Not the Offering

**What happens:** A term-rollover routine or a reporting build writes grades onto the Course Offering, reasoning that the offering is the thing being graded. Every student in that offering then shares one grade, and the individual results are gone. On EDA the grade holder is **Course Connection**; on the standard model it is `CourseOfferingPtcpResult` — "the outcome of a student's participation in a course" — with `CourseOfrPtcpActvtyGrd` for activity-level grades.

**When it occurs:** At the first term rollover, which is also the point at which the prior term's data is being touched in bulk. It is a data-loss event rather than an error, and academic records are exactly the data an institution cannot reconstruct.

**How to avoid:** Never delete or overwrite prior-term enrollment records; next term's are net-new inserts. Build the rollover to create offerings and enrollments forward, and assert on a sample student's prior-term grade after every run. Where an institution genuinely needs an offering-level statistic, compute it — do not store it on the offering, because a stored aggregate is indistinguishable from an individual grade to the next person who reads the object.

---

## Gotcha 5: Affiliation Status Is the Audit Trail, and It Is Not Retroactive

**What happens:** A student's relationship to a programme is modelled by editing the Affiliation status through `Prospect` → `Current` → `Former`, which is the correct pattern. But if field history tracking on that status was never enabled, there is no record of when each transition happened. Enrolment dates, eligibility windows, and disclosure questions all depend on that timeline, and history is not retroactive — turning tracking on in month three says nothing about month one.

**When it occurs:** At the first audit, accreditation review, or student records request. By then the transitions have already happened.

**How to avoid:** Enable field history on Affiliation status — and on the standard model, on `AcademicTermEnrollment` — as part of go-live rather than as a later hardening pass. Where the institution needs a queryable enrolment timeline rather than a history log, model it explicitly: on the standard model `AcademicTermEnrollment` already captures enrollment status per academic period, which is a reportable record rather than a field-history entry.
