---
name: apex-managed-sharing-patterns
description: "Grant row-level access programmatically via __Share records when declarative sharing rules cannot express the policy. NOT for OWD, role hierarchy, or criteria-based sharing rule design."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "need to share records based on data from another object"
  - "grant access when a custom field flips to a value"
  - "reciprocal sharing between two users on a record"
  - "manual share using apex"
tags:
  - sharing
  - apex
  - row-level-security
inputs:
  - "Target SObject"
  - "policy rule describing who sees the record and why"
outputs:
  - "Apex class that maintains __Share rows with RowCause and access levels"
  - "tests proving access is granted and revoked"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Apex Managed Sharing Patterns

Apex Managed Sharing inserts rows into the <Object>__Share table with a custom Apex RowCause so that other sharing mechanisms do not reclaim them. Use it only when OWD + sharing rules + teams cannot express the policy — the sharing-selection decision tree covers the ordering. The skill documents the canonical upsert pattern, the RowCause metadata, and the revocation logic required to keep access consistent with the driving data.

## When to Use

When a record must be shared based on a computed condition (e.g., a user listed in a related junction object) and the relationship is too dynamic for criteria-based sharing. Not for simple owner-based sharing or for one-time manual adjustments (use manual share).

Typical trigger phrases that should route to this skill: `need to share records based on data from another object`, `grant access when a custom field flips to a value`, `reciprocal sharing between two users on a record`, `manual share using apex`.

## Recommended Workflow

1. Define a custom Apex RowCause on the object's sharing settings (Metadata API: __Share.RowCause).
2. Write a service class with grant(recordId, userOrGroupId, level) and revoke(recordId, userOrGroupId) methods using upsert on the __Share SObject.
3. Invoke the service from a trigger (after insert/update) or a queueable; never from a before trigger (records may not be committed).
4. On delete of the driving relationship, delete the matching __Share rows using RowCause as the filter so you do not remove rows added by other mechanisms.
5. Write tests that create the driving relationship, runAs the shared user, and assert SELECT visibility; then remove the relationship and assert invisibility.

## Key Considerations

- __Share inserts require the running user to have 'Modify All' on the object or be the record owner. Service classes usually run as system or a dedicated integration user.
- Use the custom RowCause so the platform does not rebuild your shares during owner recalc.
- Group sharing (public groups) scales better than per-user when the population is >50.
- `with sharing` on the service does not stop you from inserting __Share rows; it controls SELECTs inside the class.

## Worked Examples (see `references/examples.md`)

- *Share Opportunity with every user named on a junction object* — Deal-Team__c junction lists users who should see the Opportunity.
- *Batched recalculation after a bulk data load* — 5M junction rows inserted by ETL at night.

## Common Gotchas (see `references/gotchas.md`)

- **Row Cause not deployed** — Insert throws INVALID_ROW_CAUSE; you cannot use RowCause until the sharing setting is enabled.
- **Forgetting to revoke** — Users keep access after leaving the team; compliance failure.
- **'with sharing' misconception** — Developer assumes 'with sharing' prevents managed-sharing inserts.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Inserting __Share rows in a before-trigger (record may not be committed → ghost shares)
- Using RowCause='Manual' from Apex (platform may recalc and remove the row)
- Per-record callouts inside a trigger to fetch the user list — always bulkify

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
