# Well-Architected Notes — Volunteer Management Requirements

## Relevant Pillars

### Operational Excellence

Volunteer management systems must be operationally maintainable without deep Salesforce expertise in the nonprofit's IT staff. This means:
- Using the appropriate platform-native tooling (V4S for NPSP orgs, NPC native objects for NPC orgs) rather than custom tables that require custom maintenance
- Documenting DPE schedule and lag behavior so staff understand why TotalVolunteerHours does not update immediately
- Building recognition automations that are explicitly decoupled from the hours-insert event and tied to the DPE completion window

### Reliability

Volunteer hours tracking must be accurate and resilient. Key reliability concerns:
- DPE job failure leaves TotalVolunteerHours stale indefinitely — monitor DPE job health via scheduled alerts
- V4S trigger-based rollup can be deactivated by an administrator unaware of its purpose — document which triggers must remain active
- Skills-matching custom logic must handle cases where a volunteer has no skills on record (null-safe SOQL)

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Operational Excellence | Use platform-native volunteer objects; document rollup timing and DPE schedule |
| Reliability | Monitor DPE job health; validate rollup triggers are active; test with pilot dataset before go-live |
| Security | Volunteer personal data (phone, email, address) requires appropriate field-level security and org-wide defaults |
| Performance | Bulk hours inserts should use Bulk API — V4S trigger-based rollup is governor-limit-aware but high-volume inserts may hit DML limits |

---

## Cross-Skill References

- `data/nonprofit-data-architecture` — Constituent data model and platform selection (NPSP vs. NPC)
- `data/constituent-data-migration` — How to migrate Contact records using NPSP DataImport__c
- `architect/nonprofit-platform-architecture` — Platform-level architecture spanning V4S, NPC, and third-party integrations

---

## Official Sources Used

- Volunteers for Salesforce (V4S) Managed Package — Salesforce.org Open Source Commons: https://github.com/SalesforceFoundation/Volunteers-for-Salesforce
- Nonprofit Cloud Developer Guide: Introduction to Nonprofit Cloud — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_intro.htm
- Salesforce Help — Data Processing Engine Overview: https://help.salesforce.com/s/articleView?id=sf.bi_dpe_overview.htm
