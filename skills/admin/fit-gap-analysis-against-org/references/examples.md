# Examples — Fit-Gap Analysis Against Org

Three worked fit-gap matrices showing the full scoring discipline: classification, effort tier, risk tag, AppExchange evaluation, and downstream-agent handoff.

---

## Example 1: Sales Cloud Greenfield (15-row sample)

**Context:** Mid-market manufacturer rolling out Sales Cloud Enterprise Edition for a 60-rep team. No existing Salesforce footprint. AppExchange policy: open to managed packages.

**Probe results:** EE, Forecasting enabled, no Sales Engagement licenses, Pardot/Account Engagement not yet purchased, no installed managed packages.

| ID | Requirement | Tier | Effort | Risk Tags | Recommended Agent | Notes |
|---|---|---|---|---|---|---|
| REQ-001 | Track Account → Contact → Opportunity hierarchy | Standard | S | — | object-designer | OOTB. |
| REQ-002 | Custom field "Customer Tier" on Account (Bronze/Silver/Gold) | Configuration | S | — | object-designer | Picklist + page-layout placement. |
| REQ-003 | Validation: Opportunity cannot close-won without primary contact role | Low-Code | S | — | flow-builder | Validation rule. |
| REQ-004 | Auto-create renewal Opp 90 days before contract end | Low-Code | M | — | flow-builder | Scheduled-path Record-Triggered Flow. |
| REQ-005 | Route inbound leads by region within 5 minutes | Low-Code | M | governance | flow-builder | Existing Lead Assignment Rules can be re-used; flag governance for naming-convention review. |
| REQ-006 | Forecast by territory hierarchy | Standard | M | — | object-designer | Standard Forecasting + Territory Mgmt. |
| REQ-007 | Real-time leaderboard widget on home page | Custom | L | customization-debt | apex-builder | Forecasting 2.0 may replace within 12 mo; flag for re-evaluation in 6 mo. |
| REQ-008 | Email cadences with multi-step nurture sequence | Unfit | XL | license-blocker | architecture-escalation | Requires Sales Engagement or Pardot — not licensed. Decision tree: integration-pattern-selection.md (point to MAP/MCAE add-on). |
| REQ-009 | Sync Opp updates to NetSuite ERP | Custom | L | — | apex-builder | REST callout via Named Credential; route through `architect/solution-design-patterns`. |
| REQ-010 | List view: "My Open Opps > $50k" | Standard | S | — | object-designer | OOTB list view. |
| REQ-011 | Custom report type: Opp + Products + Account Tier | Configuration | S | — | object-designer | Setup → Report Types. |
| REQ-012 | Slack alert when Opp moves to "Negotiation" | Low-Code | S | — | flow-builder | Slack standard action in Flow. |
| REQ-013 | Approval flow for discounts > 20% | Low-Code | M | — | flow-builder | Approval Process or Flow with approval action. |
| REQ-014 | LWC quote-builder UI | Custom | XL | customization-debt | apex-builder | CPQ would deliver this OOTB; customer declined CPQ on cost. Flag debt + revisit annually. |
| REQ-015 | Audit trail of stage changes | Standard | S | — | object-designer | Standard Field History Tracking on StageName. |

**Why it works:** Each row is anchored to the *actual* org probe. REQ-008 cannot be sneaked into "Custom" by writing a homegrown email engine — that would be an unmaintainable build that competes with MAP. Calling it Unfit forces the architecture conversation.

---

## Example 2: Service Cloud Expansion with 5 GAP Rows

**Context:** Existing Sales Cloud customer adding a 25-agent contact center. No Service Cloud licenses purchased yet at fit-gap time.

**Probe results:** Sales Cloud EE only, zero Service Cloud user licenses, zero Knowledge user licenses, no Omni-Channel SKU, Email-to-Case enabled but not configured.

| ID | Requirement | Tier | Effort | Risk Tags | Recommended Agent | Notes |
|---|---|---|---|---|---|---|
| REQ-101 | Cases auto-routed by topic to agent skill group | Unfit | XL | license-blocker | architecture-escalation | Omni-Channel routing requires Service Cloud + Omni Routing licenses. Decision tree: `automation-selection.md#routing`. |
| REQ-102 | Knowledge articles surfaced in case feed | Unfit | XL | license-blocker | architecture-escalation | Requires Knowledge user license per agent. |
| REQ-103 | Email-to-Case with auto-response template | Configuration | M | — | object-designer | Already enabled; needs setup completion + email templates. |
| REQ-104 | Live chat from public website | Unfit | XL | license-blocker | architecture-escalation | Web Chat / Messaging for Web requires Digital Engagement SKU. |
| REQ-105 | Case escalation rule: 4-hour SLA → manager | Standard | S | — | object-designer | Standard Escalation Rules. |
| REQ-106 | Macro to send canned response + close case | Standard | S | — | object-designer | Standard Macros + Lightning Console. |
| REQ-107 | Custom field "Root-Cause Category" on Case | Configuration | S | — | object-designer | — |
| REQ-108 | Cross-team case transfer with audit | Low-Code | M | governance | flow-builder | Validation rule + Flow + Field History Tracking; check existing transfer governance policy. |

**Why it works:** Four out of eight rows are `license-blocker` Unfit. A fit-gap that classified them as "Custom — build it ourselves" would have produced a multi-month doomed project. The matrix forces the licensing conversation up front.

---

## Example 3: FSC Vertical Project — 4 Rows Belong to Vertical Cloud / AppExchange

**Context:** Wealth-management firm implementing Financial Services Cloud. AppExchange policy: open. nCino is *not* on the table.

**Probe results:** FSC managed package installed, Action Plans Template installed, Compliant Data Sharing enabled, no installed nCino package, custom Household model not yet configured.

| ID | Requirement | Tier | Effort | Risk Tags | Recommended Agent | Notes |
|---|---|---|---|---|---|---|
| REQ-201 | Track Household → Member relationships with shared visibility | Standard | M | — | object-designer | FSC Household model + Compliant Data Sharing. *Re-classified from "Custom" because FSC package installed.* |
| REQ-202 | Financial Account roll-up: total AUM per Household | Standard | S | — | object-designer | Standard FSC roll-up. |
| REQ-203 | KYC document checklist per onboarding case | Standard | M | — | object-designer | FSC Action Plan Templates. |
| REQ-204 | Loan-origination workflow with credit-bureau pull | Unfit | XL | no-AppExchange-equivalent | architecture-escalation | nCino would deliver this; customer rejected nCino. No other AppExchange package matches. Decision tree: `integration-pattern-selection.md#callout-orchestration`. |
| REQ-205 | Suitability questionnaire scored at runtime | Custom | L | — | apex-builder | LWC + Apex for scoring; route via solution-design-patterns. |
| REQ-206 | Branch-office territory rollup of revenue | Standard | M | — | object-designer | Standard Territory Mgmt + reports. |
| REQ-207 | Advisor-client meeting prep dashboard | Low-Code | M | — | flow-builder | Standard Lightning record page + dynamic forms. |
| REQ-208 | Real-time market-data feed in opportunity record | Unfit | XL | no-AppExchange-equivalent | architecture-escalation | Wrong-platform: data-warehouse / mashup territory, not Apex. Decision tree: `integration-pattern-selection.md#realtime-data-virtualization` (Salesforce Connect or external app). |

**Why it works:** REQ-201 / 202 / 203 are the strongest illustration of *probing the org first*: the same three requirements would be Custom in a non-FSC org and Standard with FSC installed. The fit-gap is not stable across orgs — it must be re-run per target.

---

## Anti-Pattern: Scoring the Requirements Without Probing the Org

**What practitioners do:** Take the requirements list, run it through generic Salesforce knowledge, and produce a matrix.

**What goes wrong:** "Standard" rows are wrong because the org's edition or license SKUs do not include the feature. "Custom" rows are wrong because an installed managed package already delivers it. The matrix is unusable as a build plan.

**Correct approach:** Step 2 of the Recommended Workflow exists for a reason. Always probe the org's edition, features, license SKUs, and installed packages *before* scoring a single row.
