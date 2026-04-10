# Multi-BU Marketing Architecture — Work Template

Use this template when designing, reviewing, or documenting a Marketing Cloud Engagement multi-Business-Unit architecture for a specific implementation.

---

## Scope

**Skill:** `multi-bu-marketing-architecture`

**Request summary:** (fill in what the practitioner or stakeholder asked for)

**Org Edition:** [ ] Enterprise 2.0  [ ] Other (note: multi-BU features below require Enterprise 2.0)

---

## Context Gathered

Answer these before proceeding:

- **Number of BUs required:**
- **Relationship between BUs** (brands, regions, markets, channels):
- **Data sharing requirement** (isolation / selective sharing / full sharing):
- **User management model** (central team / delegated BU admins / hybrid):
- **Regulatory or contractual data segregation requirements:**
- **Known constraints** (existing BU structure, migration from legacy, contractual IP requirements):

---

## BU Hierarchy Design

| BU Name | Type | Owning Team | Sending Domain | IP Assignment |
|---|---|---|---|---|
| (Parent BU name) | Parent | Central admin | example.com | Shared / Dedicated |
| (Child BU 1 name) | Child | (team name) | brand1.com | Shared / Dedicated |
| (Child BU 2 name) | Child | (team name) | brand2.com | Shared / Dedicated |

**Hierarchy depth:** [ ] One tier (Parent + Children only)  [ ] Two tiers (document reason below)

**Reason for second tier (if applicable):**

---

## Shared Asset Register

List all Data Extensions and content assets that need to be accessible across BUs:

| Asset Name | Type | Owner BU | Shared To BUs | Permission Level | Data Steward |
|---|---|---|---|---|---|
| Global_Suppression_Master | Data Extension | Parent BU | All Child BUs | Read | (name/role) |
| (asset name) | (type) | (owner) | (list BUs) | Read / Read+Write | (name/role) |

---

## User Provisioning Plan

For each BU, list the users who require access:

### (Child BU 1 Name)

| User | Role | Provisioning Owner | Date |
|---|---|---|---|
| (name) | Marketing Cloud Administrator | (owner) | |
| (name) | Marketing Cloud Viewer | (owner) | |

### (Child BU 2 Name)

| User | Role | Provisioning Owner | Date |
|---|---|---|---|
| (name) | (role) | (owner) | |

**Reminder:** Roles do not cascade from the Parent BU. Each BU requires explicit provisioning.

---

## Shared DE Permission Configuration Steps

For each shared folder in the Parent BU:

1. Navigate to Parent BU > Email Studio > Data Extensions
2. Open the shared folder's properties
3. Select "Shared Data Extension Permissions"
4. Add each Child BU from the list and set permission level (Read or Read/Write)
5. Save and verify by logging into each Child BU and confirming the Shared folder appears

**Verification log:**

| Child BU | Shared Folder Visible? | Verified By | Date |
|---|---|---|---|
| (BU name) | [ ] Yes  [ ] No | | |

---

## Sender Authentication Checklist (Per Child BU)

Complete for each Child BU:

| Item | Child BU 1 | Child BU 2 |
|---|---|---|
| SAP configured | [ ] | [ ] |
| DKIM domain verified | [ ] | [ ] |
| Reply Mail Management set up | [ ] | [ ] |
| IP assignment confirmed | [ ] | [ ] |
| IP warm-up plan in place (if new IP) | [ ] | [ ] |

---

## Data Segregation Confirmation

| Separation Requirement | Mechanism | Verified |
|---|---|---|
| Brand A data not accessible from Brand B BU | Separate Child BUs, no cross-BU Shared DE permissions | [ ] |
| Global opt-outs honored across all BUs | Shared suppression DE, referenced in all BU send activities | [ ] |
| (other requirement) | (mechanism) | [ ] |

---

## Review Checklist

- [ ] Org confirmed as Enterprise 2.0
- [ ] Hierarchy is flat (one tier) unless second tier is explicitly justified and documented
- [ ] All shared DEs have explicit folder-level permissions configured and verified
- [ ] All users provisioned with roles explicitly assigned in each BU they access
- [ ] Global suppression Shared DE is in Parent BU and accessible to all sending Child BUs
- [ ] Brand/market-separated data has no unintended cross-BU Shared DE permissions
- [ ] SAP, DKIM, and Reply Mail Management configured for each Child BU
- [ ] Naming conventions and shared asset register documented

---

## Notes and Deviations

(Record any deviations from the standard patterns and the reason for each)
