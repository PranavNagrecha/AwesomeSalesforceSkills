# Examples — Change Advisory Board Process

## Example 1: Permission Set Deployment Blocked Pending CAB Approval

**Context:** A financial services firm running Salesforce Financial Services Cloud on GovCloud deploys quarterly. Their DevOps team uses Gearset connected to GitHub. A developer submits a PR that modifies the `Wealth_Manager_PS` Permission Set to grant Read/Write on the `Investment_Account__c` object.

**Problem:** Without a CAB gate, the developer merges the PR and the pipeline automatically deploys to production over the weekend. The permission expansion immediately grants 340 Wealth Managers access to investment account records they were not previously authorized to see — a data access incident that triggers a regulatory notification obligation.

**Solution:**

The team implements a PR-based change classification check:

```python
# Excerpt from PR classification check script
HIGH_RISK_METADATA = {
    "permissionsets",
    "profiles",
    "sharingrules",
    "namedcredentials",
    "connectedapps",
}

def classify_pr_diff(changed_paths: list[str]) -> str:
    """Return 'normal' if any high-risk metadata type is present, else 'standard'."""
    for path in changed_paths:
        folder = path.lower().split("/")[0] if "/" in path else ""
        if folder in HIGH_RISK_METADATA:
            return "normal"
    return "standard"
```

The script runs as a GitHub Actions check. When it returns `normal`, the pipeline blocks the deploy and posts a comment requiring a ServiceNow change request number with Approved status before the production deploy step is unlocked. The CAB review takes 48 hours and includes the Security team. The permission change is approved with an explicit data-access justification and a post-deployment access audit.

**Why it works:** Classification happens at the PR, not at deployment time. The enforcement is automated and cannot be bypassed without a documented approval. The audit trail lives in both GitHub and ServiceNow.

---

## Example 2: Emergency Flow Deployment via ECAB

**Context:** A retail company's Order Management org has a Flow that calculates shipping fees. On a Friday afternoon, a production incident is reported: the Flow is double-charging shipping on all orders due to a looping trigger. Orders are accumulating incorrect charges at a rate of several hundred per hour.

**Problem:** The normal CAB process requires a 48-hour advance change request, a scheduled Tuesday CAB meeting, and two business-owner approvals. Following the standard process would allow thousands more orders to be incorrectly charged before the fix is approved.

**Solution:**

The team invokes the Emergency CAB (ECAB) process:

1. The Salesforce Admin opens an Emergency change request in ServiceNow, marking it P1-Emergency with a clear incident description and linking the production incident ticket.
2. The ECAB quorum (Release Manager + Head of IT + on-call Salesforce Architect) is convened via Slack with a 30-minute window to review the fix.
3. The fix is a single-version Flow rollback (reverting to the last known-good Flow version), described in the change ticket with the rollback steps and the post-deployment verification plan (confirm zero duplicate shipping fee records in the next 15 minutes).
4. Two of the three ECAB members approve the ticket; the ITSM API updates the change request status to Emergency-Approved.
5. The pipeline detects the Emergency-Approved status and allows the production deploy. The Flow rollback deploys in under 5 minutes.
6. A post-implementation review is automatically scheduled for the following Wednesday.

```
# ECAB approval gate check (pipeline pseudocode)
CHANGE_REQUEST_NUMBER = $CR_NUMBER  # injected from pipeline environment
STATUS=$(curl -s "$ITSM_API/change/$CHANGE_REQUEST_NUMBER/status")

if [[ "$STATUS" == "Approved" || "$STATUS" == "Emergency-Approved" ]]; then
  echo "CAB gate passed. Proceeding with deployment."
else
  echo "ERROR: Change request $CHANGE_REQUEST_NUMBER is not in Approved state (current: $STATUS)"
  exit 1
fi
```

**Why it works:** The ECAB provides a fast but documented path. The pipeline still requires a machine-readable approval status — there is no manual override without evidence in the ITSM system. The post-review requirement ensures the root cause is addressed.

---

## Example 3: Seasonal Release Freeze Coordination

**Context:** A healthcare technology company plans to deploy a new integration (Named Credential + Remote Site Setting + three Apex classes) during the second week of February. Their Salesforce org is on NA production, which is scheduled for the Spring '25 upgrade on February 15 (Wave 1).

**Problem:** The team's sandbox is already on the Spring '25 preview. The planned deployment has been tested and passes in sandbox. However, if deployed to production on February 12, the production org is still on Winter '25. The Named Credential authentication behavior changed between Winter '25 and Spring '25. The deployment may succeed but behave differently than tested until production upgrades on February 15.

**Solution:**

The CAB change calendar maintains a rolling lookup of Salesforce upgrade windows. When the change ticket is submitted:

1. The ITSM form automatically flags: "Planned deployment date (Feb 12) is within 7 days of a production upgrade wave (Feb 15). Elevated platform drift risk."
2. The CAB meeting review notes this flag. Two options are evaluated:
   - Move the deployment to February 17 (post-upgrade) — recommended.
   - Proceed on February 12 with explicit CAB sign-off acknowledging the drift risk and a rollback plan if behavior differs post-upgrade.
3. The team elects to reschedule to February 17. The change ticket is updated with the new deployment date and marked pending re-approval.

**Why it works:** The seasonal release risk is codified in the process, not left to practitioner awareness. The CAB calendar integration surfaces the risk automatically and creates a documented decision point.

---

## Anti-Pattern: Using Salesforce Approval Processes as the CAB Gate

**What practitioners do:** Configure a custom Salesforce object (e.g., `Deployment_Request__c`) with a Salesforce Approval Process requiring manager sign-off, then mark the object as Approved before proceeding with deployments.

**What goes wrong:** The deployment pipeline has no knowledge of the Salesforce Approval Process. A developer can open the Salesforce CLI and run `sf project deploy start --target-org production` at any time regardless of whether the custom object record is Approved. The "CAB gate" exists only on paper — it enforces nothing in the actual deployment execution path. Additionally, if the Salesforce org is down or degraded, the approval mechanism itself is unavailable.

**Correct approach:** CAB enforcement must live in the deployment toolchain. The pipeline (GitHub Actions, Copado, Gearset) checks the ITSM tool's API for change request status before allowing the production deploy step. Salesforce-native objects cannot enforce this gate because they live inside the system being deployed to, not outside it.
