# Gotchas — Einstein Search Personalization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NLS Is Restricted to Five Standard Objects Only

**What happens:** Natural Language Search only processes conversational queries against Accounts, Contacts, Opportunities, Cases, and Leads. Any query typed against a custom object — or a standard object outside this list (e.g. Contracts, Products, Orders) — falls back silently to keyword search. No error or indicator is shown to the user.

**When it occurs:** Whenever a user types a conversational NLS query and the primary object they are searching is not one of the five supported objects. Common triggers: service orgs with custom "Ticket__c" or "Work_Order__c" objects, field service orgs querying ServiceAppointment, and health orgs querying custom patient objects.

**How to avoid:** Before promising NLS capability to stakeholders, confirm that the objects in scope are in the supported set. If custom objects are required, set expectations that a filter panel or custom search component is needed — NLS cannot be extended to custom objects through any configuration or Apex customization.

---

## Gotcha 2: Object Label Renaming Does NOT Update NLS Vocabulary

**What happens:** When an admin renames an object label in Object Manager (e.g. renaming "Contact" to "Client"), NLS continues to parse queries based on the API name, not the display label. Users who type "my clients from last quarter" expecting NLS to target the Contact object will instead get keyword search results because "clients" is not in the NLS parser vocabulary.

**When it occurs:** Immediately after a label rename is deployed. Affects all users whose mental model of the object uses the renamed label. Particularly common in professional services ("clients"), retail ("customers"), and healthcare ("patients") orgs that rename the Contact object.

**How to avoid:** Document the NLS vocabulary gap in user training. Train users to use the default English object name in NLS queries ("my contacts from last quarter") even when the UI label is different. There is no admin configuration to map custom labels to the NLS parser.

---

## Gotcha 3: Personalization Signals Require Activity History to Be Effective

**What happens:** When a user first starts using Lightning Experience — or when an existing user's activity history is thin — personalization signals have little or no data to work from. Results for new users are essentially unranked by personal signal, appearing closer to generic keyword-match order. This is often reported as "Einstein Search is broken" immediately after a Lightning rollout.

**When it occurs:** During Lightning Experience migrations from Classic, for new users, or for users who have been inactive for an extended period. The activity signal needs recent view and click data; the specialization signal needs a pattern of field values across accessed records.

**How to avoid:** Set user expectations upfront: personalized ranking improves over 1–2 weeks of active use. Consider enabling promoted results for the highest-traffic records to bridge the gap during the ramp-up period. Monitor user feedback 2–4 weeks post-launch rather than immediately after go-live.

---

## Gotcha 4: FLS Silently Drops NLS Field Criteria

**What happens:** If a user types an NLS query that references a field they do not have read access to (due to Field-Level Security), Einstein silently drops that field's criteria from the parsed filter. The query still executes but returns a broader result set than the user intended. No warning or error is displayed.

**When it occurs:** Common in orgs with strict FLS on sensitive fields (e.g. Annual Revenue, Salary, Priority, Custom scoring fields). A user who types "accounts with annual revenue over 1 million" but lacks FLS access to Annual Revenue will receive all accounts, not filtered ones.

**How to avoid:** During NLS rollout, audit FLS for all fields commonly referenced in expected natural language query patterns. Ensure the target user profiles have at least Read access to those fields. Document for admins that future FLS restrictions on indexed fields will silently degrade NLS query precision.

---

## Gotcha 5: Einstein Search is Lightning Experience Only — Classic Users See No Personalization

**What happens:** Einstein Search personalization signals, NLS, and promoted results are only available in Lightning Experience. Users still on Salesforce Classic or on pages rendered in Classic mode see standard keyword search with no personalization or NLS behavior.

**When it occurs:** In mixed-mode orgs where some users or some record types still open in Classic. Also occurs when Classic Override is set on specific object layouts.

**How to avoid:** Confirm that all users who are expected to benefit from Einstein Search personalization have Lightning Experience enabled on their profile and are not using Classic overrides. Map any remaining Classic-mode pages or objects and communicate the limitation to affected users.
