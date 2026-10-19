# Gotchas — Pipeline Secrets Management

## Gotcha 1: An SFDX authorization URL is the org

**What happens:** Anyone with read access to the repository, a CI log, or a support ticket that contains the URL can authorize the org.

**When it occurs:** A developer exports the URL with `sf org auth show-sfdx-auth-url --json > authFile.json` for CI and the file, or its contents, ends up committed or pasted. The guide describes the URL as containing all the information needed to authorize the org in a CI environment.

**How to avoid:** Prefer the JWT flow. If an auth URL must be used, keep it only in the CI secret store, write it to a temp file at login, and delete the file in a `trap`. Run the checker so a `force://` URL can never merge.

---

## Gotcha 2: The CLI hides secrets until a command is told to print them

**What happens:** A "debug" step prints a live access token or auth URL into a CI log that is retained and widely readable.

**When it occurs:** `sf org display` and `sf org list` no longer show secrets, but `sf org auth show-access-token`, `show-sfdx-auth-url`, and `show-user-password` do — and `--json` or `--no-prompt` skip their confirmation prompt, which is exactly how they run in CI. `SF_TEMP_SHOW_SECRETS=true` restores the old `sf org display` behaviour.

**How to avoid:** No pipeline step calls `sf org auth show-*` or sets `SF_TEMP_SHOW_SECRETS`. Check connectivity by printing only the username from `sf org display --json`.

---

## Gotcha 3: An app anyone can authorize

**What happens:** The app is open to every user in the org rather than only the integration user, so a leaked key reaches further than the pipeline ever needed.

**When it occurs:** A connected app's `isAdminApproved` defaults to false, meaning anyone in the org can authorize it; the JWT setup in the guide instead sets Permitted Users to "Admin approved users are pre-authorized".

**How to avoid:** Use admin-approved pre-authorization and grant the app only to the integration user's profile or permission set. Give that user only the permissions the pipeline needs.

---

## Gotcha 4: The wrong app type for a Dev Hub

**What happens:** CI can log in to the Dev Hub with JWT but `sf org create scratch` or `sf org create sandbox` fails in the pipeline.

**When it occurs:** The guide prefers an external client app for JWT, but says that if you authorize a Dev Hub and plan to create scratch orgs or sandboxes with those commands, you must create a connected app instead.

**How to avoid:** Decide the app type per org from what the pipeline does there; record it in the app matrix.

---

## Gotcha 5: High assurance sessions block headless login

**What happens:** The JWT login that works in a sandbox fails against production.

**When it occurs:** If the org requires high assurance (stepped-up) authentication, Salesforce prompts the user to verify identity, so the JWT flow and the SFDX authorization URL can't be used for headless authentication.

**How to avoid:** Confirm the integration user's session security requirements before building the pipeline, and adjust that user's policy rather than falling back to a stored password.

---

## Gotcha 6: External client app OAuth settings are not source

**What happens:** A retrieve of the whole org pulls the app's OAuth settings into the repository, including consumer secrets.

**When it occurs:** `ExtlClntAppGlobalOauthSettings` (`.ecaGlblOauth`) holds private and sensitive OAuth consumer information that the Metadata API guide says can't be packaged and must not be added to source control. A connected app's `consumerSecret` is likewise sensitive (it isn't returned by Metadata API once set, but a hand-written file can contain it).

**How to avoid:** Exclude `*.ecaGlblOauth*` in `.forceignore` and `.gitignore`, never write `<consumerSecret>` into a `.connectedApp` file, and let the checker fail the build if either appears.

---

## Gotcha 7: Expired certificate

**What happens:** Every deployment fails with an authentication error on one specific morning.

**When it occurs:** The JWT certificate reaches its validity end; the guide's own self-signed example is valid for 365 days, and nothing in the pipeline warns beforehand.

**How to avoid:** Track the expiry date of every CI certificate, alert well ahead of it, and rotate on a schedule using `rotation-runbook.md`.
