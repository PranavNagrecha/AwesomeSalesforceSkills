# LLM Anti-Patterns — Sandbox Refresh and Templates

Common mistakes AI coding assistants make when generating or advising on Salesforce sandbox refresh and templates.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Warning That Refresh Replaces the Sandbox's Contents

**What the LLM generates:** "Refresh your sandbox to get the latest production data" with no warning that work done only in the sandbox will not survive.

**Why it happens:** LLMs treat refresh as an incremental "update". A refresh updates the sandbox's metadata from the source org, and its data too when the sandbox is a clone or uses a template — so anything that exists only in the sandbox is at risk.

**Correct pattern:**

```text
Pre-refresh checklist:
1. Commit all in-progress metadata to source control (retrieve it first)
2. Export any sandbox-only test data you want to keep
3. Notify everyone who works in the sandbox, with the date
4. List the scheduled jobs the sandbox needs (they are not copied)
5. Confirm the definition file / Setup form names the template and the post-copy class
```

**Detection hint:** Refresh recommendations with no backup, notification, or job-rescheduling step.

---

## Anti-Pattern 2: Ignoring the SandboxPostCopy Interface for Post-Refresh Automation

**What the LLM generates:** A long manual post-refresh checklist (endpoints, users, config) with no mention of `SandboxPostCopy`.

**Why it happens:** `SandboxPostCopy` has limited coverage in training data, so models default to manual checklists.

**Correct pattern:**

```apex
global class PostRefreshSetup implements SandboxPostCopy {
    global PostRefreshSetup() {}   // required: the copy process uses the no-arg constructor
    global void runApexClass(SandboxContext context) {
        Integration_Config__c config = Integration_Config__c.getOrgDefaults();
        config.Endpoint__c = 'https://api-sandbox.example.com';
        upsert config;
        // Reschedule the jobs this sandbox needs: scheduled jobs are not copied on refresh.
        System.schedule('Sandbox nightly', '0 0 3 * * ?', new NightlySchedulable());
    }
}
```

Keep a manual runbook only for what the Automated Process user can't do, and test the class with `Test.testSandboxPostCopyScript(..., true)`.

**Detection hint:** Post-refresh instructions with five or more manual steps and no `SandboxPostCopy` class.

---

## Anti-Pattern 3: Getting Template Availability Wrong

**What the LLM generates:** "Sandbox templates only apply to Partial Copy sandboxes" or "attach a template to your Developer sandbox", often with invented per-object record counts.

**Why it happens:** Templates are discussed generically, and help-article numbers are recalled without context.

**Correct pattern:**

```text
templateId in a sandbox definition file:
  Partial  -> required
  Full     -> optional (copy only the objects you select)
  Developer / Developer_Pro -> not available
A sandbox template selects which objects to copy.
```

**Detection hint:** A template recommended for a Developer sandbox, a Partial definition with no `templateId`, or a claim that Full sandboxes can't use one.

---

## Anti-Pattern 4: Saying Scheduled Jobs Are Copied and Must Be Aborted

**What the LLM generates:** "Production's scheduled jobs will start firing in the sandbox — abort every `CronTrigger` in your post-copy class."

**Why it happens:** It sounds like the safe, defensive default, and it is repeated widely.

**Correct pattern:**

```text
Apex Developer Guide: when you refresh a sandbox, scheduled jobs from the source org
aren't copied; reschedule any jobs you need in the refreshed sandbox.
So: no abortJob loop over CronTrigger; a System.schedule call (or runbook step)
for each job the sandbox needs.
```

**Detection hint:** `System.abortJob` inside a `SandboxPostCopy` class, or "jobs are copied in a paused/active state".

---

## Anti-Pattern 5: Assuming the Post-Copy Class Runs as an Admin

**What the LLM generates:** A post-copy class that inserts users, edits permission-gated objects, and makes callouts, with no plan for what happens when that user lacks access.

**Why it happens:** Models assume setup code runs with full access.

**Correct pattern:**

```text
runApexClass runs as a special Automated Process user that isn't visible in the org
and doesn't have access to all objects and features. If the script fails, run it after
activation as a user with appropriate permissions. Test with
Test.testSandboxPostCopyScript(script, orgId, sandboxId, sandboxName, true).
```

**Detection hint:** A plan that depends on granting the Automated Process user extra access instead of the documented fallback (re-run after activation as a user with the right permissions), or a post-copy class with no fallback plan.

---

## Anti-Pattern 6: Stating Refresh Intervals as Platform Fact Without a Source

**What the LLM generates:** "Full sandboxes refresh every 29 days" presented as a hard rule inside a plan, with no check.

**Why it happens:** The numbers are widely repeated; the Help article that publishes them is not in the developer guides.

**Correct pattern:**

```text
Plan with the commonly published intervals (Developer / Developer Pro 1 day,
Partial Copy 5 days, Full 29 days), but confirm each sandbox's next available
refresh date in Setup > Sandboxes before committing a release calendar to it.
```

**Detection hint:** A release calendar keyed to refresh intervals with no step that checks the actual next-available date.
