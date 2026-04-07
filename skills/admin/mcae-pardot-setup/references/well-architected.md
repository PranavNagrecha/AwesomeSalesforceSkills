# Well-Architected Notes — MCAE (Pardot) Setup

## Relevant Pillars

- **Security** — The primary pillar. The connector user holds View All Data and Modify All Data — effectively org-wide read/write. Protecting that account from unauthorized use, ensuring it is a service account (not a named person), and regularly auditing its effective permissions are critical. Salesforce User Sync, when configured correctly, also enforces Salesforce identity governance as the single source of truth for MCAE access, reducing the risk of orphaned accounts for departed employees.

- **Operational Excellence** — A correctly configured BU setup creates a repeatable, documented baseline for marketing operations. Field sync rules, campaign connector mappings, and User Sync profile-to-role tables are configuration decisions that must be documented, not left as tribal knowledge. Setup decisions (especially the Recycle Bin sync setting and User Sync enabled state) are difficult to reverse and must be recorded in a configuration register.

- **Reliability** — Sync reliability depends on two independently managed systems (MCAE and Salesforce) staying in alignment. FLS drift (connector user's permissions changing as profiles are modified) is a silent reliability failure mode. Connector verification failures after credential rotation or OAuth token expiry are another. Setup should include monitoring: a periodic connector status check and a sample sync validation as part of the marketing ops runbook.

- **Performance** — MCAE prospect sync is near-real-time for individual record changes, but high-volume scenarios (bulk CRM imports, large list uploads) can create sync queues that take hours to process. Setup should document expected sync latency under normal and bulk-load conditions, and marketing campaigns should not be scheduled immediately after large CRM data imports when sync queues may be backed up.

- **Scalability** — A single-BU setup must account for future growth: additional business units, additional synced fields, and expanded campaign attribution requirements. The connector user permission set approach (separate from the base profile) scales better than modifying the profile directly. Designing the campaign connector configuration with a standard status vocabulary from the start avoids retroactive data hygiene work.

## Architectural Tradeoffs

**Connector User as System Administrator vs. Custom Profile:** Using the System Administrator profile for the connector user is operationally simpler — permissions never need to be updated when new fields are added. However, it violates the principle of least privilege. A compromised connector user credential on a System Admin profile has full org access. The correct tradeoff is a custom profile with only the permissions MCAE requires (View All Data, Modify All Data, API Enabled, Marketing User) plus a permission set for field-level access. This adds ongoing maintenance overhead when new synced fields are added, but contains the blast radius of a credential compromise.

**User Sync Enabled vs. Manual MCAE User Management:** Manual MCAE user management gives admins direct control and does not require Salesforce profile changes to provision or adjust MCAE access. User Sync couples MCAE access to Salesforce profile assignments, which may not always align with the desired MCAE role granularity. However, for organizations where Salesforce is already the authoritative identity system, User Sync is the architecturally correct choice — it eliminates dual administration and ensures deprovisioning is automatic when Salesforce users are deactivated.

**Recycle Bin Sync Enabled vs. Disabled:** Enabling Recycle Bin Sync keeps MCAE and CRM in tighter alignment: a deleted CRM record does not remain as an active prospect generating misleading engagement signals. However, it is destructive and retroactive on first enable. Disabling it means deleted CRM records continue to be reachable as MCAE prospects — potentially sending marketing emails to contacts who have been removed from the CRM for business reasons (churned accounts, former employees, legal requests). The conservative safe default is to leave it disabled until a deliberate review is completed.

## Anti-Patterns

1. **Using a named person's Salesforce login as the connector user** — When the person whose credentials power the v2 connector leaves the company or is deactivated, the connector immediately fails and all sync stops. Every prospect write back, campaign attribution, and user sync update halts until the connector user is changed. Correct approach: create a dedicated service account (e.g., `mcae.connector@company.com`) that is never tied to a named employee and is owned by the Salesforce admin team.

2. **Assuming the connector being Active means all fields are syncing** — An Active connector only guarantees that authentication and basic record sync are working. Field-level FLS on the connector user controls which fields actually transfer. Admins who enable the connector and then map fields in MCAE without auditing FLS are configuring a system that appears to work but silently drops data for any field the connector user cannot see. Correct approach: audit connector user FLS against the MCAE field mapping after every field addition.

3. **Enabling User Sync as a convenience shortcut without pre-migration verification** — Admins sometimes enable User Sync because it sounds like a simplification. If any MCAE user does not have a Salesforce record with a matching email on a mapped profile, that user is orphaned: they lose MCAE access immediately with no warning. In a live marketing org, this means campaign operators lose access mid-execution. Correct approach: run a sync preview, resolve all orphaned accounts, and perform the enablement during a low-activity window with rollback coordination with Salesforce Support pre-arranged.

## Official Sources Used

- Salesforce Help — Connect Account Engagement and Salesforce — https://help.salesforce.com/s/articleView?id=sf.pardot_sf_connector_parent.htm
- Salesforce Help — Configure the Account Engagement Connector User — https://help.salesforce.com/s/articleView?id=sf.pardot_sf_connector_user.htm
- Salesforce Help — Salesforce User Sync Basics — https://help.salesforce.com/s/articleView?id=sf.pardot_user_sync_basics.htm
- Salesforce Help — Account Engagement and Salesforce Sync Overview — https://help.salesforce.com/s/articleView?id=sf.pardot_sf_sync_overview.htm
- Salesforce Help — Managing Multiple Business Units — https://help.salesforce.com/s/articleView?id=sf.pardot_business_units.htm
- Salesforce Help — Account Engagement Tracking Domain Setup — https://help.salesforce.com/s/articleView?id=sf.pardot_tracking_domain.htm
- Salesforce Help — Account Engagement Campaign Sync — https://help.salesforce.com/s/articleView?id=sf.pardot_sf_campaign_sync.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
