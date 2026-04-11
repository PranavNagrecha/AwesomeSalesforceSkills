# Well-Architected Notes — Clinical Decision Support

## Relevant Pillars

- **Reliability** — Clinical alert creation triggers must be bulkified to handle high-volume clinical data loads. Alert ingestion pipelines must have retry logic and dead-letter queues for transient failures. A failed alert creation during bulk EHR data sync must not go undetected.
- **Operational Excellence** — Clinical alert generation logic (Apex triggers, BRE rules) must be versioned, tested, and documented with the clinical team. Changes to alert thresholds or rule logic must follow a change management process with clinical stakeholder review.
- **Security** — ClinicalAlert records contain PHI-adjacent data (patient identity + clinical condition details). Access must be restricted via HealthCloudICM permission set and OWD settings. Integration users that ingest CareGap records via API must have minimal required permissions.

## Architectural Tradeoffs

**Apex Triggers vs. Business Rules Engine for Alert Logic:** Apex provides full flexibility for complex clinical rule logic but requires developer involvement for every rule change. The Business Rules Engine provides declarative rule management that clinical operations teams can update without code changes. The tradeoff: BRE requires a separate license and has a learning curve; Apex requires developer resources for rule maintenance. For rules that change frequently based on clinical protocols, BRE provides better operational flexibility if licensed.

**Internal ClinicalAlert vs. External CDS Hooks:** ClinicalAlert records displayed in the Salesforce care coordinator console address internal care team workflows. CDS Hooks integration (via MuleSoft) addresses EHR-embedded clinical workflows where clinicians never leave the EHR. Both may be needed: ClinicalAlert for care coordinator outreach, CDS Hooks for point-of-care clinician alerts. These are complementary, not alternative approaches.

## Anti-Patterns

1. **Assuming Health Cloud has a native clinical rules engine** — ClinicalAlert and CareGap are storage objects only. All alert creation logic must be explicitly implemented.
2. **Manually creating CareGap records** — CareGap records must be ingested from authoritative external quality systems. Manual creation produces records not linked to quality measure lifecycles.
3. **Non-bulkified Apex triggers on clinical objects** — bulk clinical data operations will exceed limits and silently drop alerts.

## Official Sources Used

- Salesforce Health Cloud Developer Guide — ClinicalAlert Object Reference (API v51.0+): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_clinicalalert.htm
- Salesforce Health Cloud Developer Guide — CareGap Object Reference (API v59.0+): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_caregap.htm
- Salesforce Health Cloud Integrated Care Management Docs: https://help.salesforce.com/s/articleView?id=ind.hc_icm.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
