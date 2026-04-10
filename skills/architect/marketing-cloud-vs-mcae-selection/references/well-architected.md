# Well-Architected Notes — Marketing Cloud vs. MCAE Selection

## Relevant Pillars

- **Adaptability** — Platform selection has long-term architectural consequences. Choosing MCE when MCAE is the correct fit (or vice versa) locks the organization into a data model that is difficult and expensive to migrate away from. A well-architected selection decision anticipates future growth in audience size, channel scope, and sales alignment needs, and evaluates each platform's ability to scale along those dimensions without a re-platform.

- **Operational Excellence** — MCE and MCAE have substantially different operational models. MCE requires Data Extension management, Automation Studio scheduling, and sending domain maintenance. MCAE requires prospect lifecycle governance, scoring model calibration, and CRM sync monitoring. The selected platform must align with the team's operational capabilities. Recommending MCE to a team with no data engineering capacity, or MCAE to a team with no CRM admin, creates operational debt.

- **Resiliency** — Each platform has distinct failure modes. MCAE's CRM sync can queue and delay under high Salesforce API load. MCE's Journey Builder can stall when entry source data is malformed. Architects must understand the failure modes of the selected platform and design operational monitoring accordingly. Choosing a platform without understanding its failure modes produces fragile implementations.

- **Security** — Data residency and access control differ between platforms. MCAE prospect data syncs to Salesforce CRM and is subject to Salesforce org-level security (profiles, permission sets, sharing rules). MCE data lives outside the Salesforce org in the Marketing Cloud tenant, with its own role-based access control. In regulated industries (healthcare, financial services), the data store location and access model for each platform must be evaluated against compliance requirements before platform selection.

- **Performance** — MCE is architected for high-volume batch and real-time sending. MCAE is not. Attempting to use MCAE for send volumes or sending frequencies that exceed its infrastructure design will produce deliverability problems and delayed sends. Performance requirements (send volume per hour, real-time journey entry latency) must be confirmed during selection and matched to the platform's documented capabilities.

## Architectural Tradeoffs

**Tight CRM integration vs. channel breadth:** MCAE provides tighter, native CRM integration but is limited to email as a channel. MCE supports multi-channel but requires custom integration for CRM sync. Organizations must choose which tradeoff is more acceptable given their marketing motion.

**Prospect-centric vs. subscriber-centric data model:** MCAE's prospect model (one record per person, synced to a CRM object) is well-suited to B2B where individual prospect identity and activity history matter. MCE's DE model is well-suited to B2C where subscriber lists are large, audience membership is fluid, and individual identity may be less persistent. Forcing a B2C program into MCAE's prospect model creates record management overhead that does not exist in MCE.

**Build vs. buy for capability gaps:** If only one platform can be licensed, the organization must decide whether to accept the capability gaps or invest in custom development to fill them. This tradeoff should be made explicitly, not discovered during implementation.

## Anti-Patterns

1. **Selecting MCAE for high-volume consumer programs** — MCAE's prospect limits, email-only channel coverage, and per-record data model make it structurally inappropriate for consumer-facing, high-volume marketing. This is an architectural mismatch, not a configuration problem. The correct platform for high-volume B2C marketing is MCE. Selecting MCAE in this context will produce hitting edition prospect limits, deliverability problems at volume, and missing channel capabilities.

2. **Selecting MCE and assuming CRM sync is automatic** — MCE is not a native Salesforce application. Its data lives in the Marketing Cloud tenant. CRM synchronization requires Marketing Cloud Connect configuration or custom API integration. Architects who assume CRM sync is automatic will discover this gap during implementation, when it is expensive to address.

3. **Deferring platform selection to implementation** — Platform selection directly determines data model, integration architecture, and operational model. Deferring it to an implementation team without an explicit architect decision creates situations where the wrong platform is partially implemented before the mismatch is discovered. Platform selection must be a named, documented architectural decision made before any implementation work begins.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Differences Between Marketing Cloud Engagement and Account Engagement — https://help.salesforce.com/s/articleView?id=sf.mc_overview_differences.htm
- Salesforce Help: Find Your Account Engagement Edition — https://help.salesforce.com/s/articleView?id=sf.pardot_editions_and_packages.htm
- Salesforce Help: Get Started with Marketing Cloud Next for Account Engagement — https://help.salesforce.com/s/articleView?id=sf.mc_next_account_engagement_get_started.htm
- Salesforce Help: About Marketing Cloud Connect — https://help.salesforce.com/s/articleView?id=sf.mc_co_marketing_cloud_connect.htm
