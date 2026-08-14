# Examples — EDA Data Model and Patterns

Worked artifacts for the patterns in `SKILL.md`. All API names carry the EDA
managed-package namespace `hed`.

---

## Example 1: Audit Affiliation Mappings before you trust Primary Affiliation

**Context:** A campus reports that `Primary_Educational_Institution__c` is blank
on half the student Contacts even though the Affiliation records exist. (No
`hed__` prefix — see Gotcha 3; four of the six Primary Affiliation fields are
unmanaged org-level fields.)

**Problem:** Primary Affiliation lookups on Contact are populated by EDA's
Affiliation handler using rows in the `hed__Affl_Mappings__c` List custom
setting. An unmapped Account record type leaves the lookup null and raises no
error at load time. Because the setting holds *data*, not metadata, the rows are
routinely lost in a sandbox refresh or a first production deploy.

**Solution:** Query the mapping table and reconcile it against the Account
record types actually in use.

```apex
// Anonymous Apex: which Account record types have Affiliations but no mapping?
Set<String> mapped = new Set<String>();
for (hed__Affl_Mappings__c m : hed__Affl_Mappings__c.getAll().values()) {
    mapped.add(m.hed__Account_Record_Type__c);
    System.debug(m.hed__Account_Record_Type__c + ' -> ' + m.hed__Primary_Affl_Field__c);
}

for (AggregateResult ar : [
        SELECT hed__Account__r.RecordType.Name rtName, COUNT(Id) total
        FROM   hed__Affiliation__c
        WHERE  hed__Account__c != NULL
        GROUP BY hed__Account__r.RecordType.Name
]) {
    String rt = (String) ar.get('rtName');
    if (rt != null && !mapped.contains(rt)) {
        System.debug(LoggingLevel.WARN,
            'UNMAPPED: ' + rt + ' has ' + ar.get('total') + ' Affiliations');
    }
}
```

**Why it works:** `hed__Affl_Mappings__c.getAll()` reads the List custom setting
without consuming a SOQL query, and the aggregate groups live Affiliations by
the Account record type EDA keys the mapping on. Anything printed as `UNMAPPED`
is a record type whose students will never get a Primary Affiliation populated.

---

## Example 2: Enrol a student with the correct object chain

**Context:** A SIS feed delivers "Ada Lovelace enrolled in BIO-101, Fall 2026".

**Problem:** The natural-language chain (student → course → term) does not map
one-to-one onto EDA objects, and the enrollment object's label ("Course
Connection") differs from its API name (`hed__Course_Enrollment__c`).

**Solution:**

```apex
// 1. The person is a Contact. Role comes from the Affiliation, not a field.
Contact student = new Contact(FirstName = 'Ada', LastName = 'Lovelace');
insert student;

// 2. Role + institution: Affiliation to an Account of a mapped record type.
Id programAccountId = [
    SELECT Id FROM Account
    WHERE Name = 'School of Computing' LIMIT 1
].Id;

insert new hed__Affiliation__c(
    hed__Contact__c   = student.Id,
    hed__Account__c   = programAccountId,
    hed__Role__c      = 'Student',
    hed__Status__c    = 'Current',
    hed__StartDate__c = Date.newInstance(2026, 8, 24),
    hed__Primary__c   = true
);

// 3. The specific class instance: Course Offering ties Course to Term.
hed__Course_Offering__c offering = [
    SELECT Id FROM hed__Course_Offering__c
    WHERE hed__Course__r.Name = 'BIO-101'
      AND hed__Term__r.Name   = 'Fall 2026'
    LIMIT 1
];

// 4. The enrolment itself — label "Course Connection", API name Course_Enrollment__c.
insert new hed__Course_Enrollment__c(
    hed__Contact__c         = student.Id,
    hed__Course_Offering__c = offering.Id
);
```

**Why it works:** Each real-world noun lands on the object that owns it —
identity on Contact, role and institution on Affiliation, the scheduled class on
Course Offering, the enrolment on Course Enrollment. Nothing here needs a
`Student__c` object, and the faculty teaching assignment is the *same* object
with the faculty record type.

---

## Example 3: Quiet EDA automation for a bulk load, then restore it

**Context:** Loading 400,000 historical Course Connections. The first attempt ran
for hours and tripped limits inside EDA's handlers.

**Problem:** EDA dispatches through TDTM rows in `hed__Trigger_Handler__c`, so
there is no trigger to disable. Deactivating handlers globally is the tempting
move and the dangerous one — interactive users lose household and affiliation
maintenance for the duration, and a forgotten reactivation fails silently.

**Solution:** Exclude only the integration user.

```apex
// Before the load — scope the bypass to one username.
String loadUser = 'sis.integration@university.edu.prod';

List<hed__Trigger_Handler__c> handlers = [
    SELECT Id, hed__Class__c, hed__Usernames_to_Exclude__c
    FROM   hed__Trigger_Handler__c
    WHERE  hed__Object__c = 'Course_Enrollment__c'
      AND  hed__Active__c = true
];
for (hed__Trigger_Handler__c h : handlers) {
    h.hed__Usernames_to_Exclude__c =
        String.isBlank(h.hed__Usernames_to_Exclude__c)
            ? loadUser
            : h.hed__Usernames_to_Exclude__c + ',' + loadUser;
}
update handlers;
```

```apex
// After the load — remove the bypass and assert it is gone.
String loadUser = 'sis.integration@university.edu.prod';

List<hed__Trigger_Handler__c> handlers = [
    SELECT Id, hed__Usernames_to_Exclude__c
    FROM   hed__Trigger_Handler__c
    WHERE  hed__Usernames_to_Exclude__c LIKE :('%' + loadUser + '%')
];
for (hed__Trigger_Handler__c h : handlers) {
    h.hed__Usernames_to_Exclude__c = null;
}
update handlers;
System.assertEquals(0, [
    SELECT COUNT() FROM hed__Trigger_Handler__c
    WHERE hed__Usernames_to_Exclude__c LIKE :('%' + loadUser + '%')
], 'TDTM bypass was not fully removed');
```

**Why it works:** The bypass is scoped to one identity, so ordinary users keep
full EDA behaviour throughout the load, and the closing assertion turns "someone
forgot to switch it back on" from a silent data-quality decay into a failed
script. Run a household/affiliation recalculation afterwards for the rows the
handlers skipped.

---

## Anti-Pattern: Reading role from a field on Contact

**What practitioners do:** Add `Contact.Student_Status__c` or
`Contact.Is_Faculty__c` so reports and Flows can filter without a join.

**What goes wrong:** A person is routinely a student at one program, staff at
another, and an alum of a third — simultaneously, with different start and end
dates. A single field on Contact cannot hold that, so it drifts out of sync with
the Affiliation records that EDA's own automation, rollups, and packaged reports
read from. The denormalised field then becomes the thing integrations trust, and
the divergence is invisible until someone reconciles the two.

**Correct approach:** Query the Affiliation. If reporting genuinely needs a flat
flag, let EDA's Primary Affiliation lookups
(`hed__Primary_Household__c`, `hed__Primary_Organization__c`, and the unmanaged
`Primary_Academic_Program__c` / `Primary_Educational_Institution__c` /
`Primary_Department__c` / `Primary_Sports_Organization__c`) be that flag — they
are maintained by the package's Affiliation handler, so they stay correct when
an Affiliation ends.
