# Metadata Examples: Data Cloud Grounding for Agentforce

Grounding infrastructure is mostly created by the platform, not deployed. A data library provisions its own data stream, search index and retriever. Retrievers and search indexes do not travel in change sets or Metadata API deployments. So the reproducible artefact here is a scripted procedure (Salesforce CLI and the ADL Connect API), plus the one piece that is ordinary metadata: the prompt template that consumes the retriever.

## Example 1: A knowledge library scoped by data category, created from a script

**Context.** A service agent should answer product questions from published Knowledge articles in two data categories only. Each target org gets the library from the same script, because the library cannot be deployed as metadata.

**File path:** `scripts/grounding/create-knowledge-library.sh`

```bash
#!/usr/bin/env bash
# Creates the Product Support knowledge library and waits for indexing.
# Requires: Salesforce CLI with the agent plugin, Data Cloud on in the target org,
# and an org alias in $1.
set -euo pipefail
ORG="$1"

# Primary index fields are required for KNOWLEDGE libraries and immutable after creation.
# Fields must exist on the Knowledge object and be text-based (STRING or TEXTAREA).
sf agent adl create --target-org "$ORG" \
  --name "Product Support KB" \
  --developer-name Product_Support_KB \
  --source-type knowledge \
  --primary-index-field1 Title \
  --primary-index-field2 Summary \
  --content-fields UrlName \
  --data-category-names "Products.Hardware,Products.Software" \
  --wait 30 \
  --json > product_support_kb.json

LIBRARY_ID=$(jq -r '.result.libraryId // .result.id' product_support_kb.json)
echo "Library: $LIBRARY_ID"

# READY requires chunking and embedding to finish for the search index.
sf agent adl status --target-org "$ORG" --library-id "$LIBRARY_ID" --include-artifacts
```

The flag names and rules come from the Salesforce CLI help for `sf agent adl create` and `sf agent adl status` (CLI 2.151.7) and from the Agentforce Developer Guide "Knowledge Library Example". UNVERIFIED (2026-10-03): the JSON path of the library ID in the CLI's `--json` output; the script tries two plausible paths, so check the file once and pin the right one.

### The same request through the ADL Connect API

When a pipeline calls the API directly instead of the CLI, the request body is:

```json
{
  "masterLabel": "Product Support KB",
  "developerName": "Product_Support_KB",
  "groundingSource": {
    "sourceType": "KNOWLEDGE",
    "knowledgeConfig": {
      "primaryIndexField1": "Title",
      "primaryIndexField2": "Summary",
      "contentFields": ["UrlName"],
      "isDataCategoryRuleEnabled": true,
      "dataCategorySelectionNames": ["Products.Hardware", "Products.Software"]
    }
  }
}
```

POST it to `/services/data/v66.0/einstein/data-libraries`, then POST to `/services/data/v66.0/einstein/data-libraries/{libraryId}/indexing` and poll `/status` until the status is `READY` or `FAILED`. The response carries `libraryId` and `retrieverId`. Rules from the Knowledge Library Example: provide category names or category IDs, not both; names use `groupDeveloperName.categoryDeveloperName`; `contentFields` and categories can be updated after the library is READY; the primary index fields cannot; you cannot update a library while indexing is in progress; and a library referenced by an active agent cannot be deleted. Authentication uses an external client app with the client credentials flow and JWT-based access tokens (Get Started with ADL API).

## Example 2: The prompt template that consumes the retriever

The template is ordinary metadata. The retriever it calls is not, so the retriever must exist in the target org before the template that uses it is deployed (Generative AI guide, Limitations for Einstein Search).

**File path:** `force-app/main/default/genAiPromptTemplates/Answer_Product_Question.genAiPromptTemplate-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Answers a product question for a case using only grounded knowledge, with citations.</description>
    <masterLabel>Answer Product Question</masterLabel>
    <templateVersions>
        <content>You are a support assistant. Answer the customer's question about the product named in the case.
Case subject: {!$Input:Case.Subject}
Case description: {!$Input:Case.Description}
Use only the knowledge excerpts provided below. If they do not answer the question, say that you could not find the answer and offer to create a follow-up task.
</content>
        <inputs>
            <apiName>Case</apiName>
            <definition>SOBJECT://Case</definition>
            <referenceName>Input:Case</referenceName>
            <required>true</required>
        </inputs>
        <isCitationEnabled>true</isCitationEnabled>
        <primaryModel>sfdc_ai__DefaultGPT41</primaryModel>
        <status>Draft</status>
    </templateVersions>
    <type>einstein_gpt__flex</type>
    <visibility>Global</visibility>
</GenAiPromptTemplate>
```

After deploying this draft, open it in Prompt Builder and add the retriever from the Resource field: set Search Text from prompt inputs, choose the Output Fields, and set Number of Results. Then publish and retrieve the template so source control holds the version with the retriever reference. Element names follow the Metadata API reference sample for GenAiPromptTemplate; `sfdc_ai__DefaultGPT41` is listed on the Agentforce Developer Guide "Supported Models" page. UNVERIFIED (2026-10-03): the merge-field syntax Prompt Builder writes for a retriever reference; it is not shown in the sources read, which is why this example adds the retriever in the builder instead of by hand.

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Answer_Product_Question</members>
        <name>GenAiPromptTemplate</name>
    </types>
    <version>66.0</version>
</Package>
```

## Deploy order

1. Data Cloud on, Knowledge articles published and categorized.
2. Run `create-knowledge-library.sh` in the target org and wait for `READY`. This creates the data stream, search index and retriever there.
3. Deploy the prompt template, then add the retriever in Prompt Builder (or deploy the retrieved version that already references it, now that the retriever exists).
4. Assign the library to the agent (Agent Builder, Knowledge tab). Each feature uses one library at a time.

## Verification

- `sf agent adl status --library-id <id> --include-artifacts` shows every stage `SUCCESS` and the library `READY`.
- In Prompt Builder preview, the resolution shows the retriever's JSON results and the answer cites a source.
- Ask the agent about a product in a category outside `Products.Hardware` and `Products.Software`; it should say it could not find the answer.
