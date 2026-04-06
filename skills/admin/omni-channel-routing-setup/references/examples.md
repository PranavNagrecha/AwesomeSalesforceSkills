# Examples — Omni-Channel Routing Setup

## Example 1: First-Time Queue-Based Routing for a Case Support Team

**Context:** A mid-size company has a single Tier 1 case support queue with 10 agents. They have Service Cloud enabled but have never configured Omni-Channel. Cases are currently auto-assigned or manually picked up from a list view. They want automated push routing so agents receive work without monitoring queues.

**Problem:** Without Omni-Channel configuration, cases sit in queue views and agents cherry-pick easier cases, leaving complex ones unworked. There is no capacity control — agents can have 30 open cases simultaneously with no enforcement.

**Solution:**

```text
Step 1 — Enable Omni-Channel
  Service Setup > Omni-Channel Settings > Enable Omni-Channel (checkmark)
  Save. No code required.

Step 2 — Create Service Channel for Case
  Setup > Omni-Channel > Service Channels > New
  Name: Cases
  Salesforce Object: Case
  Units of Capacity: 5
  Save.

Step 3 — Create Routing Configuration
  Setup > Omni-Channel > Routing Configurations > New
  Name: Tier 1 Case Routing
  Routing Priority: 1
  Routing Model: Least Active
  Units of Capacity: 5
  Push Timeout: 30 seconds
  Save.

Step 4 — Assign Routing Configuration to Queue
  Setup > Queues > Edit "Tier 1 Support Queue"
  Routing Configuration: Tier 1 Case Routing
  Save.

Step 5 — Create Presence Configuration
  Setup > Omni-Channel > Presence Configurations > New
  Name: Support Agent Presence
  Capacity: 10
  Add Service Channel: Cases
  Save.
  Assign to Profile: Support Agent Profile (or via Permission Set)

Step 6 — Create Presence Status
  Setup > Omni-Channel > Presence Statuses > New
  Name: Available
  Status Options: Online
  Channels: Cases (Service Channel)
  Save.

Step 7 — Create Service Resources for each agent
  Setup > Service Resources > New
  Name: Agent Full Name
  User: (select user)
  Resource Type: Agent
  Active: checked
  Save. Repeat for all 10 agents.
```

**Why it works:** Each step adds one required piece of the routing chain. When an agent logs into Omni-Channel and selects "Available", the Presence Configuration links to the Case Service Channel, the Routing Configuration connects to the queue, and the routing engine can now push cases to the agent using the Least Active algorithm. Capacity enforcement limits each agent to 2 open cases (2 × 5 = 10 capacity units used).

---

## Example 2: Skills-Based Routing for a Multi-Product Support Org

**Context:** A software company supports three product lines (CRM, ERP, Analytics). Some agents specialize in one product; senior agents cover two or three. Currently all cases go to one shared queue and are manually reassigned, creating constant supervisor overhead. They want automatic routing to agents who know the relevant product.

**Problem:** With queue-based routing, the routing engine has no awareness of which agent handles which product. Cases for the ERP product get pushed to CRM specialists who cannot resolve them, leading to transfers and extended handle times.

**Solution:**

```text
Step 1 — Enable Skills-Based Routing
  Service Setup > Omni-Channel Settings
  Enable Omni-Channel: checked (already done)
  Enable Skills-Based Routing: checked
  Save.

Step 2 — Create Service Channel (if not existing)
  Cases Service Channel — already created in previous setup.

Step 3 — Create Skills
  Setup > Omni-Channel > Skills > New
  Skill 1: CRM Support   (Description: Agents supporting CRM product line)
  Skill 2: ERP Support   (Description: Agents supporting ERP product line)
  Skill 3: Analytics Support

Step 4 — Create Service Resources for all agents
  (Same as queue-based example above — one Service Resource per User)

Step 5 — Assign Service Resource Skills
  Open Service Resource record for Agent A (CRM specialist)
  Related List: Skills > New Skill
    Skill: CRM Support, Skill Level: 5 (expert)
  Open Service Resource record for Agent B (ERP + CRM generalist)
    Skill: CRM Support, Skill Level: 3
    Skill: ERP Support, Skill Level: 3

Step 6 — Create Routing Configuration (Skills-Based)
  Name: Product Skills Routing
  Routing Priority: 1
  Routing Model: Skills-Based
  Units of Capacity: 5
  Push Timeout: 30 seconds
  Save.
  Assign to "Product Support Queue" via Queue edit.

Step 7 — Create Skills-Based Routing Rules
  Setup > Omni-Channel > Skills-Based Routing Rules > New
  Rule Name: Route by Product Line
  Object: Case
  Add Rule Entry 1:
    Criteria: Case.Product_Line__c = "CRM"
    Required Skill: CRM Support
    Minimum Skill Level: 1
  Add Rule Entry 2:
    Criteria: Case.Product_Line__c = "ERP"
    Required Skill: ERP Support
    Minimum Skill Level: 1
  Add Rule Entry 3:
    Criteria: Case.Product_Line__c = "Analytics"
    Required Skill: Analytics Support
    Minimum Skill Level: 1
  Save.
```

**Why it works:** When a Case with Product_Line__c = "ERP" enters the queue, the routing engine evaluates the Skills-Based Routing Rules, identifies that ERP Support skill is required, and finds the Service Resource with that skill who has available capacity. Agent A (CRM only) is skipped. Agent B (CRM + ERP) is eligible and receives the case. Manual reassignment overhead drops to near zero.

---

## Anti-Pattern: Creating One Big Queue With Multiple Routing Configurations

**What practitioners do:** Administrators try to assign two different Routing Configurations to the same queue — one for normal cases and one for priority cases — assuming the routing engine will pick the right one per case.

**What goes wrong:** A queue can only have one Routing Configuration. The second assignment overwrites the first silently in Setup. The admin thinks both rules are active, but only the last-saved Routing Configuration applies. All cases route the same way regardless of priority, and the priority configuration is lost.

**Correct approach:** Create separate queues for each routing behavior. Use assignment rules, Flow, or Apex to place cases into the correct queue based on priority criteria before they enter Omni-Channel routing. Each queue has its own Routing Configuration with the appropriate priority level and routing model.
