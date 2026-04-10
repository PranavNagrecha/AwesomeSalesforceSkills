# Gotchas — Agentforce Service AI Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Work Summaries Requires Einstein Generative AI License — Not Just Service Cloud Einstein

**What happens:** An org purchases Service Cloud Einstein (the add-on SKU) and expects to unlock all Einstein for Service features including Work Summaries. Setup > Service > Einstein Work Summaries is either absent from the menu or visually present but greyed out with no actionable message.

**When it occurs:** Any org that has Service Cloud Einstein (add-on) without Einstein 1 Service edition or the separate Einstein Generative AI entitlement. This is a purchasing pattern common for orgs that adopted Service Cloud Einstein before generative AI features became generally available and have not upgraded.

**How to avoid:** Run the license check as the absolute first step: Setup > Company Information > Feature Licenses (look for `Service Cloud Einstein` seats) and Setup > Company Information > Permission Set Licenses (look for `Einstein Generative AI` PSL). If the Einstein Generative AI PSL is absent, Work Summaries and Service Replies cannot be enabled regardless of any configuration work. Escalate to Salesforce AE for procurement — this is not fixable by configuration.

---

## Gotcha 2: Data Cloud Entitlement Required for Work Summaries in Many Org Configurations

**What happens:** An org has the Einstein Generative AI license (or Einstein 1 Service) and attempts to enable Work Summaries. Setup > Service > Einstein Work Summaries is visible but enabling it fails silently or the feature produces no output after interactions complete.

**When it occurs:** In org configurations where Work Summaries relies on Data Cloud to ingest and process transcript data before the LLM summarization step. This dependency is not prominently documented in all Einstein for Service feature overview pages, and it surfaces only during implementation — not during the sales cycle.

**How to avoid:** Before committing to Work Summaries delivery, verify Data Cloud entitlement in Setup > Data Cloud. If Data Cloud is not provisioned, assess whether the org edition or packaging provides an alternative path, or escalate to Salesforce AE. Do not commit a Work Summaries go-live date until Data Cloud status is confirmed.

---

## Gotcha 3: Reply Recommendations Training Data Job Must Be Run Explicitly — Feature Toggle Is Not Enough

**What happens:** An admin enables Reply Recommendations in Setup, adds the Suggested Replies component to the messaging console layout, and agents see the component but it never displays any suggestions. The feature appears broken, but no error is surfaced in Setup.

**When it occurs:** Always — every org that enables Reply Recommendations without running the Training Data job will see this behavior. The feature toggle enables the feature container but does not trigger model training. Model training only begins after the Training Data job has been explicitly run by an admin.

**How to avoid:** After enabling Reply Recommendations, navigate to Setup > Service > Einstein Reply Recommendations > Training Data and click "Build Training Data." Monitor the job to completion (can take 2–24 hours depending on transcript volume). Model training begins after the job completes. Suggestions appear only after training finishes. Add a mandatory step in the activation checklist: "Confirm Training Data job status = Complete before validating suggestions."

---

## Gotcha 4: Case Classification Lightning Component Must Be Manually Added to Record Pages

**What happens:** An admin enables Case Classification in Setup, the model trains successfully, but agents see no classification suggestions on case records. No error appears in Setup. Everything looks correctly configured.

**When it occurs:** When the admin enables the feature without adding the `Case Classification` component to the Case Lightning record page or service console layout via Lightning App Builder. The feature trains and runs server-side, but classification suggestions are only displayed if the component is on the page.

**How to avoid:** After enabling Case Classification, navigate to Setup > Lightning App Builder, open the Case record page (or the Service Console app page), and explicitly add the `Case Classification` component to the layout. Save and activate the page. The same applies to the Einstein Article Recommendations component for Article Recommendations. Enabling a feature in Setup and adding its UI component to a page are always two separate steps.

---

## Gotcha 5: 1,000-Case Practical Threshold Versus 400-Case Documented Minimum

**What happens:** An admin reviews Salesforce documentation, sees "400 closed cases" as the minimum threshold for Case Classification model training, confirms the org has 600 closed cases, enables the feature, and proceeds. The model trains. In production, classification accuracy is 55–65% — agents override the suggested values constantly and stop trusting the feature within 30 days.

**When it occurs:** The 400-case minimum is the floor at which Salesforce's model training pipeline will run — not the threshold at which predictions are useful. Orgs near the 400-case floor typically produce models with insufficient training signal for reliable predictions. Orgs with fewer than 1,000 closed cases — especially if those cases have inconsistent field population — routinely see poor classification quality.

**How to avoid:** Treat 1,000 closed cases with >80% field completeness for each classified field as the practical readiness threshold for Case Classification. Before enabling the feature, run a Case report on closed cases in the past 18 months: count total cases, and for each field to be classified, calculate what percentage of records have a non-null value. If any field falls below 80% completeness or total closed case count is below 1,000, defer Case Classification and focus on building case history and improving data quality first.

---

## Gotcha 6: Messaging or Voice Channel Must Be Active for Reply Recommendations and Work Summaries

**What happens:** An org wants to enable Reply Recommendations and Work Summaries. The admin enables both features and runs the Training Data job for Reply Recommendations. Neither feature produces output.

**When it occurs:** If no Messaging channel (SMS, WhatsApp, Facebook Messenger via Messaging for In-App and Web, or Digital Engagement) or Voice channel (Einstein Conversation Intelligence) is actively receiving interactions, there is no channel to surface Reply Recommendations in and no transcripts to summarize for Work Summaries. Both features are transcript-dependent — they have no fallback for email-only service operations.

**How to avoid:** Before enabling either feature, confirm that at least one supported Messaging or Voice channel is active and receiving interactions. Email case handling alone does not qualify. If the org handles only email-based cases, Reply Recommendations and Work Summaries are not applicable features for that org's current state.
