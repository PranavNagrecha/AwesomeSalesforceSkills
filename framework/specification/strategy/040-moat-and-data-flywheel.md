# Moat and improvement flywheel

## What is not a moat

- a large prompt count;
- a copied Salesforce documentation corpus;
- a wrapper around official MCP tools;
- a set of generic subagent names;
- a one-time benchmark tuned to one model;
- host-specific file formats.

## Durable assets

### 1. Governed Salesforce knowledge

The existing skill corpus contains operational patterns, anti-patterns, examples, and references. Its value increases when selection, source freshness, usage, and scenario outcomes are recorded.

### 2. Normalized evidence contracts

Stable evidence objects across Salesforce CLI, official MCP, local projects, fixtures, analyzers, and vendor exports let products and tests survive upstream format changes.

### 3. Claim/evidence and reviewer data

Every qualified run produces machine-inspectable claims, support, contradictions, reviewer corrections, and status. Sanitized aggregates reveal where agents overclaim and which evidence closes the gap.

### 4. Context performance data

Selection reasons, token/file cost, tool bytes, omitted candidates, compaction events, and outcomes allow the framework to improve context quality empirically rather than expanding mandatory reads.

### 5. Known-truth Salesforce scenarios

Versioned scratch-org and fixture scenarios create a behavioral benchmark that can compare hosts, models, product versions, and Salesforce releases. Hidden/rotating scenarios reduce benchmark gaming.

### 6. Cross-host conformance

Portable contracts and actual adapter evidence create switching value: users can compare Cursor, Claude, Copilot, or Vibes without losing Salesforce product semantics or run history.

### 7. Incident-to-regression workflow

```text
real problem
  -> sanitized evidence fixture
  -> accepted root cause and evidence facts
  -> known-truth scenario
  -> context/reviewer/tool improvement
  -> regression gate
  -> release confidence
```

## Privacy-preserving flywheel

The moat must not depend on collecting customer data centrally. Contributions can include:

- synthetic or minimized fixtures;
- hashed/digested target identities;
- failure shapes without business payloads;
- required finding/evidence labels;
- context-selection outcomes;
- reviewer defect categories;
- aggregate timing and acceptance.

Private team/enterprise deployments can keep evidence local while contributing schema/tool compatibility and anonymized quality signals.

## Defensibility test

A feature contributes to the moat only if it improves one of:

- unique governed knowledge;
- normalized evidence coverage;
- scenario breadth/difficulty;
- reviewer defect detection;
- context efficiency;
- cross-host consistency;
- user retention and trusted resolution.
