---
name: omniscript-session-state
description: "Use when an OmniScript must persist mid-flow state across refresh, navigation, multi-device resume, or abandonment recovery. Covers session objects, staging data, OmniScript tracking, and resume URLs. Does NOT cover OmniScript UI step layout (see omniscript-design) or general Flow pause/resume (see flow-transaction-finalizer-patterns)."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Security
triggers:
  - "omniscript save and resume"
  - "persist omniscript state refresh"
  - "resume omniscript multi device"
  - "abandoned cart omniscript"
  - "omniscript tracking session object"
tags:
  - omnistudio
  - omniscript
  - session
  - resume
  - state
inputs:
  - OmniScript that requires persistence
  - Abandonment tolerance
  - Cross-device resume requirement
outputs:
  - Session object model
  - Save/resume trigger design
  - Resume URL strategy
  - Expiry + cleanup plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# OmniScript Session State

## Purpose

Long-running OmniScripts — onboarding, quote configuration, compliance
questionnaires — lose users when a refresh wipes progress. OmniScript
ships native tracking but most teams mis-use it: they either persist
too little (UI state only, not answers) or too much (including PII that
should not be stored in plain object fields). This skill codifies the
session-state model: what to persist, where, with what retention, and
how to resume across devices without re-authenticating mid-flow.

## Recommended Workflow

1. **Define the state schema.** What answers, selections, derived values
   must survive? Exclude UI-only state.
2. **Pick the store.** OmniScript tracking record (`OmniScript_Session__c`
   pattern) vs Big Object for retention vs Platform Cache for short
   sessions.
3. **Persist at boundaries.** Save on step transition, not every
   keystroke. Debounce frequent edits.
4. **Design the resume URL.** Tokenized link that validates identity and
   session id, expires, and re-authenticates if necessary.
5. **Handle concurrency.** Two open tabs of the same session — last
   write wins with version field to detect conflicts.
6. **Set expiry.** Abandoned sessions time out; document a retention
   matching compliance.
7. **Purge.** Scheduled job clears expired sessions and PII.

## State Schema

- Keep the schema flat with typed fields where possible for queryability.
- Sensitive fields (SSN, card numbers) must be in encrypted custom fields
  or tokenized.
- Always include `userId`, `createdAt`, `lastUpdatedAt`, `version`.

## Store Selection

| Store | Use When | Cons |
|---|---|---|
| Custom object (`Session__c`) | Durable, queryable, cheap | Counts against data storage |
| Platform Cache (Session) | Short-lived, in-memory, fast | Lost on logout / restart |
| Big Object | Very high volume / long retention | Limited query shapes |

## Resume URL Design

- Short-lived signed token (JWT with narrow scope) embedded in the URL.
- Server validates the token, loads session, continues OmniScript at
  `stepId`.
- Token expires in hours, not days; long-term resume requires re-auth.
- Never embed answers in the URL.

## Concurrency

- Include a `version` field on the session. Each write increments.
- On save, compare versions; on mismatch, surface a "this session was
  updated elsewhere" branch.
- Do not silently overwrite.

## Expiry

- Tier 1 (sensitive): expire ≤ 24h, purge immediately after.
- Tier 2 (non-sensitive): expire ≤ 7d.
- Tier 3 (non-PII only): up to 30d.
- Retention policy is a compliance decision; confirm with stakeholders.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Store raw PII in session object fields.
- Base64-encoded state in URL.
- Persist every keystroke via DataRaptor.
- Treat session object as "temporary" without retention.

## Official Sources Used

- OmniScript Tracking — https://help.salesforce.com/s/articleView?id=sf.os_omniscript_tracking.htm
- OmniScript Save/Resume — https://help.salesforce.com/s/articleView?id=sf.os_use_save_for_later.htm
- Platform Cache — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_namespace_overview.htm
- Salesforce Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
