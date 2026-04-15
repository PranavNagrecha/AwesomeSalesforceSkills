---
name: data-cloud-provisioning
description: "Use when enabling Data Cloud (Data 360) in an org, creating data spaces, assigning permission sets, registering ingestion API sources, or configuring activation targets. Triggers: 'enable data cloud', 'data spaces setup', 'data cloud permission sets', 'ingestion API connected app', 'activation target setup', 'data cloud licensing', 'dedicated home org vs existing org'. NOT for CRM Analytics configuration, SAQL/recipe authoring, or Data Cloud data model design after provisioning is complete."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
tags:
  - data-cloud
  - data-cloud-provisioning
  - data-spaces
  - ingestion-api
  - activation-targets
  - permission-sets
  - admin
inputs:
  - "Org edition and licensing type (whether Data Cloud is included or must be purchased)"
  - "Deployment model decision: Dedicated Home Org vs. existing Sales/Service Cloud org"
  - "List of user roles and which Data Cloud features they need"
  - "List of data sources planned for ingestion (Salesforce CRM, external APIs, batch files)"
  - "List of activation targets (Marketing Cloud, external ad platforms, etc.)"
outputs:
  - "Data Cloud provisioning checklist with all required setup steps"
  - "Data space design with segment membership and permission set assignments"
  - "Connected App configuration spec for Ingestion API"
  - "Permission set assignment matrix mapping roles to the six standard permission sets"
  - "Activation target setup guide for the planned marketing platforms"
triggers:
  - "enable data cloud in my org"
  - "set up data spaces for data cloud"
  - "assign data cloud permission sets to users"
  - "configure ingestion API connected app"
  - "set up activation targets in data cloud"
  - "dedicated home org vs existing org for data cloud"
  - "data cloud licensing and provisioning steps"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Data Cloud Provisioning

This skill activates when a practitioner needs to turn on Data Cloud in a Salesforce org, make the initial architectural decision between Dedicated Home Org and existing org deployment, create and govern data spaces, assign the correct permission sets to users, register Ingestion API sources, or configure activation targets. It produces a verified provisioning checklist and configuration specifications grounded in Salesforce Help documentation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Org model decision (irreversible):** Determine whether Data Cloud will be provisioned in a Dedicated Home Org or an existing Sales/Service Cloud org. This choice cannot be changed after provisioning. Most Salesforce-native Data Cloud features (natively connected CRM data, real-time segmentation against live CRM records) are only available in the Dedicated Home Org model.
- **License entitlement:** Confirm whether the contract includes Data Cloud credits and which add-ons (e.g., Data Cloud for Marketing, Data Cloud Plus) are active. Provisioning steps differ by license tier.
- **Who does initial enablement:** Only a system administrator with the "Customize Application" permission can turn on Data Cloud (Data 360) from Setup. Verify the administrator who will perform this step has the correct base Salesforce permissions before starting.
- **Ingestion sources and activation targets:** Identify the full list of planned data streams and marketing activation targets up front so the correct OAuth scopes and permission sets are included from day one.

---

## Core Concepts

### Dedicated Home Org vs. Existing Org — The Irreversible Choice

When provisioning Data Cloud, Salesforce offers two deployment models:

- **Dedicated Home Org:** A Salesforce org created specifically to host Data Cloud. CRM data from connected Sales or Service Cloud orgs flows in via the native Salesforce CRM connector. Most advanced features — including real-time segment refresh, natively connected CRM data streams, and Salesforce-native activation — are only supported here.
- **Existing org:** Data Cloud is enabled directly inside an already-running Sales or Service Cloud org. Simpler to start, but a significant subset of Salesforce-native Data Cloud capabilities are unavailable, and the model cannot be migrated to Dedicated Home Org later.

**This decision is permanent.** Once Data Cloud is provisioned in an existing org, the tenant cannot be migrated to a Dedicated Home Org without a full re-provisioning. Treat it as a contract-level architectural decision, not a configuration choice.

### The Six Standard Permission Sets

Data Cloud ships six standard (Salesforce-managed) permission sets. Assigning the wrong set is the most common provisioning mistake because several names sound interchangeable:

| Permission Set | Key Capability |
|---|---|
| Data Cloud Admin | Full admin access to all Data Cloud features |
| Data Cloud Marketing Admin | Admin access plus ability to create Activation Targets |
| Data Cloud User | Standard end-user read/write access |
| Data Cloud Data Aware Specialist | Access to data streams, mappings, and identity resolution |
| Data Cloud Marketing Manager | Campaign-level access without Activation Target creation |
| Data Cloud Marketing Specialist | Segment and activation execution without configuration access |

**Activation Target creation requires either Data Cloud Marketing Admin or Data Cloud Marketing Manager.** No other permission set grants this capability — not even Data Cloud Admin. This surprises most practitioners.

### Data Spaces

A data space is a logical partition within a Data Cloud tenant that groups data streams, data model objects, and calculated insights together. Every tenant starts with a Default data space. Additional data spaces can be created for organizational separation (e.g., by region, brand, or data sensitivity). Users must be assigned to a data space via a permission set before they can see its contents. Data space limits are edition-dependent; check the current Salesforce Data Cloud Limits page for exact counts.

### Ingestion API — Connected App Prerequisite

The Ingestion API allows external systems to push data into Data Cloud via HTTPS. Before registering an Ingestion API source in Data Cloud Setup, a Connected App must exist with the `cdp_ingest_api` OAuth scope. Without this scope, the source registration step in Data Cloud Setup will not be able to authenticate external callers. The Connected App must be created by an administrator and enabled before the Data Cloud Ingestion API source object is created.

---

## Common Patterns

### Pattern 1: Full Tenant Provisioning for a Net-New Data Cloud Implementation

**When to use:** A customer has purchased Data Cloud and needs it fully enabled, with data spaces, users, and at least one data stream registered.

**How it works:**
1. System admin goes to Setup > Data Cloud > Getting Started and clicks "Turn On Data 360."
2. Choose the org model (Dedicated Home Org or existing org) — document the choice before clicking.
3. Wait for provisioning email confirmation (typically minutes, but can take up to 24 hours for large orgs).
4. Create data spaces (Setup > Data Cloud > Data Spaces > New).
5. Assign users to data spaces by assigning the appropriate standard permission set for the data space.
6. Register data streams (CRM connector, cloud storage, or Ingestion API).
7. For Ingestion API sources: create Connected App with `cdp_ingest_api` scope first, then register the source in Data Cloud Setup.

**Why not the alternative:** Skipping the Connected App step means the Ingestion API source registration will fail at the OAuth scope validation step with no actionable error message displayed in the UI.

### Pattern 2: Activation Target Setup for Marketing Cloud Engagement

**When to use:** Data Cloud segments need to be activated to Marketing Cloud Engagement audiences.

**How it works:**
1. Ensure the user performing setup has either the Data Cloud Marketing Admin or Data Cloud Marketing Manager permission set — these are the only sets that grant Activation Target creation.
2. Navigate to Data Cloud > Activation Targets > New.
3. Select "Marketing Cloud Engagement" as the target type.
4. Authenticate using a Marketing Cloud account with API access.
5. Map the Data Cloud org to the correct Marketing Cloud business unit.
6. Validate the target connection before creating segments that reference it.

**Why not the alternative:** Assigning Data Cloud Admin to a marketing user and expecting them to create Activation Targets will fail. Data Cloud Admin does not include Activation Target creation — only Marketing Admin and Marketing Manager do.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New implementation, customer wants full Salesforce-native Data Cloud features | Dedicated Home Org | Only model that supports real-time CRM data streams and native Salesforce activation |
| Customer wants fastest path to pilot with limited budget, existing org already purchased Data Cloud | Existing org (with documented tradeoffs) | Simpler but limited; document the feature gaps and get sign-off on irreversibility |
| User needs to create Activation Targets | Assign Data Cloud Marketing Admin or Data Cloud Marketing Manager | Only two permission sets grant this capability |
| External system pushing data via API | Ingestion API + Connected App with `cdp_ingest_api` scope | Required OAuth scope for all Ingestion API callers |
| Multiple brands or data sensitivity tiers in same tenant | Create separate data spaces | Logical partitioning without separate tenants; check edition limits |
| User only needs to run segments and activations, not configure data streams | Data Cloud Marketing Specialist | Least privilege for execution-only marketers |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the org model decision in writing before touching Setup.** Ask: "Is this a Dedicated Home Org or an existing org?" Document the answer and the tradeoffs accepted. This decision cannot be reversed.
2. **Verify license entitlement and admin prerequisites.** Confirm the org has the Data Cloud license provisioned by the contract team. Confirm the system admin performing setup has "Customize Application" permission.
3. **Enable Data Cloud (Turn On Data 360).** Go to Setup > Data Cloud > Getting Started. Follow the wizard. Wait for the provisioning confirmation before proceeding.
4. **Create data spaces and assign permission sets.** Create the required data spaces (Setup > Data Cloud > Data Spaces > New). Assign standard permission sets to users based on the role-to-permission-set matrix in the Core Concepts section. Do not create custom permission sets for Data Cloud access — use only the six standard sets.
5. **Register data streams.** For Salesforce CRM streams: use the native connector in Data Cloud Setup. For Ingestion API streams: create the Connected App with `cdp_ingest_api` OAuth scope first, then register the source. For cloud storage: configure the appropriate source connector.
6. **Configure Activation Targets.** Assign Marketing Admin or Marketing Manager permission sets to users who need to create Activation Targets. Create the Activation Target record and validate the connection before building segments.
7. **Validate the setup.** Verify each data space shows the expected data streams. Verify each user can access only what their permission set allows. Confirm the Ingestion API Connected App can authenticate a test POST request.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org model decision (Dedicated Home Org vs. existing org) documented and acknowledged as irreversible
- [ ] Data Cloud license entitlement confirmed in the org (not just on the contract)
- [ ] "Turn On Data 360" completed and provisioning confirmation received
- [ ] All required data spaces created
- [ ] Each user assigned the correct standard permission set (not a custom clone) and added to the appropriate data space
- [ ] For Ingestion API: Connected App created with `cdp_ingest_api` OAuth scope before source registration
- [ ] For Activation Targets: assigning user has Data Cloud Marketing Admin or Data Cloud Marketing Manager (not just Data Cloud Admin)
- [ ] Activation Target connection validated via the built-in connection test
- [ ] No hand-edited generated metadata (data spaces and permission sets managed in Setup, not deployed as metadata)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data Cloud Admin cannot create Activation Targets** — Despite its name, the Data Cloud Admin permission set does not grant the ability to create Activation Targets. Only Data Cloud Marketing Admin and Data Cloud Marketing Manager include this capability. Assigning the wrong set to a marketing admin will silently block them from completing the Activation Target wizard with a permissions error.
2. **Ingestion API source registration fails silently without the correct OAuth scope** — If the Connected App used for Ingestion API does not include the `cdp_ingest_api` scope, the source registration in Data Cloud Setup will fail at the authentication step. The error message in the UI does not explicitly mention the missing scope — practitioners often waste time checking network access or Connected App IP ranges instead.
3. **Org model choice is permanent and cannot be undone after provisioning** — Salesforce does not provide a migration path from an existing-org Data Cloud deployment to a Dedicated Home Org model. If the team wants native CRM data streaming or other Dedicated Home Org features after going live on the existing-org model, a full re-provisioning is required (new org, new tenant, re-build all data streams and segments).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Provisioning checklist | Step-by-step list with owner and sign-off for each provisioning task |
| Permission set assignment matrix | Table mapping each user role to the correct Data Cloud permission set |
| Connected App spec for Ingestion API | Name, OAuth scopes (`cdp_ingest_api` required), callback URL, and IP policy |
| Data space design | List of data spaces, their purpose, and which permission sets map to each |
| Activation Target setup guide | Target type, authentication steps, and business unit mapping |

---

## Related Skills

- `admin/connected-apps-and-auth` — Use before registering an Ingestion API source; covers Connected App design, OAuth scope selection, and credential governance
- `admin/data-cloud-identity-resolution` — Use after provisioning is complete; covers identity resolution rule design and unified profile configuration
- `data/data-cloud-data-model-objects` — Use after provisioning; covers mapping ingested data to the Data Cloud data model
- `data/data-cloud-ingestion-api` — Use for detailed Ingestion API payload design and batch/streaming ingestion patterns
- `data/data-cloud-activation-development` — Use when building custom activation targets or extending standard activation
