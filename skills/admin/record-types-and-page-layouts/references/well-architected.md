# Well-Architected Mapping: Record Types and Page Layouts

---

## Pillars Addressed

### User Experience

**Principle: The Interface Matches the User's Mental Model**
A user who handles renewals shouldn't see "Prospecting" and "Discovery" stages — those are irrelevant to their process and create cognitive noise. Record Types and page layouts exist to surface the right information to the right user at the right time.

- WAF check: Does each Record Type reflect a distinct business process with meaningfully different fields or picklist values?
- WAF check: Are unnecessary fields hidden from users who don't need them?
- WAF check: Is the number of Record Types the minimum needed? (Fewer = simpler = less training burden)

**How this skill addresses it:**
- The decision framework prevents RT proliferation for non-RT problems
- Dynamic Forms guidance reduces unnecessary RTs in Lightning orgs
- Mode 3 (Simplify) provides a structured path to reduce complexity

**Risk of not following this:** Users see irrelevant stages, fields, and options. Training is harder. Data quality degrades (users pick "N/A" or leave fields blank because the right option isn't visible). Admin overhead grows with each new RT.

### Operational Excellence

**Principle: The Model Is Maintainable by the Next Admin**
A Record Type model with 15 RTs, 30 page layouts, and no documentation is a maintenance burden. The next admin can't confidently change anything because they don't know what each RT is for or who uses it.

- WAF check: Is each Record Type documented with its business purpose and assigned user groups?
- WAF check: Is the RT count the minimum needed to support actual business differentiation?
- WAF check: Are orphaned (unassigned) Record Types identified and removed?

**How this skill addresses it:**
- Audit mode surfaces orphaned and redundant RTs
- The design template captures business justification per RT
- The "RT count guide" table gives a concrete signal for when the model has grown too complex

**Risk of not following this:** Admins afraid to change anything. RT proliferation accelerates (it's always "easier" to create a new RT than understand the existing model). Org becomes unmaintainable.

---

## Pillars Not Addressed

- **Security** — Record Types do not control data access, and the Metadata API guide says so in bold: profile assignment governs create and edit access for a record type but not read access, and every user with object access can read all record type information. FLS and sharing rules control what users can see and edit; page layouts and record types are UX controls. Object and field permissions are addressed in admin/permission-sets-vs-profiles; record access in admin/sharing-and-visibility.
- **Performance** — Record Types don't affect query performance. Page layouts affect page load time only at the margins (too many related lists). Not a primary concern.
- **Scalability** — RT count grows linearly with business complexity, but the platform handles it. The scalability concern here is administrative (too many RTs = unmaintainable), not technical.
- **Reliability** — Not directly relevant. The picklist-wipe gotcha is a data integrity concern, addressed in gotchas.md.

---

## Governance Recommendations

**Who approves new Record Types?**
- Any new Record Type should require approval from a Salesforce Architect or senior Admin
- The "Do you actually need a Record Type?" framework should be run before any RT creation request is approved
- New RTs should be documented before being created

**Review cadence:**
- Audit RT count and usage annually
- Run SOQL to identify orphaned RTs (assigned to no Profiles/PSGs)
- Review after any org merge or business unit consolidation (common source of RT proliferation)

## Official Sources Used

- Metadata API Developer Guide, `RecordType` ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)) — `active`, `label`, `description` (255 chars), `compactLayoutAssignment` (29.0+), `picklistValues`/`RecordTypePicklistValue`, the `businessProcess` four-object rule, the "don't use record types as an access control mechanism" warning, the Profile/PermissionSet co-retrieval note, the two person-account retrieval notes, and the absence of `*` wildcard support (gotchas #6, #7, #9, #10; `references/metadata-examples.md`)
- Metadata API Developer Guide, `BusinessProcess` ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)) — bare vs object-qualified `fullName`, `isActive`, `values`, the sample lead process definition, and wildcard support only alongside a `RecordType` (gotchas #6; `references/metadata-examples.md` Case example and package.xml)
- Metadata API Developer Guide, `Layout` ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)) — `layoutSections`/`layoutColumns`/`layoutItems`, the `LayoutSectionStyle` and `UiBehavior` enumerations, `quickActionList`, `relatedLists` field aliases, the Case/Lead/Account-only checkbox fields, the `layouts` directory and `.layout` suffix, and the object-hyphen-layout package.xml member format (gotchas #11; `references/metadata-examples.md` layout example)
- Metadata API Developer Guide, `Profile` and `PermissionSet` ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)) — `ProfileLayoutAssignments` (`layout`, optional `recordType`), `ProfileRecordTypeVisibility` (`default`, `personAccountDefault`, `recordType`, `visible`), `PermissionSetRecordTypeVisibility` (`recordType`, `visible` only, 29.0+), the absence of `layoutAssignments` on PermissionSet, and the inactive-record-type retrieval exclusion on both types (gotchas #8; `references/metadata-examples.md` assignment section; Governance Recommendations below)
- Object Reference, `RecordType` standard object ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf)) — `SobjectType`, `DeveloperName`, `Name` (80 chars), `IsActive` ("only active record types can be applied to records"), `IsPersonType`, `BusinessProcessId`, `NamespacePrefix`, and the repeated access-control warning (verification SOQL in `references/metadata-examples.md`; gotchas #8, #10)
- Object Reference, `Case` standard object ([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf)) — `Status` ("such as New, Closed, or Escalated", drives `IsClosed`), `Priority`, and `Origin` picklist semantics used in the worked Case record type (`references/metadata-examples.md`)
- Salesforce Well-Architected — UX and governance framing for configuration sprawl (the pillar mapping and Governance Recommendations in this file)
