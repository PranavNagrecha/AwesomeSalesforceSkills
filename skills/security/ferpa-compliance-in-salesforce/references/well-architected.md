# Well-Architected Notes — FERPA Compliance in Salesforce

## Relevant Pillars

- **Security** — FERPA is a federal privacy regulation. The primary concern is preventing unauthorized disclosure of education records. Field-level security, sharing rules, and consent-driven access controls must be correctly configured to restrict who can view student data. Misconfigured FLS or overly permissive profiles are direct FERPA violations.

- **Operational Excellence** — FERPA compliance is an ongoing operational obligation, not a one-time configuration. The 45-day response window, consent expiry checks, rights-transfer automation, and directory opt-out propagation all require scheduled jobs, monitoring, and exception handling. Without operational discipline, consent records go stale and deadlines are missed.

- **Reliability** — Consent automation (flows, triggers, scheduled jobs) must be reliable. A failed batch job that does not revoke expired consent or does not transfer rights at age 18 creates a compliance gap. Error handling and monitoring are required on all FERPA automation.

## Architectural Tradeoffs

**Native FERPA fields vs. custom fields**: LearnerProfile's four FERPA booleans are purpose-built but only available in Education Cloud. Custom EDA implementations must replicate these fields, which adds maintenance cost but provides the same consent-flag pattern.

**Declarative vs. Apex consent automation**: Flows are easier for admins to maintain and audit. Apex provides more control for complex scenarios (multi-object consent propagation, bulk processing). For most institutions, a Flow-first approach with Apex fallback for batch operations is the right balance.

**Entitlement Process vs. custom SLA tracking**: Entitlement Processes provide built-in milestone timers and escalation but require Entitlements to be enabled org-wide. If the org does not use Entitlements elsewhere, the overhead may not be justified for low-volume records requests. A simpler approach — a Date field with a scheduled Flow that checks for approaching deadlines — may suffice.

**Centralized opt-out enforcement vs. per-channel checks**: A centralized utility (Apex class or invocable Flow) that checks directory opt-out before any data is surfaced is architecturally cleaner but adds a dependency to every integration and component. Per-channel checks are simpler to implement incrementally but risk missing a channel when new integrations are added.

## Anti-Patterns

1. **Treating FERPA booleans as self-enforcing** — Setting `HasFerpaParentalDisclosure = true` without building automation that reads and acts on this flag. The flag is informational; enforcement requires FLS, sharing, or query-level logic. This anti-pattern creates a false sense of compliance.

2. **Conflating FERPA and GDPR automation** — Using `Individual.ShouldForget` or GDPR erasure policies for FERPA amendment requests. FERPA requires record retention with amendments; GDPR requires erasure. Mixing the two destroys records that must be kept and retains records that should be deleted.

3. **Ignoring consent expiry** — Creating ContactPointTypeConsent records with `EffectiveTo` dates but never building a scheduled job to check for expired consent. Expired consent continues to appear valid because the LearnerProfile flags are not updated, leading to unauthorized disclosure after the consent window closes.

## Official Sources Used

- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Object Reference (LearnerProfile, Individual, ContactPointTypeConsent) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Education Cloud Documentation — https://help.salesforce.com/s/articleView?id=sf.education_cloud.htm&type=5
- U.S. Department of Education FERPA General Guidance — https://studentprivacy.ed.gov/ferpa
