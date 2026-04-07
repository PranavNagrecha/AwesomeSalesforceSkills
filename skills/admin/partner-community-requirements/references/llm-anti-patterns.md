# LLM Anti-Patterns — Partner Community Requirements

Common mistakes AI coding assistants make when generating or advising on Partner Community Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Customer Community License for PRM

**What the LLM generates:** Advice to use Customer Community Plus license for a partner portal because it provides authenticated access and is less expensive than Partner Community.

**Why it happens:** LLMs conflate "partner" (business relationship) with "portal user" (Experience Cloud access model). Customer Community Plus is a valid authenticated portal license for customers, and training data includes many examples of authenticated Experience Cloud portals that use it. The PRM-specific license gating is a Salesforce product restriction that is not obvious from the license name alone.

**Correct pattern:**

```
Partner Relationship Management features (deal registration, lead distribution,
lead inbox, MDF components) require Partner Community or Partner Community Plus
license. Customer Community and Customer Community Plus licenses do not unlock
these features.

Use Partner Community for baseline PRM.
Use Partner Community Plus when partners need:
- Reports and dashboards with pipeline visibility
- Broader sharing model (accounts, contacts, opportunities)
```

**Detection hint:** Flag any recommendation that includes "Customer Community" in a context where deal registration, lead distribution, or MDF are requirements.

---

## Anti-Pattern 2: Skipping Deal Registration Approval Flow Design

**What the LLM generates:** A deal registration implementation plan that creates a Lead-based submission form and converts the Lead to an Opportunity directly on submission, without an intervening approval process.

**Why it happens:** LLMs default to the simplest functional path. If the training data includes examples of Lead-to-Opportunity conversion, the model generates that flow without the approval governance layer that deal registration requires. The approval process is a business rule, not a Salesforce platform requirement, so it does not appear in API or metadata docs.

**Correct pattern:**

```
Deal Registration flow requires an explicit approval step:
1. Partner submits Lead with Status = "Submitted for Registration"
2. Approval process fires on entry criteria
3. Channel manager approves or rejects
4. On approval only: Flow converts Lead to Opportunity
5. On rejection: notification sent to partner with rejection reason

Do not convert Lead to Opportunity on submission. Conversion
happens only after approval is granted.
```

**Detection hint:** Flag any deal registration design that converts a Lead to an Opportunity without a preceding approval process node.

---

## Anti-Pattern 3: Not Planning the Tier Hierarchy Before Configuration

**What the LLM generates:** A PRM configuration plan that starts with Experience Cloud site setup, leaving tier hierarchy ("we can add tiers later") as a future item.

**Why it happens:** LLMs prioritize getting to a working demo quickly. Tier hierarchy feels like a business decision that can be deferred. In practice, tier drives sharing rules, assignment rules, approval criteria, MDF eligibility, and content entitlement — all of which must be built around the tier model. Retrofitting tiers after configuration requires rework of nearly every component.

**Correct pattern:**

```
Define the complete tier hierarchy BEFORE any configuration begins:
- Tier names and count (e.g., Gold / Silver / Bronze)
- Promotion/demotion criteria
- Feature access per tier (deal reg, lead pool, MDF, co-marketing)
- MDF allocation per tier
- Approval routing differences per tier

Deliver a tier decision matrix as a requirements artifact.
Configuration team cannot begin sharing rules, assignment rules,
or approval processes without this matrix.
```

**Detection hint:** Flag any PRM project plan that does not list "tier hierarchy definition" as a step before sharing rule or assignment rule configuration.

---

## Anti-Pattern 4: Confusing Lead Distribution With Lead Assignment

**What the LLM generates:** A recommendation to use Lead Assignment Rules to distribute leads to "the right partner," treating lead distribution and standard Salesforce lead assignment as interchangeable concepts.

**Why it happens:** Both involve the Lead Assignment Rules feature in Salesforce Setup. The distinction is that standard lead assignment routes leads to internal users or queues, while partner lead distribution routes to partner-user queues with additional eligibility logic (tier, territory, capacity) and requires the partner portal's lead inbox to surface the lead to the partner. LLMs merge these concepts because they share the same configuration surface.

**Correct pattern:**

```
Standard Lead Assignment Rules: route leads to internal queues/users.
Partner Lead Distribution: routes leads to partner-accessible queues.

For partner distribution, additionally required:
- Partner queue with partner users as members (not internal users)
- Sharing rules so partner users can read/edit queue-owned leads
- Portal Lead list view scoped to the partner's queue
- Tier eligibility logic: cross-object formula or Flow to stamp
  partner tier onto Lead before assignment rule evaluation

Assignment rules alone are not sufficient — sharing model and
portal list view configuration are required for partners to act on leads.
```

**Detection hint:** Flag any lead distribution design that does not include a sharing rule and portal list view specification alongside the assignment rule criteria.

---

## Anti-Pattern 5: Assuming MDF Is a Standard Out-of-the-Box PRM Feature

**What the LLM generates:** A PRM requirements document that lists "MDF tracking" as a standard feature to be configured, citing Trailhead PRM content, without noting that MDF requires custom objects or Channel Revenue Management.

**Why it happens:** Trailhead PRM modules and marketing materials describe MDF as part of the PRM feature set. LLMs trained on this content reproduce the description without the licensing and implementation caveats. The distinction between "shown in a demo org" and "available in a standard licensed org" is rarely explicit in training data.

**Correct pattern:**

```
MDF tracking in base PRM requires custom objects. There is no standard
MDF_Budget__c or MDF_Claim__c object in the core Salesforce product
(without Channel Revenue Management licensing).

To implement MDF in Salesforce:
Option A: Design custom objects (MDF_Budget__c, MDF_Request__c, MDF_Claim__c)
          with approval process for claim reimbursement.
          Effort: 2-3 days configuration, plus portal surfacing.

Option B: License Channel Revenue Management, which includes standard
          MDF objects and workflows.

Option C: Track MDF in an external finance system and surface summary
          data in the portal via integration.

Specify which option is in scope during requirements. Do not assume
MDF is available out of the box.
```

**Detection hint:** Flag any PRM requirements document that lists MDF as "standard configuration" without referencing a custom object design or Channel Revenue Management license.

---

## Anti-Pattern 6: Routing Approvals and Assignments to Named Users Instead of Queues

**What the LLM generates:** An approval process configuration where deal registration approvals are sent to a specific channel manager user record, and leads are assigned directly to individual partner user records.

**Why it happens:** Named-user routing is the simplest approval process configuration and appears frequently in introductory Salesforce documentation. LLMs default to it because queue-based routing requires additional context about queue membership and queue visibility.

**Correct pattern:**

```
Use queue-based routing for both approvals and lead assignment:

Approval routing:
- Create a Channel_Manager_Approval_Queue with all active channel managers
- Route approval steps to the queue, not to a named user
- Configure "Any member of the queue can approve" to prevent bottlenecks

Lead assignment:
- Assign leads to partner queues (e.g., Gold_West_Queue)
- Partner users are members of the queue and see leads via portal list view
- When a partner user is deactivated, their queue membership is removed
  without disrupting other queue members' access to leads

Named-user routing creates single points of failure when users are
on leave, deactivated, or change roles.
```

**Detection hint:** Flag any approval process or assignment rule that routes to a specific Salesforce user ID rather than a queue record.
