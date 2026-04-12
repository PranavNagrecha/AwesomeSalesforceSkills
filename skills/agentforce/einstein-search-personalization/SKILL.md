---
name: einstein-search-personalization
description: "Einstein Search personalization: configure search result ranking, promoted results, searchable objects, and Natural Language Search (NLS) for Lightning Experience. Triggers when users ask about search personalization signals, why search results feel irrelevant, how to enable NLS conversational queries, or how to manage Einstein Search settings in Setup. NOT for SOSL query authoring, Experience Cloud search customization, or Commerce storefront search tuning."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
triggers:
  - "Search results are not relevant to my users — how do I personalize them in Salesforce?"
  - "How do I enable Natural Language Search so users can type conversational queries like 'my open cases from last week'?"
  - "Einstein Search is not surfacing records owned by the logged-in user even though they are the most relevant"
  - "Users want promoted results for specific keywords — how do I configure that in Lightning?"
  - "Which objects support Einstein Search Natural Language Search and how do I restrict scope?"
tags:
  - Einstein-Search
  - personalization
  - NLS
  - search-ranking
  - promoted-results
  - lightning-experience
inputs:
  - Salesforce edition (Enterprise, Performance, or Unlimited required)
  - Whether Lightning Experience is enabled (required — Classic is not supported)
  - List of objects users need in global search scope
  - Whether Natural Language Search is required and which standard objects are in scope
  - Any promoted results or keyword-to-record mappings needed
outputs:
  - Einstein Search Settings configuration guidance (Setup > Einstein Search > Settings)
  - Personalization signal selection recommendations (activity, location, ownership, specialization)
  - NLS enablement steps and supported object checklist
  - Promoted Results configuration instructions
  - Searchable object management guidance
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Einstein Search Personalization

This skill activates when a practitioner needs to configure or troubleshoot Einstein Search personalization in Lightning Experience — including result ranking signals, Natural Language Search (NLS) conversational queries, promoted results, and searchable object management. It does NOT cover SOSL, Experience Cloud search, or Commerce search.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org is on Enterprise, Performance, or Unlimited Edition. Einstein Search personalization is not available on Professional or lower editions.
- Confirm Lightning Experience is enabled. Einstein Search does not run in Salesforce Classic.
- Identify which features the user needs: personalized ranking only, NLS conversational queries, promoted results, or searchable object changes.
- Note that NLS is English-only and scoped to five standard objects only: Accounts, Contacts, Opportunities, Cases, and Leads. If users want NLS on custom objects, it is not possible.

---

## Core Concepts

### Personalization Signals

Einstein Search uses four signals to rank search results for each user:

1. **Activity** — records the user has recently viewed or frequently accessed float to the top of results.
2. **Location** — records geographically close to the user's related records (e.g. accounts in the same city as the user's contacts) are ranked higher.
3. **Ownership** — records the user owns or that are related to records they own (especially Contacts marked as important) are promoted.
4. **Specialization** — records matching the user's typical industry, status, or stage values (learned from their activity patterns) rank higher.

Each signal can be toggled independently in Setup > Einstein Search > Settings. All four are on by default when Einstein Search is enabled. Disabling a signal removes it from the ranking model immediately; re-enabling it requires the model to re-learn from activity, which can take time.

### Natural Language Search (NLS)

NLS lets users type conversational, near-English queries such as "my open cases from last week" or "accounts in New York with annual revenue over 1 million." Einstein parses the query intent and translates it into a structured record filter.

Critical constraints:
- **English only.** NLS does not process queries in other languages. If a user types a query in French or Spanish, the search falls back to keyword matching.
- **Five standard objects only.** NLS works for Accounts, Contacts, Opportunities, Cases, and Leads. It cannot be extended to custom objects or other standard objects (e.g. Contracts, Products).
- **FLS enforced.** Fields referenced in a natural language query that the user cannot see due to Field-Level Security are excluded from the filter. The query still executes but the hidden field criteria are silently ignored.
- **API names drive matching, not labels.** If an admin renames an object's label (e.g. "Contact" to "Client"), NLS still matches on the API name (`Contact`). Users must type the default English object name for NLS to parse the object correctly.

### Promoted Results

Admins can configure specific records to appear at the top of search results for defined keywords. Promoted results are set per object and are visible to all users with access to that record. They do not inherit personalization signals — they always appear first regardless of a user's activity or ownership.

Promoted results are managed in Setup > Einstein Search > Promoted Search Terms.

### Searchable Objects

Admins control which objects appear in the global search scope. Objects not in the searchable set will not appear in global search results at all, regardless of personalization or NLS settings. The default set includes most standard CRM objects; custom objects must be explicitly added.

---

## Common Patterns

### Pattern: Enable Personalized Ranking for High-Volume Sales Users

**When to use:** Sales reps complain that search results show irrelevant records from other territories or old accounts. The org has many records across multiple regions.

**How it works:**
1. Navigate to Setup > Einstein Search > Settings.
2. Ensure Einstein Search is enabled.
3. Enable all four personalization signals: Activity, Location, Ownership, Specialization.
4. Confirm users are active in Lightning Experience — the model requires recent view/activity data to rank effectively. A new user will see generic results until they build activity history.
5. Optionally configure Promoted Results for key accounts or contacts that all reps need fast access to.

**Why not keyword search alone:** Pure keyword search treats every record equally. High-volume orgs with thousands of accounts return poor signal-to-noise. Personalization signals ensure the rep's own accounts surface first.

### Pattern: Enable NLS for Service Users on Standard Objects

**When to use:** Service agents want to search using natural-language queries like "open cases assigned to me from this week" without learning SOSL syntax.

**How it works:**
1. Navigate to Setup > Einstein Search > Settings.
2. Enable Natural Language Search.
3. Confirm that the objects users query are in the supported set: Accounts, Contacts, Opportunities, Cases, Leads. If users want NLS for a custom Service object (e.g. Work Orders, custom Case extensions), inform them this is not supported.
4. Test representative queries in the search bar. Verify that FLS on relevant fields (e.g. Account Name, Case Status) is correct — hidden fields will silently drop filter criteria from NLS queries.
5. Train users that NLS only interprets English. Non-English org languages will not trigger NLS parsing.

**Why not a custom search component:** NLS is zero-code. Building a custom component that interprets natural language would require a separate AI service and significant maintenance overhead.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Users want results ranked by their own activity and record ownership | Enable all four personalization signals in Einstein Search Settings | Signals work together; disabling any one degrades ranking quality for specific user behaviors |
| Users want conversational queries on Accounts, Cases, Contacts, Leads, or Opportunities | Enable Natural Language Search | NLS is declarative and zero-code for these five objects |
| Users want conversational queries on custom objects | Custom search component or filter panel | NLS cannot be extended to custom objects — do not overpromise |
| Admins need specific records to always appear for a keyword | Configure Promoted Search Terms | Promoted results bypass personalization and always rank first |
| Users search in non-English languages | Keyword search only; NLS not applicable | NLS is English-only; no workaround within the native feature |
| Object labels have been renamed | Inform users to use default English object names in NLS queries | NLS matches on API names, not custom labels |

---

## Recommended Workflow

Step-by-step instructions for configuring Einstein Search personalization:

1. **Confirm edition and feature eligibility.** Verify the org is on Enterprise, Performance, or Unlimited Edition with Lightning Experience enabled. Einstein Search personalization is not available on lower editions or in Classic. Check Setup > Einstein Search to confirm the feature is accessible.

2. **Assess user needs.** Interview or document which search improvements are required: relevance personalization (signals), conversational queries (NLS), promoted records, or object scope changes. Identify which objects are in scope and whether any are custom objects (which cannot use NLS).

3. **Configure Einstein Search Settings.** Navigate to Setup > Einstein Search > Settings. Enable Einstein Search if not already on. Toggle the four personalization signals (Activity, Location, Ownership, Specialization) based on user profile — for most CRM use cases, all four should be on. Enable Natural Language Search if conversational queries are required and the target objects are in the supported set.

4. **Configure Promoted Search Terms if needed.** Navigate to Setup > Einstein Search > Promoted Search Terms. For each keyword-to-record pairing required, select the object, choose the record, and add the trigger keywords. Verify the promoted record is accessible to the intended users (sharing rules apply).

5. **Validate NLS behavior with representative queries.** For each NLS-enabled object, run test queries that reflect real user intent (e.g. "open cases from this week", "accounts in Chicago"). Verify results match expected records. Check that FLS is correctly set on any fields referenced in those queries — if a field is hidden, its criteria will be silently excluded.

6. **Communicate language and object scope constraints to users.** Document that NLS is English-only and limited to Accounts, Contacts, Opportunities, Cases, and Leads. If object labels have been renamed, note that NLS still uses the standard English API names for query parsing.

7. **Monitor and iterate.** Personalization signals improve as users build activity history. Revisit settings after 2–4 weeks of active use and survey users on search relevance. Adjust promoted results as business priorities change.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Edition confirmed as Enterprise, Performance, or Unlimited
- [ ] Lightning Experience enabled
- [ ] Personalization signals configured and toggled per user profile analysis
- [ ] NLS enabled only for orgs targeting the five supported standard objects
- [ ] Promoted Search Terms configured where keyword-to-record pinning is required
- [ ] FLS reviewed for fields referenced in expected NLS queries
- [ ] Users informed of English-only NLS constraint and object label vs. API name behavior
- [ ] Searchable object list reviewed to confirm all required objects are included

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **NLS scope is fixed to five standard objects** — Natural Language Search cannot be extended to custom objects, regardless of org configuration or Apex customization. Practitioners who assume NLS is a general-purpose AI query layer will be surprised that their custom "Service_Request__c" object returns no NLS results.
2. **Object label renaming breaks NLS user expectations** — If an admin renames "Contact" to "Client" in Object Manager, NLS still parses on the API name `Contact`. Users typing "my clients in New York" will not get NLS filtering — they must type "my contacts in New York." This is counterintuitive and rarely documented in admin change logs.
3. **Personalization signals require activity history** — New users or users migrating from Classic will see generic, non-personalized results for days or weeks until Einstein builds a sufficient activity model. This is often reported as a bug when Lightning is first rolled out.
4. **Promoted Results ignore personalization** — Promoted records always appear first, even when personalization signals would otherwise rank them lower for a specific user. If a promoted record is not accessible to a user (due to sharing), it is excluded silently — but other promoted records for that keyword still appear.
5. **FLS silently drops NLS criteria** — If a user types "open cases with priority High" and the Priority field is hidden from their profile, Einstein silently ignores that filter. The query executes but returns all open cases, not just high-priority ones. This can return misleading results without any error message.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Einstein Search Settings configuration | Documented state of personalization signals and NLS toggle in Setup |
| Promoted Search Terms list | Keyword-to-record mappings configured for high-value records |
| Searchable objects list | Confirmed set of objects in global search scope |
| NLS constraint communication document | User-facing note on English-only support and supported object list |

---

## Related Skills

- lwc/experience-cloud-search-customization — when search customization is needed for Experience Cloud sites rather than internal Lightning Experience
- apex/commerce-search-customization — when search tuning is needed for B2B or D2C Commerce storefront product search
- architect/knowledge-vs-external-cms — when Einstein Search for Knowledge articles is part of a broader content strategy decision
