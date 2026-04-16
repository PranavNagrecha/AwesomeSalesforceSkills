---
name: data-cloud-consent-and-privacy
description: "Use this skill when implementing consent management, data subject request processing, or data retention policies in Data Cloud — including the ssot__ContactPointConsent__dlm DMO, consent-aware segmentation filters, GDPR/CCPA data deletion requests via Privacy Center or Data Deletion API, and per-DLO retention policy configuration. Triggers on: consent-aware segmentation in Data Cloud, Data Cloud GDPR deletion request, right to be forgotten Data Cloud, ContactPointConsent DMO, Data Cloud data retention policy. NOT for CRM-layer consent management (ContactPointTypeConsent standard objects on Salesforce org — use gdpr-data-privacy skill), not for general GDPR implementation outside Data Cloud."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - data-cloud
  - consent
  - privacy
  - gdpr
  - ccpa
  - data-retention
  - data-subject-rights
  - contactpointconsent
  - deletion-api
inputs:
  - "Data Cloud org with Consent Management features enabled"
  - "Contact Point Consent DMO populated with consent records"
  - "Data Use Purpose definitions configured in Data Cloud"
  - "Privacy Center connected to the Data Cloud org (for deletion requests)"
outputs:
  - "Consent-aware segment filter referencing ssot__ContactPointConsent__dlm"
  - "Data deletion request workflow via Privacy Center or Data Deletion API"
  - "Per-DLO data retention policy configuration"
  - "Consent model gap analysis (opt-out filter completeness check)"
triggers:
  - "Data Cloud segment not respecting opt-out"
  - "GDPR deletion request Data Cloud"
  - "ContactPointConsent DMO filter for segmentation"
  - "Data Cloud data retention policy setup"
  - "right to be forgotten in Data Cloud"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Data Cloud Consent and Privacy

This skill activates when a practitioner needs to implement consent enforcement, data subject request processing (GDPR/CCPA), or data retention policies within Data Cloud. It covers the Contact Point Consent DMO model, consent-aware segmentation, deletion request workflows, and retention configuration. It does NOT cover CRM-layer consent (ContactPointTypeConsent on Salesforce org objects) — use the gdpr-data-privacy skill for that.

---

## Before Starting

Gather this context before working on anything in this domain:

- Data Cloud consent is modeled through the `ssot__ContactPointConsent__dlm` DMO. Consent is NOT automatically enforced at query time — segments do NOT automatically exclude opted-out individuals. Explicit consent filter rules must be added to every segment definition.
- Deletion requests (Right to Be Forgotten) must be submitted via Privacy Center or the Data Deletion API and are processed within 90 days. Erasure propagates across the unified profile but does NOT cascade to downstream activations or external systems already seeded with that data.
- Data retention policies are configured per Data Lake Object in day-based increments with no platform-enforced minimum or maximum retention window.

---

## Core Concepts

### Contact Point Consent DMO

The `ssot__ContactPointConsent__dlm` Data Model Object is the canonical consent record in Data Cloud. Each record links:
- An **Individual** or **Party** (the data subject)
- A **Contact Point** (email, phone, postal address)
- A **Data Use Purpose** (the business purpose for which consent is given or denied)
- A **Consent Status** (Opt In, Opt Out, or Pending)

Consent enforcement requires explicit filtering on this DMO in every segment. The platform does NOT automatically exclude opted-out individuals from query results or segments.

### Consent Is Not Automatically Enforced

This is the single most critical concept: creating a consent record in `ssot__ContactPointConsent__dlm` does NOT block an opted-out individual from appearing in a segment. Segment builders must add explicit filter rules that join to the Consent DMO and exclude opt-out records. Without this explicit filter, segments will include opted-out individuals.

### Data Use Purpose

A **Data Use Purpose** defines the business context for consent (e.g., "Marketing Email", "Product Analytics"). Consent records are linked to a specific Data Use Purpose. Segments for a given marketing channel must filter consent specific to that channel's Data Use Purpose — a blanket "marketing" consent record does not cover all channels if purposes are defined granularly.

### Deletion Requests: Right to Be Forgotten

Data subject deletion requests (GDPR Right to Be Forgotten, CCPA Right to Delete) must be submitted via:
- **Privacy Center** — UI-based submission, initiates a deletion job
- **Data Deletion API** — programmatic submission for bulk or automated deletion

Processing takes up to 90 days. Deletion propagates across the unified profile and all related DMO records linked to the resolved identity. It does NOT automatically cascade to:
- External systems that received data via activation (ad platforms, SFTP exports)
- Marketing Cloud contact records if already activated
- Third-party integrations seeded with the profile data

Practitioners must handle downstream cascade deletion separately.

### Data Retention Policies

Data retention policies are configured per Data Lake Object (DLO) in day-based increments. There is no platform-enforced minimum or maximum retention window. Retention policy deletion is automatic — records older than the configured period are purged. Policies must be designed before data is ingested to avoid retaining data longer than required for compliance.

---

## Common Patterns

### Pattern 1: Consent-Aware Segment Filter

**When to use:** Any segment targeting individuals for marketing, analytics, or activation must exclude opted-out individuals.

**How it works:**

In Data Cloud Segment Builder, add a related filter on `ssot__ContactPointConsent__dlm`:

```
Filter condition:
  ssot__ContactPointConsent__dlm.DataUsePurpose = 'Marketing Email'
  AND ssot__ContactPointConsent__dlm.Status = 'OptIn'
```

This joins the segment to the Consent DMO, returning only individuals with an active opt-in for the specified Data Use Purpose.

**Why not rely on default behavior:** Without this explicit filter, the segment returns ALL individuals regardless of consent status. Sending to opted-out individuals violates GDPR/CCPA and risks regulatory penalties.

### Pattern 2: Programmatic Deletion Request via Data Deletion API

**When to use:** Bulk or automated processing of Right to Be Forgotten requests received from multiple channels.

**How it works:**

```python
# POST to Data Deletion API
import requests

headers = {
    "Authorization": f"Bearer {dc_token}",
    "Content-Type": "application/json"
}

deletion_request = {
    "identifiers": [
        {
            "type": "email",
            "value": "user@example.com"
        }
    ]
}

resp = requests.post(
    f"{dc_base}/api/v1/privacy/deletion",
    headers=headers,
    json=deletion_request
)
job = resp.json()
# Monitor job_id for completion — processing may take up to 90 days
```

**Why not use Privacy Center for bulk:** Privacy Center is UI-based and not suitable for programmatic bulk processing. The Data Deletion API handles automated DSAR processing at scale.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Segment for email marketing | Add OptIn filter on ssot__ContactPointConsent__dlm | Consent not auto-enforced |
| GDPR Right to Be Forgotten request | Privacy Center or Data Deletion API | Triggers 90-day erasure across unified profile |
| Data retention past legal requirement | Configure DLO retention policy in days | Automatic purge after configured window |
| CRM-layer opt-out (Contact object) | gdpr-data-privacy skill | Different layer — CRM ContactPointTypeConsent |
| CCPA Do Not Sell | Map to specific Data Use Purpose opt-out | No built-in CCPA purpose — configure custom purpose |

---

## Recommended Workflow

1. Confirm that `ssot__ContactPointConsent__dlm` is populated with consent records linked to the relevant Data Use Purposes — check in Data Cloud Data Explorer.
2. For every segment, add an explicit consent filter joining to the Consent DMO for the applicable Data Use Purpose and Status = OptIn.
3. For deletion requests: collect identifier type and value (email, phone, etc.) and submit via Privacy Center or Data Deletion API.
4. Monitor deletion job status — processing takes up to 90 days.
5. Identify all downstream systems that received data from activations and initiate cascade deletion separately (e.g., ad platform suppression lists, Marketing Cloud contact deletion).
6. Configure DLO retention policies before data ingestion begins to ensure compliance from day one.
7. Audit segment definitions quarterly to confirm consent filters are still correctly defined as Data Use Purpose definitions evolve.

---

## Review Checklist

- [ ] ssot__ContactPointConsent__dlm is populated with consent records for relevant Data Use Purposes
- [ ] Every marketing/activation segment has an explicit OptIn consent filter
- [ ] Data Use Purpose definitions match the channels being targeted
- [ ] Deletion request workflow is documented and tested (Privacy Center or Data Deletion API)
- [ ] Downstream cascade deletion strategy defined for activated external systems
- [ ] DLO retention policies configured per compliance requirement before ingestion
- [ ] CCPA Do Not Sell mapped to a specific Data Use Purpose opt-out if required

---

## Salesforce-Specific Gotchas

1. **Consent Is Not Automatically Enforced** — Creating a consent record in `ssot__ContactPointConsent__dlm` does NOT prevent opted-out individuals from appearing in segments. Explicit filter rules must be added to every segment. This is the most common compliance gap in Data Cloud implementations.

2. **Deletion Does Not Cascade to External Systems** — Privacy Center and Data Deletion API erasure propagates across the unified profile in Data Cloud but does NOT reach ad platforms, Marketing Cloud contact records, SFTP exports, or other downstream systems that already received the data. Cascade deletion must be orchestrated separately.

3. **No Platform-Enforced Minimum/Maximum Retention Window** — Retention policies can be set to any number of days. There is no guard rail preventing retention periods that are too long for GDPR compliance. Practitioners must design retention policies based on legal requirements, not platform defaults.

4. **CCPA Do Not Sell Has No Default Data Use Purpose** — Data Cloud does not ship with a pre-built "Do Not Sell" Data Use Purpose. Organizations must create a custom Data Use Purpose and map CCPA opt-outs to it explicitly.

5. **Consent Write Propagation Latency** — After a consent record is created or updated in `ssot__ContactPointConsent__dlm`, it may not be immediately reflected in segment membership due to the DSO → DLO → DMO pipeline lag. Do not assume real-time consent enforcement.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Consent-aware segment filter | Segment Builder configuration joining to ssot__ContactPointConsent__dlm with OptIn filter |
| Deletion request script | Python automation for Data Deletion API DSAR submission |
| DLO retention policy plan | Per-DLO retention window (days) mapped to data category compliance requirement |
| Downstream cascade deletion checklist | List of external systems requiring cascade deletion after Data Cloud erasure |

---

## Related Skills

- gdpr-data-privacy — for CRM-layer consent management (ContactPointTypeConsent on Salesforce objects)
- data-cloud-integration-strategy — for understanding the pipeline that brings consent data into Data Cloud
- data-cloud-query-api — for querying consent records in Data Cloud via SQL
