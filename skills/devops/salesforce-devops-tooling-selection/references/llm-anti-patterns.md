# LLM Anti-Patterns — Salesforce DevOps Tooling Selection

Common mistakes AI coding assistants make when generating or advising on Salesforce DevOps tooling selection. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Single Tool Without Asking About Constraints

**What the LLM generates:** "Use Gearset — it's the best Salesforce DevOps tool" or "I recommend Copado for your Salesforce CI/CD needs" without first gathering information about team composition, compliance requirements, budget, or hosting preferences.

**Why it happens:** LLMs default to the tool most frequently praised in training data (often Gearset due to content marketing volume) without recognizing that tooling selection is constraint-driven, not feature-driven.

**Correct pattern:**

```text
Before recommending a tool, I need to understand:
1. What is your team's admin-to-developer ratio and Git experience level?
2. Do you have compliance requirements (SOC 2, FedRAMP, HIPAA, data residency)?
3. What is your budget range per user or per org?
4. Which Git provider do you use (GitHub, GitLab, Bitbucket, Azure DevOps)?
5. How many production orgs and environments do you manage?
```

**Detection hint:** Look for a tool name appearing in the first paragraph of the response without preceding questions about constraints.

---

## Anti-Pattern 2: Treating DevOps Center as Feature-Complete

**What the LLM generates:** "Salesforce DevOps Center is a free, full-featured CI/CD platform that can replace commercial tools like Copado or Gearset" or listing DevOps Center as having capabilities like automated rollback, data deployment, or static code analysis.

**Why it happens:** LLMs conflate Salesforce marketing language ("DevOps Center brings DevOps to Salesforce") with actual feature parity. Training data includes aspirational product announcements alongside current documentation.

**Correct pattern:**

```text
DevOps Center is a free, native feature that provides basic source-tracking
and deployment capabilities through a GitHub integration. It does NOT include:
- Automated rollback
- Data deployment
- Static code analysis
- Support for Git providers other than GitHub
- Advanced conflict resolution
- Pipeline orchestration across multiple orgs

It is appropriate for small teams with simple deployment needs or as a
stepping stone toward more capable tooling.
```

**Detection hint:** Check for claims that DevOps Center supports rollback, data deployment, GitLab/Bitbucket, or multi-org pipeline orchestration.

---

## Anti-Pattern 3: Ignoring the Hosting Model's Compliance Implications

**What the LLM generates:** A comparison matrix that evaluates tools on features, pricing, and ease of use but omits the hosting model (SaaS vs. native) or fails to connect hosting model to compliance and data residency requirements.

**Why it happens:** LLMs treat tooling comparisons as feature checklists rather than constraint-elimination problems. Hosting model is a binary elimination criterion for regulated industries, but LLMs rank it as one factor among many.

**Correct pattern:**

```text
Step 1: Determine compliance constraints
  - FedRAMP, SOC 2, HIPAA, data residency mandates?

Step 2: Eliminate tools whose hosting model violates constraints
  - SaaS tools (Gearset, AutoRABIT, Blue Canvas) route metadata through
    external infrastructure → disqualified if data residency is required
  - Native tools (Copado, Flosum, DevOps Center) keep metadata inside
    the Salesforce trust boundary

Step 3: Only THEN compare features among remaining candidates
```

**Detection hint:** Look for comparison tables that lack a "Hosting Model" or "Data Residency" column, or that list SaaS and native tools side-by-side for a regulated customer without flagging the distinction.

---

## Anti-Pattern 4: Fabricating Pricing Details

**What the LLM generates:** Specific dollar amounts for tool pricing (e.g., "Gearset costs $75/user/month" or "Copado Enterprise is $3,500/month") that may be outdated, incorrect, or based on training data from a different pricing era.

**Why it happens:** LLMs memorize pricing from blog posts, comparison articles, and vendor pages in training data. Salesforce ecosystem tool pricing changes frequently and varies by contract terms, volume, and negotiation.

**Correct pattern:**

```text
Pricing varies by vendor, contract terms, and volume. General guidance:
- DevOps Center: free (included with Salesforce platform)
- SaaS tools (Gearset, AutoRABIT, Blue Canvas): typically per-user/month
- Native managed packages (Copado, Flosum): typically per-org/month

Contact vendors directly for current pricing. Request quotes at your
current AND projected team size to understand scaling costs.
```

**Detection hint:** Look for specific dollar amounts associated with tool names. Any precise pricing figure should be flagged as potentially outdated.

---

## Anti-Pattern 5: Conflating Salesforce CLI with a DevOps Tool

**What the LLM generates:** "You can use Salesforce CLI as your DevOps tool" — presenting the CLI as a complete alternative to platforms like Gearset or Copado, without acknowledging that the CLI is a deployment engine, not a DevOps platform.

**Why it happens:** LLMs see extensive Salesforce CLI documentation in training data and equate deployment capability with DevOps capability. The CLI handles deploy/retrieve operations but does not provide comparison UIs, conflict resolution, approval workflows, audit trails, or pipeline orchestration.

**Correct pattern:**

```text
Salesforce CLI (sf/sfdx) is the foundational deployment engine that all
DevOps tools ultimately wrap. It handles:
- Source deploy and retrieve
- Scratch org creation and management
- Metadata format conversion

It does NOT provide:
- Visual metadata comparison
- Conflict detection and resolution UI
- Approval gates and governance workflows
- Deployment audit trails
- Automated rollback
- Data deployment

Teams can build CI/CD pipelines around the CLI using GitHub Actions,
GitLab CI, or similar platforms, but this requires significant custom
scripting for comparison, conflict handling, and rollback — which is
exactly what commercial DevOps tools provide out of the box.
```

**Detection hint:** Look for recommendations that list "Salesforce CLI" as a peer option to Gearset/Copado/etc. without qualifying that it is a component, not a platform.

---

## Anti-Pattern 6: Recommending Tool Migration Without Assessing Switching Cost

**What the LLM generates:** "You should switch from Copado to Gearset for better usability" without acknowledging the migration effort, retraining cost, pipeline reconfiguration, and organizational change management required.

**Why it happens:** LLMs optimize for the "best" tool in isolation without modeling the cost of transitioning from an existing tool. Switching DevOps platforms is a 3-6 month organizational effort, not a configuration change.

**Correct pattern:**

```text
Before recommending a tool switch, assess:
1. How many pipelines and environments are configured in the current tool?
2. How many team members are trained on the current tool?
3. What custom integrations (webhooks, scripts, approval flows) exist?
4. What is the contractual lock-in period with the current vendor?
5. What is the estimated retraining and reconfiguration effort?

If the switching cost exceeds 6 months of productivity gain from the new
tool, the recommendation should be to optimize the current tool rather
than migrate.
```

**Detection hint:** Look for "switch to" or "migrate to" recommendations that do not include a switching-cost assessment or migration timeline.
