# LLM Anti-Patterns — Transaction Security Policies

Common mistakes AI coding assistants make when generating or advising on Salesforce Transaction Security Policies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating a Policy and Expecting Enforcement in Monitor Mode

**What the LLM generates:** "Create the policy with the Block action to prevent logins from outside the US" but leaves the policy in Monitor mode or does not mention the Active/Monitor distinction.

**Why it happens:** LLMs generate the creation steps without emphasizing the mode switch. Monitor mode is the default for new policies, and training data does not consistently highlight this.

**Correct pattern:**

```
Every new Transaction Security Policy starts in Monitor mode by default.
Monitor mode logs every match but takes ZERO enforcement action — no blocks,
no MFA challenges, no notifications sent.

Workflow:
1. Create the policy in Monitor mode.
2. Review the policy match log for 1-2 weeks to confirm the condition logic
   fires on expected events and does not produce false positives.
3. Only then switch to Active to enable enforcement.

If the policy is not triggering, check the Active/Monitor flag FIRST.
```

**Detection hint:** If the advice creates a policy without explicitly mentioning the Monitor-to-Active switch, enforcement will not occur.

---

## Anti-Pattern 2: Using Full Country Names Instead of ISO Codes

**What the LLM generates:** A condition filter like `Country Equals 'United States'` on a LoginEvent policy.

**Why it happens:** LLMs generate human-readable country names. The LoginEvent `Country` field stores ISO 3166-1 alpha-2 two-letter codes, not full names.

**Correct pattern:**

```
The Country field on LoginEvent uses ISO 3166-1 alpha-2 codes:
  US (not "United States")
  GB (not "United Kingdom")
  DE (not "Germany")

A condition filtering on "United States" will NEVER match — it evaluates
silently with zero results, making the policy appear broken when it is actually
a value format error.
```

**Detection hint:** If the policy condition uses a full country name rather than a two-letter ISO code, it will silently fail to match any events.

---

## Anti-Pattern 3: Targeting an Unsupported Event Type

**What the LLM generates:** "Create a Transaction Security Policy on MobileEmailEvent to block mobile email exports."

**Why it happens:** LLMs see event type names in documentation and assume all Real-Time Event Monitoring event types support policy enforcement.

**Correct pattern:**

```
Not all RTEM event types support Transaction Security Policies. Unsupported
event types include:
- MobileEmailEvent
- MobileScreenshotEvent
- IdentityVerificationEvent
- IdentityProviderEvent
- MobileEnforcedPolicyEvent

A policy created on an unsupported event type will NEVER fire — there is no
error or warning in the UI. Always verify "Can Be Used in a Transaction Security
Policy?" in the Salesforce Object Reference before designing the policy.
```

**Detection hint:** If the advice creates a policy on any of the unsupported event types listed above, the policy will silently produce no enforcement.

---

## Anti-Pattern 4: Omitting the Execution User Configuration

**What the LLM generates:** Policy creation steps that do not mention setting an execution user.

**Why it happens:** LLMs focus on the condition logic and enforcement action. The execution user is a metadata field that is easy to overlook but critical for policy evaluation.

**Correct pattern:**

```
Every Transaction Security Policy requires an execution user — an active
Salesforce user whose permissions define the security context for policy
evaluation. A policy without an execution user will not evaluate at all.

For legacy Apex-based policies, the execution user must have the "Author Apex"
permission. For Enhanced Condition Builder policies, the execution user must
simply be an active user. If the execution user is deactivated, the entire
policy stops evaluating without any system alert.
```

**Detection hint:** If the advice does not mention setting an execution user or does not warn about deactivation consequences, a critical configuration step is missing.

---

## Anti-Pattern 5: Assuming Policy Evaluation Is Synchronous and Instant

**What the LLM generates:** "The Block action prevents the operation immediately at the database level."

**Why it happens:** LLMs describe enforcement in absolute terms. Transaction Security Policy evaluation is asynchronous with a slight delay between the triggering action and the enforcement response.

**Correct pattern:**

```
Transaction Security Policy evaluation is asynchronous. There is a brief delay
between the user action and the enforcement response. Block actions will
interrupt the user's request, but the block fires after the platform's async
evaluation completes — it is not instantaneous at the database transaction level.

Do not design policies expecting sub-millisecond enforcement. For extremely
time-sensitive controls (like real-time API rate limiting), Transaction Security
Policies may introduce noticeable latency.
```

**Detection hint:** If the advice claims instant or synchronous enforcement, the async nature of policy evaluation is being understated.

---

## Anti-Pattern 6: Not Auditing Notification Recipients for Deactivated Users

**What the LLM generates:** "Set the notification recipient to the security admin" without mentioning the need for ongoing recipient maintenance.

**Why it happens:** LLMs generate one-time configuration steps. The silent failure mode for deactivated recipients is a platform-specific gotcha.

**Correct pattern:**

```
If a user set as a notification recipient is later deactivated, the notification
silently stops sending. No error is thrown and no fallback recipient is used.

After creating a policy with Notification actions:
- Document the notification recipients.
- Include recipient validation in your user offboarding checklist.
- Periodically audit all Transaction Security Policies for inactive recipients
  to avoid creating invisible alert gaps.
```

**Detection hint:** If the advice sets notification recipients without mentioning the silent-failure-on-deactivation risk, alert gaps will form when users leave the org.
