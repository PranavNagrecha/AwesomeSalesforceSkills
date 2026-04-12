# LLM Anti-Patterns — Einstein Search Personalization

Common mistakes AI coding assistants make when generating or advising on Einstein Search Personalization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming NLS Works Across All Custom Objects

**What the LLM generates:** "Enable Natural Language Search in Einstein Search Settings and users will be able to type conversational queries against any object, including your custom objects like `Service_Request__c` and `Patient__c`."

**Why it happens:** LLMs generalize from the concept of "AI-powered search" and assume NLS is a general-purpose query engine. Training data may contain marketing content about Einstein Search that describes NLS in broad terms without object scope limits.

**Correct pattern:**

```
Natural Language Search (NLS) is supported for five standard objects only:
  - Accounts
  - Contacts
  - Opportunities
  - Cases
  - Leads

NLS cannot be enabled for custom objects or for standard objects outside this list.
For custom objects, use a filter panel, list view filters, or a custom LWC search component.
```

**Detection hint:** Look for statements claiming NLS is "extensible," "configurable for any object," or "works with custom objects." All such statements are incorrect.

---

## Anti-Pattern 2: Claiming Einstein Search Supports Multiple Languages for NLS

**What the LLM generates:** "Einstein Search NLS supports multiple languages. Users in your French org can type 'mes cas ouverts de cette semaine' and the system will understand."

**Why it happens:** LLMs associate Einstein AI capabilities with modern multilingual NLP models. The assumption that any Einstein feature is multilingual is a common extrapolation error.

**Correct pattern:**

```
Einstein Search Natural Language Search is English-only.
Queries typed in any other language (French, Spanish, German, Japanese, etc.)
are not processed by the NLS parser. They fall back to standard keyword search
without any error message or indication to the user.

There is no configuration to enable additional languages.
```

**Detection hint:** Any claim that NLS supports a non-English language, or that "Einstein Search is multilingual," should be flagged as incorrect.

---

## Anti-Pattern 3: Assuming Object Label Renaming Updates NLS Parsing

**What the LLM generates:** "Since you renamed 'Contact' to 'Client' in your org, users can now search for 'my clients in New York' and Einstein NLS will map that to the Contact object."

**Why it happens:** LLMs assume Salesforce metadata is consistent across all layers. Label-driven customization is common in Salesforce, so the assumption that NLS respects custom labels is a natural (but wrong) extrapolation.

**Correct pattern:**

```
Einstein NLS parses queries based on API names, not display labels.
If Contact is renamed to "Client," users must still type "contacts" in NLS queries
for the parser to target the Contact object.

Example:
  WORKS:   "my contacts in New York"
  BROKEN:  "my clients in New York"  (falls back to keyword search)

There is no mapping configuration between custom labels and NLS vocabulary.
Train users to use the default English object names in NLS queries.
```

**Detection hint:** Any response that implies custom object labels are recognized by NLS should be flagged.

---

## Anti-Pattern 4: Treating Promoted Results as a Personalization Feature

**What the LLM generates:** "Configure Promoted Search Terms to personalize search results for each user. You can set different promoted results per user profile."

**Why it happens:** LLMs conflate "personalization" (signal-based per-user ranking) with "promoted results" (static global pinning). Both appear in Einstein Search documentation but are fundamentally different.

**Correct pattern:**

```
Promoted Search Terms are NOT personalized — they are global.
A promoted result for the keyword "horizon" will appear first for ALL users
who search "horizon" and have sharing access to that record.

Promoted results cannot be configured per user, per profile, or per role.
They are org-wide keyword-to-record pins.

Personalization (per-user signal-based ranking) comes from the four signals:
  - Activity
  - Location
  - Ownership
  - Specialization
These are configured in Setup > Einstein Search > Settings and apply automatically
to all users with Einstein Search enabled.
```

**Detection hint:** Any suggestion to "configure promoted results per user" or "use promoted results for personalization" is incorrect.

---

## Anti-Pattern 5: Assuming FLS Violations Produce Errors in NLS Queries

**What the LLM generates:** "If a user doesn't have access to the Priority field and they type 'high priority cases,' Einstein Search will throw a permissions error or display a warning."

**Why it happens:** LLMs apply a general security model where permission violations surface as errors. In most Salesforce APIs, FLS violations during data access produce errors. NLS is an exception — it silently drops the inaccessible field's criteria.

**Correct pattern:**

```
When a user types an NLS query that references a field they cannot see
(due to Field-Level Security), Einstein silently drops that field's filter criteria.

Example:
  User lacks FLS Read on Case.Priority.
  Query: "high priority cases from this week"
  Result: ALL open cases from this week (Priority filter is silently ignored).
  No error. No warning. No indication that the result is incomplete.

To prevent silent result distortion:
  - Audit FLS for fields commonly referenced in expected NLS queries.
  - Ensure target profiles have Read access to those fields before enabling NLS.
  - Test NLS queries as the target profile user, not as a System Administrator.
```

**Detection hint:** Any claim that FLS violations in NLS produce visible errors or warnings should be flagged as incorrect.

---

## Anti-Pattern 6: Suggesting SOSL as an Einstein Search Personalization Mechanism

**What the LLM generates:** "Use SOSL queries with personalization hints to control how Einstein Search ranks results for your users." Or: "Write a SOSL query that replicates the Activity signal behavior."

**Why it happens:** LLMs conflate the SOSL search language (a programmatic query mechanism for Apex and APIs) with Einstein Search's declarative personalization layer. Both deal with "Salesforce search" but are entirely separate systems.

**Correct pattern:**

```
SOSL (Salesforce Object Search Language) is a programmatic query language
used in Apex, APIs, and developer tools. It is NOT related to Einstein Search
personalization and cannot replicate or influence personalization signals.

Einstein Search personalization is configured declaratively in:
  Setup > Einstein Search > Settings

There are no developer APIs, Apex hooks, or SOSL hints that modify
Einstein Search personalization behavior.
```

**Detection hint:** Any response suggesting SOSL query modification as a way to influence Einstein Search result ranking or personalization should be flagged.
