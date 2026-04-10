# Gotchas — Marketing Cloud vs. MCAE Selection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Separate Data Stores — MC Connect Does Not Unify Them

**What happens:** When MCE and MCAE are connected via Marketing Cloud Connect (MC Connect), practitioners assume the two platforms now share a single contact/prospect database. In practice, each platform retains a completely separate data store. MCAE prospects live in the MCAE database and sync to Salesforce CRM Leads and Contacts. MCE subscribers live in Data Extensions inside the MCE business unit. MC Connect creates bridges for sending (MCAE list → MCE send) and for returning engagement data (MCE send stats → MCAE prospect activity), but it does not merge these data stores or create a unified record.

**When it occurs:** When architects design a combined MCE + MCAE implementation and assume that updating a record in one system will update the record in the other without explicit sync configuration.

**How to avoid:** Design the data flow explicitly. Document which system is the master of record for each data attribute. Plan for deduplication and conflict resolution at the Salesforce CRM layer (where both systems ultimately sync). Never assume a change in MCE contact data propagates to an MCAE prospect record or vice versa.

---

## Gotcha 2: MCAE Scoring and Grading Are Not Available in MCE — At All

**What happens:** Practitioners see "Einstein Lead Scoring" in MCE and assume it is equivalent to or a replacement for MCAE's Scoring and Grading. Einstein Lead Scoring in Sales Cloud predicts conversion likelihood using historical win/loss data — it is a different capability from MCAE's activity-based scoring (numeric points per engagement action) and profile-based grading (letter grade based on prospect fit criteria). MCE has no feature equivalent to MCAE Scoring or Grading. There is no configuration, add-on, or workaround within MCE that replicates these capabilities.

**When it occurs:** When a customer selects MCE instead of MCAE expecting to replicate a lead scoring and grading model that currently runs in MCAE (or in a competitor product like HubSpot or Marketo).

**How to avoid:** During requirements gathering, explicitly ask whether lead scoring or grading is required. If yes, MCAE is a mandatory component regardless of other platform decisions. Document this as a hard requirement, not a nice-to-have.

---

## Gotcha 3: MCE Has No Native Salesforce Object Sync

**What happens:** Unlike MCAE, which bidirectionally syncs prospect records with Salesforce Leads and Contacts on a ~2-minute cycle with configurable field-level sync rules, MCE has no native CRM object sync. MCE uses Data Extensions as its data model. Any sync with Salesforce objects (Contacts, Leads, custom objects) requires explicit configuration via Marketing Cloud Connect, custom API integration, or a third-party ETL. Even with MC Connect, the sync is not field-level bidirectional in the same way MCAE's connector operates.

**When it occurs:** When a Salesforce-first organization selects MCE and assumes it will behave like a native Salesforce app — that creating a Lead in Sales Cloud will automatically appear in MCE, or that updating an email address in MCE will update the Contact record in Salesforce.

**How to avoid:** Explicitly scope the data sync architecture when MCE is selected. Determine whether MC Connect covers the required sync use cases or whether a custom integration is needed. Budget time and cost for this integration work upfront, as it is non-trivial for complex orgs.

---

## Gotcha 4: MCAE Prospect Limits Are a Hard Ceiling by Edition

**What happens:** MCAE licenses are sold with a prospect record limit tied to the edition. The limits as of Spring '25 are: Growth (10,000), Plus (10,000), Advanced (10,000), and Premium (75,000). These are not soft guidance limits — they are enforced. An organization that exceeds its prospect limit must either purchase a higher edition or implement a prospect cleanup strategy. Prospects are counted against the limit even if they are marked as archived or unsubscribed unless explicitly deleted.

**When it occurs:** When a practitioner sizes an MCAE implementation based on the number of active marketing prospects rather than the total prospect record count including historical, recycled, or unsubscribed records.

**How to avoid:** Count all prospect records — active, archived, unsubscribed, and historical — when sizing an MCAE edition. Implement a prospect lifecycle management process that deletes or does not import prospects that will never be actively marketed to. If the total count exceeds 75,000 at any foreseeable horizon, MCAE alone is not the right platform at that scale.

---

## Gotcha 5: "Marketing Cloud" Branding Covers Multiple Distinct Products

**What happens:** Customers and practitioners use "Marketing Cloud" to refer to the entire Salesforce marketing portfolio. In practice, "Marketing Cloud" as a branded family includes MCE (Marketing Cloud Engagement), MCAE (Marketing Cloud Account Engagement), Marketing Cloud Intelligence (Datorama), Marketing Cloud Personalization (Interaction Studio), and Marketing Cloud Next. These are not editions of each other — they are separate products with separate pricing, separate data models, and in some cases separate login environments. A customer who purchases "Marketing Cloud" may have purchased only MCE, only MCAE, or some combination.

**When it occurs:** During discovery, when a customer says "we have Marketing Cloud" and the practitioner assumes they have MCE. The customer may in fact have MCAE only — or vice versa.

**How to avoid:** During initial discovery, always confirm the exact products licensed by checking the customer's Salesforce contract or navigating to Setup → Company Information → Licenses. Do not assume "Marketing Cloud" means MCE. Ask explicitly: "Do you have Marketing Cloud Engagement (the one with Journey Builder and Email Studio)? Or Marketing Cloud Account Engagement (the one formerly called Pardot, with Engagement Studio and lead scoring)? Or both?"
