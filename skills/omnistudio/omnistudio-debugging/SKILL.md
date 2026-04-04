---
name: omnistudio-debugging
description: "Use when diagnosing failures, unexpected output, or silent errors in OmniScript, DataRaptor, or Integration Procedure assets. Triggers: 'omniscript not working', 'dataraptor returns empty', 'integration procedure failing', 'debug mode', 'action debugger', 'preview not running'. NOT for Apex debugging, LWC console errors unrelated to OmniStudio, or Flow fault path debugging."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - omnistudio
  - omniscript
  - dataraptor
  - integration-procedure
  - debugging
  - troubleshooting
triggers:
  - "omniscript step not navigating correctly in preview mode"
  - "dataraptor extract returning empty results with no error"
  - "integration procedure failing silently without error message"
  - "how do I see what data an OmniStudio action is sending and receiving"
  - "omniscript preview mode behaves differently from the live component"
  - "integration procedure worked in sandbox but fails in production"
inputs:
  - "OmniScript, DataRaptor, or Integration Procedure asset name and version"
  - "Error message text, screenshot, or debug log output"
  - "User context: authenticated internal, authenticated external, or guest"
  - "Environment: sandbox or production"
outputs:
  - "Root-cause identification for the failing OmniStudio asset"
  - "Step-by-step debug procedure appropriate to the asset type"
  - "Recommendations to make future failures observable"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# OmniStudio Debugging

This skill activates when a practitioner needs to diagnose and fix a broken, silent, or misbehaving OmniScript, DataRaptor, or Integration Procedure. It provides structured debug procedures for each asset type, explains platform-specific tracing tools, and surfaces the non-obvious behaviors that make OmniStudio failures hard to read.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which asset type is failing: OmniScript, DataRaptor (Extract / Load / Transform / Turbo Extract), or Integration Procedure?
- Is the failure happening in Preview mode, in a deployed LWC, or in a production FlexCard?
- What is the user context — internal, authenticated portal, or guest? Debug tool access and behavior differ by context.
- Is the asset version active? Inactive versions do not execute.
- Was a recent change deployed? Environment-specific dependencies (Named Credentials, Remote Site Settings, Custom Settings) may not have been promoted.

---

## Core Concepts

### 1. OmniStudio Has Three Separate Debug Surfaces

OmniStudio does not use a unified debugger. Each asset type has its own tracing mechanism:

- **OmniScript Preview + Action Debugger**: The OmniScript designer's built-in Preview tab renders the script in a sandbox iframe and exposes the Action Debugger panel. The Action Debugger shows each element's input, output, and error state as the user traverses the script. Navigation Action elements are explicitly excluded from Preview — they do not fire in the Preview tab because there is no app context to navigate into. This is platform-enforced, not a bug. (Source: Salesforce Help — Preview and Test an OmniScript.)

- **Integration Procedure Debug Mode**: The IP designer has a dedicated Debug tab. When you enter input JSON and click Run, the platform executes the IP server-side and returns a step-by-step execution log. The debug log shows each action element's input, output, response code, and error information. This is the primary tool for diagnosing HTTP action failures, response mapping issues, and incorrect sequencing. (Source: Salesforce Help — Debug and Activate an Integration Procedure.)

- **DataRaptor Preview**: The DataRaptor designer provides a Preview tab where you can supply sample input, run the asset, and inspect the raw output. For Extract assets this shows the generated SOQL and the raw result set. For Load assets it shows the DML being attempted. For Transform assets it shows input-to-output mapping results. Preview runs in the context of the authenticated designer user, so it will reflect that user's record access and FLS.

### 2. Silent Failures Are the Default

OmniStudio elements do not throw errors to the user interface by default when they encounter a problem. An Integration Procedure whose HTTP action returns a 500, a DataRaptor Extract that finds no matching records, or an OmniScript Set Values element that references a missing path will all complete without visible error unless explicit error handling and response configuration has been added. This is the most common source of "it's not working but there's no error" reports. The platform follows a fail-open pattern: elements that produce no result pass forward silently unless `rollbackOnError` or a Response Action is configured.

### 3. Environment Parity Is Rarely Guaranteed

OmniStudio assets that work in sandbox often fail in production for reasons unrelated to the asset itself:

- **Named Credentials** must be separately configured in each org. An HTTP action that works in sandbox against a sandbox Named Credential will fail immediately in production if the production credential is missing, uses different auth, or points to a different endpoint.
- **Custom Settings and Custom Metadata** used by DataRaptors or Integration Procedures for dynamic values may not have been populated after a deployment.
- **Remote Site Settings** must be active in every org where outbound callouts are made from OmniStudio HTTP actions.
- **Active version mismatch**: deploying a new version of an asset does not automatically activate it. If the old version is still active in production and the new one is in sandbox, the behavior will differ.

### 4. The Action Debugger Shows Element-Level Granularity

When running an OmniScript in Preview mode, the Action Debugger panel (accessible via the debug icon in the script designer) shows a real-time tree of every element execution. Each node in the tree includes the element name, type, input data node values, output data node values, and any error returned. This is the fastest way to confirm whether a DataRaptor action, Integration Procedure action, or HTTP action inside an OmniScript is receiving and returning the expected payload. Expanding a node shows the full JSON that was sent and received by that element.

---

## How This Skill Works

### Mode 1: Debug an OmniScript

Use when: an OmniScript is not rendering correctly, steps are skipped, actions return unexpected results, or the script behaves differently in Preview vs deployment.

1. Open the OmniScript in the designer. Confirm the version shown is the active version you expect to be running.
2. Click the Preview tab. Run through the failing path manually.
3. Open the Action Debugger (debug icon, top-right of the preview pane). Expand the node for the failing element.
4. Check the Input section: does it contain the expected data? If it is empty or missing fields, trace backward to the element that should have populated the data node.
5. Check the Output section: is the shape correct? If the output is empty, the element ran but returned nothing — check for silent null handling.
6. If a Navigation Action is not firing in Preview, that is expected platform behavior. Navigation Actions require a live app or community context and are excluded from Preview. Test Navigation Actions in the deployed component.
7. For OmniScript Apex actions, check the Apex class return type and confirm it implements `omnistudio.VlocityOpenInterface2`. If the class does not implement the expected interface, the action will silently fail.
8. Once root cause is identified, fix the data path, null guard, or action configuration and re-preview.

### Mode 2: Audit a DataRaptor

Use when: a DataRaptor returns empty results, produces unexpected field values, fails to write records, or maps data incorrectly.

1. Open the DataRaptor in the designer. Confirm the type: Extract, Turbo Extract, Load, or Transform.
2. Navigate to the Preview tab. Supply representative sample input matching the expected caller contract.
3. For **Extract**: inspect the generated SOQL shown in the preview. Confirm the WHERE clause uses the correct input field path. If the query returns no records, the filter values may not match. The preview runs in the context of the logged-in designer user — if that user lacks access to the records, the result will be empty.
4. For **Turbo Extract**: Turbo Extract does not support multi-level relationships or complex input mapping. If the asset was recently changed from Extract to Turbo Extract to gain performance, verify none of the removed capabilities are needed.
5. For **Load**: review the field mapping against actual field API names and data types. A field name case mismatch or missing required field will cause a silent DML failure unless error bubbling is configured in the calling Integration Procedure.
6. For **Transform**: walk input-to-output mapping row by row. JSONPath mismatches are common when the upstream response shape changes.
7. Check whether the DataRaptor is called from an Integration Procedure. If so, run the IP debug first — the IP debug log will show the DataRaptor call's input, output, and error state without needing to isolate the DataRaptor.

### Mode 3: Troubleshoot an Integration Procedure Error

Use when: an Integration Procedure returns unexpected data, silently fails, behaves differently across environments, or produces an error message.

1. Open the Integration Procedure in the designer. Go to the Debug tab (not the designer canvas).
2. Paste or type the JSON input the IP should receive. Ensure required fields are present.
3. Click Run. The platform executes the IP synchronously and returns a full step-level execution log.
4. Review the log top-to-bottom. For each element, check: status (success / error), input, response, and error.
5. For **HTTP action failures**: check the status code. 401 or 403 usually means the Named Credential is missing or misconfigured. 404 usually means the endpoint URL is wrong. 500 is a server-side error from the external system. A timeout (no response) means the external system did not respond within the configured limit or the Remote Site Setting is blocking the call.
6. For **DataRaptor action failures inside an IP**: the IP debug log will show the DataRaptor's input and output at that step. If the output is empty, run the DataRaptor in isolation to confirm whether the issue is data shape or access.
7. Confirm `rollbackOnError` is set at the root. If it is not, a failing step may not surface to the caller.
8. If the IP works in sandbox but not production: compare Named Credential names, check that the production Remote Site Setting exists, and verify that Custom Settings or Metadata values the IP depends on are populated in production.

---

## Decision Guidance

| Situation | Debug Tool | Why |
|---|---|---|
| OmniScript element not running or producing wrong output | OmniScript Preview + Action Debugger | Shows real-time per-element input/output in the designer |
| Navigation Action not firing in Preview | Expected — test in deployed component | Navigation Actions are excluded from Preview by design |
| DataRaptor Extract returning no records | DataRaptor Preview tab | Renders generated SOQL and raw result set |
| Integration Procedure HTTP action returning error | IP Debug tab | Shows status code, request, response at each step |
| IP works in sandbox, fails in production | Verify Named Credentials, Remote Site Settings, active version in prod | Environment-specific dependencies not promoted |
| DataRaptor failing inside an IP | Run IP Debug first, then isolate DataRaptor | IP debug shows the DataRaptor input/output in context |
| Silent failure with no error message | Check `rollbackOnError` and Response Action config | OmniStudio elements fail open without explicit error handling |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking debugging work complete:

- [ ] Confirmed the active version in the target environment is the version that was tested
- [ ] Action Debugger used to trace element-level input and output in the OmniScript
- [ ] IP Debug tab used with production-representative input JSON before marking IP as working
- [ ] All HTTP actions have a Named Credential name confirmed to exist in the target environment
- [ ] DataRaptor Preview run with sample input that matches the caller's actual data shape
- [ ] `rollbackOnError` confirmed at IP root to ensure failures are surfaced
- [ ] Response Action or failure response text is meaningful, not placeholder copy
- [ ] Remote Site Settings verified in target environment for outbound HTTP actions

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Navigation Actions are silently skipped in Preview** — OmniScript Preview mode does not execute Navigation Action elements. This is documented platform behavior, not a bug. Teams that rely on Preview to validate full end-to-end flows will miss broken navigation paths. Always test Navigation Actions in a deployed LWC or Experience Site context.

2. **DataRaptor Preview reflects the designer user's access** — When a DataRaptor Extract returns zero records in Preview, it does not mean the SOQL is wrong. It may mean the logged-in designer user simply lacks visibility to those records. Always test with a user whose profile and permissions match the actual runtime context, or verify the generated SOQL directly against a SOQL query tool.

3. **IP active version and deployed version can diverge without warning** — Deploying or importing a new IP version via a change set does not automatically activate it. If a sandbox IP was activated and the deployment moved a new version to production without activating it, the old version silently remains active in production. Always verify the active version after any deployment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Debug finding report | Root cause of the OmniStudio failure with the specific element, data node, or configuration item identified |
| Environment delta checklist | List of Named Credentials, Remote Site Settings, Custom Settings, and active version states to verify between environments |
| Remediation steps | Ordered fix list addressing the root cause and adding observable error handling to prevent recurrence |

---

## Related Skills

- `omnistudio/integration-procedures` — Use when the Integration Procedure design itself needs to change, not just be debugged.
- `omnistudio/dataraptor-patterns` — Use when the DataRaptor asset pattern is fundamentally wrong and needs to be redesigned.
- `omnistudio/omniscript-design-patterns` — Use when the OmniScript structure is the root cause, not a configuration or data mapping error.
- `omnistudio/omnistudio-security` — Use when debug output reveals a data exposure or access control problem.
