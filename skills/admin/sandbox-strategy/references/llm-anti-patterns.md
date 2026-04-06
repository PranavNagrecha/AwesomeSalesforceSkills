# LLM Anti-Patterns — Sandbox Strategy

Common mistakes AI coding assistants make when generating or advising on Salesforce sandbox strategy and environment planning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Full sandboxes for development work

**What the LLM generates:** "Create a Full sandbox for each developer so they have production data to work with."

**Why it happens:** LLMs default to the most capable sandbox type. Full sandboxes are expensive (limited quantity per org), copy all production data (including potentially sensitive PII), and have long refresh intervals (29 days minimum). Developer work should use Developer or Developer Pro sandboxes, which are faster to create and refresh.

**Correct pattern:**

```
Sandbox type selection by purpose:
| Purpose          | Sandbox Type    | Data     | Refresh Interval | Quantity |
|------------------|-----------------|----------|------------------|----------|
| Developer coding | Developer       | No data  | 1 day            | Many     |
| Config + testing | Developer Pro   | No data  | 1 day            | Moderate |
| Integration test | Partial Copy    | Subset   | 5 days           | Few      |
| UAT / Staging    | Full            | Full copy| 29 days          | 1-2      |
| Performance test | Full            | Full copy| 29 days          | 1        |

Rules:
- Developers get Developer sandboxes (no production data needed).
- Use Partial Copy for integration testing with a data subset.
- Reserve Full sandboxes for UAT and performance testing only.
```

**Detection hint:** If the output recommends Full sandboxes for development, the sandbox type is too expensive and risky for the purpose. Search for `Full sandbox` combined with `development` or `developer`.

---

## Anti-Pattern 2: Ignoring data masking requirements for sandboxes with production data

**What the LLM generates:** "Refresh the Full sandbox from production. The team can start testing with real data."

**Why it happens:** LLMs skip data sensitivity analysis. Full and Partial Copy sandboxes copy production data, which may include PII (names, emails, phone numbers, SSNs), financial data, or health data. Without data masking, non-production environments contain sensitive data accessible to developers and testers who may not be authorized to view it.

**Correct pattern:**

```
Data masking for sandbox environments:
1. Identify sensitive fields: PII, financial, health data.
2. Configure Sandbox Data Mask (Salesforce feature):
   - Setup → Sandboxes → Data Mask.
   - Apply masking rules per field:
     - Email → random@example.com
     - Phone → 555-XXX-XXXX
     - Name → randomized
     - SSN → fully masked
3. Apply masking as a post-refresh step (or use a third-party tool
   like OwnBackup, Prodly, or custom Apex batch).
4. For Partial Copy sandboxes: define the sandbox template to
   exclude objects containing the most sensitive data.
5. Document the masking policy and verify after every refresh.
```

**Detection hint:** If the output refreshes a sandbox with production data without mentioning data masking, sensitive data is exposed. Search for `mask`, `PII`, `sensitive data`, or `Data Mask` in the refresh instructions.

---

## Anti-Pattern 3: Not planning post-refresh steps

**What the LLM generates:** "Refresh the sandbox. It is ready to use."

**Why it happens:** LLMs treat sandbox refresh as a self-contained operation. After a refresh, the sandbox requires post-refresh configuration: updating integration endpoints (sandbox URLs, not production), re-enabling email deliverability (sandboxes default to "System Only"), verifying user accounts, and re-setting custom settings that may be environment-specific.

**Correct pattern:**

```
Post-refresh checklist:
1. Email deliverability: set to "All Email" if testing emails,
   or keep "System Only" to prevent sending to real customers.
   Setup → Email → Deliverability.
2. Integration endpoints: update Named Credentials, Remote Site Settings,
   and Custom Metadata to point to sandbox/staging endpoints.
3. Scheduled jobs: review and reschedule or disable scheduled Flows
   and Apex batch jobs that should not run in sandbox.
4. Users: sandbox users have modified usernames (appended with .sandboxname).
   Verify key test users can log in.
5. Data Mask: run masking if not automated during refresh.
6. Connected Apps: update callback URLs for sandbox My Domain.
7. Custom Settings: update environment-specific values.
```

**Detection hint:** If the output says the sandbox is "ready to use" after refresh without a post-refresh checklist, critical configuration is being skipped. Search for `post-refresh`, `email deliverability`, or `integration endpoints` after the refresh step.

---

## Anti-Pattern 4: Using one sandbox for all purposes

**What the LLM generates:** "Use the Full sandbox for development, integration testing, and UAT."

**Why it happens:** LLMs consolidate environments to keep the architecture simple. Sharing a single sandbox for development, testing, and UAT causes conflicts: developers overwrite QA configurations, UAT data is polluted by incomplete development work, and a refresh for one purpose disrupts another. Each purpose needs its own sandbox.

**Correct pattern:**

```
Sandbox per purpose:
| Purpose        | Sandbox       | Who Uses It           | Refresh Cadence   |
|----------------|---------------|-----------------------|-------------------|
| Dev (per dev)  | Developer     | Individual developer  | Weekly or as needed|
| Integration    | Dev Pro/Partial| Integration team     | Per sprint        |
| QA / Testing   | Partial Copy  | QA team              | Per sprint        |
| UAT / Staging  | Full          | Business stakeholders | Per release        |
| Training       | Developer Pro | Training team         | Per training cycle |

Key principles:
- Never mix development and UAT in the same sandbox.
- Refresh cadence matches the team's workflow.
- Lower environments (Dev) refresh more often than higher (UAT).
```

**Detection hint:** If the output uses one sandbox for multiple purposes (development + UAT, or development + integration), the environment strategy is under-resourced. Check if multiple activities share the same sandbox.

---

## Anti-Pattern 5: Recommending sandbox refresh without checking for in-flight work

**What the LLM generates:** "Refresh the sandbox now to get the latest production metadata."

**Why it happens:** LLMs trigger refreshes without checking for work in progress. A sandbox refresh DESTROYS all current content -- metadata changes, data, configurations -- and replaces it with a copy of production. Any un-deployed work in the sandbox is permanently lost.

**Correct pattern:**

```
Pre-refresh checklist:
1. Confirm NO in-flight work exists in the sandbox:
   - All deployable changes have been committed to source control
     or deployed to the next environment.
   - All test data that needs to be preserved has been exported.
2. Notify all sandbox users of the refresh schedule.
3. Check the sandbox's last refresh date:
   - Developer: can refresh every 1 day.
   - Developer Pro: can refresh every 1 day.
   - Partial Copy: can refresh every 5 days.
   - Full: can refresh every 29 days.
4. Schedule the refresh during off-hours to minimize disruption.
5. Document what was in the sandbox at the time of refresh
   (for audit purposes if needed).
```

**Detection hint:** If the output refreshes a sandbox without checking for in-flight work or notifying users, un-deployed changes may be lost. Search for `in-flight`, `notify`, or `pre-refresh` before the refresh step.
