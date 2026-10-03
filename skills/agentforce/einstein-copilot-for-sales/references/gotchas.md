# Gotchas: Einstein Copilot for Sales

Non-obvious behaviours in the Sales Cloud Einstein features this skill covers. Gotchas 1 to 5 are carried from the earlier version; two of them are corrected by sources read for this revision (Gotchas 2 and 3), and claims that rest only on Help articles that do not fetch are marked UNVERIFIED. Gotchas 6 to 13 are cited.

## Gotcha 1: Opportunity Scoring needs enough closed history, counted won and lost separately

**What happens:** The feature is on and the score field is on layouts, but no scores ever appear.

**When it occurs:** The org has too little closed history, or a lopsided pipeline (many wins, few losses).

**How to avoid:** Count closed-won and closed-lost separately before enabling, with the two queries in `references/metadata-examples.md`. The earlier version of this gotcha gave a single combined count query, which contradicts its own two-floor rule; it is corrected there.

**Source:** UNVERIFIED (2026-10-03): the thresholds (at least 200 closed-won and 200 closed-lost in the last 24 months, each open at least two days) and the "Insufficient Data" status come from Help articles that do not fetch. Object Reference: `IqScore` is populated only when Einstein Opportunity Scoring is enabled.

---

## Gotcha 2: Activity Capture data and standard activity reports

**What happens:** Managers build activity reports and do not see emails and events that appear in the Activity Timeline.

**When it occurs:** Activity Capture syncs into its own store and the org relies on standard Task and Event reports.

**How to avoid:** Validate reporting needs before committing to Activity Capture. Check whether "Sync Email as Salesforce Activity" (`EACSettings.syncEmailToCoreActivity`, API 63.0 and later) meets the need, and test it in a sandbox.

**Correction:** the earlier skill said no configuration makes Activity Capture data appear in standard activity reporting. The Metadata API reference now documents a "Sync Email as Salesforce Activity" setting. UNVERIFIED (2026-10-03): exactly which report types then include the synced email.

**Source:** Metadata API reference, EACSettings (`syncEmailToCoreActivity`). UNVERIFIED (2026-10-03): the separate data store and report-type behaviour, which rest on Help articles.

---

## Gotcha 3: "Einstein for Sales" and "Sales Cloud Einstein" are different entitlements

**What happens:** A project promises generative email on the assumption that the add-on excludes it, or promises model-factor reporting on the wrong license.

**When it occurs:** Similar product names are treated as one SKU.

**How to avoid:** Read the Feature Licenses and Permission Set Licenses on the Company Information page and map each feature to the entitlement its documentation names.

**Correction:** the earlier version said the Einstein for Sales add-on does not include generative email drafting. The Spring '26 Generative AI guide lists the Einstein for Sales add-on among those that carry Einstein generative AI usage (Einstein Requests, available in Enterprise, Performance and Unlimited editions with an Einstein for Sales, Einstein for Platform or Einstein for Service add-on), and lists Einstein Sales Emails as a generative feature. Model-factor access, by contrast, is documented against a "Sales Cloud Einstein license".

**Source:** Generative AI guide, Generative AI Billable Usage Types and Einstein Generative AI Features; Object Reference, SalesAIScoreCycle and SalesAIScoreModelFactor special access rules.

---

## Gotcha 4: Pipeline Inspection needs more than the toggle

**What happens:** Pipeline Inspection is enabled and the insights panel is empty.

**When it occurs:** The setting is on but the Setup configuration is incomplete, or scoring has not produced data yet.

**How to avoid:** Finish the Pipeline Inspection setup steps (turn on `enableExpandedPipelineInspectionSetup` to get the guided page). Confirm scoring is producing `IqScore` values before presenting AI insights.

**Source:** Metadata API reference, OpportunitySettings (`enablePipelineInspection` also enables historical trending and "additional configuration in Setup is required"; the Flow Chart needs Revenue Insights access; Revenue Insights is an additional cost). UNVERIFIED (2026-10-03): that the AI insights panel depends on a trained scoring model.

---

## Gotcha 5: Relationship features need mail history

**What happens:** Relationship views show no connections in the first weeks.

**When it occurs:** Activity Capture was turned on at the same time as the relationship feature.

**How to avoid:** Let Activity Capture run first and set expectations that relationship data grows with history. The Buyer Relationship Map has its own setting (`relationshipGraphPref`, API 61.0 and later).

**Source:** Metadata API reference, EACSettings (`relationshipGraphPref`: "whether Buyer Relationship Map is enabled"). UNVERIFIED (2026-10-03): the earlier claims about Einstein Relationship Insights requiring 30 days of Activity Capture history.

---

## Gotcha 6: The score field is `Opportunity.IqScore`, not a custom field

**What happens:** A report, flow or integration references `Opportunity_Score__c` and fails.

**When it occurs:** The field's API name is guessed from its label.

**How to avoid:** Use `IqScore` (label Opportunity Score), an integer from 1 to 99.

**Correction:** the earlier skill named the fields `Opportunity_Score__c` (0 to 99) and `Opportunity_Score_Change__c`. The Object Reference documents `IqScore` on a 1 to 99 scale; UNVERIFIED (2026-10-03): any standard score-change field.

**Source:** Object Reference (Summer '26), Opportunity, `IqScore`.

---

## Gotcha 7: Model factors need a permission that is off by default

**What happens:** An admin cannot see why the model scores the way it does, and a model-factor report is empty for most users.

**When it occurs:** The View Scoring Model Factors permission was never granted.

**How to avoid:** Grant View Scoring Model Factors to the people who review the model. Query `SalesAIScoreModelFactor` for active factors ordered by `ScoreCorrelation`.

**Source:** Object Reference, SalesAIScoreCycle and SalesAIScoreModelFactor ("users need a Sales Cloud Einstein license with the 'View Scoring Model Factors' permission enabled. The permission isn't enabled by default").

---

## Gotcha 8: Activity Capture shares with everyone by default unless you change it

**What happens:** New users' captured emails and events are visible to everyone in the org.

**When it occurs:** Activity Capture is enabled with default settings.

**How to avoid:** Set `enableInboxActivitySharing` to false and `enableEnforceEacSharingPref` to true before rollout, turn on `sensitiveEmailFilter`, and decide `enableEACForEveryonePref` (default true: users without Activity Capture can still see captured emails and events in their timeline).

**Source:** Metadata API reference, EACSettings (`enableInboxActivitySharing` default true sets new users' sharing to Everyone; `enableEACForEveryonePref` default true; `provisionProductivityFeatures` must be true for `enableActivityCapture`).

---

## Gotcha 9: Settings wildcards do not retrieve individual feature settings

**What happens:** A manifest with `<members>*</members>` under `Settings` does not give the team the one settings file it expected, or pulls every setting.

**When it occurs:** Feature settings are listed like other metadata.

**How to avoid:** Name each settings member (`OpportunityScore`, `EAC`, `Opportunity`).

**Source:** Metadata API reference, OpportunityScoreSettings and EACSettings ("The wildcard character * ... doesn't apply to metadata types for feature settings").

---

## Gotcha 10: Einstein Opportunity Insights on mobile is retired

**What happens:** A rollout plan promises deal predictions and follow-up reminders in the mobile app from the old Opportunity Insights feature.

**When it occurs:** Older material is reused.

**How to avoid:** Use Opportunity Scoring and Pipeline Inspection instead and remove Opportunity Insights from plans.

**Source:** Metadata API reference, OpportunitySettings (`enableOpportunityInsightsInMobile` is "Deprecated in API version 59.0 and later because the feature is no longer available").

---

## Gotcha 11: Some sales agents cannot be moved with Bot metadata

**What happens:** A team tries to promote a Sales Coach or Lead Nurturing agent with a Bot manifest and the deploy does not carry it.

**When it occurs:** Sales agents are treated like service agents in the release process.

**How to avoid:** Plan to configure those agents in each org.

**Source:** Metadata API reference, Bot and BotVersion: "Bot metadata deployment and retrieval are not supported for Lead Nurturing and Sales Coach Agents."

---

## Gotcha 12: Sales agent usage is billed per conversation, and the definition differs by agent

**What happens:** Consumption forecasts are wrong because "a conversation" means different things.

**When it occurs:** The SDR and Sales Coach agents are budgeted like chat sessions.

**How to avoid:** Budget SDR by leads contacted (one conversation per initial email to a lead, with a restart consuming another) and Sales Coach by feedback requests (one per "Get Feedback" click).

**Source:** Generative AI guide, Generative AI Billable Usage Types (Agentforce: SDR and Agentforce: Sales Coach subtypes).

---

## Gotcha 13: Agent tone settings do not change email drafting tone

**What happens:** The agent's tone is set to Formal and drafted sales emails still sound casual.

**When it occurs:** Tone is expected to flow into the Draft or Revise Email action.

**How to avoid:** Tune email tone in the action's prompt template, not in agent tone settings. Reps review and customize Einstein Sales Emails before sending.

**Source:** Generative AI guide, Considerations for Agents ("Tone settings don't affect the output of agent actions that have a specified tone, such as Draft or Revise Email") and Einstein Generative AI Features (Einstein Sales Emails).
