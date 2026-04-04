# Org Edition and Feature Licensing — Assessment Template

Use this template when evaluating whether a planned solution can run on the customer's current org edition and licensing.

---

## Org Profile

| Field | Value |
|---|---|
| Salesforce Edition | ___ (confirm from Setup > Company Information) |
| Current add-on licenses (from Feature Licenses) | ___ |
| Org provisioning date (approx.) | ___ |
| Primary cloud (Sales / Service / Platform / other) | ___ |

---

## Required Features Matrix

List all features the solution requires and their edition/licensing status:

| Feature | Platform Feature Name | Minimum Edition | Add-On Required | Included in Current Edition | Enablement Required |
|---|---|---|---|---|---|
| Apex Triggers | Apex | Enterprise+ | No | Yes / No | No (available when edition met) |
| Flow Orchestration | Flow Orchestration | Enterprise+ | No | Yes / No | Yes — Setup > Process Automation Settings |
| Agentforce | Agentforce | Any edition | Yes — Agentforce Add-On | Yes / No | Yes — Setup + PSL assignment |
| Shield Encryption | Platform Encryption | Enterprise+ | Yes — Salesforce Shield | Yes / No | Yes |
| CRM Analytics | Tableau CRM | Not included by default | Yes — CRM Analytics Add-On | Yes / No | Yes |
| Full Sandbox | Full Sandbox | Enterprise+ | 1 included in Enterprise | Yes / No | N/A |
| API Access | API | Enterprise+ (or Pro add-on) | No (Enterprise+) / Yes (Pro) | Yes / No | No |
| ___ | ___ | ___ | ___ | ___ | ___ |

---

## Gap Analysis

| Gap Type | Feature | Action Required |
|---|---|---|
| Edition blocker | ___ | Upgrade to ___ Edition |
| Add-on required | ___ | Purchase ___ add-on license |
| Enablement only | ___ | Enable in Setup: ___ |
| PSL assignment | ___ | Assign PSL to affected users |

---

## Licensing Dependency Documentation (For Technical Design)

Include in the technical design document:

> This solution requires the following licenses in addition to the base [Edition] Edition:
> - [Add-on 1] — required for [Feature]
> - [Add-on 2] — required for [Feature]
>
> PSL assignment is required per user for: [Feature List]
>
> License dependencies must be included in annual renewal planning.

---

## Upgrade Evaluation (If Applicable)

If an edition upgrade is under consideration:

| Factor | Current Edition | Target Edition |
|---|---|---|
| Apex triggers | Not available / Available | Available |
| Sandbox types | ___ | ___ |
| API limits | ___ req/day | ___ req/day |
| Storage | ___ GB | ___ GB |
| Annual cost impact (approx.) | ___ | ___ |
| Migration risks | Profile/PSset changes, sandbox reconfiguration | ___ |

---

## Verification Checklist

- [ ] Edition confirmed from Setup > Company Information
- [ ] Feature Licenses section reviewed for existing add-ons
- [ ] Each required feature mapped to edition or add-on
- [ ] Enable toggles checked for features in current edition
- [ ] PSL assignment steps documented for add-on features
- [ ] Licensing dependencies documented in solution design
- [ ] License renewal calendar updated (if add-ons were purchased)
