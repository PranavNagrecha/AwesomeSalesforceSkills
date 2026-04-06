# LLM Anti-Patterns — Email-to-Case Configuration

Common mistakes AI coding assistants make when generating or advising on Email-to-Case configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Standard Email-to-Case as the Default

**What the LLM generates:** Instructions that default to Standard Email-to-Case, including steps to download and configure the Java agent, as if On-Demand does not exist or is not the recommended approach.

**Why it happens:** Older Salesforce documentation and training materials covered Standard Email-to-Case before On-Demand existed. LLMs trained on legacy content surface Standard as the primary configuration path. The existence of On-Demand as the preferred no-agent alternative is underrepresented in older training data.

**Correct pattern:**

```
Default recommendation: On-Demand Email-to-Case.
Rationale: no local agent required, no API call consumption, Salesforce-hosted.
Use Standard only when: data residency or firewall policy explicitly prohibits
email content routing through Salesforce infrastructure.
```

**Detection hint:** Any response that leads with "download the Email-to-Case agent" without first asking about infrastructure requirements or recommending On-Demand as the default.

---

## Anti-Pattern 2: Stating That On-Demand and Standard Have Identical Attachment Limits

**What the LLM generates:** A statement that both modes support the same attachment limits: total email size of 25 MB, without mentioning the On-Demand per-attachment cap.

**Why it happens:** The 25 MB total limit applies to both modes and is the most commonly cited number. The 10 MB per-attachment cap is specific to On-Demand and is documented in the limits article, not in the main setup article. LLMs conflate the two and omit the per-attachment cap.

**Correct pattern:**

```
Both modes: maximum total email size 25 MB.
On-Demand only: maximum individual attachment size 10 MB.
Standard: no per-attachment cap (total 25 MB still applies).
Orgs migrating from Standard to On-Demand must communicate the
10 MB per-attachment limit to customers and support teams.
```

**Detection hint:** Any response describing attachment limits that mentions only the 25 MB limit without differentiating On-Demand's 10 MB per-attachment cap.

---

## Anti-Pattern 3: Describing Email Threading as Automatic Without Caveats

**What the LLM generates:** A confident statement that Email-to-Case automatically threads customer replies into the original case, presented as a guaranteed behavior with no conditions.

**Why it happens:** Threading is described as a feature in the Salesforce documentation without the prominent caveat that it depends on the Lightning thread token surviving the round-trip through the customer's mail client and any corporate email gateway. LLMs summarize the feature description without the failure conditions.

**Correct pattern:**

```
Threading works when: the Lightning thread token in the email body (ref:...:ref)
or subject line survives the full round-trip.
Threading fails when:
- Mail server or security gateway strips the token
- Customer's mail client strips quoted content AND modifies the subject
- Routing address is misconfigured
Required: end-to-end threading test through the production mail gateway
before go-live, not just in sandbox.
```

**Detection hint:** Any response describing threading that does not mention the token, mail gateway risk, or the requirement for end-to-end testing. Flag: "automatically threads" without qualification.

---

## Anti-Pattern 4: Omitting the Auto-Response and Assignment Rule Dependency

**What the LLM generates:** Configuration instructions for an auto-response rule that do not mention the requirement for an active, matching case assignment rule, or troubleshooting advice for "auto-response not sending" that does not check the assignment rule first.

**Why it happens:** Auto-response rules appear as a standalone configuration in Setup. The dependency on assignment rule execution is a platform behavior documented in the auto-response rules help article but not surfaced in the Email-to-Case setup flow. LLMs treat them as independent features.

**Correct pattern:**

```
Auto-response rule fires ONLY when the active case assignment rule fires.
Before configuring or troubleshooting auto-response:
1. Confirm an active case assignment rule exists.
2. Confirm it has a rule entry that will match cases created by Email-to-Case.
3. Confirm the rule is active (not draft).
If no assignment rule is active or matching, auto-response will not fire
regardless of auto-response rule configuration.
```

**Detection hint:** Auto-response configuration instructions that do not mention assignment rules, or troubleshooting responses that suggest re-saving or reactivating the auto-response rule without first verifying the assignment rule.

---

## Anti-Pattern 5: Not Warning About Auto-Response Email Loops

**What the LLM generates:** Auto-response rule configuration instructions that set the "From" address to the same email address as the Email-to-Case routing address, or that do not warn about the loop risk.

**Why it happens:** LLMs completing a "configure auto-response for Email-to-Case" task focus on making the auto-response send and do not model the round-trip: auto-response → customer inbox → customer reply → routing address → new case → auto-response. The loop risk requires thinking about the mail flow end-to-end, which LLMs commonly skip.

**Correct pattern:**

```
Auto-response rule "From" address must NOT be the same as or forward to
any Email-to-Case routing address.
Recommended: use a dedicated no-reply address (e.g., no-reply@company.com)
that does not forward back to Salesforce.
Test: send one inbound email, monitor Case count for 5 minutes to confirm
no unbounded case creation.
```

**Detection hint:** Auto-response configuration that sets the From address to the support email address without checking whether that address is a routing address. Flag: auto-response From = routing address email value.

---

## Anti-Pattern 6: Skipping Routing Address Verification in Setup Instructions

**What the LLM generates:** Email-to-Case setup instructions that configure the routing address and mail server forwarding rule but omit the "Send Verification Email" step, or present verification as optional.

**Why it happens:** The verification step is a UI action in the routing address record and is easy to overlook in procedural instructions. LLMs generating setup steps from documentation summaries commonly skip it because it is presented as a post-save action rather than part of the main configuration form.

**Correct pattern:**

```
After saving the routing address:
1. Click "Send Verification Email" on the routing address record.
2. Confirm the forwarding rule is active (the verification email routes
   to the Salesforce-generated address).
3. Open the verification email and click the verify link.
4. Confirm the routing address status shows "Verified."
Salesforce will NOT process inbound email for an unverified routing address.
```

**Detection hint:** Email-to-Case setup instructions that end with "Save the routing address and configure your mail server" without including verification. Any instructions that call verification "optional."
