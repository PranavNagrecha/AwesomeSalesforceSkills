# Adoption and distribution

## Product-led first experience

The first user path must not require reading the architecture:

```text
install/link plugin
  -> reload Cursor
  -> /sfskills-doctor
  -> /triage-deployment --result-file examples/...
  -> inspect evidence-linked result
  -> optionally connect explicit org/project
```

The fixture experience proves product shape without credentials. The doctor explains missing dependencies and safety boundaries. The first result should be shorter and more actionable than the raw fixture.

## Distribution phases

### Local design-partner package

- direct ZIP/repository install;
- current local Cursor plugin path;
- no public Marketplace claim;
- fixture and explicit read-only org modes;
- feedback/replay export.

### Team distribution

- team plugin marketplace or controlled repository import where licensing permits;
- shared policies, source records, org allowlists, private knowledge overlays, and scenario packs;
- signed/versioned adapters and run bundles.

### Portable ecosystem

- Agent Plugin for portable skills/MCP where the format and license permit;
- Claude Code and VS Code/Copilot adapters;
- Vibes proof path;
- public evidence/run schemas and conformance tests.

### Hosted/enterprise option

- evidence gateway, central QA dashboard, policy/RBAC, private scenarios, retention, signed attestations, and support;
- never require hosted service for basic local diagnosis or evidence transparency.

## Distribution constraints

The current source-available license and Cursor public Marketplace rules require an explicit legal/product decision. Do not call the repository open source or promise public listing until the license path is resolved.

## Content strategy

Lead with jobs and evidence:

- “Why did this deployment fail?”
- “Why are these Apex tests failing together?”
- “Why can’t this user edit this record?”
- “What breaks if we change this field/flow?”

Demo the difference between raw log, vanilla host, and SfSkills claim/evidence result. Avoid leading with skill count.

## Community contribution paths

- submit/fix a Salesforce skill source;
- add a sanitized fixture;
- add a known-truth scenario;
- improve an evidence normalizer;
- improve a context trigger;
- add an adapter conformance result;
- report a reviewer escape or safety bypass.

Every contribution type needs a validator and quality bar.
