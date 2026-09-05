# Gotchas — Portal Requirements Gathering

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Skipping Contact Reason Analysis Produces a Portal With Near-Zero Deflection

**What happens:** Teams skip the 60–90 day contact data pull and build based on stakeholder preference — usually a knowledge base, search, and case form. Post-launch deflection rate is under 5% because the content and features do not match the real reasons customers contact support.

**When it occurs:** Any portal project where requirements are gathered through stakeholder interviews alone, without pulling actual support volume data. Common on fast-moving projects where business owners are confident they know customer needs.

**How to avoid:** Make the contact reason data pull a hard prerequisite before any feature scoping session. Categorize each contact reason as Answers, Status, or Action. Use the breakdown to set the feature priority stack. Do not hold a feature scoping session until the data is in hand.

---

## Gotcha 2: License Choice Is Locked at Provisioning and Costly to Reverse

**What happens:** Customer Community is selected during requirements as the lower-cost option. Post-launch, the business needs manual sharing or role hierarchy on custom objects — capabilities that Customer Community does not include. Upgrading to Customer Community Plus requires deactivating and reprovisioning every user record.

**When it occurs:** When license selection is treated as a cost-optimization decision without confirming whether the required sharing and object access capabilities are present in the chosen license. Discovered at build time when a developer tries to implement selective sharing on a custom object.

**How to avoid:** During requirements, walk through every sharing requirement: does the org need customers to share records with each other? Do customers need to see custom object data beyond Cases and Knowledge? If yes to either, Customer Community Plus is required. Record the decision and its rationale before any users are provisioned. The platform draws the line at the user type, not the marketing name: the Object Reference describes `PowerCustomerSuccess` (label *Customer Portal Manager*) as a user who "can view and edit data they directly own or data owned by or shared with users below them in the Customer Portal role hierarchy", while `CspLitePortal` (label *High Volume Portal*) carries no such statement — the two sit under different Experience Cloud licences (Object Reference, `Profile.UserType`, L232430–L232470). Phrase the requirement as "does any external persona need to see records owned by another external user beneath them?"; a yes puts that persona on a role-hierarchy-capable user type.

---

## Gotcha 3: Gamification and Social Features Defer Deflection Validation Indefinitely

**What happens:** Phase 1 scope includes idea exchange, chatter, leaderboards, and community forums alongside the core self-service features. The portal launches. Social engagement is measurable but deflection is not, because the core self-service loop was not instrumented first. Leadership cannot confirm the business case.

**When it occurs:** When stakeholders treat the portal as a community engagement initiative rather than a deflection initiative. Social features have visible, easy-to-measure engagement metrics that create the illusion of success even when deflection is zero.

**How to avoid:** Explicitly defer all social and gamification features to phase 2 in the requirements document. Mark them as "deferred — pending deflection validation" rather than "rejected." Set a measurable deflection target as the gate to phase 2.

---

## Gotcha 4: Hybrid Access Model Guest User Profile Is Overly Permissive by Default

**What happens:** A hybrid access model is chosen. The guest user profile is cloned from an existing profile without tightening object permissions. Post-launch, a security review finds that anonymous visitors can read Account or Contact records through the API, not just the portal UI.

**When it occurs:** When access architecture is decided but guest user profile lockdown is not assigned as a named deliverable during requirements. Developers focus on public page content and assume default guest permissions are safe.

**How to avoid:** When hybrid access is selected, add "guest user profile lockdown" explicitly to the build checklist in the requirements document. Assign an owner. List every object the guest user should and should not be able to read. Two `CustomSite` fields make the exposure surface concrete enough to scope in requirements: `guestProfile` is read-only — "the name of the profile associated with the guest user" — so the guest identity is created by the site rather than chosen, and `siteGuestRecordDefaultOwner` is "the username of the user who owns all new records that unauthenticated guest users create" (Metadata API Guide, `CustomSite`, L46959–L46960 and L47040–L47042). Both are build decisions this skill only has to name an owner for: the lockdown itself belongs to `admin/experience-cloud-guest-access`, and the guest user's own record-access model to `security/guest-user-security`. In the catalogue, a guest-facing row without a named `guest_review` fails the checker for exactly this reason.

---

## Gotcha 5: Partner Community Requires Underlying Sales Cloud License

**What happens:** A service-heavy org selects Partner Community licenses for a PRM portal. During build, the developer discovers that Lead and Opportunity objects are unavailable because the org only has Service Cloud, not Sales Cloud. The entire PRM use case is blocked until Sales Cloud is procured.

**When it occurs:** When license selection focuses on the Experience Cloud license tier without confirming that the underlying CRM product license (Sales Cloud) is present. Common when the portal project is owned by a marketing or channel team without IT involvement in the license review.

**How to avoid:** During license selection in requirements, explicitly verify that the CRM product license required by the use case is present in the org. PRM requires Sales Cloud (Lead + Opportunity). Document this dependency in the requirements before any procurement or build planning.

---

## Gotcha 6: An External User Cannot Exist Unless Their Contact Already Has an Account

**What happens:** The requirements list a persona — "channel technician", "end user at a customer site" — that has no Contact record, or has a Contact created without an Account. User creation fails at build time. The Object Reference states the rule on `User.ContactId` plainly: "ID of the Contact associated with this account. The contact must have a value in the `AccountId` field or an error occurs" (Object Reference, `User` fields, L295088–L295092). `User.AccountId` is "ID of the Account associated with a Customer Portal user" and "is null for Salesforce users" (L294996–L295001).

**When it occurs:** Wherever a persona is described by job title rather than by its record shape. Consumer-facing portals hit this hardest: a B2C persona that has no natural Account forces either a bucket Account or Person Accounts, and both are data-model decisions that belong in requirements, not in a build sprint.

**How to avoid:** Give every persona row in the persona/licence matrix a fourth column: which Contact and which Account this user hangs off. If the answer is "we don't have one", the requirement is a data-model requirement before it is a portal requirement. `User.PortalRole` behaves the same way — when it is null and a `ContactId` is provided, the user is assigned to the User role (L295670–L295675), which is a silent default rather than a decision.

---

## Gotcha 7: Sharing Sets Are Licence-Scoped, and the Licence List Is Not the One Most Requirement Docs Assume

**What happens:** A requirement is written as "customer admins see all cases on their account, delivered by a sharing set", against a persona whose profile sits on a licence that cannot use sharing sets. The `SharingSet` metadata type names its own licence list: Authenticated Website, Customer Community Login, Customer Community Plus, Partner Community, Customer Community User, High Volume Customer Portal, High Volume Portal, Overage Authenticated Website User, Overage High Volume Customer Portal User (Metadata API Guide, `SharingSet` → Special Access Rules, L130389–L130398). The `profiles` field is constrained the same way: "Profiles must be associated with a license that can use sharing sets" (L130415–L130417).

**When it occurs:** When the requirements doc names a mechanism ("sharing set") in the same breath as a licence, without checking the two against each other. It also occurs in reverse: teams assume sharing sets are a Customer Community-only feature and design an account-role hierarchy for a Partner Community persona that a sharing set would have covered — Partner Community is on the list.

**How to avoid:** Treat the licence and the mechanism as one paired decision in the catalogue row, and check the pair against the `SharingSet` Special Access Rules list before sign-off. The mapping itself — `object`, `objectField`, `userField`, `accessLevel` — is owned by `admin/sharing-and-visibility`, which holds the deployable XML; record the four values in the requirement row and let that skill author it.

---

## Gotcha 8: Login-Based and Member-Based Licences Are Separate Allocation Rows, Not a Billing Detail

**What happens:** A persona is scoped on cost alone — "these users log in twice a year, put them on a Login licence" — and the API allocation goes unread. The App Limits cheat sheet lists the variants as distinct rows with distinct per-licence API allocations: `Customer Community: 0`, `Customer Community Login: 0`, `Customer Community Plus: 200`, `Customer Community Plus Login: 10`, `Partner Community: 200`, `Partner Community Login: 10` (Salesforce Developer Limits and Allocations Quick Reference, "Total API Request Allocations", L533–L547). The org total is `100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons` (L529–L531).

**When it occurs:** On portals with a companion mobile app or a middleware layer that calls the API as the portal user. The licence chosen for cost reasons turns out to contribute a 0 or 10 call-per-day allocation, and the integration burns the org's base allocation instead.

**How to avoid:** Record the cheat-sheet allocation line beside every persona in the licence matrix, and ask whether anything will call the API *as* that persona. Login-vs-member commercial selection is owned by `architect/experience-cloud-licensing-model`; this skill's job is to surface the API consequence so that selection is made with it in view.

---

## Gotcha 9: Knowledge That Internal Agents Can Read Is Invisible to Portal Users Until Data Category Visibility Is Declared

**What happens:** The requirement says "customers can read our how-to articles". Articles are published, the portal is built, and external users see an empty Knowledge component. Data category visibility is a per-profile setting: `Profile.categoryGroupVisibilities` holds a `dataCategoryGroup`, an array of `dataCategories`, and a required `visibility` of `ALL`, `CUSTOM`, or `NONE` (Metadata API Guide, `Profile` → `ProfileCategoryGroupVisibility`, L97911–L97930). The external profile carries its own setting; the internal agent's visibility says nothing about it.

**When it occurs:** Whenever a Knowledge requirement is written as a content requirement rather than an access requirement, and the taxonomy work happens in a different workstream from the profile work.

**How to avoid:** Every Knowledge row in the catalogue names the data category group and the specific categories the external profile may see, so the row carries the `CUSTOM` value list rather than an implied `ALL`. Taxonomy design itself belongs to `admin/knowledge-base-administration`; the requirement row only has to state which slice of it is external. UNVERIFIED (2026-09-04): the default `visibility` for a newly created external profile is not stated in the extracted Metadata API Guide — treat it as undeclared and set it explicitly rather than relying on a default.

---

## Gotcha 10: Self-Registration Is a Site-Level Switch That Manufactures Duplicate Contacts

**What happens:** Self-registration is turned on for one persona. Every self-registering visitor lands on the single profile named in `Network.selfRegProfile` — the field is "the profile assigned to users who self-register" and "is used only if `selfRegistration` is enabled for the site" (Metadata API Guide, `Network`, L91038–L91045). A person who is already a Contact registers under a slightly different email or name spelling and a second Contact is created beside the first, splitting their case history across two records.

**When it occurs:** On any portal where the same humans already exist in the org as marketing or support Contacts — which is most B2B support portals. It surfaces months later as "why can't this customer see the case they raised last year".

**How to avoid:** Any catalogue row with `auth: self-registration` must name its duplicate control before sign-off: the matching rule and duplicate rule pair that runs on Contact, designed via `admin/duplicate-management`. Record the decision on registration collisions too — block, merge, or route for review — because the registration path needs an answer for each. `selfRegistration` is one boolean for the whole site, so a persona that must not self-register is separated after registration by profile and licence, never by the switch.
