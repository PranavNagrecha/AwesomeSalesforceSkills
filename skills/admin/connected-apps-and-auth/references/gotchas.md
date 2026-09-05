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

---

## The Consumer Secret Does Not Come Back From a Retrieve

**What happens:** A team retrieves a working connected app from production, commits the file, and deploys it to a second org expecting an identical app. The Metadata API Developer Guide says of `consumerSecret`: "When set, the value isn't returned in Metadata API requests." The retrieved XML has no secret in it, so the deploy creates an app with a *new* Salesforce-generated secret that nobody has recorded. `consumerKey` has the mirror-image problem: "In API version 32.0 and later, you can set this field's value only during creation. After you define and save the value, it can't be edited," and "Consumer keys must be globally unique."

**When it bites you:** At cutover, when the external caller presents the production `client_id`/`client_secret` pair against the new org and gets an authentication failure — long after the deploy reported success. It also bites any "rotate the key by editing the file" plan, because the field is immutable after save.

**How to avoid it:** Treat the key/secret pair as environment data held by the *caller*, not as source. Record which org each pair belongs to at creation time. To change a key on a connected app, create a replacement app and cut the caller over; on an External Client App, use `shouldRotateConsumerKey` / `shouldRotateConsumerSecret`, which regenerate on deploy and require the ignore-warnings attribute in the deploy command.

---

## Admin-Approved Is a Two-Field Contract, and Half of It Deletes Silently

**What happens:** An app is deployed with `<isAdminApproved>true</isAdminApproved>` and no `permissionSetName` or `profileName`. The deploy succeeds and the app is now pre-authorized for exactly nobody. The guide is explicit in both directions: setting `isAdminApproved` to true means "only users with the appropriate profile or permission set can access the app," and both access fields carry "To use this field, the `isAdminApproved` field on the `ConnectedAppOauthConfig` subtype must be set to true." The reverse case is worse — deploying an empty element removes every assignment: "You can delete individual permission sets or remove all permission sets from a connected app by entering an empty `permissionSetName` string on deployment."

**When it bites you:** Immediately after a deploy that looked like a no-op, because a partial source file omitted the access elements. Also in Group Edition, where the guide notes the setting "isn't available" at all.

**How to avoid it:** Never deploy `isAdminApproved` without the matching `permissionSetName` (one name per line) or repeated `profileName` elements in the same file, and never let a generated or hand-trimmed file ship an empty one. `scripts/check_connected_auth.py --manifest-dir <dir>` fails the build on this exact shape.

---

## `refreshTokenPolicy` Defaults to Never Expiring, and Tightening It Does Not Log Anyone Out

**What happens:** The field is Required on `ConnectedAppOauthPolicy`, and its default is `infinite` — "the refresh token is used indefinitely, unless revoked by the user or Salesforce admin. Default setting." Teams then over-correct and assume that shortening the policy evicts current sessions. It does not: "The Refresh Token policy is evaluated only during usage of the issued refresh token and doesn't affect a user's current session."

**When it bites you:** Twice, in opposite directions. In an audit, when a five-year-old integration turns out to hold a refresh token that has never expired. And during incident response, when someone shortens the policy expecting an immediate cut-off and the compromised session keeps working until its access token expires.

**How to avoid it:** Set an explicit value on every app — `specific_lifetime:<n>:HOURS|DAYS|MONTHS` for a hard ceiling, `specific_inactivity:<n>:...` for a use-it-or-lose-it window whose clock resets on each exchange. For an actual cut-off, revoke the grant (`OauthToken.DeleteToken`) or block the app; the policy is a ceiling, not a kill switch.

---

## The Four `ipRelaxation` Values Are Not a Strictness Ladder

**What happens:** `ipRelaxation` reads like ENFORCE > ENFORCE_RELAXREFRESH > BYPASS_2FACTOR > BYPASS, so people pick a middle value to "loosen it a bit." The guide's definitions do not line up that way. `BYPASS_2FACTOR` only means anything for the web server flow — it applies when "the app has a list of allowed IP ranges and is using the web server OAuth authorization flow," or when the app has no ranges "but it uses the web server authentication flow" and the user completes identity verification on a new browser or device. `ENFORCE_RELAXREFRESH` enforces org IP restrictions but "bypasses these restrictions when the connected app uses refresh tokens to get access tokens."

**When it bites you:** On a JWT-bearer or client-credentials integration set to `BYPASS_2FACTOR`, where the value does nothing the admin thought it did because there is no web server flow to qualify. And on a long-running integration set to `ENFORCE_RELAXREFRESH`, where every renewal after the first legitimately skips the IP check.

**How to avoid it:** Choose by flow, not by strictness. Headless flows: `ENFORCE` plus a real `ipRanges` list. Web server flows from known networks: `ENFORCE`. Reserve `ENFORCE_RELAXREFRESH` for the case you can name out loud — a client that renews from addresses you cannot enumerate — and `BYPASS` for nothing in production.

---

## An External Client App Is Not a Renamed Connected App

**What happens:** A migration script rewrites `<ConnectedApp>` to the ECA types and changes nothing else. Four things break, all documented. The scope element changes cardinality: repeated `<scopes>` become one `<commaSeparatedOauthScopes>` string. `isPkceRequired` flips default — `false` on `ConnectedApp`, and on `ExtlClntAppGlobalOauthSettings` "If set to `true` (default) Proof Key for Code for Exchange (PKCE) is required." IP and refresh-token policy move to a different vocabulary and casing (`ipRelaxationPolicyType` `Enforce`; `refreshTokenPolicyType` `SpecificInactivity` plus a separate period and unit). And the secrets are carved into their own file, `ExtlClntAppGlobalOauthSettings`, which "include[s] private and sensitive OAuth consumer information that can't be packaged and must not be added to source control."

**When it bites you:** At deploy, on the enum casing, and at runtime for anything that quietly inherited a flipped PKCE default. Also on day one in a locked-down org: `ExternalClientApplication` "requires orgs to enable the Opt in to External Client Apps permission in Setup," and the OAuth plugin types require the "Allow Access to OAuth Consumer Secrets via Metadata API" permission.

**How to avoid it:** Hand-map the four fields rather than search-and-replacing, enable the Setup permissions before the first deploy, keep `ExtlClntAppGlobalOauthSettings` out of the repo, and see the side-by-side table in `references/metadata-examples.md`.

---

## Post-Deploy Verification Against `OauthToken` Fails on Two Rules Nobody Reads

**What happens:** A verification step queries `OauthToken` to prove which users hold grants for an app, and returns an empty list. Two Object Reference rules explain it. Visibility: "Users with the Customize Application permission see all tokens for all users in the org. Otherwise, you see only your own tokens." And transaction shape: "If you try to use Apex DML operations and then query this object in the same call, you get an `UncommittedWork` error … To avoid this error, execute DML operations and queries in separate, asynchronous calls."

**When it bites you:** When the verification runs as a deliberately least-privileged integration user — the exact principal you were told to use everywhere else — and reports "no one is using this app" about an app in daily use. And in any Apex verification helper that logs a record and then queries in the same transaction.

**How to avoid it:** Run the token inventory as a user who holds Customize Application, and state that requirement in the runbook next to the query. In Apex, split the write and the query into separate asynchronous calls. Treat an empty `OauthToken` result as unproven, never as proof of disuse.
