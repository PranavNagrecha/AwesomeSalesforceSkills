# Gotchas — Change Management and Training

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: In-App Guidance Prompts Ignore Permission Sets — Profile-Only Targeting

**What happens:** In-App Guidance in Salesforce allows you to target prompts by user profile. If your org has moved to a "one profile fits all" model with permission sets controlling access, every user in that profile sees the prompt — including users who are not affected by the change.

**When it occurs:** Most frequently in orgs that standardized on a single "Standard User" profile and use permission sets for all granular access. A BA sets up a walkthrough for "Agents who use the new Case Status field" but targets the "Standard User" profile — which also includes Managers, Admins, and Sales Reps.

**How to avoid:** Before configuring In-App Guidance, confirm whether affected users share a profile that is NOT used by unaffected users. If not, stop using profile targeting. The `Prompt` metadata type carries three different audience controls and they are not equivalent: `userProfileAccess` (`Everyone` or `SpecificProfiles`, API 48.0 and later) is the profile filter that fails here; `userAccess` (`Everyone` or `SpecificPermissions`) shows the guidance only to users holding *all* the named user permissions; and `uiFormulaRule` takes criteria whose `leftValue` may be `{!$Permission.CustomPermission.<name>}` or `{!$Permission.StandardPermission.<name>}`, evaluated against the viewing user. Grant a custom permission through the same permission set that grants the change's field access and filter the prompt on that — one assignment then opens the field and turns on the guidance for exactly the same population, on the same day. Test in a sandbox with users on both sides of the filter before go-live.

---

## Gotcha 2: Path Coaching Text Does Not Inherit Across Record Types

**What happens:** When you add coaching text to a stage in Path Settings, the configuration applies to a specific combination of Object + Record Type + Picklist field. If you configure coaching for the "Enterprise Opportunity" record type and later add a "Mid-Market Opportunity" record type, the new record type has no coaching text — it is not inherited.

**When it occurs:** During rollouts that add new record types to an existing object where Path is already configured. Admins assume that since the picklist values are shared, the coaching text is shared. It is not. Users assigned the new record type see an empty Path.

**How to avoid:** After adding a new record type, navigate to Setup > Path Settings and explicitly configure coaching text for every new record type + picklist combination. Include a Path review in your deployment checklist whenever a record type is added or cloned. The Metadata API states the scoping rule plainly for `PathAssistant`: only one path can be created per record type for each object, including the `__Master__` record type, and `recordTypeName` is required and not updateable — so a path is bound to its record type at creation and a new record type always starts with none. The guide also warns that a missing `pathAssistantSteps` entry in the retrieved XML means that step has *not been configured*, not that the stage does not exist, so a diff between two record types will look deceptively small. Count steps against the picklist, not against the file.

---

## Gotcha 3: Adoption Dashboard Login Metrics Include API and Integration Logins

**What happens:** The Salesforce Adoption Dashboards package (Salesforce Labs, AppExchange) measures user activity using the LoginHistory standard object. This object records all successful authentications — including OAuth logins from connected apps, integration users, and scheduled jobs. If an integration user runs nightly syncs, it will appear as a daily "active user" in the adoption reports.

**When it occurs:** Any org with integration users, connected apps, or API-based automations running under named user credentials. The inflated active user count makes adoption appear higher than it is, masking real adoption gaps.

**How to avoid:** When building or reviewing adoption reports, filter LoginHistory by `LoginType = 'Application'` to capture only standard browser-based logins. Exclude integration users by filtering out known service account usernames or by using a dedicated Integration profile that is excluded from adoption report filters. Document this filter in the report description so future admins do not remove it.

**Deeper trap in the same object:** the `LoginType` picklist is not a human/machine split. Its values include `Application`, `Remote Access 2.0` (OAuth), `SAML Sfdc Initiated SSO`, `SAML Idp Initiated SSO`, `Lightning Login` and `Help And Training`. In an SSO org a human's browser login records a SAML value, not `Application` — so the widely copied `LoginType = 'Application'` filter returns near-zero for exactly the orgs most likely to be running it. Profile the org first with `SELECT LoginType, LoginSubType, COUNT(Id) FROM LoginHistory WHERE LoginTime = LAST_N_DAYS:7 GROUP BY LoginType, LoginSubType`, then write the filter against the values that org actually produces.

---

## Gotcha 4: Trailhead myTrailhead Content Is Org-Specific and Not Shared Across Orgs

**What happens:** myTrailhead (the branded, org-specific Trailhead experience) allows companies to create custom modules and trails. Content created in one Salesforce org's myTrailhead instance is not accessible from another org or from standard public Trailhead. Users assigned to a trail in one org cannot access it from a different org login.

**When it occurs:** When a company has multiple Salesforce orgs (e.g., separate EMEA and AMER instances) and attempts to roll out a myTrailhead learning path across all of them. Admins set up the trail in one org and share the link — users in other orgs cannot authenticate.

**How to avoid:** For multi-org environments, either (a) use standard public Trailhead trails which are org-agnostic, or (b) confirm that myTrailhead licenses cover all target orgs before investing in custom content creation. If only one org has myTrailhead, host custom training in that org and grant cross-org access via SSO or a dedicated training org.


---

## Gotcha 5: The Training Sandbox Is a Copy of Production As It Was, Not As It Will Be

**What happens:** Reps are booked into hands-on labs a week before go-live, in a sandbox refreshed a few days earlier "so the data is fresh". The refresh copies production — which still has the old page assignment. The lab teaches the layout the reps are about to lose, and the first time anyone sees the shipping configuration is on go-live morning.

**When it occurs:** Whenever the refresh is scheduled by the data team for freshness and the deploy is scheduled by the release team for a change window, with nobody sequencing the two. It is worse for a Full sandbox, because a sandbox has a mandatory minimum interval between refreshes — a mistimed refresh strands the training org in the wrong state for weeks rather than hours. **UNVERIFIED (2026-09-04): the minimum refresh interval per sandbox type is not stated in the eight extracted PDFs (Metadata API, Object Reference, Apex Developer, Apex Reference, Data Loader, Bulk API, App Limits, REST), and help.salesforce.com cannot be fetched; the per-type intervals are documented in `skills/devops/sandbox-refresh-and-templates/SKILL.md`.**

**How to avoid:** Fix the order in the plan artefact, not in a conversation: deploy to the training sandbox → validate → run the labs → deploy to production → refresh the training sandbox from the now-current production. Record the refresh date on the persona's `training_env` row so the sequence is reviewable. If a refresh must happen before go-live for data reasons, redeploy the change into the sandbox immediately after the refresh completes and re-run one lab exercise as a smoke test before the first session.

---

## Gotcha 6: Screenshots Taken in a Sandbox Show Data Users Will Not Recognise

**What happens:** The training deck is built from sandbox screenshots. Every username in the screenshots carries a sandbox suffix and every email address is broken by design, so the "Owner" and "Contact Email" values in the deck match nothing a user has seen. Reps stop reading the instruction and start asking why their record shows a different owner.

**When it occurs:** Any deck, recording or quick-reference card captured in a sandbox — which is to say, all of them, because you cannot capture the new configuration in production before it ships. **UNVERIFIED (2026-09-04): the specific transformation Salesforce applies to usernames and email addresses on sandbox creation is not stated in the eight extracted PDFs and help.salesforce.com cannot be fetched. The masking convention itself is visible in this repo at `skills/devops/sandbox-refresh-and-templates/references/examples.md`, which uses an invalid TLD (`@example-sandbox.invalid`) so that sandbox mail cannot deliver.**

**How to avoid:** Two habits, both cheap. Crop or blur the header row and any email column before a screenshot goes into a deck — the training content is the field layout, not the owner. And create the lab personas with recognisable display names (`Training Rep 01`, not `bsmith.uat2`), because the display name is what appears in the screenshot even when the username does not. Where a screenshot must show an email, use the company's own domain in the sample data rather than the copied production value.

---

## Gotcha 7: Announcing a Field Before Its Permission Set Is Assigned

**What happens:** The pre-go-live email tells 84 reps about the new Close Plan field. The permission set that grants the field deploys with everything else, and everyone assumes access ships with it. It does not. `PermissionSetAssignment` is a standard object whose supported calls are `create()`, `delete()`, `describeSObjects()`, `query()`, `retrieve()` and `update()` — assignments are *data records created per user*, not part of the metadata deployment. The reps who read the email go looking for a field they cannot see and open tickets.

**When it occurs:** Every time the comms schedule is written from the deploy date and the assignment step lives only in the deployment runbook. It also occurs in reverse: `PermissionSetAssignment.ExpirationDate` (API 52.0 and later) lets an assignment expire on a date, so a pilot group's access can end silently while the training material still describes the field as available.

**How to avoid:** Put the assignment on the same timeline as the messages, and make the message that names a new field land *after* it. Verify before sending, not after: `SELECT COUNT(Id) FROM PermissionSetAssignment WHERE PermissionSet.Name = 'Opportunity_Path_Rep'` should equal the persona headcount in the plan. Check `ExpirationDate` on pilot assignments before writing any material that assumes the pilot still has access. Note also that reading this object requires View Setup and Configuration, Assign Permission Sets, or Manage User (Summer '20 and later), so the enablement lead may need the query run for them.

---

## Gotcha 8: The Screen You Trained On Is Not the Screen That Profile Sees

**What happens:** A Lightning record page assignment is not a property of the object. In the Metadata API it is an `AppProfileActionOverride` inside `CustomApplication.profileActionOverrides`, keyed on `pageOrSobjectType`, `recordType`, `profile` and `formFactor` (with `Large` meaning the Lightning Experience desktop). The admin who built the training deck was logged in as System Administrator, on desktop, viewing the record type they used for testing — a different key, and therefore potentially a different page — from the reps in the room.

**When it occurs:** In any org with more than one record type on the object or more than one profile using it, and in every org where someone views the page on mobile. It is invisible to the author: the page looks correct, because for their key it is correct.

**How to avoid:** Build the screenshot matrix before capturing anything: one row per profile × record type × form factor that a trained persona actually uses, and capture each from a login with that combination. Where a persona is *unaffected* because their record type keeps the old assignment — the Renewals row in `worked-examples.md` §2 — say so explicitly in their message. Users assume any announced change applies to them unless told otherwise. See `admin/record-types-and-page-layouts` for how the record-type split itself is designed, and `admin/lightning-record-page-configuration` for the assignment mechanics.

---

## Gotcha 9: The Seasonal Release Moves the UI Underneath Your Rollout

**What happens:** A rollout scheduled across six weeks crosses the org's Spring, Summer or Winter upgrade weekend. Screenshots, walkthrough anchor points and click paths recorded in week one no longer match the platform in week five, and the reps trained last are trained on a UI that no longer exists. Worse, targeted in-app guidance anchors to a page element; if the release changes that element the prompt is left pointing at nothing.

**When it occurs:** Most often when the go-live date was chosen for business reasons (quarter end, campaign launch) with no reference to the instance's upgrade date, and when the training sandbox has been opted into Sandbox Preview while production has not — so the training org is already a release ahead of the org the reps will use.

**How to avoid:** Check the instance's upgrade date before the go-live date is committed, and record the check in the plan artefact's `release_window_check` field so the decision is auditable. If the rollout must cross the window, split it: everything before the upgrade weekend, then a re-verification pass on screenshots and prompt anchors, then the remainder. Do not run training in a preview sandbox for a production org that has not yet upgraded. `admin/salesforce-release-preparation` owns the upgrade-date lookup, the Release Updates triage and the Sandbox Preview opt-in decision — including the fact that preview opt-in cannot be rolled back for that release cycle.

---

## Gotcha 10: The Communication Plan Has No Row for Users Who Never See the UI

**What happens:** Every message in the plan is aimed at people who open Lightning pages. Integration users, API-only accounts and middleware service accounts get nothing — yet a new required field, a new validation rule or a changed picklist value breaks their writes exactly as hard as it changes a rep's screen. The failure surfaces as an integration error hours after go-live, owned by a team that was never told the change was happening.

**When it occurs:** Whenever the persona list is built from "who uses the screen" rather than "who touches the object". In-app guidance cannot reach these users at all: `Prompt` guidance renders on Lightning Experience and Experience Cloud pages, so an account that authenticates over OAuth and posts records never encounters it. They are also the users who quietly inflate adoption counts, since their logins land in `LoginHistory` alongside everyone else's.

**How to avoid:** Add a row per integration user or service account to the persona table with `training_format: none`, an owner from the integration team, and an explicit note on what changed at the field level. Their message is a mapping request, not an announcement — "this field is being added, confirm whether your sync writes it" — and it goes out with the same lead time as the user-facing messages. Exclude these user ids from every adoption metric by id, not by a `LoginType` filter, which does not reliably separate them. See `worked-examples.md` §2 for the row and §6 for the exclusion.
