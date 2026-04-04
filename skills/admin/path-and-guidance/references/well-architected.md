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

- **Security** — Path is a display component. It does not enforce access control, field-level security, or record sharing. FLS still applies: key fields respect the running user's FLS, so fields the user cannot see will not appear even if added to the path. This is correct behavior, not a gap.
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

3. **Path duplication instead of record-type paths** — Some admins create multiple active paths for the same object and the same record type to show different guidance to different profiles. Path does not filter by profile — it filters by record type only. Using record type to differentiate guidance is correct; using profile is not possible with standard Path.

## Official Sources Used

- Salesforce Help: Guide Users with Path — https://help.salesforce.com/s/articleView?id=sales.path_overview.htm
- Salesforce Help: Considerations and Guidelines for Creating Paths — https://help.salesforce.com/s/articleView?id=sales.path_considerations.htm
- Lightning Component Reference: lightning:path — https://developer.salesforce.com/docs/component-library/bundle/lightning:path
- Salesforce Well-Architected Overview — architecture quality framing for User Experience and Operational Excellence pillars — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
