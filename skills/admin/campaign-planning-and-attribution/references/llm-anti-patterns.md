# LLM Anti-Patterns — Campaign Planning And Attribution

Ways an AI assistant gets campaign attribution wrong. Each entry names the wrong output,
why the model produces it, what the guides actually say, and the corrected form.
Line references are into the Summer '26 (v62) text extracts of
[api_meta.pdf](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)
and [object_reference.pdf](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf).

## Anti-Pattern 1: Telling the User to "Enable Customizable Campaign Influence First"

**What the assistant produces:** A step-one instruction to go to Setup and switch CCI on,
often framed as irreversible.

**Why it happens:** Years of blog posts opened that way, and the training data is
dominated by the era when 1.0 was the default.

**What the guide says:** `CampaignSettings.enableCampaignInfluence2` — "Indicates whether
Customizable Campaign Influence is enabled (true) or not (false). When true, Campaign
Influence 1.0 is hidden from users and is no longer active. **The default value is
true**" (api_meta.txt:111568–111571).

**Corrected output:** Tell the user to retrieve `settings/Campaign.settings-meta.xml`
and read the flag. If it is true, the feature is on and 1.0 is already inactive; the
work is model configuration, not enablement.

---

## Anti-Pattern 2: Describing CCI and Campaign Influence 1.0 as Coexisting and Conflicting

**What the assistant produces:** A cleanup plan for "duplicate `CampaignInfluence`
records written by both systems", and a step to disable auto-association rules before
CCI can be trusted.

**Why it happens:** "Two systems, therefore two sets of records" is a plausible
inference, and nothing in the phrasing of most sources rules it out.

**What the guide says:** They are mutually exclusive by contract.
`enableAutoCampInfluenceDisabled` requires `enableCampaignInfluence2` to be **false**
(api_meta.txt:111556–111559), and the Object Reference stamps "This information applies
only to Customizable Campaign Influence and not to Campaign Influence 1.0" on both
`CampaignInfluence` and `CampaignInfluenceModel` (object_reference.txt:57898, 58007).
Campaign Influence 1.0 does not write `CampaignInfluence` rows.

**Corrected output:** State the exclusion, and drop the cleanup phase from the plan.

---

## Anti-Pattern 3: Treating `ActualCost` on the Parent as the Hierarchy Rollup

**What the assistant produces:** A program ROI report or formula built on `ActualCost`
and `AmountWonOpportunities` on the parent campaign, described as "summed from children".

**Why it happens:** Those are the field names a human says out loud, and the guide's
hierarchy fields have long, easy-to-skip names.

**What the guide says:** `ActualCost` is "the amount of money spent to run the campaign"
(object_reference.txt:57100–57105) — that campaign. Hierarchy aggregation lives in
`HierarchyActualCost`, `HierarchyAmountWonOpportunities` and siblings
(object_reference.txt:57273–57359), with a second family named `TotalAmountAllWonOpportunities`,
`TotalNumberofResponses` and so on (object_reference.txt:57704–57810).

**Corrected output:** Name the `Hierarchy*` or `Total*` field explicitly, and say which
family the report uses. Flag that `HierarchyNumberOfLeads` and
`HierarchyNumberOfResponses` are documented with type `currency` despite holding counts
(object_reference.txt:57338, 57354).

---

## Anti-Pattern 4: Querying `CampaignInfluence.Revenue`

**What the assistant produces:** SOQL, a report column, or Apex referencing a `Revenue`
field on `CampaignInfluence`, usually as `SELECT CampaignId, Influence, Revenue …`.

**Why it happens:** "Attributed revenue" is the phrase everyone uses, and `Revenue` is
the obvious field name for it.

**What the guide says:** The field is `RevenueShare` — "the amount of revenue from the
related opportunity attributed to the campaign" (object_reference.txt:57987–57992). The
complete field list is `CampaignId`, `CampaignMemberId`, `ContactId`, `Influence`,
`ModelId`, `OpportunityContactRoleId`, `OpportunityId`, `RevenueShare`
(object_reference.txt:57915–57992), and two of those — `CampaignMemberId` and
`OpportunityContactRoleId` — are documented as "Not available in the UI".

**Corrected output:** `RevenueShare` for currency, `Influence` for the percentage of the
opportunity's `Amount`. When designing a report type, note which two fields the report
builder will not offer.

---

## Anti-Pattern 5: Asserting Time-Decay and U-Shaped Models with Weightings

**What the assistant produces:** A confident table of native or MCAE model types
including time-decay and position-based, often with "first and last touches each receive
40%, middle touches split the remaining 20%".

**Why it happens:** Those are the standard marketing-attribution vocabulary and the
percentages are conventional across the industry — so they generate fluently, with no
signal that they are unsourced for Salesforce specifically.

**What the guide says:** Nothing. `grep -i "time.decay\\|u-shaped\\|position-based\\|multi-touch"`
over `object_reference.txt` and `api_meta.txt` returns no hits. The only model vocabulary
the guides define is the six-value `ModelType` picklist: Primary Campaign Source, Custom,
First Touch, Last Touch, Even Distribution, Data-Driven (object_reference.txt:58105–58118).

**Corrected output:** Give the six `ModelType` values as the grounded list. Present any
Account Engagement model names or weightings as a vendor claim to confirm in the org,
marked UNVERIFIED with the date — never as a platform fact.

---

## Anti-Pattern 6: Stating a Maximum Campaign Hierarchy Depth

**What the assistant produces:** "Salesforce supports up to 5 levels of Campaign
Hierarchy", sometimes elaborated as "root plus 4 children levels", and a design
validated against it.

**Why it happens:** The figure is repeated widely enough to read as settled, and a
number feels more helpful than an admission of uncertainty.

**What the guide says:** No maximum appears in the Object Reference's `Campaign` section,
in the Metadata API guide, or in the App Limits cheat sheet — `grep -i campaign` over
`salesforce_app_limits_cheatsheet.txt` returns zero rows.

**Corrected output:** Say the number is not in the official references you can cite, mark
it UNVERIFIED with the date, and tell the user to confirm it in the target org. The
design advice that follows — encode dimensions as Campaign fields rather than as levels
— stands regardless of what the ceiling turns out to be.

---

## Anti-Pattern 7: Claiming a Bad Campaign Member Status "Fails" or "Is Dropped"

**What the assistant produces:** Advice that a load carrying an undefined member status
will error, or that Account Engagement "silently drops the record" — followed by a
troubleshooting plan that looks for failures.

**Why it happens:** Salesforce rejects most invalid picklist values, so generalising is
reasonable. The failure mode here is the opposite of the general rule.

**What the guide says:** "If the specified Status value isn't a valid status, the API
assigns the default status to the Status field and updates the HasResponded field with
the associated value. However, if the given Campaign doesn't have a default status, the
API assigns the value specified in the call to the Status field, and the HasResponded
field is set to false" (object_reference.txt:58572–58577). The row inserts either way.

**Corrected output:** Warn that the load will report success and the funnel will be
wrong. Direct the reconciliation at counts per status, not at an error log, and note that
the status must be sent as **text**, never as a `CampaignMemberStatus` Id
(object_reference.txt:58504–58513).

---

## Anti-Pattern 8: Presenting Opportunity Contact Roles as a Documented CCI Requirement

**What the assistant produces:** "CCI produces no records without Contact Roles on the
Opportunity" stated as platform behaviour, usually as the first thing to check when
attribution is empty.

**Why it happens:** It is good operational advice and is almost certainly true in
practice, which makes it read like a documented rule.

**What the guide says:** The requirement is not stated. What is documented is that
`CampaignInfluence` carries `ContactId` and `OpportunityContactRoleId` fields
(object_reference.txt:57941–57946, 57963–57969) — circumstantial support, not a quoted
rule.

**Corrected output:** Keep the advice, label the mechanism UNVERIFIED with the date, and
give the user a check they can run in their own org rather than a claim they will repeat.

---

## Anti-Pattern 9: Recommending Model Deactivation as a Reversible Cleanup

**What the assistant produces:** "Deactivate the old model to tidy the picker — you can
always turn it back on."

**Why it happens:** Active/inactive flags are reversible almost everywhere else on the
platform.

**What the guide says:** "Active models can generate campaign influence records.
**Deactivating a model deletes its campaign influence records.** Custom models are always
active and this field is ignored" (api_meta.txt:31892–31895).

**Corrected output:** Call `isActive` a data-retention flag. Recommend changing
`isDefaultModel` when the goal is visibility, exporting the rows first when deactivation
is genuinely wanted, and treating a deploy that flips `isActive` to false as a
data-deleting change that belongs in release change control.
