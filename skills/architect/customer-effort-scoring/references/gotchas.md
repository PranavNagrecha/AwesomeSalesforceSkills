# Gotchas — Customer Effort Scoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NPS Bucket Boundaries Are Hardcoded and Cannot Be Customized

**What happens:** The native NPS question type in Salesforce Surveys automatically assigns responses to three fixed buckets: Detractor (0–6), Passive (7–8), Promoter (9–10). These boundaries are hard-wired in the platform. There is no picklist, setting, or formula override that changes the bucket thresholds on an NPS question type. Trying to "reclassify" Detractors starting at 0–5 instead of 0–6 is impossible without abandoning the native NPS question type entirely.

**When it occurs:** This surfaces when an org has an existing NPS program with non-standard bucket definitions (some industries use 0–4 / 5–7 / 8–10) and tries to migrate it to Salesforce Surveys while maintaining their historical benchmark methodology.

**How to avoid:** If the org requires non-standard NPS bucketing, use a plain Rating question type (scale 0–10) instead of the NPS question type. Build the bucketing logic in a formula field on `SurveyResponse`, a Flow that stamps a bucket picklist value, or a CRM Analytics recipe. This adds reporting complexity but preserves methodological continuity. Document the decision in the CX measurement strategy record so future admins understand why the NPS question type was not used.

---

## Gotcha 2: Survey Invitations Sent to Opted-Out Contacts Fail Silently

**What happens:** Creating a `SurveyInvitation` record in a Flow for a Contact with `HasOptedOutOfEmail = true` does not throw an error, does not fault the Flow, and does not surface any warning. The invitation record is created successfully in the database, but no email is delivered. From a reporting perspective, the invitation counts as "sent" but will never convert to a response — making response rates appear artificially low with no obvious explanation.

**When it occurs:** Any time a Record-Triggered Flow creates `SurveyInvitation` records without a prior opt-out check on the Contact. This is particularly common when the Flow was originally built in a sandbox where all test contacts have `HasOptedOutOfEmail = false`, so the bug is invisible during testing.

**How to avoid:** Always add a Flow Decision element before the Create Records step that checks `{!Get_Contact.HasOptedOutOfEmail}` and routes opted-out contacts to an End element (or an alternative path that logs the skip reason). Also check `Contact.Email = null` to avoid invitation creation for contacts without an email address — those also fail silently.

---

## Gotcha 3: CES Response Data Cannot Be Natively Linked to a Case

**What happens:** The standard `SurveyResponse` object does not have a `CaseId` lookup field. When a CES survey is sent post-case-closure, the response is linked to the `SurveyInvitation` and the `Contact` — but not to the specific Case that triggered the survey. This means case-level CES reporting (e.g., "what is the average CES for cases handled by Agent X?") is impossible with standard report types alone.

**When it occurs:** Every post-case survey deployment will encounter this unless the linkage is explicitly designed into the solution. The problem is discovered after deployment when the reporting team tries to build a case-level CES dashboard and finds no direct relationship between `SurveyResponse` and `Case`.

**How to avoid:** At design time, create a custom Lookup field on `SurveyInvitation` (e.g., `Related_Case__c` pointing to Case). In the Flow that creates the `SurveyInvitation`, populate `Related_Case__c` with the triggering Case's ID. Then build a custom Report Type that joins `SurveyInvitation` → `SurveyResponse` with Case via `Related_Case__c`. This enables all case-level CES reporting. An alternative approach uses a custom lookup on `SurveyResponse` itself, but because `SurveyResponse` records are created by the respondent (not the org's automation), populating a custom field on response creation requires a trigger or Flow on `SurveyResponse`.

---

## Gotcha 4: Monthly Response Cap Resets on Calendar Month, Not 30-Day Rolling Window

**What happens:** The Feedback Management response cap (e.g., 1,000 responses/month on Starter tier) resets at the start of each calendar month, not on a rolling 30-day basis. This means an org that sends heavy volume in the last week of one month and the first week of the next month effectively gets double the cap across those two weeks — but an org that hits the cap early in a calendar month is locked out of sending new invitations for the remainder of that month with no overflow mechanism.

**When it occurs:** Most commonly when case volume spikes (e.g., product incident, seasonal peak) in the middle of a calendar month and burns through the entire monthly cap in a few days. New invitations after the cap is reached produce no email sends without any visible error to the agent or admin — they simply do not deliver.

**How to avoid:** Monitor monthly response consumption weekly using the Feedback Management usage report in Setup. Build in a 20% headroom buffer when selecting the license tier (e.g., if expected volume is 800 responses/month, the Starter 1,000 cap has only 25% headroom — consider Growth tier). For orgs with highly variable volume, consider a send rate throttle: instead of sending a CES invitation to every closed case, sample a percentage (e.g., 1 in 3 cases) to stay well within cap while still collecting statistically meaningful data.

---

## Gotcha 5: Scheduled Path Delay of Zero Minutes Sends Survey Before Case Closure Is Confirmed

**What happens:** When a Record-Triggered Flow on Case uses a Scheduled Path with a 0-minute delay (or no Scheduled Path at all — just an Immediate Action), the `SurveyInvitation` is created and the email is dispatched in the same transaction as the case closure. In practice, the customer often receives the "how did we do?" survey email before they have received the case closure notification email — or before they have had a chance to verify that their issue was actually resolved.

**When it occurs:** Whenever a Flow is configured with immediate action logic (no scheduled delay) for survey delivery. This is the default pattern when practitioners copy survey delivery Flows from documentation examples that omit the timing dimension.

**How to avoid:** Always use a Scheduled Path with a minimum 15-minute delay for post-case surveys. For orgs with longer resolution workflows (e.g., technical cases where the fix is pushed overnight), a 30–60 minute delay is more appropriate. The recommended window for CES is 15–60 minutes post-closure. For CSAT, up to 2 hours post-closure is acceptable. Never exceed 24 hours for either CES or CSAT — response rates and data quality degrade significantly beyond that window.
