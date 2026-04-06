# LLM Anti-Patterns — Sandbox Refresh and Templates

Common mistakes AI coding assistants make when generating or advising on Salesforce sandbox refresh and templates.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Mentioning That Sandbox Refresh Overwrites All Changes

**What the LLM generates:** "Refresh your sandbox to get the latest production data" without warning that a refresh completely replaces ALL metadata and data in the sandbox, destroying any in-progress development work.

**Why it happens:** LLMs treat refresh as an "update" operation. In reality, it is a destructive replacement — the sandbox is deleted and recreated from the production snapshot.

**Correct pattern:**

```text
Sandbox refresh behavior:
- DELETES the existing sandbox entirely
- RECREATES it as a copy of production (metadata + data for Full/Partial)
- All in-progress work in the sandbox is PERMANENTLY LOST
- Usernames change to include the sandbox name suffix

Pre-refresh checklist:
1. Commit all in-progress code to source control
2. Export any sandbox-specific test data you want to preserve
3. Document custom configurations not in production
4. Notify all sandbox users that their work will be lost
5. Export Named Credential secrets (not copied during refresh)
6. Save a list of scheduled jobs and Apex Schedulable configurations
```

**Detection hint:** Flag sandbox refresh recommendations that do not include a pre-refresh backup or notification step. Look for "refresh to get latest" without a destruction warning.

---

## Anti-Pattern 2: Ignoring the SandboxPostCopy Interface for Post-Refresh Automation

**What the LLM generates:** "After refreshing the sandbox, manually update the integration endpoints, reset test users, and configure Named Credentials" without mentioning the `SandboxPostCopy` Apex interface that automates post-refresh tasks.

**Why it happens:** SandboxPostCopy is a Salesforce-specific automation interface with limited coverage in training data. LLMs default to manual post-refresh checklists instead of automated solutions.

**Correct pattern:**

```apex
// Implement SandboxPostCopy to automate post-refresh tasks:
global class PostRefreshSetup implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        // 1. Update integration endpoints to sandbox URLs
        Integration_Config__c config = Integration_Config__c.getOrgDefaults();
        config.Endpoint__c = 'https://api-sandbox.example.com';
        upsert config;

        // 2. Reset email deliverability (sandbox default = System Only)
        // Note: cannot change email deliverability via Apex

        // 3. Deactivate production scheduled jobs
        List<CronTrigger> jobs = [SELECT Id FROM CronTrigger];
        for (CronTrigger job : jobs) {
            System.abortJob(job.Id);
        }

        // 4. Create test users or activate sandbox-specific users
        // 5. Update Custom Metadata or Custom Settings for sandbox behavior
    }
}
```

**Detection hint:** Flag post-refresh instructions that list 5+ manual steps without mentioning `SandboxPostCopy` or an Apex class for automation.

---

## Anti-Pattern 3: Recommending Sandbox Templates Without Noting Partial Copy Limitations

**What the LLM generates:** "Use a sandbox template to control which data gets copied during refresh" without specifying that sandbox templates only work with Partial Copy sandboxes (not Developer, Developer Pro, or Full Copy).

**Why it happens:** Sandbox templates are discussed generically in training data without consistently specifying which sandbox type supports them.

**Correct pattern:**

```text
Sandbox template availability by type:

Developer:        NO data copied, NO template support
Developer Pro:    NO data copied, NO template support
Partial Copy:     Template REQUIRED to select objects, max 10,000 records/object
Full Copy:        ALL data copied, NO template needed (copies everything)

Partial Copy template rules:
- Select up to 200 objects to include
- Maximum 10,000 records per object
- Records selected based on standard criteria (most recent, etc.)
- Relationships are NOT automatically followed (children of selected
  parent records are not guaranteed to be included)
- Template must be created before starting the refresh

For Partial Copy, design the template to include:
1. All objects needed for testing scenarios
2. Objects in parent-before-child order for referential integrity
3. Account and Contact pairs (not just Accounts without Contacts)
```

**Detection hint:** Flag sandbox template recommendations for Developer or Full Copy sandboxes. Check for missing mention of the 10,000 records per object limit.

---

## Anti-Pattern 4: Forgetting That Named Credential Secrets Are Not Copied During Refresh

**What the LLM generates:** "After refresh, all integrations will work the same as production" without noting that Named Credential secrets (OAuth tokens, passwords, API keys) are blanked out during sandbox refresh for security reasons.

**Why it happens:** Named Credential metadata is copied (endpoint URL, authentication type), but the actual secret values are stripped. LLMs do not distinguish between metadata and credential values.

**Correct pattern:**

```text
Components NOT preserved during sandbox refresh:

- Named Credential secrets (OAuth tokens, passwords, API keys)
- External Credential secrets
- Connected App consumer secrets (if the Connected App is in the sandbox)
- Encryption keys (Shield tenant secrets)
- Scheduled Apex job schedules (jobs exist but are paused)

Post-refresh credential restoration:
1. Re-enter Named Credential authentication values in Setup
2. Re-authorize OAuth-based Named Credentials
3. Update Connected App callback URLs if using sandbox-specific URLs
4. Automate what you can via SandboxPostCopy (Custom Settings, endpoints)
5. Maintain a secure credential vault for sandbox secrets
```

**Detection hint:** Flag post-refresh instructions that claim integrations work immediately. Look for missing Named Credential re-authentication steps.

---

## Anti-Pattern 5: Not Accounting for Sandbox Refresh Intervals

**What the LLM generates:** "Refresh your sandbox whenever you need fresh data" without noting that each sandbox type has a minimum refresh interval, and refreshing before the interval expires is not possible.

**Why it happens:** Refresh intervals are operational constraints that vary by sandbox type. Training data covers the concept of refresh but not the cooldown periods.

**Correct pattern:**

```text
Sandbox refresh intervals:

Developer:        1 day
Developer Pro:    1 day
Partial Copy:     5 days
Full Copy:        29 days

Additional constraints:
- Only one refresh can run at a time per sandbox
- Full Copy refresh can take 1-7+ days for large orgs
- Refresh queue position depends on org size and Salesforce load
- You cannot use the sandbox while refresh is in progress

Planning implications:
- Full Copy: plan refreshes at the start of each release cycle
- Partial Copy: can refresh more frequently for QA cycles
- Developer: use for feature development, refresh as needed
- Consider multiple Developer sandboxes to avoid waiting for refresh
```

**Detection hint:** Flag sandbox strategies that assume on-demand refresh for Full Copy sandboxes. Check for missing refresh interval documentation in environment planning.
