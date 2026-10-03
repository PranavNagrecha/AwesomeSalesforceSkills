# Metadata and API Examples: OmniScript Flow Design Requirements

Deployable and runnable artifacts for this skill. Each block names the file path it lives at. Narrative examples are in `references/examples.md`.

## Example 1: Requirements Spec the Developer Can Build From

**Context:** The Edit Account interaction from Trailhead's "Optimize Workflow with OmniScript Design" unit: a service rep opens it from an account FlexCard, sees the account name read-only, edits phone and website, and returns to the card.

**Artifact:** a requirements spec checked into the project next to the build, at `docs/omniscripts/team_editAccount_English.requirements.yaml`.

```yaml
# docs/omniscripts/team_editAccount_English.requirements.yaml
identity:
  type: team                 # Type starts lowercase (Trailhead recommendation)
  subType: editAccount
  language: English
  name: Edit Account         # display name; does not need to be unique
runtime: managed-package     # or standard; state it, the build differs
license_confirmed: true      # OmniStudio license checked against the contract
launch:
  from: FlexCard action "Edit Account"
  inputs:
    - node: AccountId        # same name in every element that passes it
      source: FlexCard record context
actions:
  - name: IPGetAccountDetails
    kind: Integration Procedure
    placement: before StepAccount        # runs automatically, fills the Step
    send: { ContextId: AccountId }
  - name: IPSaveAccountDetails
    kind: Integration Procedure
    placement: after StepAccount         # runs automatically on Next
  - name: NavBackToCard
    kind: Navigate Action
    placement: after IPSaveAccountDetails
    destination: return to the launching console tab
steps:
  - name: StepAccount
    elements:
      - { name: AccountName, type: Text,      label: Account Name, readOnly: true,  json_node: AccountName }
      - { name: Phone,       type: Telephone, label: Phone,        required: true,  json_node: Phone }
      - { name: Website,     type: URL,       label: Website,      required: false, json_node: Website }
conditional_views: []        # none in this journey; list element, operator, value when present
cross_step_rules: []         # Set Errors entries; required flags only guard the current Step
children: []                 # child OmniScripts nest one level only
acceptance:
  - Phone and Website pre-fill from IPGetAccountDetails for an account with both values
  - Saving updates the Account and returns the rep to the card
  - Clearing Phone blocks Next with the required-field message
```

**Retrieving the built OmniScript for review:** the OmniScript metadata type is documented in the Salesforce Industries Developer Guide with suffix `omniScript`, folder `omniScripts`, and `uniqueName` in the form Type_SubType_Language_VersionNumber.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>team_editAccount_English_1</members>
        <name>OmniScript</name>
    </types>
    <version>67.0</version>
</Package>
```

UNVERIFIED (2026-10-03): that the `package.xml` member equals the `uniqueName` (Type_SubType_Language_VersionNumber) is inferred from the field description; the guide's sample manifest uses a wildcard. The guide documents the type in the Discovery Framework section, and its Special Access Rules mention the Discovery Framework feature, so confirm retrieval of non-Discovery OmniScripts in your org.

**Why it works:** Every field in the spec maps to a question a developer would otherwise ask: identity for versioning, placement for timing, JSON node for pre-fill, and destination for the Navigate Action. Reviewers can compare the retrieved metadata to the spec line by line.
