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
  - Support Agent Role: visibility = Custom → General_FAQ + Internal_Procedures
  - Partner Role:       visibility = Custom → General_FAQ + Partner_Resources
  - Customer Role:      visibility = Custom → General_FAQ

Guest User (unauthenticated) — has no role, so role-based visibility never applies:
  - Set Data Category Visibility on the site's Guest User profile
    (or a permission set assigned to it): Support_Topics = None
  - Org-wide fallback for users with no visibility from any source is
    configured separately under Default Data Category Visibility
```

Articles assigned only to `Internal_Procedures` are invisible to partners and customers even if those users have Knowledge read permission on their profile. Articles left uncategorized are *not* hidden by this configuration — they remain visible but surface only under the No Filter option in the category dropdown, so assign at least one category to keep articles browsable.

**Why it works:** Data Category visibility is a separate control layer from object-level permissions; a user sees an article only if they can see at least one category in *every* category group assigned to that article. Role-based visibility scales with headcount because child roles inherit the parent's settings and stay in sync with them — but that inheritance is a ceiling, not a floor: a child can be reduced below its parent, never raised above it. Guest and high-volume portal users have no role, so their visibility must come from a profile or permission set. Where role, permission set, and profile each define visibility for the same user, Salesforce combines them with a logical OR.

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

## Example 3: Exposing Knowledge on a Help Center Site for Case Deflection

**Context:** A support organization wants customers to find answers themselves rather than opening cases, without requiring a portal login first. Roughly 60 published "How-To" and "FAQ" articles already exist and are visible to internal agents. Nothing is visible outside the org.

**Problem:** The articles are Published, correctly categorized, and the org has an active Experience Cloud site — yet nothing renders for customers. Publishing controls *status*, not *audience*, and there is no single toggle that pushes internal Knowledge onto a site.

**Solution:**

```
1. Author permissions (permission set: Knowledge_Manager)
   Object: Knowledge
     Read, Create, Edit, Delete, View All Records, Modify All Records
   App permissions:
     Manage Articles
     Manage Knowledge Article Import/Export
     Manage Salesforce Knowledge
     Publish Articles
     Share internal Knowledge articles externally   ← required to surface content externally
     (View Archived Articles + View Draft Articles enable automatically)
   System permission:
     Manage Data Categories
   Per user: Knowledge User checkbox on the user record

2. Topics prerequisite (hard gate)
   Setup > Topics for Objects > Knowledge
     Enable Topics = ON
     Fields scanned: Title

3. Site
   New site from the Help Center template — documented as a public-access,
   self-service site where guest users search the knowledge base
   (Knowledge search, article pages, topic navigation pre-wired)
   Enable Salesforce Knowledge on the site itself — a distinct step from
   org-level enablement (Salesforce Help: "Enable Salesforce Knowledge in
   Your Experience Cloud Site")

4. Article channel — chosen by reader, not by template
   Knowledge__kav.IsVisibleInPkb = true   ← unauthenticated visitors (guests)
   Knowledge__kav.IsVisibleInCsp = true   ← only if authenticated customer
                                            users also read this site
   Note: IsVisibleInApp is NOT settable. The object reference gives it
   Properties "Defaulted on create, Filter, Group, Sort" — no Create, no
   Update — unlike the three external flags. Internal agent access is a
   given, not something a data load writes.

5. Access
   Guest users have no role, so role-based visibility never reaches them.
   Site's Guest User profile (or a permission set assigned to it):
     Knowledge object: Read
     Data Category Visibility: Support_Topics = Custom → General_FAQ

   For the authenticated variant, assign the same category visibility to
   the Customer Community permission set.

6. Topics + components
   Experience Workspaces > Content Management > Topics
     Article Management  → assign topics to the 60 articles
     Navigational Topics → browse tree
     Featured Topics     → home page highlights
   Experience Builder: Topic Catalog, Top Articles by Topic, Article Content
```

**Why it works:** Each layer answers a different question. The permission set answers *can this author push content out of the org*. Topics answers *can articles be rendered outside the org at all*. The channel flag answers *which audience surface is this article eligible for*. Data Category Visibility answers *which of the eligible articles may this specific user read*. The Experience Builder components answer *where on the page does it appear*. Miss any one and the site is silently empty — no error, no warning, no failed save.

**The channel is the step teams get wrong.** Help Center's description says "customers," which pulls admins toward `IsVisibleInCsp`. But an unauthenticated visitor is a guest, and Salesforce Help's *View Knowledge Base Articles on a Lightning Platform Site* states that "only articles marked as Public Knowledge Base will be available to guest users." A Help Center flagged only for the Customer channel renders empty article pages to everyone who has not logged in. Verify the guest path in a logged-out private browser window — an Experience Builder preview runs as the admin and will render articles a real guest cannot see.

---

## Anti-Pattern: Relying on Permission Sets Alone for Article Audience Segmentation

**What practitioners do:** Admins create separate permission sets for "Internal Agent Knowledge Access" and "Partner Knowledge Access," assign the `Knowledge__kav` read permission to both, and assume that articles will be visible only to the appropriate audience. They skip Data Category configuration entirely.

**What goes wrong:** Object-level read permission on `Knowledge__kav` grants the ability to read any article the user can reach — but Salesforce still applies Data Category visibility as a separate layer. If no role, permission set, or profile visibility has been set up at all, "all users can see all data categories." Once any visibility is configured, a user with none of it sees "only uncategorized articles and questions" — every article classified into an active group disappears for them. Either way, the permission set alone cannot segment article visibility by audience.

**Correct approach:** Object-level permissions (profiles/permission sets) control whether a user can interact with the Knowledge object at all. Data Category visibility controls which specific articles that user can see. Both layers must be configured. Assign Data Category Group visibility through Roles (preferred for scale, remembering the parent role caps the child) or Profiles/Permission Sets (for fine-grained overrides, and mandatory for guest and high-volume portal users, who have no role), in addition to granting object-level read access.
