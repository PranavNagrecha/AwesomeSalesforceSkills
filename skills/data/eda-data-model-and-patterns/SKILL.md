---
name: eda-data-model-and-patterns
description: "Education Data Architecture (EDA) data model deep dive: Contact-centric, Affiliations, Relationships, Account record types (Academic Program, Educational Institution, Sports Organization), Course_Offering__c, Term__c, Course_Connection__c patterns. NOT for Education Cloud setup (use education-cloud-eda-setup). NOT for generic data modeling."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
tags:
  - eda
  - education-cloud
  - data-model
  - higher-education
  - k12
  - contact-centric
  - affiliations
triggers:
  - "what is the eda data model and how do affiliations work"
  - "eda contact-centric architecture higher education"
  - "course offering term course connection eda data model"
  - "eda account record types academic program institution"
  - "eda relationships vs affiliations when to use each"
  - "education data architecture schema patterns"
inputs:
  - Education vertical (Higher Ed, K-12, continuing ed, global)
  - Existing EDA installation status
  - Data volume (students, courses, terms, enrollments)
  - Integrations (SIS, LMS, finance)
outputs:
  - EDA data-model documentation at object + field level
  - Recommended record types per use case
  - Pattern library for common education modeling questions
  - Integration field mapping (SIS / LMS ↔ EDA)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# EDA Data Model and Patterns

Activate when working with the Education Data Architecture (EDA) data model in depth: object relationships, record types, extension patterns, and the contact-centric philosophy that underpins it. EDA is the backbone of Education Cloud and underpins most higher-ed + K-12 Salesforce implementations.

## Before Starting

- **Confirm EDA (HEDA) is installed.** EDA is a managed package; verify version and whether customization has already extended it.
- **Understand the contact-centric philosophy.** Students, faculty, alumni, guardians — all Contacts. The model disambiguates role via Affiliations and Relationships, NOT by separate objects per role.
- **Know the record types.** Many EDA objects (Account, Affiliation, Contact, Course_Offering__c) rely on record types for semantics. Without record types, the model collapses.

## Core Concepts

### Contact-centric model

Every Person = Contact. Roles are expressed via:
- **Affiliation__c** — Contact to Account relationship with role, status, dates (Student at MIT, Faculty at Harvard, Staff at a program).
- **Relationship__c** — Contact to Contact (Parent, Sibling, Advisor, Partner) with bidirectional symmetry handled by trigger.

### Account record types

- `Academic_Program` — a program offered by an institution.
- `Educational_Institution` — the school/university itself.
- `Household_Account` — a Household (parallel to NPSP).
- `Sports_Organization`, `Business_Organization` — extracurricular affiliations.

### Course data model

- `Course__c` — the abstract course (Intro to Biology).
- `Course_Offering__c` — a specific instance of a course for a term (Biology 101, Fall 2025, Prof Smith).
- `Term__c` — academic term.
- `Course_Connection__c` — a student's enrollment in a Course_Offering (and the faculty's teaching assignment is also a Course_Connection with record type Faculty).

### Attributes

Student health, test scores, demographics often live in `Attribute__c` (a generic key-value pattern) to avoid endless fields on Contact. This is a contested design choice — it trades schema clarity for extensibility.

## Common Patterns

### Pattern: Student → Institution via Affiliation__c

When a student enrolls: create Contact, create Affiliation__c with Role = "Student", Status = "Current", related Account = Academic_Program. Historical affiliations remain with Status = "Former" when they graduate.

### Pattern: Faculty teaching assignment

Faculty are Contacts with an Affiliation__c (Role = "Faculty") to the Academic_Program. Their teaching load is Course_Connection__c with record type "Faculty" (or similar) to a Course_Offering__c.

### Pattern: Parent / Guardian

Guardian is a Contact. Relationship__c between student Contact and guardian Contact with Type = "Parent". Bidirectional trigger creates the reverse Relationship__c automatically.

### Pattern: Multi-campus student

Student Contact has multiple Affiliations to different Account (Academic_Program) records, each with its own status. Reports aggregate by Affiliation, not Contact.

## Decision Guidance

| Question | Answer |
|---|---|
| Where do I store student role? | `Affiliation__c` with Role = Student |
| Where do I store parent relationship? | `Relationship__c` with Type = Parent |
| Where do I store enrollment in a specific class? | `Course_Connection__c` |
| Where does graduation date live? | End Date on the Student Affiliation |
| Where do I store extended demographics? | Prefer fields on Contact; use Attribute__c only when schema truly varies |

## Recommended Workflow

1. Document the real-world concepts (student, faculty, course, term) and map each to an EDA object + record type.
2. Draft the ERD with record types called out explicitly.
3. Build a reference dataset: 10 students, 5 courses, 2 terms, 3 faculty.
4. Validate reports and Affiliation rollups work on the reference dataset.
5. Plan any extensions as fields on existing EDA objects; avoid shadow custom objects.
6. Map integration fields (SIS → EDA) with record type resolution.
7. Write an admin runbook for onboarding new student → Contact → Affiliation → Course_Connection.

## Review Checklist

- [ ] All record types in use are documented
- [ ] Reference dataset exercises all role/relationship variants
- [ ] Affiliation status and date semantics are agreed
- [ ] Course / Course_Offering / Course_Connection consistently modeled
- [ ] Attribute__c usage deliberately scoped
- [ ] SIS and LMS integrations map to correct record types
- [ ] Reports on Affiliation and Course_Connection match source data

## Salesforce-Specific Gotchas

1. **Relationship__c bidirectional trigger runs on insert/update.** Bulk loads must expect double the record count.
2. **Course_Connection__c has record types that change the page layout.** A "Student" connection and a "Faculty" connection use the same object — layout validation is per record type.
3. **Affiliation rollups (Primary Affiliation, Primary Household) are governed by EDA settings.** Changing the hierarchy setting after data load causes rollup drift.

## Output Artifacts

| Artifact | Description |
|---|---|
| EDA ERD with record types | Canonical schema view |
| Object + field dictionary | Detailed field-level reference |
| Record-type matrix | Object × record type × use case |
| SIS/LMS mapping | Integration field map |

## Related Skills

- `admin/education-cloud-eda-setup` — install + configure
- `integration/integration-pattern-selection` — SIS integration patterns
- `data/data-import-pipelines` — large-volume student loads
