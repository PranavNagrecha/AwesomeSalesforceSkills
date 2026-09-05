# Examples — Flow Action Framework

## Example 1: Wire a bulk-safe Apex action from a record-triggered Flow

**Context:** A record-triggered Flow runs after save on Case. For each Case in the batch, a custom scoring algorithm in Apex must run, but the team wants one invocable call per transaction chunk instead of looping per record.

**Problem:** An early design used **Loop → Apex action** with a single-Id input. In full bulk saves, the Flow approached governor limits and behaved inconsistently compared to sandbox tests with one Case.

**Solution:**

1. Refactor the Apex class to expose `@InvocableMethod` with `List<CaseScoreRequest>` in and `List<CaseScoreResult>` out (see `invocable-methods` for wrapper details).
2. In the Flow, pass `{!$Record}` via a **Get Records** collection or the triggering record collection into the Apex action’s collection input once per path, not inside a loop.
3. Map `CaseScoreResult` output fields back with **Assignment** to related records or staging variables.

**Why it works:** The invocable contract is list-first; Flow’s bulk interview aligns with a single bulk-chunked Apex call, reducing overhead and matching platform expectations.

---

## Example 2: Replace duplicated element blocks with a subflow action

**Context:** Three department-specific onboarding flows each repeated the same ten-step “provision chatter group and log milestone” sequence.

**Problem:** A wording change in one branch was updated in only two of three flows, causing production divergence.

**Solution:**

1. Extract the shared sequence into **Onboarding_Common_Subflow** with defined input variables (user Id, department code) and output variables (success flag, log Id).
2. In each department Flow, replace the block with **Run Subflow**, mapping parent variables into the child inputs and reading outputs for branching.

**Why it works:** Subflows are first-class actions with a stable boundary; updates ship once in the child flow.

---

## Anti-Pattern: Use Apex action for pure field updates

**What practitioners do:** Create an `@InvocableMethod` that only performs `update` on fields available in **Update Records**.

**What goes wrong:** Higher maintenance (tests, deployments), loss of self-documenting Flow, and unnecessary governor use for logic the platform already expresses declaratively.

**Correct approach:** Use **Update Records** or **Assignment** plus **Update Records** unless a genuine gap (validation, unsupported logic, reuse outside Flow) forces Apex.

---

## Example 3: Auditing an org's action inventory before a refactor

**Context:** A team inherited 40 flows and wants to know which action families are actually
in use before consolidating. "Open each one in Flow Builder" is not an answer at that size.

**Problem:** The action *type* is the field that determines limits, packaging obligations,
fault semantics and transaction behaviour — and it is invisible in the canvas, where an
Apex action and an External Service action look alike.

**Solution:** Read it out of the retrieved source. Every action call in a flow is an
`<actionCalls>` element with a required `<actionType>` (`api_meta.txt` L68465-68466), and
every subflow is a `<subflows>` element, so one pass over the directory gives the whole
inventory:

```bash
# every action family in use, with a count, across the retrieved flows
grep -h -o '<actionType>[^<]*</actionType>' force-app/main/default/flows/*.flow-meta.xml \
  | sed 's|</\?actionType>||g' | sort | uniq -c | sort -rn

# which flows call Apex, and which class each one names
grep -l '<actionType>apex</actionType>' force-app/main/default/flows/*.flow-meta.xml \
  | while read -r f; do
      printf '%s\n' "$(basename "$f" .flow-meta.xml)"
      grep -o '<actionName>[^<]*</actionName>' "$f" | sed 's|</\?actionName>|  |g'
    done

# action calls that ship with no fault path at all
for f in force-app/main/default/flows/*.flow-meta.xml; do
  python3 - "$f" <<'PY'
import sys, xml.etree.ElementTree as ET
NS = "{http://soap.sforce.com/2006/04/metadata}"
root = ET.parse(sys.argv[1]).getroot()
for call in root.findall(f"{NS}actionCalls"):
    name = call.findtext(f"{NS}name", "")
    if call.find(f"{NS}faultConnector") is None:
        print(f"{sys.argv[1]}: {name} ({call.findtext(f'{NS}actionType','')}) has no faultConnector")
PY
done
```

Then reconcile the `apex` rows against the org's real catalogue — the describe call answers
as the *calling user*, so run it as a representative end user rather than as an admin:

```bash
curl -s "https://MyDomainName.my.salesforce.com/services/data/v66.0/actions/custom/apex" \
  -H "Authorization: Bearer $SF_TOKEN"
```

**Why it works:** The `actionType` value is the only thing in the file that tells you which
rulebook applies. Once the inventory is grouped by type, the follow-up questions become
mechanical: every `apex` row needs an Apex-class-access grant and a manifest entry; every
`emailAlert` row burns the workflow email allocation and needs its template added by hand
(`api_rest.txt` L13765-13766, L13787-13800); every `externalService` row needs a Named
Credential. The checker in this skill's `scripts/` automates the fault-connector and
class-resolution halves of the same pass.
