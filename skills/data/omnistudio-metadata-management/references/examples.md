# Examples — OmniStudio Metadata Management

## Example 1: Impact Analysis Before Deleting a Shared DataRaptor

**Context:** A team is refactoring their data access layer and wants to delete a DataRaptor named `GetContactAddressDetails` that they believe is unused. The Tooling API MetadataComponentDependency query returns zero results, so they assume it is safe to delete.

**Problem:** The Tooling API query returns no dependency edges for OmniStudio cross-component references because those references are stored in embedded JSON inside each component's body — not as explicit Tooling API edges. Three FlexCards and one OmniScript in fact call this DataRaptor. Deleting it would cause silent runtime failures in all four calling components.

**Solution:**

Retrieve all OmniStudio metadata and parse the JSON bodies to build the real dependency graph:

```bash
# Step 1: Retrieve all OmniStudio metadata types
sf project retrieve start \
  --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig \
  --target-org myorg \
  --output-dir ./retrieved

# Step 2: Inspect the retrieved metadata structure
ls ./retrieved/force-app/main/default/omniUiCards/
ls ./retrieved/force-app/main/default/omniProcesses/
```

```python
# Step 3: Parse JSON bodies to extract DataRaptor references
import base64, json, xml.etree.ElementTree as ET
from pathlib import Path

TARGET = "GetContactAddressDetails"
callers = []

for xml_file in Path("./retrieved").rglob("*.xml"):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # OmniStudio metadata wraps JSON in <content> element
    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
    content_el = root.find(".//content") or root.find(".//sf:content", ns)
    if content_el is None or not content_el.text:
        continue
    try:
        body = json.loads(base64.b64decode(content_el.text).decode("utf-8"))
    except Exception:
        continue

    body_str = json.dumps(body)
    if TARGET in body_str:
        callers.append(xml_file.name)

print("Callers of", TARGET, ":", callers)
```

**Why it works:** The dependency graph is built from the ground truth — the actual component JSON bodies — rather than the Tooling API which does not track embedded JSON references. The script surfaces all callers regardless of component type.

---

## Example 2: Detecting a Mixed-Mode Pipeline Before Deployment

**Context:** A team has enabled OmniStudio Metadata API Support in their developer sandbox and CI sandbox to modernize their pipeline. Their UAT sandbox and production org were not updated. They attempt to deploy an OmniScript retrieved from the CI sandbox to UAT using `sf project deploy start`.

**Problem:** The retrieved metadata is in `OmniProcess` format (Standard Runtime with Metadata API Support). UAT does not have the setting enabled, so it does not recognize `OmniProcess` as a valid metadata type. The deployment fails with a metadata type unrecognized error. The team has no visibility into which orgs have the setting enabled.

**Solution:**

Audit the Metadata API Support setting across all orgs before beginning deployment:

```bash
# Query OmniStudio settings in each org to confirm uniform enablement
# Run for each org alias in the pipeline
for ORG in dev-sandbox ci-sandbox uat-sandbox production; do
  echo "=== $ORG ==="
  sf data query \
    --query "SELECT Id, SettingValue FROM OmniUiCardMetadataSetting LIMIT 1" \
    --target-org $ORG \
    --use-tooling-api 2>/dev/null \
    || echo "OmniStudio Metadata API types not recognized — setting likely disabled"
done
```

If UAT and production still return unrecognized type errors:

1. Enable OmniStudio Metadata API Support in UAT via Setup > OmniStudio Settings > Enable OmniStudio Metadata API Support.
2. Wait for the org to complete the background migration of existing components to the new metadata format (this is asynchronous and can take minutes to hours depending on component volume).
3. Re-run the pipeline after all orgs confirm enablement.

**Why it works:** Catching the mixed-mode state before deployment — rather than discovering it mid-pipeline — prevents incomplete deployments and component format corruption. The audit step is lightweight and can be embedded as a pipeline pre-check.

---

## Anti-Pattern: Trusting Tooling API MetadataComponentDependency for OmniStudio Cross-Component Analysis

**What practitioners do:** Run a Tooling API SOQL query against `MetadataComponentDependency` filtered on `MetadataComponentType IN ('OmniUiCard','OmniProcess')` and treat the result as the complete dependency graph before making deletion or refactor decisions.

**What goes wrong:** The Tooling API tracks explicit metadata references declared in structured metadata XML. OmniStudio cross-component references (FlexCard → DataRaptor, OmniScript → Integration Procedure) are stored as string values in nested JSON structures inside the component body. The Tooling API cannot parse or index those embedded references. The query returns zero cross-component edges, which practitioners incorrectly interpret as "this component has no dependents." Components are deleted and callers fail silently at runtime.

**Correct approach:** Retrieve all four OmniStudio metadata types, decode and parse each component's JSON body, extract cross-reference fields by component type (see Core Concepts in SKILL.md), and build the dependency graph from the parsed JSON. The Tooling API query is appropriate for non-OmniStudio metadata dependency analysis.
