---
name: media-cloud-setup
description: "Media Cloud setup for advertising sales management, audience segmentation, campaign management, revenue management, and cross-channel ad products. NOT for Salesforce Marketing Cloud (use marketing-cloud-account-setup). NOT for Data Cloud audience activation (use data-cloud-activation-patterns)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - media-cloud
  - advertising-sales
  - ad-operations
  - industries
  - audience-segmentation
  - revenue-management
  - campaign-management
triggers:
  - "how do i set up media cloud for ad sales"
  - "advertising order management and ad product catalog"
  - "campaign management for publisher ad inventory"
  - "media cloud revenue recognition and billing"
  - "media buyer seller relationship and deal cycle"
  - "cross channel ad placement linear digital print"
inputs:
  - Media Cloud license and edition
  - Ad product catalog (digital, linear, print, OOH, streaming)
  - Order-to-cash scope (deal, contract, delivery, billing, recognition)
  - Integration points (ad server, billing system, audience platform)
outputs:
  - Media Cloud feature activation plan
  - Ad product catalog + rate card structure
  - Deal-to-contract-to-invoice flow configured
  - Audience segmentation and campaign reporting scaffold
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Media Cloud Setup

Activate when configuring Salesforce Media Cloud for a publisher, broadcaster, streaming service, or ad sales organization. Media Cloud is the industry bundle for advertising sales management — deal-to-cash for media — distinct from Marketing Cloud (marketer outbound) and Data Cloud (CDP / audience store).

## Before Starting

- **Distinguish Media Cloud from Marketing Cloud.** Media Cloud is ad-sales revenue-facing (publisher → advertiser). Marketing Cloud is outbound messaging. Practitioners routinely confuse the two; clarify up front.
- **Map the ad product catalog.** Digital display, connected TV, streaming audio, linear spot, print, out-of-home, sponsorships each have different inventory, delivery, and pricing rules. Catalog design is the hardest part of Media Cloud setup.
- **Identify the ad-server integration.** Most publishers have GAM, FreeWheel, Adswizz, or a proprietary ad server. Media Cloud expects to push order data into that system and pull back delivery metrics.

## Core Concepts

### Deal → Contract → Placement → Delivery

Media Cloud extends Revenue Cloud with media-specific objects. `MediaDeal` holds the negotiated scope. `MediaContract` is signed and versioned. `MediaPlacement` is the buy — a line item per ad product, flight, and target audience. `DeliveryActual` records served impressions from the ad server.

### Audience segmentation and targeting

Audiences come from Data Cloud or a DMP. Media Cloud references audience segments on each Placement. Audience fill rates and forecast availability are live calculations against the ad-server's inventory, not static lookups.

### Revenue recognition per media type

Recognition rules differ by ad product: digital is delivery-based (ASC 606 performance obligation satisfied as impressions serve), linear is broadcast-based, print is issue-date-based. Media Cloud Revenue Management models these with product-specific rules.

## Common Patterns

### Pattern: Digital display order from deal to invoice

`MediaDeal` negotiated → `MediaContract` signed → `MediaPlacement` created per flight / audience / creative → order pushed to ad server → daily delivery pulls back via integration → `DeliveryActual` aggregates → invoice generated from delivered impressions at contracted CPM.

### Pattern: Linear spot avail and rate card

Rate cards are matrix: daypart × program × week. Forecasting avails uses Programmatic Scheduler or integration with a broadcast traffic system. Deals reserve spots; confirmation locks inventory.

### Pattern: Cross-channel bundled sponsorship

One deal spans digital + linear + streaming. A parent Contract; child Placements per channel. Revenue recognition rules differ per child — the Contract aggregates but each Placement runs its own recognition rule.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Ad inventory forecasting | Ad-server integration with cached availability | Live inventory source of truth |
| Audience targeting | Data Cloud + Media Cloud Placement reference | Single audience catalog |
| Rate card management | Media Cloud rate cards per product | Shipped versioning |
| Revenue recognition | Media Cloud Revenue Management | Handles product-specific rules |
| Multi-channel bundle | One Contract, multiple Placements | Aggregated deal, per-channel rec |

## Recommended Workflow

1. Confirm Media Cloud license, Revenue Cloud dependency, and ad-server integration path.
2. Define the ad product catalog per media type (digital, linear, print, OOH, streaming).
3. Build rate cards for each product with appropriate versioning and effective-dating.
4. Configure Deal → Contract → Placement records; validate with a sample flight end-to-end.
5. Integrate with ad server: order push, daily delivery pull, reconciliation job.
6. Configure revenue recognition rules per product family; validate with accounting.
7. Build a campaign performance dashboard; sign off with sales, ops, and finance.

## Review Checklist

- [ ] Ad product catalog covers every media type actually sold
- [ ] Rate cards versioned with effective dates
- [ ] Ad server integration round-trips a flight end-to-end
- [ ] Revenue recognition rules validated by finance
- [ ] Audience segments fed from a single source (Data Cloud or DMP)
- [ ] Cross-channel bundles tested (digital + linear + streaming)
- [ ] Deal pipeline visible to sales leadership in a dashboard

## Salesforce-Specific Gotchas

1. **Ad server delivery volumes are huge.** Loading raw impression logs into Salesforce kills storage; aggregate upstream and sync daily rollups only.
2. **Audience size forecasts expire fast.** A Placement forecast based on yesterday's audience can mislead pricing; refresh on save.
3. **Rate card versioning is not retroactive.** New rate card versions apply to new Placements only; in-flight contracts keep their original rates.

## Output Artifacts

| Artifact | Description |
|---|---|
| Media Cloud activation plan | License, package, and feature toggle order |
| Ad product catalog | Product-level rate/inventory/delivery rules |
| Ad-server integration spec | Endpoints, payload, reconciliation schedule |
| Revenue recognition rulebook | Per-product recognition rule set |

## Related Skills

- `admin/revenue-cloud-cpq-setup` — underlying Revenue Cloud
- `integration/platform-events-basics` — delivery-sync backbone
- `data/data-cloud-activation-patterns` — audience source
