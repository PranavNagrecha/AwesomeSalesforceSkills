---
name: omnistudio-debugging
description: "Use when diagnosing failures, unexpected output, or silent errors in OmniScript, DataRaptor (Data Mapper), or Integration Procedure assets. Triggers: 'omniscript not working', 'dataraptor returns empty', 'integration procedure error', 'debug an omniscript'. NOT for Apex debugging, LWC console errors unrelated to OmniStudio, or Flow fault paths; for slow OmniStudio assets use omnistudio/omnistudio-performance."
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
  - "debug why my omniscript action returns no data"
  - "trace an integration procedure step by step in preview"
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
runtime_orphan: true
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# OmniStudio Debugging

This skill activates when a practitioner needs to diagnose and fix a broken, silent, or misbehaving OmniScript, DataRaptor (Omnistudio Data Mapper), or Integration Procedure. It gives a debug procedure per asset type, names the tracing tool for each, and lists the platform behaviors that make OmniStudio failures hard to read.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which asset type is failing: OmniScript, DataRaptor (Extract, Turbo Extract, Load, Transform), or Integration Procedure?
- Is the failure in a designer Preview, in a deployed Lightning page or Experience Cloud site, or in a FlexCard?
- What is the user context: internal, authenticated portal, or guest? Field access and record visibility differ by context.
- Which version is active in this environment? Only one OmniScript version is active at a time, and the `isActive` flag travels in the metadata.
- What changed recently? Named credential endpoints and secrets, custom settings, and custom metadata values often differ between orgs.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Does the failure reproduce in the designer Preview with the same input JSON? | The OmniScript Preview has a Data JSON pane and an Action Debugger; the Integration Procedure Preview pane has Errors/Debug Output. | Moves the investigation from "it's broken" to one failing step. | Every later fix is checked with the same input. |
| Which version is active in this org, and does the deployed file say `isActive` true? | Only one OmniScript version is active at a time; Integration Procedure and Data Mapper metadata carry `isActive` / `active` flags. | Confirms you are debugging the code that actually runs. | Release runbooks record the active version per environment. |
| Is the missing data dropped by a Response Action, a cache block, or a skipped block? | A Response Action trims what returns; a Cache Block serves stored output; a block whose Execution Conditional Formula is false is skipped. | Explains "no error, no data" cases. | Each block's purpose and condition are documented. |
| How should failures surface to the caller? | A Try-Catch Block returns specified output or calls an Apex class when a step fails. | A defined error contract between IP and OmniScript. | Users see a real message instead of an empty screen. |
| Does the HTTP action use a named credential endpoint? | Apex callouts to a named credential endpoint need no Remote Site Setting; other endpoints do. | The right environment check for callout failures. | No time lost adding Remote Site Settings that don't apply. |
| Is the Data Mapper checking field access, and who runs it? | The Options tab can check field access before running; Preview runs as the designer user. | A test plan that uses a representative user. | Restricted users get the same result in production as in testing. |

---

## Core Concepts

### 1. OmniStudio Has Separate Debug Surfaces

| Asset | Tool | What it shows |
|---|---|---|
| OmniScript | Designer Preview: Context ID, Data JSON pane, Action Debugger | Live data JSON as you fill the script; each action's request and response, searchable, with copyable nodes (Trailhead) |
| Integration Procedure | Designer Preview pane with Errors/Debug Output | Input parameters, execution result, and per-step debug output (Trailhead) |
| DataRaptor | Designer Preview tab | Response for Key/Value input parameters (Extract); objects created or updated (Load), which are saved permanently |

UNVERIFIED (2026-10-03): Salesforce Help states that Navigate Action elements don't run in the OmniScript Preview, and that DataRaptor Extract Preview shows the generated query. Neither statement appears in the fetched sources; test navigation in the deployed page either way.

### 2. Silent Failures Are Common

Several documented behaviors produce "no error, no data":

- A block whose **Execution Conditional Formula** evaluates to false is skipped (Trailhead, Integration Procedure Designer).
- A **Response Action** limits what the IP sends back, so data visible in the IP debug output can be absent in the OmniScript.
- A **Cache Block** returns stored output from session or org cache until it expires.
- A DataRaptor Load **skips** records whose Is Required For Upsert fields are empty.
- A Load with `errorIgnored` true continues after errors; with `rollbackOnError` false it commits partial work.

Design error handling on purpose: a Try-Catch Block "returns specified output or calls an Apex class if a step within it fails."

### 3. Environment Parity Is Rarely Guaranteed

OmniStudio assets that work in a sandbox often fail in production for reasons outside the asset:

- **Named credentials**: the `NamedCredential` definition is metadata, but credentials and per-org endpoints often differ. An HTTP action that works in a sandbox fails if the production credential is missing or points elsewhere.
- **Remote Site Settings**: required for callouts to endpoints that are not named credentials. "If the callout specifies a named credential as the endpoint, you don't need to configure remote site settings" (Apex Developer Guide). `RemoteSiteSetting` is a deployable Metadata API type.
- **Custom settings and custom metadata** read by Data Mappers or IPs may not be populated after deployment.
- **Active version**: a deployment can bring a new version without making it the active one, or carry `isActive` true unexpectedly. Check after every deployment.

The retrieve-and-diff script, a Remote Site Setting file, and a repeatable Preview input record are in [references/metadata-examples.md](references/metadata-examples.md).

### 4. The Action Debugger Shows Element-Level Detail

In the OmniScript Preview, the Action Debugger lists each action's request and response. Search for the action, expand it, and copy the node you need. "Reset Data" reloads the canvas and refreshes the Data JSON and the Action Debugger (Trailhead, "Dig into the Omniscript Designer"). Action element labels, not names, appear in the debugger, so give actions clear labels.

---

## How This Skill Works

### Mode 1: Debug an OmniScript

Use when an OmniScript is not rendering correctly, steps are skipped, actions return unexpected results, or Preview and deployment behave differently.

1. Open the OmniScript and confirm the version in the header is the version that is active in the org you are debugging.
2. Open Preview, enter a real record ID in Context ID, and run the failing path.
3. Open the Action Debugger and find the failing action by its label. Check the request: does it contain the expected data? If not, trace back to the element that should have populated it in the Data JSON.
4. Check the response: is the shape right? An empty response usually points to the Integration Procedure or Data Mapper behind it; run that asset's own Preview with the same input.
5. For navigation problems, test in the deployed Lightning page or site, not only in Preview.
6. For Remote Action and Apex-backed elements, confirm the class and method names match and that the class implements the interface your OmniStudio runtime expects. UNVERIFIED (2026-10-03): the interface name (for example `omnistudio.VlocityOpenInterface2` in the managed package) is documented only in Salesforce Help.
7. Fix the data path, condition, or action configuration and re-run Preview with Reset Data.

### Mode 2: Audit a DataRaptor

Use when a DataRaptor returns empty results, unexpected values, fails to write, or maps data incorrectly.

1. Confirm the type: Extract, Turbo Extract, Load, or Transform.
2. For an Extract or Turbo Extract, open Preview and enter Key/Value input parameters that match what the caller sends. Check the filters and the Extract Output Paths.
3. If the result is empty, check record visibility and field access for the running user. Preview runs as the designer user; turn on the Options-tab field access check (`fieldLevelSecurityEnabled`) for restricted users and test as one of them.
4. For a Turbo Extract, remember it reads a single object (with related-object fields) and supports no formulas or complex output mappings.
5. For a Load, check Upsert Keys and Is Required For Upsert fields: empty required fields skip the record. Preview writes real records, so preview Loads only in a developer sandbox.
6. If the DataRaptor is called from an Integration Procedure, run the IP Preview first; its debug output shows the DataRaptor step's input and output in context.

### Mode 3: Troubleshoot an Integration Procedure

Use when an IP returns unexpected data, silently fails, behaves differently across environments, or reports an error.

1. Open the IP designer and use the Preview pane, not the canvas.
2. Enter the input JSON the IP should receive, including required keys.
3. Execute and read Errors/Debug Output top to bottom: each step's input, output, and errors.
4. For steps that never appear in the output, check the enclosing block's Execution Conditional Formula.
5. For HTTP action failures: 401 or 403 usually means the named credential is missing or misconfigured; 404 means a wrong endpoint path; 5xx is the external system; a callout to a non-named-credential endpoint with no Remote Site Setting fails before it is sent.
6. For data that exists in the debug output but not in the caller, check the Response Action and any Cache Block.
7. If the IP works in a sandbox but not in production, compare named credentials, Remote Site Settings for non-named-credential endpoints, custom setting values, and the active version.

---

## Decision Guidance

| Situation | Debug Tool | Why |
|---|---|---|
| OmniScript element produces the wrong output | Preview + Data JSON + Action Debugger | Shows each action's request and response |
| Navigation not working | Deployed page or site | Navigation needs the real app context |
| DataRaptor Extract returns nothing | DataRaptor Preview with caller's input, then test as a restricted user | Input or access is the usual cause |
| IP HTTP action returns an error | IP Preview Errors/Debug Output | Shows the failing step and its response |
| Data in IP debug output but missing in OmniScript | Response Action and Cache Block review | The IP trims or caches what it returns |
| Steps silently skipped | Execution Conditional Formula on the enclosing block | False condition skips the block |
| Works in sandbox, fails in production | Named credential, Remote Site Setting (non-named-credential endpoints), custom settings, active version | Environment-specific dependencies |

---

## Recommended Workflow

1. Identify the asset and the active version in the failing environment, and capture the exact input JSON or Context ID.
2. Reproduce in the designer Preview of the closest asset (Action Debugger for OmniScripts, Errors/Debug Output for IPs, Preview for DataRaptors).
3. Walk downstream to the first step whose output is wrong, checking conditions, Response Actions, caches, and Load skip rules on the way.
4. Retrieve the assets and run `python3 skills/omnistudio/omnistudio-debugging/scripts/check_omnistudio_debugging.py --manifest-dir force-app` to flag placeholder failure messages, inactive assets, FLS off, and partial-commit Loads.
5. Fix, re-run the same Preview input, then verify in the deployed context as a representative user and record the active version.

---

## Review Checklist

Run through these before marking debugging work complete:

- [ ] Confirmed the active version in the target environment is the version that was tested
- [ ] Action Debugger used to trace element-level requests and responses in the OmniScript
- [ ] IP Preview run with production-representative input JSON; Errors/Debug Output reviewed
- [ ] Response Actions, Cache Blocks, and Execution Conditional Formulas checked for dropped data
- [ ] HTTP actions use named credentials, or Remote Site Settings exist for their endpoints
- [ ] DataRaptor tested as a representative user with the field access check decided
- [ ] Try-Catch Blocks return meaningful output to the caller
- [ ] Load Preview run only in a developer sandbox

---

## Salesforce-Specific Gotchas

Full write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Skipped blocks | A false Execution Conditional Formula skips the block with no error. |
| Response Action | Data in the IP debug output can be trimmed before it reaches the caller. |
| Cache Block | Cached output hides fixes until the cache expires. |
| Load Preview | Previewing a Load writes real records. |
| Named credentials | Callouts to named credential endpoints need no Remote Site Setting. |
| Active version | Deployments don't guarantee the intended version is active. |
| Preview identity | Preview runs as the designer user, not the end user. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Debug finding report | Root cause with the specific element, data node, or configuration item |
| Environment delta checklist | Named credentials, Remote Site Settings for non-named-credential endpoints, custom settings, and active versions to compare between orgs |
| Remediation steps | Ordered fix list, plus the error handling (Try-Catch, Response Action) that makes the next failure visible |

---

## Related Skills

- `omnistudio/integration-procedures`: Use when the Integration Procedure design itself needs to change, not just be debugged.
- `omnistudio/dataraptor-patterns`: Use when the DataRaptor asset pattern is fundamentally wrong and needs to be redesigned.
- `omnistudio/omniscript-design-patterns`: Use when the OmniScript structure is the root cause, not a configuration or data mapping error.
- `omnistudio/omnistudio-security`: Use when debug output reveals a data exposure or access control problem.
