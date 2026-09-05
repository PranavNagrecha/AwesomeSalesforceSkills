# Well-Architected Mapping: Path and Guidance

## Pillars Addressed

### User Experience

Path is fundamentally a user-experience feature. Its entire purpose is to reduce cognitive load for end users by surfacing the right fields and instructions at the right moment in a process.

- Stage-specific key fields eliminate the need to scroll through a dense page layout looking for what to fill in next.
- Guidance text replaces tribal knowledge stored in documents no one reads, embedding process instructions directly in the record context.
- Confetti provides psychological reward for milestone completion, reinforcing adoption of the CRM as the system of record for deals and cases.
- Keeping stage labels concise and guidance text scannable directly affects the quality of the experience on both desktop and mobile.

Poor Path design — too many key fields, walls of text in guidance, confetti on every stage — degrades the experience and trains users to ignore the component.

### Operational Excellence

Path configuration must be maintainable. Stage content that goes stale becomes noise and erodes trust.

- Each stage's guidance text and key fields should be owned by someone (a sales ops admin, a service manager) who is responsible for keeping it current.
- When the Sales Process changes (new stages added, old stages removed), Path configurations must be reviewed and updated in lockstep. A stage present in Path but removed from the Sales Process will silently disappear; a new stage added to the Sales Process will appear in Path with no key fields or guidance.
- Multiple paths for different record types add maintenance surface. Document which record type each path serves and who owns it.
- Activation state (active vs. inactive) should be intentional. Leaving inactive paths in Path Settings creates clutter and makes troubleshooting harder.

## Pillars Not Addressed

- **Security** — Path is a display component. It does not enforce access control, field-level security, or record sharing. FLS still applies: key fields respect the running user's FLS, so fields the user cannot see will not appear even if added to the path. This is correct behavior, not a gap. UNVERIFIED (2026-09-05): the FLS-respecting render behaviour is not stated in the Metadata API guide or the Object Reference — `fieldNames` is documented only as the fields that "will display in this step" (api_meta.txt L94545). What the guides *do* establish is a different security point worth carrying: business processes and record types are not access controls, and their descriptions, names, and picklist values are readable by anyone with access to the object (api_meta.txt L42961–42967, L44974–44980) — so do not put sensitive wording in a stage name that a Path will render.
- **Performance** — Path does not introduce meaningful performance overhead. The component renders synchronously with the record page. There are no governor limit implications for Path configuration.
- **Reliability** — Path has no transaction behavior. It cannot fail in a way that breaks data. If the component cannot render (e.g., missing org toggle), it simply does not appear — it does not throw an error that disrupts the record save operation.

## Architectural Tradeoffs

| Decision | Tradeoff |
|---|---|
| Add more key fields per stage for completeness | More fields = more noise; limit to the 2–3 truly essential fields per stage |
| Write detailed guidance text covering every edge case | Long guidance text is skipped; aim for scannable bullets under 300 words per stage |
| Enable confetti on many stages | Dilutes the reward signal; reserve for genuinely significant milestones |
| Use Path as the only user education mechanism | Path is in-context but static; pair with In-App Guidance walkthroughs for onboarding scenarios |

## Anti-Patterns

1. **Path as enforcement** — Admins design key fields expecting they will function like required fields on a page layout. Path does not enforce. This creates false confidence in data completeness. Use validation rules for enforcement; use Path for guidance.

2. **Stale guidance text** — Guidance text written at launch and never reviewed becomes misleading. A link to a deprecated playbook or an outdated SLA in the guidance erodes the usefulness of the entire component. Build a quarterly review of Path guidance into the admin calendar.

3. **Path duplication instead of record-type paths** — Some admins create multiple active paths for the same object and the same record type to show different guidance to different profiles. The platform does not allow it: "Only one path can be created per record type for each object, including `__Master__` record type" (api_meta.txt L94496). The unique key is `(entityName, recordTypeName)` — the driver picklist field is not part of it, so a second path on a different field is not an escape hatch either. Using record type to differentiate guidance is correct; using profile is not possible with standard Path.

4. **Treating a retrieved path as a complete backup** — `PathAssistant` carries no celebration element, and rich text guidance "cannot be retrieved or deployed from or to translation workbench" (api_meta.txt L94497). A source-controlled path is therefore an incomplete record of the configured experience. Document what lives outside the file, or the next org build quietly loses it.

## Official Sources Used

- **Metadata API Developer Guide — `PathAssistant` / `PathAssistantStep`** (api_meta.txt L94490–94615) — the complete field set (`active`, `entityName`, `fieldName`, `masterLabel`, `pathAssistantSteps`, `recordTypeName`; per step `fieldNames`, `info`, `picklistValueName`), the one-path-per-record-type rule, the not-updateable bindings, the "missing step is unconfigured, not absent" note, and the fact that the preference need not be on to deploy. Supports the Operational Excellence maintenance argument and Anti-Pattern 3 below. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide — `PathAssistantSettings`** (api_meta.txt L124200–124240) — `pathAssistantEnabled` defaulting to `true` only in Enterprise Edition, and `canOverrideAutoPathCollapseWithUserPref` defaulting to `false` in all editions. Supports the User Experience claim that a path can be present and effectively invisible, and the tradeoff table row on guidance visibility.
- **Metadata API Developer Guide — `BusinessProcess` and `RecordType`** (api_meta.txt L42955–43060, L44968–45131) — the business process lives inside the object definition, `RecordType.businessProcess` takes the bare name and is required for lead, opportunity, solution and case record types, and `RecordTypePicklistValue` decides which values a record type exposes. Supports the Operational Excellence claim that a Sales Process change and a Path change must move together.
- **Metadata API Developer Guide — `StandardValueSet` and Appendix C** (api_meta.txt L130740–130828, L141982 / L142581 / L142674 / L142923) — the `OpportunityStage`, `LeadStatus`, `CaseStatus`, `QuoteStatus` mappings, and the note that values loaded via the Metadata API are not selected on record types by default. Supports the claim that a stage silently missing from the chevron bar is a record-type problem.
- **Metadata API Developer Guide — `FlexiPage` sample definition** (api_meta.txt L67728–67999) — `runtime_sales_pathassistant:pathAssistant` in the `subheader` region of `flexipage:recordHomeWithSubheaderTemplateDesktop`. Supports the placement guidance and the "correct path, wrong page" failure mode.
- **Object Reference — `OpportunityStage`, `RecordType`, `User`** (object_reference.txt L195434–195560, L244491–244525, L296509–296528) — `ApiName` / `IsActive` / `IsClosed` / `IsWon` on stage values, `RecordType.BusinessProcessId` being required for Opportunity and Lead, and `User.UserPreferencesPathAssistantCollapsed` (API 35.0+, superseding `UserPreferencesProcessAssistantCollapsed`). Supports every SOQL verification in `references/metadata-examples.md` § 7. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Salesforce Developer Limits and Allocations Quick Reference** — checked and reported as a **negative result**: the document contains no occurrence of "path", "picklist", or "record type". Neither the five-key-field cap nor any guidance-text character limit is a documented platform limit; both are marked UNVERIFIED where this skill states them.
- **Salesforce Well-Architected Overview** — architecture quality framing for the User Experience and Operational Excellence pillars. https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
