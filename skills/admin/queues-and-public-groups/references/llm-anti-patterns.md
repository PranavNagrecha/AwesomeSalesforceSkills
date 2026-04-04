# LLM Anti-Patterns — Queues and Public Groups

Common mistakes AI coding assistants make when generating or advising on Queues and Public Groups.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Queues for Objects That Do Not Support Them

**What the LLM generates:** Advice to create a queue and assign Opportunity, Account, or Contact records to it for team-based visibility or routing.

**Why it happens:** LLMs associate "queues" with "team routing" and "Salesforce" generically, without knowledge of which specific standard objects support queue ownership. Training data includes queue references in many contexts, causing overgeneralization.

**Correct pattern:**

```
Queues support: Case, Lead, Order, and custom objects with "Allow Queues" enabled.
Queues do NOT support: Opportunity, Account, Contact, and most other standard objects.

For Opportunity team access: use Public Group + Sharing Rule.
For Opportunity routing: use Assignment Rules (Lead/Case only natively) or Flow to set Owner.
```

**Detection hint:** If the LLM's queue recommendation involves Opportunity, Account, or Contact as the "Supported Object," flag it immediately. Check whether the object is in the supported list.

---

## Anti-Pattern 2: Using a Queue to Grant Read Access (Sharing)

**What the LLM generates:** A recommendation to add users to a queue so they can "see" records, treating queue membership as a sharing mechanism.

**Why it happens:** Queue membership does grant list view visibility to queue-owned records, which LLMs conflate with general record sharing. The LLM misses that this only works for records the queue already owns, and that sharing rules + public groups are the correct mechanism for cross-user access without ownership transfer.

**Correct pattern:**

```
Queue membership grants visibility to records OWNED BY THAT QUEUE only.
It does not grant access to records owned by other users.

To share records across users without changing ownership:
  → Create a Public Group with the intended members
  → Create a Sharing Rule: "Share records owned by [group] with [group]" at desired access level
```

**Detection hint:** Watch for advice like "add the user to the queue so they can view the cases" when the cases are not owned by that queue.

---

## Anti-Pattern 3: Ignoring Queue Email Notification Configuration

**What the LLM generates:** Queue setup instructions that omit the queue email field, or instructions that say the queue will "notify all members" when a record is assigned.

**Why it happens:** LLMs often describe email notification at a high level without knowing the specifics of Salesforce's queue email behavior. The assumption that "the system notifies members" is a general software pattern that does not match Salesforce's actual implementation.

**Correct pattern:**

```
Queue email behavior:
  - One email address per queue (not per member)
  - When a record is assigned to the queue, Salesforce emails ONLY the queue email address
  - Individual queue members do NOT receive individual notifications
  - If queue email is blank, NO notification is sent

To notify individual members: use a Flow that sends emails to each member,
or configure Omni-Channel routing with presence-based delivery.
```

**Detection hint:** If generated guidance says "queue members will be notified" without mentioning the queue email address or distinguishing per-member vs. team-level notification, flag it.

---

## Anti-Pattern 4: SOQL Queries That Filter Queue-Owned Records Without Owner.Type

**What the LLM generates:** SOQL like `WHERE OwnerId = '00G...'` to find queue-owned records, hardcoding a specific queue ID, or simply omitting the ownership filter entirely when the query should cover all queue-owned records.

**Why it happens:** LLMs treat OwnerId as a simple lookup field and hardcode IDs they hallucinate or infer. They often don't know that queue IDs start with `00G` (the Group prefix) versus user IDs which start with `005`, and they don't know the `Owner.Type` relationship field.

**Correct pattern:**

```soql
-- Find all queue-owned Cases:
SELECT Id, CaseNumber, Owner.Name
FROM Case
WHERE Owner.Type = 'Queue'

-- Find Cases owned by a specific named queue:
SELECT Id, CaseNumber, Owner.Name
FROM Case
WHERE Owner.Name = 'Tier 1 Support'
  AND Owner.Type = 'Queue'

-- Avoid: WHERE OwnerId = '00G000000000000' (brittle, org-specific, hardcoded)
```

**Detection hint:** Any SOQL that filters by OwnerId with a hardcoded Id starting with `00G`, or any queue-ownership query that lacks `Owner.Type = 'Queue'`, should be replaced with the correct relationship field pattern.

---

## Anti-Pattern 5: Deeply Nesting Public Groups Without Performance Warning

**What the LLM generates:** A public group hierarchy with 3–5 levels of nesting (groups containing groups containing groups) as a "clean" way to model an org chart for sharing rules, with no mention of sharing recalculation performance impact.

**Why it happens:** LLMs model group hierarchies based on general software design principles (inheritance, composition) without knowing that Salesforce's sharing recalculation engine has quadratic-like scaling behavior with nested groups. Deep nesting looks elegant in design but is operationally risky.

**Correct pattern:**

```
Prefer flat public group membership:
  - Add Roles and Subordinates directly to the group
  - Avoid groups-within-groups beyond one level of nesting
  - Each additional nesting level multiplies sharing recalculation cost

If hierarchy modelling is required:
  - Use Roles and Role Hierarchy (built-in, optimized)
  - Use Territories for account-based hierarchy access
  - Reserve nested public groups for small, stable teams only

Warn stakeholders: changing membership of a deeply nested group
can trigger a long-running sharing recalculation job that affects
org performance and delays access for new members.
```

**Detection hint:** If the LLM's group design includes more than two levels of group nesting and no mention of sharing recalculation risk, flag it and recommend flattening the structure.

---

## Anti-Pattern 6: Treating Public Groups and Queues as Interchangeable

**What the LLM generates:** Instructions that swap "public group" and "queue" as if they are the same thing, or advice to "use a queue or a public group" for both routing and sharing without distinguishing the two.

**Why it happens:** Both constructs aggregate users and are found in Salesforce Setup under similar navigation paths. LLMs trained on informal documentation often conflate them.

**Correct pattern:**

```
Queue:    → owns records → routes work → used with Case, Lead, Order, queue-enabled custom objects
           → queue email notification → members claim ownership from shared pool

Public Group: → does NOT own records → grants access via sharing rules/manual sharing
               → used for any object → no notification mechanism → members stay in group permanently

Diagnosis:
  "I want multiple agents to work from a shared pool" → Queue
  "I want multiple users to read each other's records"  → Public Group + Sharing Rule
```

**Detection hint:** If the generated advice uses "queue" and "public group" interchangeably in the same sentence without distinguishing their roles, flag it and clarify the distinction.
