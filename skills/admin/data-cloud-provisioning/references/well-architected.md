# Well-Architected Notes — Data Cloud Provisioning

## Relevant Pillars

- **Security** — The permission set model is the primary security control for Data Cloud. Misassigning permission sets leads to over-privileged marketing users with platform admin access, or under-privileged admins who cannot complete required configuration tasks. The `cdp_ingest_api` OAuth scope on Connected Apps follows the principle of least privilege: external callers receive only the Data Cloud Ingestion API scope rather than broad `api` access. Data space membership provides an additional layer of data access segregation within a tenant.

- **Reliability** — The irreversibility of the org model choice is the highest-risk reliability concern at provisioning time. A wrong decision here cannot be corrected through a config change or deployment; it requires a full tenant re-provisioning. Treating this decision as a formal architecture milestone with documented sign-off reduces the risk of costly remediation.

- **Operational Excellence** — Provisioning order matters. Attempting to register Ingestion API sources before the Connected App is in place, or assigning users before data spaces exist, creates confusing failure states that are difficult to diagnose without knowing the correct prerequisite sequence. A verified, ordered provisioning checklist eliminates ad hoc troubleshooting.

- **Scalability** — Data space count limits are edition-dependent. Before designing a data space strategy with many partitions (e.g., one per brand or region), confirm the org's edition supports the required count. Exceeding limits requires either a license upgrade or a data space consolidation redesign.

- **Performance** — Not directly applicable at provisioning time, but the data stream registration decisions made during provisioning (e.g., batch vs. streaming ingestion, data space assignment) have downstream performance implications for segment refresh rates and query execution.

---

## Architectural Tradeoffs

**Dedicated Home Org vs. Existing Org**

The primary architectural tradeoff at provisioning time is org model selection. Dedicated Home Org provides full Salesforce-native Data Cloud capabilities including real-time CRM data streams, but requires the overhead of managing a second Salesforce org (separate user management, release cycles, sandbox strategy). The existing-org model reduces operational complexity but permanently caps the feature set available. Neither is universally correct — the decision depends on the customer's feature requirements and operational maturity.

**Fine-grained data spaces vs. single Default data space**

Partitioning data into multiple data spaces provides access control isolation and organizational clarity but introduces ongoing operational complexity: every new user must be explicitly assigned to each relevant data space, and data sharing across spaces requires deliberate design. For most initial implementations, starting with the Default data space and adding partitioned spaces only when a concrete access control or organizational requirement emerges reduces provisioning risk.

**Six standard permission sets vs. custom clones**

Using Salesforce-managed standard permission sets means Salesforce maintains the capabilities as the platform evolves (new features automatically appear for the correct role). Cloning and customizing permission sets transfers maintenance responsibility to the org admin and risks capability gaps after each Salesforce release. Always prefer the standard sets.

---

## Anti-Patterns

1. **Provisioning in the wrong org model to save short-term effort** — Teams that provision Data Cloud in an existing org to avoid standing up a new org frequently discover 6–12 months later that a key feature they now need requires the Dedicated Home Org model. The re-provisioning effort is always larger than the initial org setup effort would have been. Always make the org model decision explicitly and document it.

2. **Using Data Cloud Admin as the catch-all permission set** — Assigning Data Cloud Admin to every Data Cloud user because "it's the most permissive" violates least-privilege principles and specifically blocks Activation Target creation (which requires Marketing Admin or Marketing Manager). Map each user role to the minimum sufficient permission set from the six standard options.

3. **Registering Ingestion API sources before Connected App setup** — Starting source registration before the Connected App with `cdp_ingest_api` scope exists wastes time diagnosing authentication errors that have a simple prerequisite fix. Always complete Connected App setup as a prerequisite step, not as a parallel track.

---

## Cross-Skill References

- `admin/connected-apps-and-auth` — OAuth scope design, Connected App security, and credential rotation patterns that apply to the Ingestion API Connected App
- `admin/data-cloud-identity-resolution` — Next step after provisioning; requires a properly provisioned tenant with data streams registered
- `data/data-cloud-data-model-objects` — Data model mapping work that follows provisioning and data stream registration

---

## Official Sources Used

- Salesforce Help: Turn On Data 360 — https://help.salesforce.com/s/articleView?id=sf.c360_a_setup_provision.htm
- Salesforce Help: Create a Data Space — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_spaces_create.htm
- Salesforce Help: Assign a Data Space Permission Set — https://help.salesforce.com/s/articleView?id=sf.c360_a_assign_permission_set.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
