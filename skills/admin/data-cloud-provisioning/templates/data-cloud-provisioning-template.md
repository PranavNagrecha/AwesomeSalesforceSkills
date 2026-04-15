# Data Cloud Provisioning — Work Template

Use this template when provisioning Data Cloud for a new implementation or when reviewing an existing provisioning configuration.

---

## Scope

**Skill:** `admin/data-cloud-provisioning`

**Request summary:** (fill in what the customer or project has asked for)

**Provisioning type:** [ ] Net-new tenant  [ ] Adding features to existing tenant  [ ] Audit/review of existing setup

---

## Pre-Provisioning Decision Record

### Org Model

**Decision:** [ ] Dedicated Home Org  [ ] Existing Sales/Service Cloud Org

**Rationale:** (document why this model was chosen and what tradeoffs were accepted)

**Stakeholder sign-off:** (name and date — required before provisioning begins)

**Features unavailable with this model (if existing org):**
- Real-time CRM data stream refresh
- (list any other Dedicated Home Org features the project will forgo)

**Acknowledgment that this decision is permanent:** [ ] Yes, documented and accepted

---

## License Entitlement Confirmation

| License / Add-On | Required | Confirmed in Org | Notes |
|---|---|---|---|
| Data Cloud (base) | Yes | [ ] | |
| Data Cloud for Marketing | (if activation targets needed) | [ ] | |
| (other add-ons as applicable) | | [ ] | |

**Confirmed by:** (admin name and date)

---

## Data Spaces Design

| Data Space Name | Purpose / Scope | Who Needs Access | Permission Set |
|---|---|---|---|
| Default | (describe default scope) | | |
| (additional space) | | | |
| (additional space) | | | |

**Edition data space limit confirmed:** [ ] Yes  Limit: ___

---

## User Permission Set Assignment Matrix

Complete this table for every user who will access Data Cloud.

| User Name | Role | Permission Set Assigned | Data Space(s) Assigned | Activation Targets Needed? |
|---|---|---|---|---|
| | | | | [ ] Yes / [ ] No |
| | | | | [ ] Yes / [ ] No |
| | | | | [ ] Yes / [ ] No |

**Reminder:** Only Data Cloud Marketing Admin and Data Cloud Marketing Manager can create Activation Targets. Do not assign Data Cloud Admin to users who need this capability — assign Marketing Admin instead.

---

## Connected App Specification (Ingestion API)

Complete only if one or more Ingestion API sources are planned.

**Connected App Name:** (e.g., "Data Cloud Ingestion API - [Org Name]")

| Setting | Value |
|---|---|
| OAuth Callback URL | |
| Required OAuth Scopes | `api`, `cdp_ingest_api` |
| IP Restrictions | (specify allowed IP ranges or "Relax IP restrictions" if using tokens) |
| Consumer Key (note location, not value) | Stored in: |
| Consumer Secret (note location, not value) | Stored in: |

**Connected App created before source registration?** [ ] Yes (required — do not register Ingestion API source without this)

---

## Data Stream Registration Plan

| Stream Name | Source Type | Data Space | Refresh Type | Status |
|---|---|---|---|---|
| (e.g., CRM Contact Stream) | Salesforce CRM | Default | Real-time | [ ] Registered |
| (e.g., Web Clickstream) | Ingestion API | Default | Streaming | [ ] Registered |
| | | | | [ ] Registered |

---

## Activation Targets

| Target Name | Target Type | Auth Account | Business Unit | Connection Validated |
|---|---|---|---|---|
| | Marketing Cloud | | | [ ] Yes |
| | | | | [ ] Yes |

**Assigned by user with Marketing Admin or Marketing Manager permission set:** [ ] Yes

---

## Provisioning Checklist

Work through each step in order. Do not advance to the next step until the current step is complete.

- [ ] Org model decision documented and signed off
- [ ] License entitlement confirmed in org (not just on contract)
- [ ] System admin has "Customize Application" permission
- [ ] "Turn On Data 360" completed in Setup > Data Cloud > Getting Started
- [ ] Provisioning confirmation email received — do not proceed until this arrives
- [ ] Data spaces created per design table above
- [ ] All standard permission sets assigned per matrix above (no custom clones)
- [ ] Each user added to their assigned data space(s) via Data Spaces > Manage Assignments
- [ ] Connected App created with `cdp_ingest_api` scope (if Ingestion API is planned)
- [ ] All data streams registered and showing active status
- [ ] All Activation Targets created and connection-tested
- [ ] Smoke test: each user logs in and confirms they can see their expected data space and streams

---

## Deviations and Notes

(Record any deviations from the standard provisioning pattern and the reason for each)

| Step | Deviation | Reason | Approved By |
|---|---|---|---|
| | | | |

---

## Sign-Off

**Provisioned by:** ______________________

**Date completed:** ______________________

**Reviewed by:** ______________________
