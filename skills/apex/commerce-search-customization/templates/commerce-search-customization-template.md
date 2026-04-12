# Commerce Search Customization — Work Template

Use this template when configuring or troubleshooting B2B Commerce or D2C Commerce storefront search. Fill every section before marking the task complete.

## Scope

**Skill:** `commerce-search-customization`

**Request summary:** (describe what the buyer, admin, or dev team asked for — e.g., "Add Voltage Rating as a search facet", "Fix missing products in search", "Configure Einstein recommendations")

**Storefront type:** [ ] B2B Commerce  [ ] D2C Commerce

**WebStore ID:** _______________________________

## Context Gathered

Record answers to the Before Starting questions from SKILL.md before touching any configuration.

- **WebStore ID confirmed:** Yes / No
- **Current hourly rebuild count:** _______ of 60
- **Einstein Activity Tracking instrumented:** Yes / No / Not applicable
- **BuyerGroup entitlement audited for affected products:** Yes / No / Not applicable
- **Known constraints:** (e.g., catalog size, active buyer sessions, deployment window)
- **Failure mode confirmed before proceeding:** (entitlement gap / index configuration gap / recommendation data gap / other)

## Current Index Configuration (Pre-Change)

Record the result of `GET /commerce/webstores/{webstoreId}/search/indexes` before making any changes.

```json
{
  "searchableAttributes": [],
  "facetableAttributes": [],
  "sortRules": []
}
```

## Changes Made

### Searchable Attributes

| Field API Name | Priority | Added / Modified / Removed |
|---|---|---|
| | | |

### Facetable Attributes

| Field API Name | Display Type | Display Rank | Added / Modified / Removed |
|---|---|---|---|
| | | | |

### Sort Rules

| Field API Name | Sort Order | Priority | Added / Modified / Removed |
|---|---|---|---|
| | | | |

## Updated Index Configuration (POST Payload)

Paste the complete payload sent to `POST /commerce/webstores/{webstoreId}/search/indexes`:

```json
{
  "searchableAttributes": [],
  "facetableAttributes": [],
  "sortRules": []
}
```

## Index Rebuild Log

| Timestamp (UTC) | Triggered By | Rebuild Status | Confirmed COMPLETED At |
|---|---|---|---|
| | | | |

## Entitlement Policy Audit (if applicable)

| Product ID | Product Name | Entitlement Policy ID | BuyerGroup Count | Gap Found | Resolution |
|---|---|---|---|---|---|
| | | | | | |

## Einstein Activity Tracking Instrumentation (if applicable)

| Page / Component | Event Type | Instrumented | Notes |
|---|---|---|---|
| Product List Page | Page View | Yes / No | |
| Product Detail Page | Product View | Yes / No | |
| Cart Page | Add to Cart | Yes / No | |
| Order Confirmation | Purchase | Yes / No | |

**Data collection start date:** _______________________________

**Estimated recommendation readiness date (2–4 weeks after instrumentation):** _______________________________

## Approach Rationale

(Which pattern from SKILL.md was applied and why? Note any deviations from the standard workflow and the reason.)

## Review Checklist

- [ ] All three attribute sets (searchable, facetable, sort rules) included in every POST payload — none omitted
- [ ] Index rebuild triggered after all configuration changes were batched into one POST
- [ ] Rebuild polled to `COMPLETED` status before testing search behavior
- [ ] Rebuild count verified below 60/hour before triggering
- [ ] Entitlement policy assignment audited for any products reported as missing
- [ ] 2,000 BuyerGroup-per-product limit checked for broadly assigned products
- [ ] Einstein Activity Tracking instrumented before recommendation components enabled (if applicable)
- [ ] Final index configuration payload checked into source control

## Notes and Deviations

(Record any decisions that differ from the standard pattern, and why they were made.)
