# LLM Anti-Patterns — Integration Admin: Connected Apps

Common mistakes AI coding assistants make when advising on Connected App configuration.

## Anti-Pattern 1: Recommending Pre-Authorized Mode Without Profile/Permission Set Assignment

**What the LLM generates:** "Set the Permitted Users option to 'Admin approved users are pre-authorized' to restrict the connected app to specific users. This will prevent unauthorized OAuth access."

**Why it happens:** LLMs describe the pre-authorized setting correctly but omit the mandatory follow-up step of assigning the connected app to a Profile or Permission Set, which is documented separately in Salesforce help.

**Correct pattern:**

```
After setting "Admin approved users are pre-authorized":
1. Go to: Setup > Users > Profiles > [Integration User Profile]
2. Find "Connected App Access" section
3. Enable the checkbox for the connected app
4. Save

OR via Permission Set:
1. Go to: Setup > Permission Sets > [Integration Permission Set]
2. Click "Assigned Apps"
3. Enable the connected app

Without this assignment, ALL authentication attempts fail.
```

**Detection hint:** Any recommendation to set "Admin approved users are pre-authorized" without immediately following with the Profile or Permission Set assignment steps.

---

## Anti-Pattern 2: Recommending CSP Trusted Sites for Connected App Callout Issues

**What the LLM generates:** "Add your integration endpoint to CSP Trusted Sites to allow the connected app to call the external service."

**Why it happens:** LLMs conflate browser-side CSP (which governs what resources Lightning components can load) with server-side callout restrictions (which are governed by Remote Site Settings). Connected apps and their OAuth flows involve server-side calls, not browser-side CSP.

**Correct pattern:**

```
Connected App OAuth flows are server-side — governed by Remote Site Settings, not CSP.

For Apex callouts from Salesforce to an external system:
→ Add the endpoint URL to Remote Site Settings (Setup > Security > Remote Site Settings)

For Lightning components loading external resources in the browser:
→ Add to CSP Trusted Sites (Setup > CSP Trusted Sites)

CSP Trusted Sites have NO effect on Apex callouts or OAuth server-to-server flows.
```

**Detection hint:** Any suggestion to add a connected app endpoint to CSP Trusted Sites to fix an integration or callout issue.

---

## Anti-Pattern 3: Using Login History as the Source for OAuth Token Monitoring

**What the LLM generates:** "To monitor connected app usage, check Setup > Security > Login History and filter by the integration user."

**Why it happens:** Login History is the most visible audit tool in Salesforce Setup. LLMs recommend it for any monitoring question. It does not capture OAuth token-level events.

**Correct pattern:**

```
Login History: Shows login events (username, IP, login type). 
NOT sufficient for OAuth token monitoring.

For OAuth token-level monitoring:
- Requires Event Monitoring add-on
- Query EventLogFile via REST API:
  GET /services/data/vXX.0/query?q=SELECT+Id+FROM+EventLogFile
  +WHERE+EventType='ConnectedAppOAuth'+AND+LogDate=TODAY
- Download the CSV log and review TOKEN_TYPE, GRANT_TYPE, IP_ADDRESS columns
```

**Detection hint:** Any monitoring recommendation that only mentions Login History for connected app or OAuth investigation.

---

## Anti-Pattern 4: Recommending System Administrator Profile for Integration Users

**What the LLM generates:** "For simplicity, assign the System Administrator profile to your integration user to ensure it has all necessary permissions."

**Why it happens:** System Administrator profile is the universal "all access" shortcut in Salesforce. LLMs recommend it to resolve permission errors without considering the principle of least privilege.

**Correct pattern:**

```
NEVER assign System Administrator profile to integration users.
Reasons:
- Bypasses API-only flag (grants interactive login capability)
- Violates least privilege — gives access to all data and configuration
- Creates security risk if token is compromised

Correct approach:
1. Use Salesforce Integration user license
2. Pair with "Minimum Access - API Only Integrations" profile (non-editable, enforces API-only)
3. Grant specific object/field access via targeted Permission Sets
4. Assign connected app to the Permission Set
```

**Detection hint:** Any recommendation to assign System Administrator profile or a "cloned admin" profile to an integration user.

---

## Anti-Pattern 5: Ignoring the September 2025 Uninstalled App Blocking Policy

**What the LLM generates:** "The integration worked before the app was uninstalled — the tokens should still be valid and the integration should continue working."

**Why it happens:** Historically, uninstalled connected app tokens did continue to work. The September 2025 policy change (blocking uninstalled apps by default) post-dates much of the training data.

**Correct pattern:**

```
As of September 2025: Uninstalled connected apps are blocked by default.

If an integration is failing with OAuth errors after an app was uninstalled:
1. Go to: Setup > Apps > Connected Apps > OAuth Usage
2. Identify the uninstalled app still in use
3. Either: Re-authorize the app (re-install or re-register)
         Or: Migrate the integration to a new connected app
4. Run quarterly audits to catch orphaned integrations before they fail
```

**Detection hint:** Any claim that uninstalled connected app tokens remain valid without qualifying with the current Salesforce policy.

---

## Anti-Pattern 6: Prescribing "Use Any API Client" to Unblock a Third-Party OAuth Client

**What the LLM generates:** "API Access Control is blocking that app. Grant the user the 'Use Any API Client' permission and the OAuth authorization will go through."

**Why it happens:** This was the correct fix for years and is the answer baked into older admin blogs and forum threads. The restriction that removed it landed the week of December 8, 2025 as a dated security enforcement rather than a release feature, and its replacement permission did not exist before September 2025.

**Correct pattern:**

```
Org preference "For admin-approved users, limit API access to only
allowlisted connected apps" ENABLED, and the app is NOT installed:

  Use Any API Client on its own -> self-authorization BLOCKED
  (changed the week of December 8, 2025)

Fix, in order of preference:
1. Install the connected app in the org and allowlist it.
   This is the remedy Salesforce directs admins to.
2. Only when an admin or developer must test before installing:
   grant "Approve Uninstalled Connected Apps" to that individual —
   not to a profile, and not to end users.

Preference DISABLED -> Salesforce publishes no behavior table for
this case. Uninstalled apps are still blocked by default for most
users under the September 2025 policy, so verify in a sandbox
rather than assuming the old override still works.

Already-active sessions keep working; only new authorizations break.
```

**Detection hint:** Any recommendation to grant "Use Any API Client" to unblock an OAuth client, or any connected-app troubleshooting list that never mentions "Approve Uninstalled Connected Apps."

---

## Anti-Pattern 7: Writing a Revocation Step as DML Against `OauthToken`

**What the model produces:** A "revoke the integration's access" runbook step written as
`DELETE FROM OauthToken WHERE ...`, an Apex `delete [SELECT Id FROM OauthToken ...]`, a
record-triggered Flow, or a Data Loader delete job — all of which look plausible because
`OauthToken` is a queryable sObject with a `DeleteToken` field.

**Why it is wrong:** The Object Reference lists exactly two supported calls on `OauthToken`:
`describeSObjects()` and `query()`. There is no `delete()`, so none of those constructs compile or
run. The `DeleteToken` field is not a flag to update — it is "a token that can be used at the revoke
OAuth token endpoint to remove this token", used as
`https://MyDomainName.my.salesforce.com/services/oauth2/revoke?token=(the Delete Token)`.

An Apex version fails a second way even for the *query*: "If you try to use Apex DML operations and
then query this object in the same call, you get an `UncommittedWork` error." A helper that logs a
record and then reads `OauthToken` in the same transaction breaks on the read.

**Correct approach:** Query `DeleteToken` as a user with Customize Application, then call the revoke
endpoint over HTTP. For an org-wide stop, **Block** the app on the Connected Apps OAuth Usage page or
deploy `sessionPolicy/policyAction` = `Block`.

**Detection hint:** Any generated runbook, Flow, or Apex snippet that deletes, updates or upserts
`OauthToken`; any Apex helper that performs DML and then queries `OauthToken` without splitting into
asynchronous calls.

---

## Anti-Pattern 8: Filtering `LoginHistory` by `Application`, `Status`, or `SourceIp`

**What the model produces:** The natural-language request "show me logins through the Billing Sync
connected app from unexpected IPs" turned into
`SELECT ... FROM LoginHistory WHERE Application = 'Billing Sync JWT' AND Status = 'Success'` or a
`WHERE SourceIp != '203.0.113.10'` clause. The field names are real, the fields are returned in
`SELECT`, and the query reads correctly — it simply cannot be filtered on.

**Why it is wrong:** The Object Reference publishes a closed filterable list for `LoginHistory`:
`AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`,
`NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`, `UserId`. `Application`, `Status` and
`SourceIp` carry only `Group, Nillable, Sort`.

**Correct approach:** Filter on `UserId` and `LoginTime`, then read the other columns off the result;
or aggregate with `GROUP BY Application, LoginType, Status`. When filtering by `LoginType`, quote the
values exactly — `Application`, `Oauth, Remote Access Client`, `Oauth2, Remote Access 2.0` — two of
which contain a comma inside the value.

**Detection hint:** Any generated `LoginHistory` SOQL whose `WHERE` clause names a field outside the
twelve-field list, or that splits `LoginType` values on a comma.

---

## Anti-Pattern 9: Presenting a 2,500-Row Token Query as a Complete Inventory

**What the model produces:** "Here are all the users holding tokens for this app" followed by a
`SELECT AppName, UserId, LastUsedDate FROM OauthToken` with no count query, no paging, and no caveat
— and often keyed on `Id`.

**Why it is wrong:** "A `query()` call returns up to 500 rows. A `queryMore()` call returns 500 more,
up to 2,500 total. No more records are returned after 2,500." The truncation is silent. `OFFSET` is
capped at 2,000 ("Requesting an offset greater than 2,000 results in a
`NUMBER_OUTSIDE_VALID_RANGE` error"), and `Id` on this object is "Reserved for future use. Currently,
the value is always null", so it cannot key or de-duplicate the results. Separately, a query run
without Customize Application returns only the caller's own tokens, which produces a confident and
completely wrong "nobody uses this app."

**Correct approach:** Run `SELECT COUNT() FROM OauthToken` first, compare it against the rows
returned, and page by `UserId` (or `LIMIT 2000 OFFSET n`) when it exceeds 2,500. State the running
user's permission requirement next to the query.

**Detection hint:** A token-inventory answer with no `COUNT()`, no paging strategy, no mention of
Customize Application, or a result set of exactly 500 or 2,500 rows described as "all".

---

## Anti-Pattern 10: Claiming a Connected App's Consumer Key or Secret Can Be Rotated by Editing the XML

**What the model produces:** A rotation runbook that says to retrieve the `connectedApp-meta.xml`,
change `consumerKey` (or `consumerSecret`), and redeploy — sometimes with a diff showing the old and
new values side by side.

**Why it is wrong:** `consumerKey`: "In API version 32.0 and later, you can set this field's value
only during creation. After you define and save the value, it can't be edited." `consumerSecret` is
also uneditable after save and "isn't returned in Metadata API requests", so the retrieved file never
contained the old value to diff against. The rotation flags exist only on the External Client App's
`ExtlClntAppGlobalOauthSettings` — `shouldRotateConsumerKey` and `shouldRotateConsumerSecret` — and
both state: "To maintain security, if this field is set to `true`, you must include the ignore
warnings attribute in the deploy command." A generated rotation deploy without that attribute is
rejected, and the model usually reads the rejection as a pipeline bug.

**Correct approach:** For a connected app, rotation is a replacement app plus a coordinated caller
cutover. For an External Client App, set both flags `true`, deploy with the ignore-warnings
attribute, then set them back to `false`.

**Detection hint:** Any rotation instruction that edits `consumerKey`/`consumerSecret` in place; any
ECA rotation deploy command without an ignore-warnings flag; any claim that a retrieved connected app
file is a complete backup.
