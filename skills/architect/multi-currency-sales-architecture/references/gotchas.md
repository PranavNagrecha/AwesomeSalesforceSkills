# Gotchas — Multi-Currency Sales Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ACM Enablement Is Irreversible

**What happens:** Once advanced currency management is enabled in a Salesforce org, there is no way to disable it — not through Setup, not through Salesforce Support. The org permanently uses dated exchange rates for supported objects.

**When it occurs:** An admin enables ACM in production to "try it out" without realizing it is a one-way door. Or ACM is enabled in a sandbox, the team assumes production can be rolled back, and then discovers otherwise.

**How to avoid:** Treat ACM enablement as a permanent architecture decision. Document the rationale, get stakeholder sign-off, and test thoroughly in a full-copy sandbox first. Never enable ACM in production without an explicit go/no-go decision.

---

## Gotcha 2: Roll-Up Summaries Always Use the Static Rate

**What happens:** Roll-up summary fields on parent objects (e.g., Account rolling up Opportunity amounts) always convert child currency values using the single static `CurrencyType` rate, even when ACM is enabled and the child records use dated rates. The parent's rolled-up total will not match the sum of the children's `ConvertedAmount` values.

**When it occurs:** Any org with ACM enabled that uses native roll-up summary fields to aggregate currency amounts across parent-child relationships. The discrepancy grows as exchange rates diverge from the static rate over time.

**How to avoid:** Replace native roll-up summaries with Apex-based or Flow-based aggregation that queries `ConvertedAmount` (which does use dated rates on supported objects) or that manually applies the correct dated rate during summation. Document this limitation for every roll-up summary field in the org.

---

## Gotcha 3: Custom Objects Do Not Use Dated Exchange Rates

**What happens:** Even with ACM enabled, custom objects use the static `CurrencyType` conversion rate — not `DatedConversionRate`. The `ConvertedAmount`-equivalent fields on custom objects recalculate using whatever the current static rate is, ignoring the record's date context.

**When it occurs:** A team creates a custom object (e.g., `Revenue_Forecast__c`) with a currency field and expects it to behave like Opportunity with dated rate conversion. It does not. Converted values shift every time the static rate changes.

**How to avoid:** For custom objects that need date-aware conversion, implement Apex logic that queries `DatedConversionRate` based on the record's relevant date and computes the conversion manually. Store the result in a custom field.

---

## Gotcha 4: Changing a Static Rate Retroactively Affects All Non-ACM Records

**What happens:** Updating the `ConversionRate` field on a `CurrencyType` record immediately recalculates every converted amount field on every record using that currency — across all objects that rely on the static rate. There is no batching, no versioning, and no undo. Historical reports instantly change.

**When it occurs:** An admin updates EUR's exchange rate in Setup. Every EUR-denominated record on custom objects, and on standard objects that do not support dated rates, immediately reflects the new rate. Reports run yesterday now show different numbers.

**How to avoid:** If historical accuracy matters, enable ACM so that supported objects use dated rates and are insulated from static rate changes. For custom objects, snapshot converted values at the time they matter (e.g., close date, invoice date) so they do not shift.

---

## Gotcha 5: Report Currency Follows the Running User's Personal Currency

**What happens:** When a user runs a report with converted amount fields, the values display in that user's personal currency (set in their user record under "Currency"), not the corporate currency. Two users running the identical report see different numbers.

**When it occurs:** Always, unless the report explicitly overrides the display currency using the "Show > Currencies" menu in the report builder. Most users are unaware this setting exists.

**How to avoid:** For finance and executive reports, explicitly set the report's display currency to the corporate currency. For dashboards consumed by mixed audiences, set the dashboard's running user to a service account whose personal currency is the corporate currency. Document which reports use which currency setting.

---

## Gotcha 6: DatedConversionRate Gaps Cause Silent Fallback

**What happens:** If there is no `DatedConversionRate` row covering a particular date for a given currency, Salesforce silently falls back to the static `CurrencyType` rate. There is no error, no warning, and no log entry. The conversion just uses the wrong rate.

**When it occurs:** An integration that loads daily rates misses a day (weekend, holiday, outage). An Opportunity with a CloseDate on the missing date gets converted at the static rate instead of the expected dated rate.

**How to avoid:** Build a monitoring job (scheduled Apex or Flow) that checks for date coverage gaps in `DatedConversionRate` for all active currencies. Alert the operations team immediately when a gap is detected. Ensure weekend and holiday rates are loaded explicitly or that rate ranges span those dates.
