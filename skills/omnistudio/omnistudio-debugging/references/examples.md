# Examples: OmniStudio Debugging

## Example 1: Integration Procedure HTTP Action Failing in Production After Sandbox Promotion

**Context:** A team built an Integration Procedure that calls an external REST API using a Named Credential. The IP works correctly in their sandbox. After deploying to production via a change set, every call to the IP silently returns an empty response with no error message shown to the user.

**Problem:** The team deployed the IP metadata but did not recreate the Named Credential in production. The HTTP action references the Named Credential by name, `ExternalCRM_Credential`, which exists in sandbox but does not exist in production. The HTTP step's error never reached the user because the IP had no Try-Catch Block around the call and the Response Action returned only the (empty) data node.

**Solution:**

1. Open the IP in the production designer and use the Preview pane.
2. Enter the expected input parameters and execute. Keep the input as a file so every re-run uses the same data:

```json
{
  "AccountId": "001XXXXXXXXXXXXXXX",
  "includeContacts": true
}
```

3. Read Errors/Debug Output for the HTTP step. The error points at the missing named credential.
4. In production Setup, create the Named Credential with the same name (`ExternalCRM_Credential`) pointing to the production endpoint with correct auth.
5. Re-run the Preview with the same input. Confirm the HTTP step now returns data.
6. Wrap the HTTP step in a Try-Catch Block that returns a specific error output, and have the OmniScript show it.

**Why it works:** The IP Preview pane runs the procedure in the current org and shows Errors/Debug Output per step, which the end user never sees. Recreating the named credential fixes the transport. The Try-Catch Block ("returns specified output or calls an Apex class if a step within it fails") closes the silent failure path. Because the endpoint is a named credential, no Remote Site Setting is needed.

---

## Example 2: DataRaptor Extract Returns Empty Records for All Users Except the Designer

**Context:** A DataRaptor Extract was built and tested by a system administrator with full access. The asset retrieves `Opportunity` records filtered by the current account ID passed as input. When a portal user triggers the OmniScript that calls this DataRaptor, the step returns empty results and the OmniScript continues as if no opportunities exist.

**Problem:** The DataRaptor Preview runs in the context of the logged-in designer (a system administrator with full access). The Opportunity records are visible to the admin, so Preview appears to work. In production, portal users have a community profile with restricted Opportunity visibility, they can only see Opportunities they own or that are shared with them via sharing rules. The DataRaptor respects the runtime user's record access. Because the portal user has no Opportunities in their visibility scope matching the account ID filter, the Extract returns empty results. The OmniScript treats the empty result as a valid response (no records found) rather than an error.

**Solution:**

1. In sandbox, create or use a test user with the portal profile.
2. Log in as that test user (or use Login As) and run the OmniScript.
3. Open the Action Debugger in Preview (logged in as the portal user via Experience Builder preview). Expand the DataRaptor action node.
4. Confirm the input is correctly populated with the account ID.
5. Run the DataRaptor Preview with the same input parameters, and compare its result with what the portal user receives. UNVERIFIED (2026-10-03): Salesforce Help says the Extract Preview shows the generated query; the fetched sources don't.
6. Verify that the portal user has the expected sharing access to those Opportunity records. If not, update sharing rules or use a dedicated Integration Procedure with system-level access where the business requirement justifies it.

**Why it works:** The Extract returns what the running user can see, which differs from the designer's view (UNVERIFIED (2026-10-03): the exact sharing behavior of Extracts is documented only in Salesforce Help; the Options-tab field access check is in Trailhead). Running Preview as the designer obscures access problems. Testing with a representative user profile and using the Action Debugger's per-element input/output trace exposes the gap between what the system administrator sees and what the portal user sees.

---

## Example 3: OmniScript Navigation Action Not Firing: Mistaken for a Bug

**Context:** An OmniScript includes a Navigation Action element that should redirect the user to a Record Detail page after the final step completes. During testing in the OmniScript designer's Preview tab, the Navigation Action appears to do nothing, the script just stops after the last step without any redirect.

**Problem:** The team suspects a configuration error in the Navigation Action element and spends time checking the page reference type, object API name, and record ID data path, all of which are correctly configured. The likely cause is the Preview environment itself: it has no Lightning app or site context to navigate into. UNVERIFIED (2026-10-03): Salesforce Help states that Navigate Actions don't run in Preview; the fetched Trailhead units describe Preview without saying so.

**Solution:**

1. Stop debugging the Navigation Action element configuration in Preview: that environment will never execute it.
2. Deploy or activate the OmniScript in a sandbox Lightning app page or Experience Site.
3. Launch the OmniScript from the deployed context. Complete all steps.
4. Observe whether the Navigation Action fires correctly in the live component context.
5. If the Navigation Action still does not fire in the deployed context, then check the element configuration: page reference type, record ID source, and whether the action is conditional on a data node value that may be null.

**Why it works:** Testing navigation in the deployed page removes the Preview environment as a variable. If it still fails there, the element configuration is the real cause.

---

The retrieval, diff, and Remote Site Setting files for the environment comparison are in [metadata-examples.md](metadata-examples.md).

---

## Anti-Pattern: Using OmniScript Preview as a Substitute for End-to-End Testing

**What practitioners do:** Teams build and test OmniScripts entirely in the designer's Preview tab. They treat a clean Preview run as confirmation that the script is production-ready.

**What goes wrong:** Preview may not exercise navigation (UNVERIFIED (2026-10-03), Help only), runs in the designer user's security context (not the runtime user's), and does not exercise environment-specific dependencies like production Named Credentials or experience site routing. Silent element failures that only surface with portal users or in production environments are not caught. Teams ship scripts that appear to work in Preview but fail for real users.

**Correct approach:** Use Preview for rapid iteration on data paths, element configuration, and step logic. Use the Action Debugger to inspect element-level input/output during Preview. Then test with a representative user in the actual deployment context, a sandbox Lightning app page or sandbox Experience Site, before promoting to production. Validate Navigation Actions, sharing-dependent data, and environment-specific credentials only in a deployed context.
