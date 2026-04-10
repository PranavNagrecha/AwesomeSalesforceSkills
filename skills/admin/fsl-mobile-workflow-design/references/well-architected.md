# Well-Architected Notes — FSL Mobile Workflow Design

## Relevant Pillars

- **Reliability** — FSL Mobile workflows must function correctly in degraded or no-connectivity conditions. Offline-first design requires that every critical workflow path (status update, data capture, signature, parts consumption) can complete on-device and sync reliably without data loss or sync failure. Reliability failures in FSL Mobile manifest as silent data gaps (blank service report fields) or sync errors that surface after the technician has left the customer site.
- **Security** — Service report signatures, customer data captured offline, and inventory consumption records must be captured and stored in compliance with org data governance requirements. Briefcase configuration must be scoped to the minimum necessary records — a technician should not prime records for appointments not assigned to them. ContentDocument access for signatures must be restricted to authorized users.
- **Operational Excellence** — FSL Mobile workflows involve field workers who cannot easily escalate issues mid-job. Operational excellence requires that validation rules, required fields, and data quality checks are surfaced in the mobile UI before sync rather than failing at sync time. Runbooks for sync error resolution must exist and be accessible to field supervisors.
- **Performance** — Briefcase size directly affects priming time and device storage. Overly broad briefcase configurations (too many records, too many fields, too many linked objects) increase the time to prime and the risk of stale data on device. Briefcase scope should be tuned to the rolling horizon of appointments a technician will work in a typical shift.
- **Scalability** — As the field workforce scales, the volume of ProductConsumed, ServiceAppointment, and ContentDocument records will grow. Server-side automations (Record-Triggered Flows) triggered at sync must handle concurrent sync events from multiple technicians without governor limit violations or lock contention on shared parent records (e.g., a Work Order with many concurrent SA updates).

## Architectural Tradeoffs

**Offline depth vs. priming time:** Deeper briefcase coverage (more objects, more fields, longer record history) increases data availability offline but increases priming time and device storage consumption. Design the briefcase for a 24–48 hour working window, not unlimited history.

**Validation at mobile vs. at sync:** Enforcing data quality in the mobile UI (required fields in mobile layout, Data Capture flow validations) provides immediate feedback to the technician and prevents sync failures. Validation at sync only catches errors after the technician is no longer at the site, making correction expensive. Prefer mobile-side enforcement for fields that must be captured during the job.

**Real-time inventory vs. sync-on-reconnect:** Requiring connectivity for parts consumption gives real-time inventory accuracy but breaks the offline-first model for parts-heavy jobs in low-connectivity areas. The platform default (sync-on-reconnect) is the correct tradeoff for most field service deployments; exceptions should be documented and scoped to specific high-value parts.

**Data Capture flows vs. classic FSL quick actions:** Data Capture (Spring 25 GA) provides native offline conditional logic, richer form components, and signature capture without Apex. Classic FSL quick actions are more flexible for complex UI requirements but lack native offline execution guarantees. For Spring 25+ orgs, default to Data Capture unless a specific gap requires quick actions.

## Anti-Patterns

1. **Assuming SA status cascades to WO automatically** — Deploying FSL Mobile without building SA→WO status automation leaves Work Order status permanently stale. Every downstream process (billing, SLA, replenishment) that depends on WO status will fail silently. Always implement an explicit Record-Triggered Flow for status cascade.
2. **Treating the briefcase as a full org mirror** — Adding every field and object to the briefcase to "be safe" creates unnecessarily large priming payloads, slows device startup, and increases the attack surface for data exposure on lost/stolen devices. Scope the briefcase to fields actually used in the mobile UI and service report template.
3. **Expecting server-side logic to enforce data quality offline** — Validation rules and Apex that enforce data quality are not a substitute for mobile-side required field configuration. If a field must be filled during the job, it must be surfaced and required in the FSL Mobile layout — not just enforced by a server-side rule that fires at sync.

## Official Sources Used

- Field Service Mobile App (Offline Considerations) — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_offline.htm
- Configure Offline Mode — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_mobile_offline.htm
- Track Field Service Jobs — Trailhead — https://trailhead.salesforce.com/content/learn/modules/field-service-mobile-app/track-field-service-jobs
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
