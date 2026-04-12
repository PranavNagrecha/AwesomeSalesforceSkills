# Examples — Einstein Search Personalization

## Example 1: Enabling Personalized Search Ranking for a Sales Org

**Context:** A mid-size sales org with 50,000+ accounts has rolled out Lightning Experience. Sales reps report that global search returns accounts from other territories and old, closed accounts before their own active accounts. The search experience feels "broken" compared to what they expected from the migration.

**Problem:** Einstein Search is enabled but personalization signals (Activity, Location, Ownership, Specialization) were never turned on. The org is returning results based on keyword relevance alone, with no weighting toward the logged-in user's records.

**Solution:**

```
Setup Path:
  Setup > Einstein Search > Settings

Steps:
  1. Confirm Einstein Search is toggled ON.
  2. Enable "Activity" signal — ranks records the user has recently viewed or frequently accessed.
  3. Enable "Ownership" signal — promotes records the user owns or that are related to records they own.
  4. Enable "Location" signal — ranks records geographically close to the user's accounts and contacts.
  5. Enable "Specialization" signal — ranks records matching the user's typical industry or status patterns.
  6. Save settings.
  7. Inform users that rankings improve over 1–2 weeks as Einstein builds their activity model.
     New users on Lightning will see generic results initially.
```

**Why it works:** Each signal adds a separate ranking dimension. A sales rep who primarily works with Technology accounts in the Pacific Northwest will see those surface first — not because of a static filter, but because Einstein learns from their navigation and ownership patterns. The four signals stack: a record the user owns AND has recently viewed AND is in their region ranks very highly.

---

## Example 2: Configuring Natural Language Search for a Service Team

**Context:** A service org has Cases, Contacts, and Accounts. Agents regularly need to find "my open cases from this week" or "high-priority cases from Acme Corp." The team lead wants to reduce the time agents spend on complex filters and let them search conversationally.

**Problem:** NLS is not enabled. Agents type natural language queries but get keyword-fragmented results ("my", "open", "cases", "week" treated as separate tokens), returning irrelevant records.

**Solution:**

```
Setup Path:
  Setup > Einstein Search > Settings

Steps:
  1. Enable Natural Language Search toggle.
  2. Confirm the objects agents will query are in the NLS-supported set:
       Accounts   — YES (supported)
       Contacts   — YES (supported)
       Cases      — YES (supported)
       Leads      — YES (supported)
       Opportunities — YES (supported)
       Custom objects (e.g. Work_Order__c) — NO (not supported — inform team)

  3. Review FLS for fields commonly referenced in queries:
       Case: Status, Priority, CreatedDate, OwnerId
       Account: Name, BillingCity, Industry
       Contact: Name, AccountId
     Ensure agents' profiles have Read access to these fields. Hidden fields silently
     drop criteria from NLS query parsing.

  4. Test sample queries as an agent-profile user:
       "my open cases from this week"
       "high priority cases from Acme Corp"
       "contacts in Chicago"
     Verify results match expected records.

  5. Document for agents: NLS is English-only. Non-English queries fall back to keyword
     search without error. If an object label has been renamed, agents must use the
     original English name in NLS queries (e.g. "Contact" not "Client" even if
     the label was renamed).
```

**Why it works:** NLS interprets user intent from a controlled English grammar matched against a fixed set of object fields. The underlying parser maps phrases like "my open cases" to `OwnerId = :currentUser AND Status != 'Closed'`. This is invisible to the user — they just get filtered results. The FLS check is critical: a missing field permission silently breaks the filter without alerting the user or admin.

---

## Example 3: Pinning a Key Account to Promoted Search Results

**Context:** A financial services org has a major named account "Horizon Capital" that all account executives need to access frequently. The account name is common enough that it competes with other records in search. AEs want it to always appear first when they search for "horizon."

**Problem:** Because other records contain "horizon" in their names, and personalization signals are user-specific, the named account is not consistently first for all AEs.

**Solution:**

```
Setup Path:
  Setup > Einstein Search > Promoted Search Terms

Steps:
  1. Click "New Promoted Search Term."
  2. Select object: Account.
  3. Search for and select the record: "Horizon Capital."
  4. Enter trigger keywords: "horizon", "horizon capital."
  5. Save.
  6. Verify record sharing: confirm all AEs have at least Read access to Horizon Capital.
     Users without access will not see the promoted result — but no error is shown.
```

**Why it works:** Promoted results bypass personalization ranking entirely. Any user with access who searches for "horizon" will see Horizon Capital at the top, regardless of their individual activity history. This is appropriate for a small set of universally-important records; overuse of promoted results degrades search quality because they compete for the top position across all users.

---

## Anti-Pattern: Assuming NLS Works on a Renamed Object

**What practitioners do:** An admin renames the Contact object label to "Client" for a professional services org. The support team then tells users: "Just search for 'my clients in New York' and Einstein will find them." Users report that the natural language query returns generic keyword results instead of a filtered Contact list.

**What goes wrong:** NLS matches on API names, not custom labels. The parser does not know about the custom label "Client" — it only knows the API name `Contact`. The query "my clients in New York" does not trigger NLS parsing for the Contact object because "clients" is not in the NLS vocabulary for Contacts.

**Correct approach:** Either train users to use the original English object name in NLS queries ("my contacts in New York"), or document the limitation explicitly in training materials. There is no configuration option to add custom object labels to the NLS vocabulary.
