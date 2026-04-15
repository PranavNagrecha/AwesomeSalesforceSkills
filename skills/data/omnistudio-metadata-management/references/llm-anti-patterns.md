# LLM Anti-Patterns — OmniStudio Metadata Management

Common mistakes AI coding assistants make when generating or advising on OmniStudio metadata management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Tooling API MetadataComponentDependency to Map OmniStudio Dependencies

**What the LLM generates:** A Tooling API SOQL query such as:

```soql
SELECT MetadataComponentId, MetadataComponentName, MetadataComponentType,
       RefMetadataComponentId, RefMetadataComponentName, RefMetadataComponentType
FROM MetadataComponentDependency
WHERE MetadataComponentType IN ('OmniUiCard', 'OmniProcess', 'OmniDataTransform')
```

…presented as a complete dependency graph query that will surface all FlexCard → DataRaptor and OmniScript → Integration Procedure relationships.

**Why it happens:** LLMs are trained on general Salesforce metadata dependency documentation where `MetadataComponentDependency` is the standard, correct answer for dependency tracking. The OmniStudio-specific exception — that cross-component references are embedded in JSON bodies, not tracked as Tooling API edges — is rarely documented explicitly and does not appear in LLM training data at the same frequency as the general pattern.

**Correct pattern:**

```bash
# Step 1: Retrieve all OmniStudio metadata types
sf project retrieve start \
  --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig \
  --target-org <alias>

# Step 2: Parse each component's base64 JSON body and extract cross-reference fields
# See examples.md for a Python parsing implementation
```

OmniStudio cross-component references (FlexCard → DataRaptor, OmniScript → Integration Procedure) live inside the component's `propertySet` and `actionList` JSON fields — not in the Tooling API dependency graph. The Tooling API query returns zero cross-component edges and must not be used for OmniStudio impact analysis.

**Detection hint:** Any response that uses `MetadataComponentDependency` filtered on `OmniUiCard` or `OmniProcess` types and presents the result as an impact analysis or dependency graph for OmniStudio is applying this anti-pattern.

---

## Anti-Pattern 2: Assuming OmniStudio Metadata API Support Is Always Enabled

**What the LLM generates:** Instructions that assume `OmniProcess`, `OmniDataTransform`, `OmniUiCard`, and `OmniInteractionConfig` are available as metadata types in any Salesforce org with OmniStudio installed, without first confirming the setting is enabled:

```bash
# LLM-generated instruction (WRONG without confirming setting first)
sf project retrieve start \
  --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig \
  --target-org myorg
```

If OmniStudio Metadata API Support is not enabled, this command fails with a metadata type not found error, which the LLM then misdiagnoses as a CLI version or permission issue.

**Why it happens:** LLMs conflate "OmniStudio is installed" with "OmniStudio Metadata API Support is enabled." The enablement is a separate org-level toggle introduced after the initial OmniStudio product release, and its existence is not consistently prominent in documentation indexed by LLMs.

**Correct pattern:**

```
Before issuing any retrieve or deploy command using OmniStudio metadata types:
1. Confirm OmniStudio Metadata API Support is enabled in the org:
   Setup > OmniStudio Settings > Enable OmniStudio Metadata API Support
2. If not enabled, enable it and wait for the background component migration to complete
3. Confirm all orgs in the pipeline have the same setting before proceeding
```

**Detection hint:** Any instruction that uses `OmniProcess`, `OmniDataTransform`, `OmniUiCard`, or `OmniInteractionConfig` metadata types without first verifying the setting is enabled is applying this anti-pattern.

---

## Anti-Pattern 3: Treating Roadmap Automated Dependency Management as a Current Capability

**What the LLM generates:** Architectural guidance or pipeline designs that reference "Salesforce's automated OmniStudio dependency management" as a currently available feature to rely on for deployment ordering:

```
# LLM-generated recommendation (WRONG — feature not yet shipped)
"Use Salesforce's built-in OmniStudio dependency management to automatically
 sequence your component deployments — the platform will resolve dependencies
 and deploy in the correct order."
```

**Why it happens:** The February 2026 Salesforce developer blog post announcing the roadmap item is indexed by LLMs alongside current documentation. LLMs do not reliably distinguish between "announced" and "available" unless the distinction is explicit in the source text.

**Correct pattern:**

```
As of Spring '25, Salesforce has announced automated OmniStudio dependency 
management on their roadmap (Feb 2026 blog post, targeted mid-2026). This 
feature is NOT yet available in production orgs. Pipelines must implement 
manual dependency ordering using JSON body parsing to sequence deployments 
correctly. Revisit this assessment when Salesforce publishes GA release notes 
for the automated dependency management feature.
```

**Detection hint:** Any guidance that instructs a practitioner to "let the platform handle dependency ordering" or "use Salesforce's dependency manager" for OmniStudio components should be flagged for verification against current release notes.

---

## Anti-Pattern 4: Assuming All Component Metadata Lives in XML Element Attributes

**What the LLM generates:** Parsing logic that reads OmniStudio metadata XML directly from element attributes or child elements without decoding the base64 JSON body:

```python
# WRONG — reads XML structure only, misses embedded JSON
import xml.etree.ElementTree as ET
tree = ET.parse("MyFlexCard.omniUiCard-meta.xml")
for el in tree.iter():
    if "dataRaptor" in el.tag.lower():
        print("Found DataRaptor reference:", el.text)
```

This produces no output because DataRaptor references are not XML elements — they are string values inside a base64-encoded JSON blob in the `<content>` element.

**Why it happens:** LLMs are trained on standard Salesforce metadata file patterns where component configuration is expressed as XML child elements. OmniStudio metadata files use a hybrid format — the outer structure is XML, but the full component definition is encoded as a JSON blob inside `<content>`. This pattern is unusual in the Salesforce metadata ecosystem and is underrepresented in training data.

**Correct pattern:**

```python
import base64, json, xml.etree.ElementTree as ET

tree = ET.parse("MyFlexCard.omniUiCard-meta.xml")
root = tree.getroot()
# Find the <content> element (may or may not use namespace)
content_el = root.find(".//content")
if content_el is not None and content_el.text:
    body = json.loads(base64.b64decode(content_el.text).decode("utf-8"))
    # Now navigate the parsed JSON to find cross-component references
    data_raptor_name = body.get("propertySet", {}).get("dataRaptorBundleName")
```

**Detection hint:** OmniStudio metadata parsing code that uses `ET.iter()` or XPath element searches without first extracting and decoding the `<content>` base64 blob is almost certainly missing all embedded cross-component references.

---

## Anti-Pattern 5: Recommending DataPacks for Dependency Analysis in Standard Runtime Orgs

**What the LLM generates:** Guidance that uses DataPack JSON export as the source for dependency analysis in Standard Runtime orgs:

```bash
# WRONG for Standard Runtime orgs with Metadata API Support enabled
sf omnistudio datapack export --target-org myorg --output ./datapacks
# "Now parse the DataPack JSON to find dependencies..."
```

**Why it happens:** DataPack JSON is well-documented and historically was the only way to get machine-readable OmniStudio component data. LLMs trained on pre-2024 documentation will default to DataPack workflows regardless of runtime mode. In Standard Runtime orgs with Metadata API Support enabled, DataPack export is either unavailable or produces output in a different format than expected, and DataPack mechanics are a separate concern from metadata type management.

**Correct pattern:**

```
For Standard Runtime orgs with OmniStudio Metadata API Support enabled:
  Use: sf project retrieve start --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig
  Parse: base64-decoded JSON body from <content> element in each retrieved XML file

For Package Runtime orgs (DataPack mode):
  Use: DataPack export via sf omnistudio datapack commands
  See: data/omnistudio-datapack-migration skill for DataPack mechanics

Do NOT mix these two approaches within the same org or pipeline.
```

**Detection hint:** Any dependency analysis workflow that recommends `sf omnistudio datapack export` for a Standard Runtime org (or for an org where OmniStudio Metadata API Support is enabled) is applying this anti-pattern.

---

## Anti-Pattern 6: Ignoring FlexCard-to-FlexCard Child Card Dependencies

**What the LLM generates:** Dependency analysis code that only extracts DataRaptor and Integration Procedure references from FlexCard JSON bodies, omitting child FlexCard references:

```python
# WRONG — incomplete; misses nested child FlexCard references
def extract_flexcard_refs(body):
    refs = []
    prop = body.get("propertySet", {})
    if prop.get("dataRaptorBundleName"):
        refs.append(prop["dataRaptorBundleName"])
    for action in body.get("actionList", []):
        remote = action.get("actionAttributes", {}).get("remoteClass")
        if remote:
            refs.append(remote)
    return refs  # Missing: child FlexCard references in childElements
```

**Why it happens:** Most OmniStudio dependency documentation focuses on DataRaptor and Integration Procedure as the primary cross-component call targets. FlexCard-to-FlexCard composition is less commonly documented as a separate dependency class. LLMs learn the two-tier reference model (FlexCard calls DataRaptor/IP) and miss the FlexCard composition tier.

**Correct pattern:**

```python
def extract_flexcard_refs(body):
    refs = []
    prop = body.get("propertySet", {})
    if prop.get("dataRaptorBundleName"):
        refs.append(("DataRaptor", prop["dataRaptorBundleName"]))
    for action in body.get("actionList", []):
        remote = action.get("actionAttributes", {}).get("remoteClass")
        if remote:
            refs.append(("IP_or_OmniScript", remote))
    # Also extract child FlexCard references
    for child in body.get("childElements", []):
        if child.get("type") == "card" or "cardName" in child.get("propertySet", {}):
            child_name = child.get("propertySet", {}).get("cardName")
            if child_name:
                refs.append(("FlexCard", child_name))
    return refs
```

**Detection hint:** FlexCard dependency analysis code that does not inspect `childElements` for nested card references is producing an incomplete dependency graph.
