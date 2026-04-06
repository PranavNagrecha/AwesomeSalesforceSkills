# Gotchas — Territory Design Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Date Fields Are Not Valid Assignment Rule Criteria

**What happens:** Territory design documents specify date-based segmentation (e.g., "assign accounts to the Renewal Q2 territory if ContractRenewalDate__c is between April 1 and June 30"). When the ETM administrator attempts to configure this rule, the date field does not appear in the assignment rule criteria field picker.

**When it occurs:** Any time a requirements document calls for date field criteria in ETM account assignment rules. ETM supports only text, picklist, numeric (number, currency, percent), and checkbox field types as assignment rule criteria. Date and datetime fields are explicitly excluded.

**How to avoid:** During requirements gathering, audit every proposed assignment criterion against supported field types. Where date-based segmentation is required, design a numeric or picklist proxy field on the Account object (e.g., a `RenewalQuarter__c` picklist with values Q1/Q2/Q3/Q4, or a `RenewalMonth__c` number field). Document the proxy field in the requirements and create it before ETM configuration begins.

---

## Gotcha 2: Overlapping Assignment Rule Criteria Causes Multi-Territory Assignment

**What happens:** Two territories at the same hierarchy level have assignment rules that can match the same account — for example, Territory A uses `BillingState = 'CA'` and Territory B uses `AnnualRevenue > 1000000`. A large California company matches both rules and is assigned to both territories simultaneously. Both reps gain access to the account, both managers see it in their forecasts, and opportunity territory assignment behaves unpredictably based on territory type priority.

**When it occurs:** When requirements do not specify that primary coverage criteria must be mutually exclusive. Overlay territory types intentionally create multi-territory assignment — but for primary geographic or segment coverage, overlapping criteria is almost always unintentional.

**How to avoid:** As part of requirements definition, explicitly document the mutual exclusivity constraint for primary coverage criteria. For each proposed leaf-level territory, verify that no account could match the criteria of more than one peer territory at the same level. Where business requirements genuinely require shared access (enterprise overlays), document the intent as an overlay territory type with a corresponding priority value to govern OTA.

---

## Gotcha 3: The 1,000-Territory-Per-Model Limit Cannot Be Changed Reactively in Production

**What happens:** An org designs a territory model with 700 territories for the initial rollout, planning to expand to 1,200 territories in the next fiscal year. The model is activated in production at 700. Six months later, the admin begins adding territories and hits the 1,000 limit. The limit increase requires a Salesforce Support case and may take days to resolve — blocking the fiscal year territory realignment project.

**When it occurs:** Enterprise and large commercial organizations planning phased territory expansion. The default limit of 1,000 territories per model applies to Enterprise Edition orgs. Performance and Unlimited Edition orgs can request higher limits, but the increase must be granted by Salesforce Support — it is not self-serve.

**How to avoid:** During requirements gathering, capture the full projected territory count over the expected model lifecycle (not just current state). If the projected count approaches or exceeds 1,000, document a Salesforce Support request for a limit increase as a pre-implementation prerequisite. Include the increase as a gating dependency in the project plan. Do not assume the limit will be automatically raised when production approaches the ceiling.

---

## Gotcha 4: Territory Access Cannot Restrict Below the Org-Wide Default

**What happens:** A requirements document states: "Sales reps should only see accounts in their assigned territory — no other accounts." The administrator configures ETM and sets Account OWD to Private, expecting territory membership to handle all visibility. Reps in adjacent territories still see each other's accounts because Account OWD is Public Read/Write in the org, and territory membership is additive — it adds access but cannot restrict it.

**When it occurs:** When requirements mix territory coverage with access restriction without verifying the underlying OWD configuration. Territory membership adds Read (or Read/Write, per Territory2ObjSharingConfig) access to assigned accounts, but it never narrows access below the OWD floor. If Account OWD is Public Read/Write, every user already sees all accounts regardless of territory membership.

**How to avoid:** During requirements gathering, confirm the Account OWD setting and document it explicitly. If access restriction to territory accounts is a requirement, the OWD must be set to Private (handled in the sharing-and-visibility skill — not in territory design). Territory design requirements should document the expected OWD as a pre-condition and flag any discrepancy between desired access behavior and current OWD.

---

## Gotcha 5: Assignment Rules Must Be Manually Rerun After Rule Changes — There Is No Automatic Backfill

**What happens:** After go-live, the territory admin adds a new territory for the Southwest region and creates assignment rules for it. Existing accounts in Arizona and New Mexico are not automatically re-evaluated against the new rules. Those accounts remain unassigned to the new territory until a manual rule run is triggered. The new Southwest rep cannot see those accounts in their territory, and the accounts are missing from the Southwest territory forecast.

**When it occurs:** Any time new or modified assignment rules are added to an already-active territory model. ETM assignment rules execute automatically on account create and update events, but they do not retroactively re-evaluate existing accounts when the rules themselves change.

**How to avoid:** Document in the requirements that a manual assignment rule run process must be part of any territory realignment or territory addition workflow. Include a post-configuration step in the implementation checklist: after adding or modifying assignment rules, run rules at the model or territory level to backfill existing accounts. For large account volumes, plan the rule run for off-peak hours and monitor Territory2AlignmentLog for completion.
