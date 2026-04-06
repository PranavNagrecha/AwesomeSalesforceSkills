# LLM Anti-Patterns — Sandbox Data Isolation Gotchas

Common mistakes AI coding assistants make when generating or advising on sandbox data isolation in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming All Email Addresses Are Changed to `.invalid` on Sandbox Refresh

**What the LLM generates:** "When you refresh a sandbox, Salesforce automatically changes all email addresses to `.invalid` so no real emails are sent to customers."

**Why it happens:** Salesforce documentation does describe the `.invalid` email suffix behavior. LLMs generalize from the User object behavior to all objects, missing the key caveat that only the User object's Email field is obfuscated. Training data often contains simplified summaries of this behavior without the object-specific scoping.

**Correct pattern:**

```
Only User object Email fields are changed to .invalid during sandbox refresh.
Contact, Lead, Person Account, and all other objects' email fields are NOT modified.
You must explicitly scrub those fields in a SandboxPostCopy Queueable or manual data script.

Audit query: SELECT COUNT() FROM Contact WHERE Email != null AND Email NOT LIKE '%.invalid'
```

**Detection hint:** Look for the phrase "all email addresses" combined with "`.invalid`" in any sandbox refresh guidance. If the claim is not scoped to the User object specifically, it is incorrect.

---

## Anti-Pattern 2: Assuming SandboxPostCopy Runs With Full Admin Permissions

**What the LLM generates:** Code that performs DML on custom objects, calls `System.abortJob()`, or inserts records without any note about user permissions — implying the code will work as-is.

**Why it happens:** LLMs generating Apex code default to assuming system-level or admin-level execution context. The SandboxPostCopy constraint (Automated Process user, minimal permissions) is a niche platform behavior not prominent in general Apex training data.

**Correct pattern:**

```apex
// The SandboxPostCopy runApexClass method runs as the Automated Process user.
// This user does NOT have access to custom objects by default.
// Before the refresh:
//   1. Create a Permission Set with the required object and field permissions.
//   2. Assign that Permission Set to the Automated Process user in production.
// In the class, wrap DML operations in try/catch to handle permission failures gracefully:
try {
    My_Custom_Object__c rec = new My_Custom_Object__c(Field__c = 'value');
    insert rec;
} catch (System.NoAccessException e) {
    System.debug(LoggingLevel.ERROR, 'Permission missing for My_Custom_Object__c: ' + e.getMessage());
}
```

**Detection hint:** Any SandboxPostCopy code that touches custom objects or calls `System.abortJob()` without mentioning the Automated Process user permission requirement is likely incomplete.

---

## Anti-Pattern 3: Recommending Named Credential Secret Rotation Via Apex

**What the LLM generates:** "In your SandboxPostCopy class, update the Named Credential to point at the sandbox endpoint and re-enter the credentials programmatically."

**Why it happens:** LLMs may conflate Named Credential URL updates (partially possible via Metadata API in some contexts) with setting Named Credential secrets (passwords, OAuth tokens). Named Credential secrets have never been settable via Apex, and programmatic URL updates have limitations depending on the auth protocol. The LLM pattern-matches on "update configuration in SandboxPostCopy" and over-applies it.

**Correct pattern:**

```
Named Credential secrets (passwords, OAuth tokens) cannot be set via Apex or Metadata API.
They must be re-entered manually in Setup > Named Credentials after each sandbox refresh.

What CAN be done programmatically:
- Update Custom Settings or Custom Metadata records that store non-secret endpoint URLs.
- Update Custom Labels that contain endpoint hostnames (via Metadata API in a deployment, not Apex at runtime).

The post-refresh runbook must include a manual step:
"Update Named Credential [name] endpoint URL to [sandbox URL] and re-enter the API key/OAuth credentials."
```

**Detection hint:** Any suggestion to "set" or "update" Named Credential secrets or OAuth tokens from Apex or SandboxPostCopy is incorrect. Flag it.

---

## Anti-Pattern 4: Treating `System Email Only` as a Complete Isolation Guarantee

**What the LLM generates:** "Set sandbox email deliverability to 'System Email Only' and you won't have any risk of sending emails to real customers."

**Why it happens:** The Salesforce deliverability documentation describes `System Email Only` as suppressing workflow email alerts and Apex emails, which LLMs interpret as a complete solution. The interaction between deliverability settings and Contact/Lead email address content is a separate concern that the LLM does not connect.

**Correct pattern:**

```
System Email Only suppresses:
- Workflow rule email alerts
- Apex Messaging.sendEmail() calls
- Process Builder and Flow email actions

System Email Only does NOT prevent:
- System-generated emails that include data from Contact/Lead fields
  (e.g., a case notification that includes the case contact's email in the body)
- Callout-based integrations that send email via external systems using
  Contact/Lead email addresses retrieved by Apex

Defense in depth requires BOTH:
1. Set deliverability to System Email Only (or No Access)
2. Scrub Contact and Lead email fields to append .invalid

Neither control alone is sufficient for orgs with complex automation.
```

**Detection hint:** If advice says "just set deliverability to System Email Only" without also recommending Contact/Lead email scrubbing, the guidance is incomplete for Full or Partial Copy sandboxes.

---

## Anti-Pattern 5: Suggesting `System.schedule()` to Re-Register Jobs in SandboxPostCopy Without Isolating Them First

**What the LLM generates:** "In SandboxPostCopy, abort production jobs and then re-register the safe ones with System.schedule() pointing at sandbox endpoints."

**Why it happens:** The pattern of "clean up and re-register" is a reasonable general pattern. LLMs apply it to sandbox jobs without recognizing that re-scheduling jobs in SandboxPostCopy creates a new risk: the re-registered jobs run as the Automated Process user context, may have incorrect endpoint references, and may fire sooner than intended if the schedule is miscalculated.

**Correct pattern:**

```apex
// In SandboxPostCopy: ONLY abort. Do NOT re-register.
// Re-registering in SandboxPostCopy introduces risks:
// - The Automated Process user may not have permission to schedule jobs
// - The sandbox may not have the correct integration config yet when the class runs
// - Jobs re-registered immediately may fire before manual isolation steps complete

// ABORT all jobs in SandboxPostCopy:
for (CronTrigger ct : [SELECT Id FROM CronTrigger WHERE State IN ('WAITING','ACQUIRED','EXECUTING')]) {
    System.abortJob(ct.Id);
}

// Re-register safe sandbox jobs MANUALLY after the post-refresh runbook is complete
// and all integration endpoints have been verified.
```

**Detection hint:** Any SandboxPostCopy code that calls `System.schedule()` to re-register jobs should be flagged for review. Aborting is always safe; re-registering requires the full isolation runbook to be complete first.

---

## Anti-Pattern 6: Recommending Sandbox Isolation Only for Full Sandboxes

**What the LLM generates:** "These isolation concerns only apply to Full sandboxes since those are the only ones with real production data."

**Why it happens:** LLMs anchor on "Full sandbox = production data copy" and conclude that other sandbox types are safe. In reality, Partial Copy sandboxes also copy production records (including Contact/Lead emails), and all sandbox types carry the scheduled job and Named Credential risks.

**Correct pattern:**

```
Sandbox type → Isolation requirements:

Developer / Developer Pro:
- Email deliverability: verify (default is System Email Only but can drift)
- Contact/Lead emails: not applicable (no data copied)
- Scheduled jobs: not copied
- Named Credentials: copied (URL unchanged, secrets blanked)
  → Verify Named Credential URLs before integration testing

Partial Copy:
- All isolation controls apply
- Contact/Lead emails ARE present (depending on template and parent record pull-in)
- Scheduled jobs ARE copied
- Named Credentials ARE copied

Full:
- All isolation controls apply, at full production data volume
```

**Detection hint:** Any advice that scopes isolation steps to "Full sandboxes only" is incorrect. Partial Copy sandboxes require the same isolation discipline.
