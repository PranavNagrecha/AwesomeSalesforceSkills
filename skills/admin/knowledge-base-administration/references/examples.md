# Examples — Knowledge Base Administration

## Example 1: Configuring Data Category Visibility for a Multi-Audience Org

**Context:** A company uses Salesforce Knowledge to serve three audiences: internal support agents, partner users (via Experience Cloud), and end customers (via Experience Cloud). All audiences should see "General Product FAQ" articles, but only internal agents should see "Internal Escalation Procedures" articles. Partners should see a "Partner Pricing Guide" category that customers and agents cannot see.

**Problem:** Without Data Category visibility configuration, all Knowledge articles are either visible to everyone or invisible to everyone. Sharing rules and permission sets alone cannot restrict article visibility — Data Category visibility is a separate, mandatory control layer.

**Solution:**

```
Data Category Group: Support_Topics
  ├── General_FAQ             ← visible to: All Roles (agents, partners, customers)
  ├── Internal_Procedures     ← visible to: Support Agent Role only
  └── Partner_Resources       ← visible to: Partner Community Role only

Visibility assignments in Setup > Roles:
  - Support Agent Role: visibility = General_FAQ + Internal_Procedures (include subcategories)
  - Partner Role: visibility = General_FAQ + Partner_Resources (include subcategories)
  - Customer Role: visibility = General_FAQ (include subcategories)
  - Guest User (unauthenticated): visibility = none (Knowledge Settings > Guest User Category Access = No Access)
```

Every article must be assigned to at least one category. Articles assigned only to `Internal_Procedures` are invisible to partners and customers even if those users have Knowledge read permission on their profile.

**Why it works:** Salesforce evaluates Data Category visibility as a pre-filter before applying object-level permissions. The role-based visibility model uses role hierarchy inheritance, so child roles automatically inherit parent visibility unless explicitly overridden. By assigning visibility at the role level rather than individual profiles, the configuration scales as users are added to roles.

---

## Example 2: Layering an Approval Process on Knowledge Article Publishing

**Context:** A financial services company requires a compliance officer to review and approve all Knowledge articles before they are published. Without an approval gate, any author with "Manage Articles" permission can publish directly.

**Problem:** Native Knowledge statuses (Draft → Published) have no built-in approval gate. An admin must configure an Approval Process on `Knowledge__kav` to enforce the compliance review step.

**Solution:**

```
Approval Process configuration on Knowledge__kav:
  Name: Compliance_Review_Before_Publish
  Entry Criteria: Status EQUALS Draft AND Validation_Status EQUALS "Ready for Review"
  Approval Steps:
    Step 1 — Approver: Compliance Officer role
             Action on Approve: Field Update → set Validation_Status = "Validated"
             Action on Reject: Field Update → set Validation_Status = "Not Validated", notify submitter
  Final Approval Actions:
    - Field Update: set Validation_Status = "Validated"
    (Author must then manually publish — approval does not auto-publish)

Validation Status picklist values (enabled in Knowledge Settings):
  - Draft
  - Ready for Review
  - Validated
  - Not Validated
```

Authors set Validation Status to "Ready for Review" and submit for approval. The compliance officer approves or rejects. After approval, the author (or an admin) manually clicks Publish to transition the article from Draft to Published. The approval process does not auto-publish — this is an intentional design to keep the publish action explicit.

**Why it works:** Salesforce Approval Processes on `Knowledge__kav` use the same framework as any other object. The Validation Status picklist acts as a handshake signal between the author and the approver. Keeping the final publish action manual ensures that authors confirm the approved content before it goes live, which matters when articles are iteratively revised during approval.

---

## Anti-Pattern: Relying on Permission Sets Alone for Article Audience Segmentation

**What practitioners do:** Admins create separate permission sets for "Internal Agent Knowledge Access" and "Partner Knowledge Access," assign the `Knowledge__kav` read permission to both, and assume that articles will be visible only to the appropriate audience. They skip Data Category configuration entirely.

**What goes wrong:** Object-level read permission on `Knowledge__kav` grants the ability to read any article the user can reach — but Salesforce still applies Data Category visibility as a separate layer. Without category visibility assigned, users may see all articles (if no groups are active) or no articles (if groups are active but visibility is unassigned). The permission set alone cannot segment article visibility by audience.

**Correct approach:** Object-level permissions (profiles/permission sets) control whether a user can interact with the Knowledge object at all. Data Category visibility controls which specific articles that user can see. Both layers must be configured. Assign Data Category Group visibility through Roles (preferred for scale) or Profiles/Permission Sets (for fine-grained overrides), in addition to granting object-level read access.
