# CPQ Custom Actions — Work Template

Use this template when implementing or troubleshooting `SBQQ__CustomAction__c` records in a Salesforce CPQ org.

## Scope

**Skill:** `cpq-custom-actions`

**Request summary:** (fill in what the user asked for — e.g., "Add a validation button to the QLE that runs a compatibility check Flow")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **CPQ package version:** (e.g., 242.0.1 — check Setup > Installed Packages)
- **Target screen:** Line Item / Group / Global / Configurator / Amendment
- **Existing action count for target location:** (run SOQL: `SELECT COUNT() FROM SBQQ__CustomAction__c WHERE SBQQ__Location__c = '<location>' AND SBQQ__Active__c = true`)
- **Action type needed:** URL / Flow / Calculate / Save / Add Group
- **Apex logic required?** Yes / No — if Yes, specify workaround: Flow-bridge / VF+Apex URL
- **Conditional visibility required?** Yes / No — if Yes, specify condition fields and values
- **Known constraints:** (e.g., at limit of 5 actions, Flow not yet built, external URL CSP not configured)

## Existing Action Audit

```
Location: ___________________
Active action count: ___ / 5

Existing active actions at this location:
1. Name: _______________ | Type: _______________ | Order: ___
2. Name: _______________ | Type: _______________ | Order: ___
3. Name: _______________ | Type: _______________ | Order: ___
4. Name: _______________ | Type: _______________ | Order: ___
5. Name: _______________ | Type: _______________ | Order: ___
```

## SBQQ__CustomAction__c Record Specification

```
Name (button label):        ___________________________________
SBQQ__Type__c:              URL / Flow / Calculate / Save / Add Group
SBQQ__Location__c:          Line Item / Group / Global / (other)
SBQQ__DisplayOrder__c:      ___
SBQQ__Active__c:            true / false

If Type = Flow:
  SBQQ__FlowName__c:        ___________________________________ (API name, must be Active)

If Type = URL:
  SBQQ__URL__c:             ___________________________________
  CSP Trusted Site added?:  Yes / No / Not needed (opens in new tab)
```

## Conditional Visibility Specification (if applicable)

```
SBQQ__ConditionsMet__c on parent: All / Any / Formula

Condition records:
  Condition 1:
    SBQQ__FilterField__c:     ___________________________________
    SBQQ__FilterOperator__c:  Equals / Not Equal / Greater Than / Less Than / Starts With / Contains
    SBQQ__FilterValue__c:     ___________________________________

  Condition 2 (if needed):
    SBQQ__FilterField__c:     ___________________________________
    SBQQ__FilterOperator__c:  ___________________________________
    SBQQ__FilterValue__c:     ___________________________________
```

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Flow-backed validation button — Apex logic required, Flow bridges to @InvocableMethod
- [ ] URL action to external tool — Navigation only, no Salesforce data written
- [ ] URL action to Visualforce — Apex required, no Flow; VF page hosts Apex controller
- [ ] Standard CPQ operation (Calculate / Save / Add Group) — No custom logic needed
- [ ] Other: _______________________________________________

## Pre-Build Checklist

- [ ] Existing action count for target location confirmed as < 5
- [ ] Flow is built and Activated (if Type = Flow)
- [ ] Visualforce page deployed (if Type = URL to VF)
- [ ] External URL added to CSP Trusted Sites (if applicable)
- [ ] Condition fields and values confirmed with business stakeholder

## Post-Build Checklist (from SKILL.md Review Checklist)

- [ ] Active custom action count for the target location is 5 or fewer
- [ ] Flow is activated (not Draft) before the custom action record was saved
- [ ] For URL actions, target URL domain added to CSP Trusted Sites if it opens in Lightning
- [ ] Conditional visibility is configured via CPQ condition records, not Flow decisions or Apex
- [ ] Action tested on target CPQ screen (QLE, configurator, or amendment)
- [ ] Action tested on amendment/renewal quote if applicable
- [ ] Button label in `Name` field is clear and rep-facing
- [ ] `SBQQ__DisplayOrder__c` confirmed, no collision with existing actions

## Notes

Record any deviations from the standard pattern and why.

(e.g., "Button consolidation was required — combined three existing actions into a single Flow with a radio-button choice screen to stay within the 5-action limit.")
