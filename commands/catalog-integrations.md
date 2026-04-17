# /catalog-integrations — Build the org's integration catalog

Wraps [`agents/integration-catalog-builder/AGENT.md`](../agents/integration-catalog-builder/AGENT.md). Named Credentials + Remote Sites + Connected Apps + Auth Providers + Certificates, cross-referenced with Apex/Flow usage, scored for posture.

---

## Step 1 — Collect inputs

```
1. Target org alias?
```

## Step 2 — Load the agent

Read `agents/integration-catalog-builder/AGENT.md` + mandatory reads.

## Step 3 — Execute the plan

Inventory NCs + RemoteSites + ConnectedApps + AuthProviders + Certificates, cross-reference Apex/Flow usage, score endpoints, emit catalog + cleanup queue.

## Step 4 — Deliver the output

Summary, catalog table, findings table, cleanup queue, Process Observations, citations.

## Step 5 — Recommend follow-ups

- `/architect-perms` for integration user PSG cleanup
- `/scan-security` for callout classes flagged as concerning

## What this command does NOT do

- Does not rotate certificates.
- Does not modify Connected Apps / NCs / Remote Sites.
- Does not test endpoint reachability.
