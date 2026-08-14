# Gotchas — Revenue Intelligence Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: You cannot source-control history tracking for `Opportunity.Amount` or `CloseDate`

**What happens:** A team puts Revenue Intelligence's prerequisite field-history tracking into the repo by adding `<trackHistory>true</trackHistory>` to `Opportunity.Amount` and `Opportunity.CloseDate`, deploys, and gets no history rows. The Metadata API scopes the field precisely: `trackHistory` "Indicates whether history tracking is enabled for the field (true) or not (false). Also available for standard object fields (picklist and lookup fields only) in API version 30.0 and later." Amount is a currency field and CloseDate is a date field — neither is a picklist or a lookup, so the standard-object route the guide describes does not cover them.

**When it occurs:** Any org that manages Opportunity configuration as source, which is most orgs with a CI pipeline. It is discovered weeks later, when the change waterfall renders empty because there is no history to diff.

**How to avoid:** Treat Amount and CloseDate history tracking as a Setup step in the deployment runbook, verified per environment, not as a deployable artifact. Verify it explicitly before declaring the environment ready — query `OpportunityFieldHistory` for the field after a test edit rather than trusting that the deploy did it.

---

## Gotcha 2: Field-level tracking silently does nothing until object-level tracking is on

**What happens:** Tracking is enabled for individual fields on a custom object that mirrors Opportunity data, the deploy succeeds with no warning, and no history rows appear. The Metadata API is explicit about the dependency: for `trackHistory` to take effect, "the enableHistory field on the associated standard or custom object must also be true" — where `CustomObject.enableHistory` "Indicates whether the object is enabled for history tracking (true) or not (false)."

**When it occurs:** New custom objects added to the reporting model, and sandboxes where object-level tracking was never turned on because it was inherited from production rather than deployed.

**How to avoid:** Deploy the object and the fields together, and assert the object-level flag first. The failure is silent in both directions — turning the object flag *off* later stops collection with no error either.

---

## Gotcha 3: Four forecast types, hard stop

**What happens:** A rollout designs five forecast types — revenue, quantity, product-family revenue, split revenue, and a territory view — and the fifth cannot be created. The Metadata API states the limit without qualification: on `ForecastingSettings.forecastingTypeSettings`, "The maximum number of forecast types is four."

**When it occurs:** During design, usually after the segmentation has already been promised to sales leadership. The limit is not visible until you try to add the fifth.

**How to avoid:** Budget the four before designing dashboards around them, and make each one earn its slot. `ForecastingType` (API version 52.0 and later) is where the shape of each is declared — `amount` ("If true, the forecast type is based on a revenue measure"), `quantity` ("If true, the forecast type is based on a quantity measure"), `hasProductFamily`, `opportunitySplitType`, `territory2Model`, and `dateType`, whose valid values are `OpportunityCloseDate`, `ProductDate`, `ScheduleDate`, `OLIMeasureCloseDateOnly`, `ProductDateOnly`, and `ScheduleDateOnly`. A revenue-and-quantity split of the same segmentation consumes two of your four.

---

## Gotcha 4: `dateType` determines which date the forecast rolls up on, and changing it re-bases every number

**What happens:** A forecast type is created with `dateType` = `OpportunityCloseDate`, dashboards are built, and then someone switches it to `ScheduleDate` to reflect revenue recognition. Every historical comparison breaks, because the periods each Opportunity falls into have changed.

**When it occurs:** Mid-rollout, when finance and sales discover they were forecasting different things. It is a configuration change with the blast radius of a data migration.

**How to avoid:** Settle the date basis with finance before the first forecast type is created — `OpportunityCloseDate`, `ProductDate` and `ScheduleDate` are the three most commonly used of the six documented values, and they answer different questions. If both bases are genuinely needed, that is two of your four forecast types, decided deliberately, rather than one type flipped later.

---

## Gotcha 5: `ForecastingSettings` changed shape twice, so old deployment scripts fail in confusing ways

**What happens:** A migration script or a copied gist deploys `ForecastingSettings` and fails on unrecognised elements, or succeeds while silently omitting settings that moved. The type has been available since API version 28, but its structure "changed significantly in API version 30.0 and again in API version 53.0" — `globalAdjustmentsSettings` ("The adjustment options for forecasts"), `globalForecastRangeSettings` ("The default periods and range selections in forecasts"), and `globalQuotasSettings` ("Enables or disables quotas in Salesforce Forecasting") are all "Available in API version 53.0 and later."

**When it occurs:** Anywhere the project's `sourceApiVersion` is older than the settings being deployed, and anywhere guidance was copied from a pre-53.0 article.

**How to avoid:** Retrieve `ForecastingSettings` from the target org first and diff against it, rather than hand-authoring. Pin the project's API version above 53.0 before touching forecast configuration. The related toggles — `enableForecasts` ("Set to true to enable and false to disable the functionality") and, for the Einstein scoring that feeds deal insights, `OpportunityScoreSettings.enableOpportunityScoring` ("The default value is false", API version 49.0 and later) — are separate switches and neither implies the other.
