# Gotchas: Connected Apps and Auth

---

## Using Admin Users for Integrations

**What happens:** A system integration authenticates as a human admin because it was the fastest way to get moving.

**When it bites you:** Security reviews, incident response, and any permission-related defect investigation.

**How to avoid it:** Use a dedicated integration principal with minimal permission sets and documented ownership.

---

## Hardcoded Endpoints and Tokens in Code

**What happens:** Developers or admins put API URLs or bearer tokens directly into Apex, JavaScript, or config files.

**When it bites you:** Environment promotion, credential rotation, and emergency revocation.

**How to avoid it:** Use Named Credentials and External Credentials as the default integration boundary.

---

## Choosing the Wrong OAuth Flow

**What happens:** A user-delegated scenario is built with machine auth, or a system-to-system integration is awkwardly forced through user consent.

**When it bites you:** Token lifecycle, access reviews, and long-term operability.

**How to avoid it:** Choose the auth flow based on whether user context is required and whether certificate management exists.

---

## No Revoke or Rotation Runbook

**What happens:** The integration works until a secret must be rotated or a connected app must be revoked quickly. Nobody knows the blast radius.

**When it bites you:** Expiring certificates, security incidents, and audit findings.

**How to avoid it:** Treat revoke, rotate, and recover as tested operational procedures.

---

## Assuming You Can Create a New Connected App in Spring '26+

**What happens:** A design calls for a brand-new connected app, but starting in Spring '26 Salesforce blocks connected-app creation by default — through both the UI and the Metadata API. Only package installation is excepted, and creation otherwise requires an exception from Salesforce Support.

**When it bites you:** Mid-build, when the "create connected app" step in the UI or a `ConnectedApp` metadata deploy fails in a Spring '26+ org and the whole integration timeline stalls.

**How to avoid it:** Design net-new inbound integrations on an External Client App (ECA), which Salesforce calls the new and improved generation of connected apps. If a connected app is genuinely required, deliver it through a package install or request a Support exception. All existing connected apps continue to work, so this only affects net-new creation.

---

## Treating Block and the Permitted Users Switch as Reversible Experiments

**What happens:** During a hardening pass an admin clicks **Block** on a connected app in the OAuth Usage page to see who complains, or flips **Permitted Users** from *All users may self-authorize* to *Admin approved users are pre-authorized* before assigning anyone.

**When it bites you:** Immediately. Blocking ends all current user sessions for the app and prevents future sessions. Switching Permitted Users to admin-approved revokes access for current users unless their profile or permission set already grants access to the app.

**How to avoid it:** Establish usage and ownership from the Connected Apps OAuth Usage page first, assign the profile or permission set before switching Permitted Users, and reserve Block for apps you have already decided to kill.

---

## Assuming an External Client App Can Be Created Anywhere a Connected App Could

**What happens:** After hearing that connected apps are frozen in Spring '26, a team swaps every app to an External Client App and hits three walls that connected apps never had. Salesforce DX still splits org auth by command — an ECA is required for `org login jwt`, but "If you're authorizing a Dev Hub org and plan to create scratch orgs or sandboxes with the `org create scratch|sandbox` commands, then you create a connected app instead." You also can't build an ECA in a scratch org from Setup: "You can't create External Client Apps directly in scratch orgs using the Setup UI." And the metadata type has a floor — `ExternalClientApplication` components are available in API version 59.0 and later.

**When it bites you:** In the CI/CD pipeline, not the design review. The JWT auth step passes, then `org create scratch` fails because the Dev Hub was re-pointed at an ECA. Or a scratch-org-based test fails with no app to authorize against. Or the ECA deploys fine from one repo and is rejected from an older one whose `sourceApiVersion` (in `sfdx-project.json`) or `package.xml` `<version>` still sits below 59.0 — this floor is the project's deploy API version, not the org's release, so a Spring '26 org will still reject an ECA pushed at 58.0.

**How to avoid it:** Enumerate the sf commands the pipeline runs before choosing a container. Where a Dev Hub both authenticates by JWT and provisions scratch orgs, the two rules collide — the doc says to create a connected app *instead* of an ECA for that org, not alongside it — so decide which command the pipeline actually depends on rather than assuming you can satisfy both. For scratch-org testing, follow the documented path: "create the External Client App in a developer hub org, add it to a package, and install the package in the target scratch org." Raise `sourceApiVersion` to 59.0+ in any project that will deploy ECA metadata.
