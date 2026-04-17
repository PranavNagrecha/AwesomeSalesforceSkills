# Naming Conventions — canonical patterns

Used by agents that create or evaluate metadata (`object-designer`, `field-impact-analyzer`, `csv-to-object-mapper`, `record-type-and-layout-auditor`, `picklist-governor`).

These conventions are drawn from Salesforce's own API naming rules plus the patterns repeatedly endorsed by the `admin/object-creation-and-design` + `admin/custom-field-creation` skills. When agents generate API names, they conform to this file. When agents audit existing metadata, findings are scored against this file.

---

## Hard rules (enforced by Salesforce)

| Element | Rule |
|---|---|
| Custom object API name | Must end with `__c`. Max 40 chars including suffix. PascalCase. No leading numerals. |
| Custom field API name | Must end with `__c`. Max 40 chars. PascalCase. |
| Custom relationship field | Must end with `__c` on the relationship name itself (not `__r`). Inbound relationship uses `<Name>__r` automatically. |
| Namespace prefix (managed package) | 15 chars max, lowercase letters + underscores, starts with a letter, globally unique. |
| API name character set | A–Z, a–z, 0–9, `_`. No consecutive underscores, no trailing underscores before `__c`. |
| Reserved words | Apex keywords + object-reserved words (`Name`, `Id`, `OwnerId`, `CreatedDate`, etc.) cannot be custom-field labels that collide with standard fields on the same sObject. |

**Agent action:** any candidate API name that violates a hard rule is rejected outright and regenerated. No override.

---

## Soft rules (org-level best practice)

### Object names

- **Prefix by domain when the org has > 100 custom objects.** Example: `Billing_Account__c` / `Billing_Invoice__c` / `Billing_Payment__c` over scattered `Account2__c` / `BillItm__c`. Without a prefix, the SfSkills `org-cleanup-and-technical-debt` pattern takes over fast.
- **Singular, not plural.** `Invoice_Line__c` not `Invoice_Lines__c`. The `Plural_Label__c` field handles grammar.
- **Avoid abbreviations shorter than 4 chars.** `Inv__c` is illegible a year later. `Invoice__c` is not.
- **Do not encode the relationship in the object name.** `Account_Contract__c` is wrong if it's really just `Contract__c` with an Account lookup.

### Field names

- **Pattern:** `[Domain_]Concept[_Type]__c` when ambiguity would otherwise creep in. Example: `Account.Credit_Limit_Amount__c` over `Account.Credit__c`.
- **Checkbox fields** SHOULD be named as an affirmative flag — `Is_Active__c`, `Requires_Approval__c` — not `Inactive__c` / `Not_Approved__c`.
- **Date vs DateTime fields** — include `_Date__c` or `_DateTime__c` suffix when confusion is plausible. `Closed_Date__c` vs `Closed_DateTime__c`.
- **Currency fields** — include `_Amount__c` suffix when the field sits next to a non-currency numeric twin. `Total_Amount__c` vs `Total_Count__c`.
- **Percent fields** — include `_Percent__c`. Avoids the "is 0.5 or 50" mental override.
- **External Id fields** — include `_External_Id__c` suffix and set `unique=true` + `externalId=true`. Enables upsert-by-key.
- **Lookup/master-detail fields** — name after the *relationship*, not the target object. `Primary_Account__c` on Case is better than `Account__c` when more than one Account lookup exists or is plausible.
- **Formula fields** — prefix with `Calc_` or use a suffix like `_Calculated__c` when a parallel stored field exists and confusion is plausible. Optional but high-signal.
- **Audit fields** you roll your own (because Field History Tracking is full) — pattern `Last_<Event>_<Attribute>__c`. Example: `Last_Stage_Change_User__c`, `Last_Stage_Change_DateTime__c`.

### Record types

- **Pattern:** `<Object><Persona_or_Process>` — `Case_Billing`, `Case_Technical_Support`, `Opportunity_New_Business`, `Opportunity_Renewal`.
- **Never use sales verbs / marketing terms as record type names** when they mean different things per region — `Opportunity_Enterprise` is geographic-ambiguous across orgs.
- **Description field is required** — agents must populate it with the business persona + a link to the process map. `record-type-and-layout-auditor` flags missing descriptions.

### Validation rules

- **Pattern:** `<Object>_<Field_or_Concept>_<Action>` — `Opportunity_CloseDate_Required`, `Account_Industry_Must_Match_Segment`.
- **Suppress-by-context VRs** that wrap `$Setup.Integration_Bypass__c.IsActive__c` or a Custom Permission should be named `..._Except_<Bypass_Reason>` so the audit agent can classify them.

### Permission sets / Permission Set Groups

- **Pattern for PS:** `<Cloud>_<Persona_or_Feature>_Access` — `Sales_Collaborative_Forecasts_Access`, `Service_Knowledge_Author_Access`, `Integration_Bulk_Loader_Access`.
- **Pattern for PSG:** `<Persona>_Bundle` — `SDR_Bundle`, `Service_Agent_Tier1_Bundle`.
- **Muting PS:** prefix `Mute_` and make the parent PSG explicit. `Mute_Field_Level_Export_In_Sandboxes` muting `SDR_Bundle`.

### Flows

- **Pattern:** `<Object>_<Trigger_or_Channel>_<Intent>` — `Opportunity_AfterUpdate_Sync_Forecast`, `Case_Screen_Close_With_Resolution`.
- **Subflows** — suffix `_Subflow`. Callers can find them at a glance.

### Apex (for admin-authored classes that back flows/actions)

- **Invocable action classes:** `<Object><Verb>Action` — `AccountRefreshSegmentAction`, `CaseDeflectViaKnowledgeAction`.

---

## What the agent should do with this file

When an agent (like `object-designer`, `field-impact-analyzer`, or `csv-to-object-mapper`) is proposing metadata:

1. Generate a **candidate API name** following the rules above.
2. Run the **hard-rules gate** — reject if any hard rule fires.
3. Run the **soft-rules gate** — produce a finding per violated soft rule with severity P1/P2 and a suggested replacement. The human decides overrides.
4. In the **Process Observations** block, note any inconsistency between the candidate name and existing neighbors (e.g. "new field named `IsActive__c` but sibling `Active_Flag__c` already exists on the same object — consider renaming sibling during the same change").

When an agent is **auditing** existing metadata:

1. Score each item against the hard + soft rules.
2. Flag every naming drift the agent noticed, but do not generate migration patches — naming changes break integrations and should be a separate human decision.
3. In Process Observations, surface *patterns* the agent saw — "the `Billing_*` prefix is used on 12 of 15 billing-related objects; the 3 outliers predate the convention". Pattern signal > individual signal.

---

## Source skills

- `skills/admin/object-creation-and-design`
- `skills/admin/custom-field-creation`
- `skills/admin/record-type-strategy-at-scale`
- `skills/admin/validation-rules`
- `skills/admin/permission-set-architecture`
- `skills/admin/picklist-and-value-sets`
