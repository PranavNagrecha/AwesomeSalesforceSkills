# LLM Anti-Patterns — Education Cloud EDA Setup

Common mistakes AI coding assistants make when configuring EDA / Education Cloud.

## Anti-Pattern 1: Creating a custom `Student__c` object

**What the LLM generates:** A custom object `Student__c` with fields for name, GPA, program, term, because that "matches the domain."

**Why it happens:** The model reaches for obvious domain-object naming rather than mapping to EDA's contact-centric model.

**Correct pattern:**

```
Students are Contacts with an Affiliation of type 'Primary Academic' to an
Academic Program Account. Custom fields on Contact extend the student
record. Do NOT introduce a new object.
```

**Detection hint:** A custom object named `Student__c`, `Applicant__c`, or `Pupil__c` in an EDA org is a red flag.

---

## Anti-Pattern 2: Storing grades on Course Offering

**What the LLM generates:** Adds a `Grade__c` field to `Course_Offering__c` because "the offering is the thing that ran."

**Why it happens:** The four-level Term / Course / Course Offering / Course Connection model is non-obvious from training data.

**Correct pattern:**

```
Grades live on Course_Connection__c, the junction between Contact
(student) and Course_Offering__c. Course Offering is the class section;
Course Connection is the enrolled student's record of it.
```

**Detection hint:** Any field named `Grade__c`, `Final_Grade__c`, or `Mark__c` on `Course_Offering__c`.

---

## Anti-Pattern 3: Flat role hierarchy with no Household model

**What the LLM generates:** One role per advisor, flat OWDs, no Household Account usage — "parents can see their student as related Contacts."

**Why it happens:** Household-based sharing is an EDA/NPSP convention unfamiliar to the model.

**Correct pattern:**

```
Enable Automatic Household Naming and Household Account creation. Parents,
guardians, and siblings share a Household Account; Affiliations model
non-household relationships (employer, sports, former school).
```

**Detection hint:** An EDA org with no Household Account record type in use.

---

## Anti-Pattern 4: Rebuilding Advisor Link UI

**What the LLM generates:** A custom LWC advisor dashboard showing caseload, alerts, and appointments.

**Why it happens:** The model does not know Advisor Link ships as a packaged app.

**Correct pattern:**

```
Install Advisor Link / Student Success Hub. Extend with custom tabs and
LWCs only where the packaged UI does not fit. Replacing it wholesale
means losing shipped alerts, pathways, and success plan features on
every upgrade.
```

**Detection hint:** An LWC named like `advisorDashboard` or `caseloadViewer` in an org that owns Advisor Link.

---

## Anti-Pattern 5: Deleting Course Connection records at term end

**What the LLM generates:** A scheduled job that deletes `Course_Connection__c` records older than one term to "keep the object small."

**Why it happens:** The model treats historical enrollment records as noise. In reality they are the transcript.

**Correct pattern:**

```
Never delete Course Connections. They are the academic history. Archive
via a separate big-object or external data warehouse if size becomes a
problem — but transactional Course Connection stays put.
```

**Detection hint:** Any scheduled Apex or Flow that performs DML delete on `Course_Connection__c`.
