#!/usr/bin/env python3
"""
build_plugin.py — Claude Code plugin packaging (tiered router architecture)

Generates every artifact needed to install SfSkills as a Claude Code plugin:

  .claude-plugin/plugin.json          plugin manifest
  .claude-plugin/marketplace.json     repo-as-its-own-marketplace manifest
  .claude/skills/salesforce/          Tier-1 top-level router
  .claude/skills/salesforce-<domain>/ Tier-1 domain routers (11) + rosters
  .claude/agents/<agent-id>.md        Tier-3 subagent loaders, PROJECT scope
  agents/<agent-id>.md                Tier-3 subagent loaders, PLUGIN scope

The two subagent loader sets are byte-identical by construction: one
``render_subagent()`` call is written to both paths. They are needed for two
different mechanisms and neither substitutes for the other — see
``PLUGIN_AGENT_SCAN_DIR`` below.

Why a tiered layout: the 1,027 skill packages carry ~536 KB of name +
description text. Claude Agent Skills load every skill's name + description
up front, so a flat export would spend ~134k tokens before the user types.
The routers cost ~1.3k. Tier 2 stays exactly where it is and is reached on
demand by path under ${CLAUDE_PLUGIN_ROOT}. Run ``--measure`` for the live
numbers.

Schema sources (researched, not guessed):
  https://code.claude.com/docs/en/plugins-reference
  https://code.claude.com/docs/en/plugin-marketplaces
  https://code.claude.com/docs/en/sub-agents

Usage:
  python3 scripts/build_plugin.py                 # build in place
  python3 scripts/build_plugin.py --check         # drift gate, exit 1 on diff
  python3 scripts/build_plugin.py --measure       # token-budget JSON
  python3 scripts/build_plugin.py --verify-seeds  # resolve the curated seeds
  python3 scripts/build_plugin.py --audit-install # what an INSTALL exposes

Stdlib only. Deterministic: sorted iteration, "\\n" line endings, no
timestamps, no hostnames — so ``--check`` is a true drift gate.
"""

import argparse
import json
import math
import re
import sys
import tempfile
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
REGISTRY_FILE = REPO_ROOT / "registry" / "skills.json"
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"
COMMANDS_DIR = REPO_ROOT / "commands"
TREES_DIR = REPO_ROOT / "standards" / "decision-trees"
TEMPLATES_DIR = REPO_ROOT / "templates"

PLUGIN_MANIFEST_DIR = Path(".claude-plugin")
ROUTER_ROOT = Path(".claude/skills")
SUBAGENT_ROOT = Path(".claude/agents")

# Where Claude Code's default subagent scan actually looks: flat `*.md`
# directly under `<plugin root>/agents/`. Nothing else loads — see
# `AGENT_LOADING_MATRIX` below. This repo's `agents/` also holds the
# `<id>/AGENT.md` playbook packages, which that scan skips (variant A'), so
# the flat loaders sit BESIDE them rather than replacing them.
#
# The same loader body is written twice, to two different mechanisms:
#   agents/<id>.md          plugin scope  — what an INSTALL exposes
#   .claude/agents/<id>.md  project scope — what a CLONE exposes
# Per https://code.claude.com/docs/en/plugins, a project-local
# `.claude/agents/` definition OVERRIDES a same-named plugin agent. Inside a
# clone the project copy therefore always wins and the plugin copy is never
# exercised, so drift between the two would be invisible from the inside.
# Generating both from one `render_subagent()` call is what makes drift
# impossible; `--check` is what proves it stayed that way.
PLUGIN_AGENT_SCAN_DIR = Path("agents")

PLUGIN_NAME = "sfskills"
MARKETPLACE_NAME = "sfskills"
PLUGIN_VERSION = "1.1.0"
AUTHOR_NAME = "Pranav Nagrecha"
REPO_URL = "https://github.com/PranavNagrecha/AwesomeSalesforceSkills"

# The marketplace entry's `skills` field is load-bearing. Per
# plugins-reference "Path behavior rules", `skills` normally ADDS to the
# default `skills/` scan; the one exception is a marketplace entry whose
# `source` resolves to the marketplace root, where the listed paths REPLACE
# it. That exception is what keeps the 1,027 Tier-2 packages out of the
# always-on index. Do not drop either half of the (source, skills) pair.
PLUGIN_SKILLS_PATH = "./.claude/skills/"

# `commands` REPLACES the default `commands/` scan. Naming the default folder
# explicitly is the documented way to declare it without losing it
# (plugins-reference, "Path behavior rules": Claude Code "doesn't warn when
# the manifest key points into the default folder, for example
# `"commands": ["./commands/deploy.md"]`, because that path names the folder
# explicitly"). Measured on 2.1.209: loads all 66 command files.
PLUGIN_COMMANDS_PATH = "./commands/"

# ── Why there is no `agents` key ──────────────────────────────────────────────
#
# Measured on Claude Code 2.1.209 (2026-08-01) with a throwaway probe plugin
# installed into an isolated CLAUDE_CONFIG_DIR, read back with
# `claude plugin details`. Reproduce with the probe procedure in
# docs/installing-the-plugin.md, "Known limitation 1".
#
#   variant                                            validate   Agents()
#   A  no `agents` key, flat agents/foo.md              pass       1  foo
#   A' no `agents` key, nested agents/x/AGENT.md only   pass       0
#   B  plugin.json  agents: ["./custom-agents/"]        ERROR      —   dir rejected
#   C  plugin.json  agents: ["./custom-agents/a.md"]    pass       0
#   D  plugin.json  agents: ["./.claude/agents/a.md"]   pass       0
#   E  plugin.json  agents: ["./agents/foo.md"]         pass       0  suppresses A
#   F  marketplace  agents: ["./.claude/agents/a.md"]   pass       0  (the 1 seen
#                                                                     was still A)
#   G  marketplace  agents: [dir]                       ERROR      —   dir rejected
#   H  strict:false + marketplace components            pass       load failure:
#                                                          "conflicting manifests"
#
# Conclusion: on this version the ONLY mechanism that ships a subagent is a
# flat `.md` directly inside `<plugin root>/agents/`. Every custom path form
# loads zero, and variant E shows the key also suppresses the one scan that
# works. So declaring `agents` is strictly worse than omitting it, and the
# generated manifests deliberately omit it.
#
# The corollary used to be an open defect: this repo's `agents/` holds
# `<id>/AGENT.md` packages, which variant A' shows the flat scan skips, and
# the generated loaders lived ONLY at `.claude/agents/` — a PROJECT-LOCAL
# path Claude Code reads for anyone sitting in this repo, plugin or not. That
# is why the plugin appeared to ship agents when it never did, and it shipped
# `Agents (0)`.
#
# Closed by variant A: this build now also emits the loaders to
# `agents/<id>.md`, beside (never instead of) the `<id>/AGENT.md` packages.
# Re-measured on this repository, installed from a local-path marketplace
# source into an isolated CLAUDE_CONFIG_DIR from outside the working tree:
# `claude plugin details sfskills` reports `Agents (48)`.
AGENT_LOADING_MATRIX_VERSION = "2.1.209"

# ── Token model — an exact closed form, not a fit ─────────────────────────────
#
# Claude Code's always-on charge for one plugin component is:
#
#     always_on = 0.25 * (len(qualified_name) + len(description)) + 0.25
#
# where
#
#     qualified_name = "<plugin>:<name>"  for skills and commands
#     qualified_name = "<name>"           for agents  (NOT namespaced)
#     description    = the frontmatter `description` for skills and agents,
#                      and for a command the FULL H1 text (everything after
#                      "# "), hard-truncated at COMMAND_DESCRIPTION_CHARS.
#
# The install total is `round(sum over components)` — the rounding happens
# once, at the end, which is why per-component halves cancel.
#
# HOW THIS WAS DERIVED, and why the previous three constants were wrong.
#
# The superseded model hard-coded SKILL_OVERHEAD_TOKENS=3, AGENT_OVERHEAD=1 and
# COMMAND_OVERHEAD=9 as "measured per-tier intercepts". They were an artifact of
# the probe METHOD: each tier was probed under a plugin named differently from
# this one ("tierrouters", 11 chars; "tiercommands", 12) rather than "sfskills"
# (8). Because skills and commands are billed as `<plugin>:<name>`, the extra
# plugin-name characters were absorbed into what looked like a per-component
# overhead — and that is exactly why the "agent overhead" came out near zero:
# agents are not namespaced, so their probe had no qualifier to misattribute.
# The same artifact produced the "unexplained 75-token sub-additivity" the docs
# used to report: 12 skills x 3 extra name chars x 0.25 = 9, plus 66 commands
# x 4 x 0.25 = 66, plus 0 for agents = 75 exactly. There is no sub-additivity.
#
# Re-derived 2026-08-07 on Claude Code 2.1.209 with nine controlled probes,
# each installed from a local-path marketplace into a throwaway
# CLAUDE_CONFIG_DIR outside this repository and read with `claude plugin
# details`. Every prediction below was written down BEFORE the probe ran:
#
#   probe                                                  predicted  measured
#   A1  plugin "sfskills"(8),     10 skills,  desc 100          280      280
#   A2  plugin "sfskillsabcd"(12),10 skills,  desc 100          290      290   <- +4 name chars x 10 x 0.25 = +10: skills ARE namespaced
#   A3  plugin "sfskills",        10 skills,  desc 300          780      780   <- slope exactly (780-280)/2000 = 0.25
#   B1  plugin "sfskills",        10 agents,  desc 100          258      258   <- bare name (namespaced would be 280)
#   B2  plugin "sfskillsabcd",    10 agents,  desc 100          258      258   <- UNCHANGED by plugin name: agents are NOT namespaced
#   C1  10 commands, H1 = "/cN — " + 50 chars                   170      170   <- full H1 billed (stripped subtitle would be 155)
#   C2  10 commands, H1 length 146                              280      280   <- truncated to 100
#   C3  10 commands, H1 length 100 exactly                      280      280   } cap is exactly
#   C4  10 commands, H1 length 101                              280      280   } 100 characters
#
#   R   replica of this plugin's real Tier-1 files (12 routers +
#       48 agent loaders + 66 commands, unmodified, plugin "sfskills")
#                                                            6117.8     6,118
#
# R is the acid test: 126 components with real, variable-length descriptions,
# predicted to a tenth of a token. Reproduce any row with the procedure in
# docs/installing-the-plugin.md, "Re-calibrating the token model" — and note
# that step 1 there is to name the probe plugin "sfskills", because getting
# that wrong is what produced the constants this block replaced.
TOKENS_PER_CHAR = 0.25
COMPONENT_INTERCEPT_TOKENS = 0.25
COMMAND_DESCRIPTION_CHARS = 100

# The ONE safety margin. The closed form above is exact on 2.1.209, so this is
# not a fudge factor covering a bad model — it is headroom against a future
# Claude Code changing its accounting slightly, and it is applied once, to the
# total, where it can be seen. `--measure` reports the exact prediction AND the
# padded figure, and gates on the padded one.
SAFETY_MARGIN_RATIO = 0.01

# The install this model is checked against. Reported by `--measure` so the
# estimate always travels with the measurement that validates it.
MEASURED_REFERENCE = {
    "claude_code_version": "2.1.209",
    "measured_on": "2026-08-07",
    "method": "nine probe plugins (parameter sweeps + a full-replica acid "
              "test) installed from a local-path marketplace into a throwaway "
              "CLAUDE_CONFIG_DIR outside the repo, read with "
              "`claude plugin details`",
    "model": "0.25 * (len(qualified_name) + len(description)) + 0.25 per "
             "component, summed then rounded once",
    "replica_predicted_tokens": 6117.8,
    "replica_measured_tokens": 6118,
    "note": "the replica carried the Tier-1 files as they stood BEFORE the "
            "2026-08-07 gloss/boilerplate rework; re-run the replica probe to "
            "re-validate against the current build",
}

BUDGET_TIER1_TOKENS = 6000
BUDGET_TIER1_RATIO = 0.05

# Max characters for a router `description:` value. Claude Code has no hard
# cap, but every character here is always-on cost: 0.25 tok/char, forever, in
# every session. Keyword lists earn their place or they come out.
MAX_DESCRIPTION_CHARS = 900

# ── Roster gloss budget ───────────────────────────────────────────────────────
#
# A gloss sits beside the skill id, which is ALREADY PRINTED on the same line.
# So a gloss that restates the name is dead weight, and the generator's job is
# to carry what the name cannot: the trigger vocabulary and the NOT-for
# redirect. The old rule ("first sentence, truncated to 120 chars") kept
# exactly the wrong third — measured over all 1,027 packages, 923 (89.9%) of
# its glosses were cut MID-WORD and 673 (65.5%) opened with "Use when"
# boilerplate that discriminates nothing.
#
# Registry descriptions are written in three parts, and the generator splits on
# them (see `split_description`):
#
#   lead      generic purpose, usually "Use when <gerund phrase>"   1,027 have
#   triggers  `Triggers:` / `Trigger keywords:` <quoted phrases>      571 have
#   NOT-for   `NOT for <X> - use <Y> for that.`                       995 have
#
# Allocation order is PRIORITY order, and the lead is paid LAST, out of
# whatever is left. Measured over all 1,027 packages at MAX_GLOSS_CHARS=220,
# paying the lead first vs last:
#
#   lead floor   full trigger list kept   cross-reference kept   admin roster
#   90 chars                       25%                    38%        68.3 KB
#   60 chars                       54%                    41%        68.4 KB
#   0  (last)                      54%                    67%        67.3 KB
#
# Paying the lead last is better on every axis at the same cost, which is the
# measurement behind "the name is already printed".
#
# COST OF THE LENGTH CHOICE. Rosters are Tier 2 — read on demand, one domain at
# a time — so they do not touch the 6,000-token always-on budget. The cost that
# matters is reading ONE roster, and the worst case is `admin` at 253 entries.
# Measured, per-domain-file, over the full corpus:
#
#   MAX_GLOSS_CHARS   admin roster   ~tok to read it   full triggers   xref kept
#   120 (the old rule)     43.8 KB           11.2k            n/a           n/a
#   180                    57.0 KB           14.6k            54%           55%
#   220  (chosen)          67.3 KB           17.2k            54%           67%
#   240                    71.8 KB           18.4k            54%           79%
#
# 220 is where the two measured routing failures both resolve: the literal
# trigger 'why can user see too much' survives in admin/sharing-and-visibility
# (it did not at 180), and data/large-scale-deduplication keeps its
# "(use admin/duplicate-management)" redirect. Past 220 the curve is still
# rising but no longer buys a known failure, so it stops here.
MAX_GLOSS_CHARS = 220
# Sub-caps, so no one part can starve the others. TRIGGER_CAP is what makes
# `full triggers` plateau at 54% — lists longer than this clip at a comma, on
# purpose. NOTFOR_CAP costs 4 points of cross-reference retention and buys 11
# points of lead retention, which matters because for the 456 packages with no
# trigger line the lead is the only subject matter there is.
GLOSS_TRIGGER_CAP = 150
GLOSS_NOTFOR_CAP = 140
GLOSS_LEAD_CAP = 150
# A lead shorter than this is a stub, not a phrase ("designing …."). Below the
# threshold the lead is dropped outright rather than shipped as noise.
GLOSS_LEAD_MIN = 40
# Visible, unambiguous, one character. Truncation is always on a word, comma or
# whole-clause boundary — never mid-word.
GLOSS_ELLIPSIS = "…"

# Roster files are on-invoke cost only, but a runaway roster is still a bill
# someone pays. Sized to leave headroom above the current worst case
# (`admin`, 253 packages, ~67 KB) without leaving room for another doubling.
MAX_ROSTER_BYTES = 80 * 1024

DOMAIN_ORDER = [
    "admin",
    "agentforce",
    "apex",
    "architect",
    "data",
    "devops",
    "flow",
    "integration",
    "lwc",
    "omnistudio",
    "security",
]

# ── Curated seed table — THE ONLY HAND-AUTHORED INPUT ─────────────────────────
#
# Everything else (domain list, skill counts, rosters, agent set, manifests)
# is derived from registry/skills.json, agents/*/AGENT.md and commands/*.md.
#
# Every skill id below is resolved against the registry at build time, so a
# rename or deletion fails the build loudly instead of shipping a dead path.
# `python3 scripts/build_plugin.py --verify-seeds` is the standalone gate.

# domain -> (one-line scope, trigger vocabulary)
#
# THESE LISTS ARE A PROMISE ABOUT WHAT THE ROSTER CONTAINS. A router that
# advertises a keyword whose packages live in a different domain sends the
# reader to a roster that cannot answer them, and the reader has no way to
# know that — they scan the wrong 60 KB and conclude the library has no
# coverage. Three such mis-routes were measured on 2026-08-07 and all three
# are fixed below by naming the SPLIT in both descriptions rather than by
# moving skills (moving them would churn 1,027 paths for no retrieval gain):
#
#   concept        counted in the registry              how it is split now
#   sharing        admin 7 / security 4 / data 4        admin = design the model
#                  (admin/sharing-and-visibility is     security = troubleshoot
#                   the design-level package)                     a live denial
#   REST/callouts  apex 17 / integration 8 (callout)    integration = inbound
#                  apex/callouts-and-http-integrations  apex = outbound
#                  is the outbound package
#   duplicates     data 11 / admin 4                    admin = prevention
#                  (admin/duplicate-management)         data = cleanup at volume
#   Bulk API       data 13 / integration 11             data = the load/extract
#                                                       integration = the API
#   governor lim.  apex 5 / flow 2                      each names its own
#
# Counts reproduce with a case-insensitive search of registry/skills.json over
# name + description. Re-run it before editing a list: the honest keyword list
# is the one that matches where the packages actually are.
DOMAIN_META: dict[str, tuple[str, str]] = {
    "admin": (
        "Declarative Salesforce configuration: objects, fields, record types, "
        "page layouts, permission sets, reports, the record-access model "
        "(OWD, role hierarchy, sharing rules), and the requirements work that "
        "precedes them.",
        "custom object, custom field, picklist, record type, page layout, "
        "permission set, profile, validation rule, report, dashboard, queue, "
        "approval process, user setup, sharing rule, org-wide default, OWD, "
        "role hierarchy, record access, record visibility, who can see this "
        "record, duplicate rule, matching rule, duplicate prevention, "
        "clean up duplicates, merge governance, Spring release, seasonal "
        "release, Release Updates, Sandbox Preview",
    ),
    "agentforce": (
        "Agentforce and Einstein: agents, topics, actions, prompt templates, "
        "grounding, guardrails, evaluation and production readiness.",
        "Agentforce, agent topic, agent action, prompt builder, Einstein, "
        "Trust Layer, grounding, RAG, guardrails, agent evaluation, "
        "prompt injection",
    ),
    "apex": (
        "Apex and SOQL: triggers, Apex governor limits, async processing, "
        "OUTBOUND HTTP callouts, security enforcement, and test patterns. "
        "Owns calling an external API FROM Salesforce; "
        "salesforce-integration owns inbound. Generic nightly scheduling "
        "without naming code belongs to salesforce-flow. Codebase security "
        "review belongs to salesforce-security. NOT for SOSL — use "
        "salesforce-data.",
        "Apex, trigger, SOQL, Apex governor limit, batch, queueable, "
        "@future, schedulable, test class, CPU time, heap, with sharing, "
        "StripInaccessible, callout, HTTP callout, HttpRequest, call an "
        "external API, consume a REST API from Apex, Named Credential in "
        "Apex, HttpCalloutMock, Apex REST service",
    ),
    "architect": (
        "Solution and platform architecture: multi-org strategy, scalability "
        "limits, licensing, Well-Architected reviews and architecture "
        "decision records.",
        "architecture, solution design, ADR, Well-Architected, scalability, "
        "large data volume, multi-org, licensing, tenant isolation, "
        "HA/DR, technical debt",
    ),
    "data": (
        "Data model, data movement and data quality: migrations, bulk loads, "
        "query optimisation, deduplicating at volume, archival. Ordinary-volume "
        "duplicate cleanup and prevention use salesforce-admin; come here for "
        "hundreds-of-thousands+ dedup or third-party tools. LDV architecture "
        "uses salesforce-architect.",
        "data model, data migration, data load, Data Loader, Bulk API, "
        "external id, deduplication at volume, archival, SOSL, cross-object "
        "search, sandbox seed data, SandboxPostCopy, native Data Seeding",
    ),
    "devops": (
        "Salesforce delivery: source tracking, packaging, branching, CI/CD "
        "pipelines, environment strategy and deployment troubleshooting.",
        "deploy, deployment, sfdx, sf CLI, scratch org, sandbox, unlocked "
        "package, change set, CI/CD, GitHub Actions, release, rollback, "
        "source tracking",
    ),
    "flow": (
        "Flow Builder: record-triggered, screen, scheduled and orchestration "
        "flows, bulkification, fault handling, limits, testing. \"My flow\" "
        "belongs here even when salesforce-apex also names the limit. "
        "Nightly scheduling without naming code defaults here; apex takes it "
        "when code/class/Apex is named. Flow-vs-Apex choice before anything "
        "is built: admin/process-automation-selection.",
        "Flow, Flow Builder, record-triggered flow, screen flow, scheduled "
        "flow, subflow, fault path, flow element, orchestration, "
        "Process Builder migration, Workflow Rule migration, flow limit, "
        "flow hitting SOQL limit, too many SOQL queries in a flow, flow "
        "bulkification, Get Records performance",
    ),
    "integration": (
        "INBOUND integration and the API surface itself: the Salesforce REST "
        "and SOAP APIs, Bulk API 2.0 jobs, Platform Events, CDC, Pub/Sub, "
        "Named Credentials and middleware. For calling OUT to someone else's "
        "API from Apex, use salesforce-apex instead.",
        "integration, Salesforce REST API, composite API, SOAP API, Bulk API "
        "2.0 job, Platform Event, Change Data Capture, Pub/Sub, inbound "
        "webhook, Named Credential, OAuth, connected app, MuleSoft, "
        "Salesforce Connect, external system calling Salesforce",
    ),
    "lwc": (
        "Lightning Web Components: reactivity, wire adapters, component "
        "communication, accessibility, performance, security and Jest "
        "testing.",
        "LWC, Lightning Web Component, wire, @api, @track, lightning-record-"
        "form, shadow DOM, Jest, Lightning Message Service, Aura migration, "
        "Lightning page",
    ),
    "omnistudio": (
        "OmniStudio: OmniScripts, FlexCards, DataRaptors, Integration "
        "Procedures, Business Rules Engine and DataPack deployment.",
        "OmniStudio, OmniScript, FlexCard, DataRaptor, Integration "
        "Procedure, Business Rules Engine, calculation procedure, DataPack, "
        "Vlocity",
    ),
    "security": (
        "Platform security and compliance: org hardening, encryption, session "
        "policy, MFA, monitoring, incident response, and TROUBLESHOOTING a "
        "specific record-access denial. Designing the sharing model itself "
        "(OWD, role hierarchy, sharing rules) is salesforce-admin.",
        "security, org hardening, Shield, platform encryption, field audit "
        "trail, MFA, SSO, SAML, session policy, guest user, event "
        "monitoring, GDPR, XSS, injection, why can this one user see this "
        "record, Apex managed sharing, sharing recalculation",
    ),
}

# domain -> [(skill id, why it is a good entry point)]  — 5 to 10 per domain.
FEATURED_SKILLS: dict[str, list[tuple[str, str]]] = {
    "admin": [
        ("admin/object-creation-and-design", "start here for any new sObject — naming, relationships, and the fields you will regret later"),
        ("admin/custom-field-creation", "field types, FLS, and the ones that cannot be changed after data lands"),
        ("admin/validation-rules", "declarative enforcement, and where a validation rule fights automation"),
        ("admin/record-types-and-page-layouts", "record type strategy before it multiplies out of control"),
        ("admin/permission-set-architecture", "the permission-set-first access model that replaces profiles"),
        ("admin/user-management", "user lifecycle, licences, freeze vs deactivate, and integration users"),
        ("admin/duplicate-management", "matching rules and duplicate rules, including the person-account edge cases"),
        ("admin/reports-and-dashboards-fundamentals", "report types, folder sharing, and why a report returns the wrong rows"),
    ],
    "agentforce": [
        ("agentforce/agentforce-agent-creation", "the end-to-end shape of an Agentforce agent before you write an action"),
        ("agentforce/agent-topic-design", "topic scoping and instructions — the single biggest driver of agent quality"),
        ("agentforce/agent-actions", "action design, slot filling, and what belongs in Apex vs Flow"),
        ("agentforce/agentforce-guardrails", "keeping an agent inside its lane, with refusal behaviour"),
        ("agentforce/prompt-builder-templates", "prompt templates, grounding fields, and versioning them safely"),
        ("agentforce/einstein-trust-layer", "masking, zero-retention, and the audit trail your security team will ask for"),
        ("agentforce/agentforce-testing-strategy", "how to test a non-deterministic agent without hand-checking transcripts"),
        ("agentforce/agentforce-production-readiness-checklist", "the pre-launch gate for anything customer-facing"),
    ],
    "apex": [
        ("apex/trigger-framework", "one trigger per object, handler dispatch, and recursion control"),
        ("apex/governor-limits", "the limit table and which ones actually bite in practice"),
        ("apex/soql-fundamentals", "selectivity, relationship queries, and queries inside loops"),
        ("apex/apex-security-patterns", "CRUD/FLS enforcement, sharing keywords, and injection-safe dynamic SOQL"),
        ("apex/batch-apex-patterns", "Batchable structure, chaining, scope sizing and failure recovery"),
        ("apex/apex-queueable-patterns", "the default async choice, with chaining depth and callout rules"),
        ("apex/test-data-factory-patterns", "a reusable factory so bulk tests are not copy-pasted record builders"),
        ("apex/test-class-standards", "assertions, bulk cases, negative paths, and what coverage does not prove"),
    ],
    "architect": [
        ("architect/solution-design-patterns", "the pattern catalogue to check before inventing a design"),
        ("architect/well-architected-review", "running a Salesforce Well-Architected assessment against a real org"),
        ("architect/architecture-decision-records", "capturing the decision and its alternatives so it survives the team"),
        ("architect/large-data-volume-architecture", "skinny tables, custom indexes, sharing recalculation and LDV design"),
        ("architect/limits-and-scalability-planning", "org-level limits that constrain a design before code does"),
        ("architect/integration-framework-design", "the org-wide integration layer, not a single point-to-point callout"),
        ("architect/security-architecture-review", "the access model as an architecture concern rather than a config task"),
        ("architect/multi-org-strategy", "when a second org is right and what it costs forever after"),
    ],
    "data": [
        ("data/data-model-design-patterns", "relationship choices, junctions, and normalisation on a multi-tenant platform"),
        ("data/data-migration-planning", "sequencing, dependencies, and the dry runs that keep a cutover honest"),
        ("data/bulk-api-and-large-data-loads", "batch sizing, parallel vs serial, and lock contention during a load"),
        ("data/external-id-strategy", "upsert keys, idempotency, and cross-system record identity"),
        ("data/soql-query-optimization", "selective filters, index usage, and reading the query plan"),
        ("data/data-quality-and-governance", "ownership, standards, and the metrics that keep quality from decaying"),
        ("data/large-scale-deduplication", "deduplicating at volume without a merge storm"),
        ("data/data-archival-strategies", "Big Objects, off-platform archives, and storage-limit relief"),
    ],
    "devops": [
        ("devops/salesforce-dx-project-structure", "project layout, sfdx-project.json, and package directories"),
        ("devops/environment-strategy", "sandbox tiers, scratch orgs, and what each environment is allowed to prove"),
        ("devops/git-branching-for-salesforce", "a branching model that survives metadata merge conflicts"),
        ("devops/release-management", "release trains, cutover windows, and change control"),
        ("devops/pre-deployment-checklist", "the go/no-go gate before a production deploy"),
        ("devops/deployment-error-diagnosis", "decoding the deploy failures that do not say what is wrong"),
        ("devops/unlocked-package-development", "packaging as the modularisation strategy, with dependency ordering"),
        ("devops/github-actions-for-salesforce", "a working CI pipeline: auth, validate, test, deploy"),
    ],
    "flow": [
        ("flow/record-triggered-flow-patterns", "before-save vs after-save, entry criteria, and re-entry"),
        ("flow/flow-bulkification", "the Flow equivalent of queries-in-loops, and how to see it in the debug log"),
        ("flow/fault-handling", "fault paths as a design requirement, not an afterthought"),
        ("flow/screen-flows", "screen composition, validation, and reactive components"),
        ("flow/scheduled-flows", "schedule-triggered flows, batch limits, and the scheduled-path alternative"),
        ("flow/subflows-and-reusability", "decomposing a flow before it becomes unmaintainable"),
        ("flow/flow-testing", "Flow tests, coverage expectations, and what they cannot assert"),
        ("flow/flow-performance-optimization", "Get Records tuning, loop cost, and CPU time inside a flow"),
    ],
    "integration": [
        ("integration/rest-api-patterns", "the default synchronous inbound/outbound shape and its limits"),
        ("integration/bulk-api-2-patterns", "high-volume loads and extracts without holding a transaction open"),
        ("integration/named-credentials-setup", "credentials, auth providers, and never putting a secret in Apex"),
        ("integration/oauth-flows-and-connected-apps", "picking the right OAuth flow for the right client"),
        ("integration/platform-events-integration", "publish/subscribe decoupling, delivery guarantees and replay"),
        ("integration/pub-sub-api-patterns", "the gRPC Pub/Sub API for events and Change Data Capture"),
        ("integration/error-handling-in-integrations", "failure taxonomy, dead letters, and what the caller sees"),
        ("integration/retry-and-backoff-patterns", "idempotent retries that do not amplify an outage"),
    ],
    "lwc": [
        ("lwc/component-communication", "parent/child, events, and when to reach for Lightning Message Service"),
        ("lwc/wire-service-patterns", "@wire, reactive parameters, and refreshing cached data"),
        ("lwc/lifecycle-hooks", "connected/rendered/disconnected and the work that belongs in each"),
        ("lwc/lwc-performance", "render cost, wasted reactivity, and the LWC side of a slow page"),
        ("lwc/lwc-security", "Lightning Web Security, sanitisation, and safe use of API data"),
        ("lwc/lwc-accessibility", "keyboard, focus and screen-reader behaviour as acceptance criteria"),
        ("lwc/lwc-testing", "Jest setup, mocking wire adapters, and asserting rendered output"),
        ("lwc/lwc-error-boundaries", "containing a component failure instead of blanking the page"),
    ],
    "omnistudio": [
        ("omnistudio/omniscript-design-patterns", "OmniScript structure, steps, and where the logic should live"),
        ("omnistudio/integration-procedures", "server-side orchestration and when it replaces an OmniScript action"),
        ("omnistudio/dataraptor-patterns", "Extract, Transform and Load DataRaptors, and their field mappings"),
        ("omnistudio/flexcard-design-patterns", "FlexCard composition, state, and data sources"),
        ("omnistudio/business-rules-engine", "expression sets and decision matrices instead of hard-coded rules"),
        ("omnistudio/omnistudio-performance", "caching, remote actions, and the OmniStudio-specific slow paths"),
        ("omnistudio/omnistudio-deployment-datapacks", "DataPack export/import and the CI story for OmniStudio metadata"),
        ("omnistudio/omnistudio-vs-flow-decision", "when OmniStudio is the wrong answer and Flow is the right one"),
    ],
    "security": [
        ("security/org-hardening-and-baseline-config", "the baseline every org should already meet"),
        ("security/permission-set-groups-and-muting", "composing access with groups, and muting the over-grant"),
        ("security/record-access-troubleshooting", "why this user can (or cannot) see this record"),
        ("security/platform-encryption", "Shield Platform Encryption and everything it breaks"),
        ("security/mfa-enforcement-patterns", "MFA rollout without locking out integration users"),
        ("security/xss-and-injection-prevention", "output encoding, SOQL injection, and unsafe HTML in components"),
        ("security/secure-coding-review-checklist", "the review gate for Apex, LWC and callouts"),
        ("security/event-monitoring", "Event Monitoring, Shield log retention, and detecting misuse"),
    ],
}

# Top-level router entry points — at least one per domain.
ENTRY_SKILLS: list[tuple[str, str]] = [
    ("admin/object-creation-and-design", "designing a new object or reworking an existing one"),
    ("admin/permission-set-architecture", "who can see and do what"),
    ("apex/trigger-framework", "any trigger work at all"),
    ("apex/governor-limits", "anything that says \"too many\" or \"exceeded\""),
    ("apex/soql-fundamentals", "query correctness and selectivity"),
    ("flow/record-triggered-flow-patterns", "the most common declarative automation"),
    ("lwc/component-communication", "the first thing an LWC build gets wrong"),
    ("data/data-model-design-patterns", "relationships and normalisation"),
    ("integration/rest-api-patterns", "talking to or from an external system"),
    ("security/org-hardening-and-baseline-config", "the org security baseline"),
    ("architect/well-architected-review", "assessing an org against Salesforce Well-Architected"),
    ("devops/salesforce-dx-project-structure", "getting metadata into source control"),
    ("agentforce/agentforce-agent-creation", "building an Agentforce agent"),
    ("omnistudio/omniscript-design-patterns", "OmniStudio guided flows"),
]

# domain -> [(decision-tree filename, why this domain reads it)]
DOMAIN_TREES: dict[str, list[tuple[str, str]]] = {
    "admin": [
        ("automation-selection.md", "read before choosing a declarative automation over Apex"),
        ("sharing-selection.md", "read before designing an object's access model"),
    ],
    "agentforce": [
        ("agentforce-capability-selector.md", "Agentforce vs Prompt Builder vs Next Best Action vs Model Builder"),
        ("automation-selection.md", "read when an agent action could equally be a Flow or Apex"),
    ],
    "apex": [
        ("automation-selection.md", "read before writing Apex that a Flow could do"),
        ("async-selection.md", "@future vs Queueable vs Batch vs Schedulable vs Platform Events"),
        ("performance-tuning.md", "read on any CPU, heap, SOQL or limit symptom"),
    ],
    "architect": [
        ("automation-selection.md", "the platform's automation routing, one layer above any skill"),
        ("integration-pattern-selection.md", "REST vs Bulk vs events vs Connect vs MuleSoft"),
        ("sharing-selection.md", "the access-model decision at design time"),
        ("performance-tuning.md", "where the time goes, before proposing a redesign"),
    ],
    "data": [
        ("integration-pattern-selection.md", "read before moving data in or out at volume"),
        ("performance-tuning.md", "SOQL, indexing, sharing recalculation and LDV symptoms"),
        ("sharing-selection.md", "read when a data model change moves record visibility"),
    ],
    "devops": [
        ("automation-selection.md", "no devops-specific tree exists yet; the Flow-vs-Apex choice drives deployment ordering and packaging boundaries"),
    ],
    "flow": [
        ("automation-selection.md", "read FIRST — it decides whether Flow is the right tool at all"),
        ("flow-pattern-selector.md", "read SECOND — which kind of Flow to build"),
        ("async-selection.md", "read when the work should leave the transaction"),
    ],
    "integration": [
        ("integration-pattern-selection.md", "the primary tree for this domain"),
        ("async-selection.md", "read when a callout has to move off the synchronous path"),
    ],
    "lwc": [
        ("performance-tuning.md", "the LWC render branch, for any \"the page is slow\" report"),
    ],
    "omnistudio": [
        ("automation-selection.md", "read before assuming OmniStudio is the answer"),
        ("performance-tuning.md", "the OmniStudio branch, for cache and remote-action symptoms"),
    ],
    "security": [
        ("sharing-selection.md", "OWD vs role hierarchy vs sharing rules vs manual vs Apex managed sharing"),
    ],
}

# domain -> a representative file under templates/<domain>/ worth naming.
DOMAIN_TEMPLATE_HINTS: dict[str, list[str]] = {
    "admin": ["naming-conventions.md", "permission-set-patterns.md", "validation-rule-patterns.md"],
    "agentforce": ["AgentActionSkeleton.cls", "AgentTopic_Template.md", "AgentEval_Fixture.md"],
    "apex": ["TriggerHandler.cls", "SecurityUtils.cls", "tests/TestDataFactory.cls"],
    "flow": ["RecordTriggered_Skeleton.flow-meta.xml", "FaultPath_Template.md", "Subflow_Pattern.md"],
    "lwc": ["jest.config.js", "component-skeleton", "patterns"],
}


# ── Input loading ─────────────────────────────────────────────────────────────

def load_registry() -> dict:
    """Load registry/skills.json. This is the canonical Tier-2 inventory."""
    if not REGISTRY_FILE.exists():
        raise SystemExit(
            f"ERROR: {REGISTRY_FILE.relative_to(REPO_ROOT)} does not exist — "
            "run `python3 scripts/skill_sync.py --all` first."
        )
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> dict:
    """Parse the flat scalar keys of a YAML frontmatter block. Stdlib only.

    Only the keys this generator needs (``id``, ``class``, ``status``) are
    flat scalars, so a full YAML parser would be overkill and would add a
    dependency this repo does not carry.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    meta: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if not line or line.startswith((" ", "\t", "#")):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip().strip('"').strip("'")
        if value:
            meta[key.strip()] = value
    return meta


def command_index() -> list[tuple[str, str]]:
    """[(stem, first H1 heading)] for every commands/*.md, sorted by stem."""
    entries = []
    for path in sorted(COMMANDS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        heading = match.group(1).strip() if match else path.stem.replace("-", " ")
        entries.append((path.stem, heading))
    return entries


def _command_title(stem: str, heading: str) -> str:
    """Strip the ``/slug — `` prefix off a command H1 to get its title.

    ``# /refactor-apex — Refactor an Apex class`` -> ``Refactor an Apex class``.
    A handful of commands (``/audit-router``) have no subtitle; those fall
    back to a derived phrase so no wrapper ships an empty description.

    The separator must be a dash *surrounded by whitespace*. An earlier
    ``^/\\S+\\s*[—–-]\\s*(.+)$`` allowed a bare hyphen with no spaces, and
    since ``\\S+`` backtracks, ``# /audit-router`` matched with ``/audit`` as
    the slug and ``router`` as the title. Two agents therefore shipped with the
    description "router." — a routing signal of nothing at all. Requiring the
    surrounding whitespace makes the no-subtitle case fall through to the
    derived phrase, which is what it was always supposed to do.
    """
    match = re.match(r"^/\S+\s+[—–-]\s+(.+)$", heading)
    if match:
        return match.group(1).strip()
    return UNTITLED_COMMAND.format(stem=stem)


# What `_command_title` returns when a command H1 carries no subtitle at all.
# Two commands are in that state today (`/audit-router`,
# `/automation-migration-router`); `commands/*.md` is hand-authored, so the
# generator has nothing better to say and must not pretend otherwise. Callers
# that would read awkwardly with a placeholder check for it — see
# `render_subagent`.
UNTITLED_COMMAND = "Run the SfSkills {stem} run-time agent"


def _is_untitled(title: str) -> bool:
    return title.startswith("Run the SfSkills ")


DOMAIN_REF_RE = re.compile(r"\b(" + "|".join(DOMAIN_ORDER) + r")/[a-z0-9][a-z0-9-]*")


def shipped_agents_on_disk() -> list[str]:
    """Agent names the INSTALLED plugin exposes given the WORKING TREE as it
    stands right now, sorted.

    Not the repo's roster — the roster is what `runtime_agents()` returns and
    it is what the plugin *would* ship if the loaders were in the right place.
    This is the subset Claude Code's default scan can see: flat ``*.md``
    directly under ``<plugin root>/agents/``. See ``AGENT_LOADING_MATRIX``.

    Keeping the two apart is the whole point, and it is why this reads the
    filesystem rather than the roster: it is the ``--audit-install`` gate's
    view, so "you edited the roster but never re-ran the build" shows up as a
    gap instead of being papered over.

    The manifest renderers deliberately do NOT call this — they use
    ``shipped_agents_in_build()`` over the output map, because a manifest
    rendered from pre-build disk state would describe the previous build and
    ``--check`` would report drift on the very next run.
    """
    base = REPO_ROOT / PLUGIN_AGENT_SCAN_DIR
    if not base.is_dir():
        return []
    return sorted(p.stem for p in base.glob("*.md"))


def shipped_agents_in_build(out: dict[Path, str]) -> list[str]:
    """Same question as ``shipped_agents_on_disk``, asked of the artifacts
    THIS build emits: flat ``*.md`` directly under ``agents/`` in the output
    map, sorted.

    Derived from the output map rather than from ``runtime_agents()`` on
    purpose. If the loader emit is ever dropped, this returns ``[]`` and the
    manifest description loses its agent clause automatically — the manifest
    still cannot advertise a component the plugin does not ship.
    """
    return sorted(
        rel.stem for rel in out
        if rel.parent == PLUGIN_AGENT_SCAN_DIR and rel.suffix == ".md"
    )


def runtime_agents() -> list[dict]:
    """Every ``agents/<id>/AGENT.md`` with class runtime and a live status.

    The agent's domain is DERIVED, not curated: AGENT.md carries no domain
    field, so we take the modal domain across every ``<domain>/<slug>`` skill
    reference in the file (ties broken alphabetically). The wrapping command
    is the one whose stem equals the agent id, else the first by sort order.
    """
    commands = dict(command_index())
    by_agent: dict[str, list[str]] = {}
    for stem in sorted(commands):
        text = (COMMANDS_DIR / f"{stem}.md").read_text(encoding="utf-8")
        for agent_id in sorted(set(re.findall(r"agents/([a-z0-9][a-z0-9-]*)/AGENT\.md", text))):
            by_agent.setdefault(agent_id, []).append(stem)

    agents = []
    for agent_dir in sorted(AGENTS_DIR.iterdir()):
        agent_md = agent_dir / "AGENT.md"
        if not agent_md.exists():
            continue
        meta = parse_frontmatter(agent_md)
        if meta.get("class") != "runtime" or meta.get("status") == "deprecated":
            continue
        agent_id = meta.get("id") or agent_dir.name

        counts: dict[str, int] = {}
        for domain in DOMAIN_REF_RE.findall(agent_md.read_text(encoding="utf-8")):
            counts[domain] = counts.get(domain, 0) + 1
        domain = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if counts else ""

        stems = by_agent.get(agent_id, [])
        stem = agent_id if agent_id in stems else (stems[0] if stems else "")
        agents.append({
            "id": agent_id,
            "dir": agent_dir.name,
            "domain": domain,
            "command": stem,
            "title": _command_title(stem, commands[stem]) if stem else
                     f"Run the SfSkills {agent_id} run-time agent",
        })
    return sorted(agents, key=lambda a: a["id"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def always_on_tokens(qualified_name: str, description: str) -> float:
    """Claude Code's always-on charge for ONE component, in tokens.

    The closed form derived at the top of this file. Returns a float on
    purpose: the install total is the sum rounded ONCE, so rounding here would
    accumulate error across 126 components.
    """
    return (
        TOKENS_PER_CHAR * (len(qualified_name) + len(description))
        + COMPONENT_INTERCEPT_TOKENS
    )


def qualified_skill_name(name: str) -> str:
    """Skills and commands are billed as ``<plugin>:<name>``."""
    return f"{PLUGIN_NAME}:{name}"


# ── Roster gloss construction ─────────────────────────────────────────────────

# "Use when …" / "Use this skill when …" — 673 of 1,027 descriptions open with
# one of these and none of them discriminates anything. Stripped, not kept.
_LEAD_BOILERPLATE_RE = re.compile(
    r"^(?:Use\s+this\s+skill\s+(?:when|for)|Use\s+this\s+when|Use\s+when|Use\s+for)\s+",
    re.IGNORECASE,
)
# `Triggers:` / `Trigger keywords:` / `Trigger phrases:` — the vocabulary block.
_TRIGGER_RE = re.compile(
    r"\b(?:Trigger\s+keywords?|Trigger\s+phrases?|Triggers?)\s*:\s*", re.IGNORECASE
)
# A NOT-for clause, only where it STARTS a sentence — so an incidental "… is
# NOT for production" inside prose does not split the description.
_NOTFOR_RE = re.compile(r"(?:^|(?<=[.;]\s))NOT\s+for\b")


def split_description(text: str) -> tuple[str, str, str]:
    """Split a registry description into (lead, triggers, not-for).

    Any part may be empty. The lead has its "Use when" boilerplate stripped and
    its trailing punctuation removed, so the caller can re-punctuate.
    """
    flat = " ".join(text.split())
    match = _NOTFOR_RE.search(flat)
    notfor = flat[match.start():].strip() if match else ""
    head = (flat[: match.start()] if match else flat).strip()

    trigger_match = _TRIGGER_RE.search(head)
    if trigger_match:
        lead = head[: trigger_match.start()]
        triggers = head[trigger_match.end():]
    else:
        lead, triggers = head, ""
    lead = _LEAD_BOILERPLATE_RE.sub("", lead.strip())
    return lead.strip(" .;,"), triggers.strip(" .;,"), notfor.strip()


def _clip_words(text: str, limit: int) -> str:
    """Truncate at a WORD boundary, marked. Never mid-word."""
    if len(text) <= limit:
        return text
    if limit < 12:
        return ""
    cut = text[: limit - 2].rsplit(" ", 1)[0].rstrip(" ,;:-—")
    return f"{cut} {GLOSS_ELLIPSIS}" if cut else ""


def _clip_keywords(text: str, limit: int) -> str:
    """Truncate a comma-separated keyword list at a KEYWORD boundary, marked.

    Dropping whole trailing keywords keeps every surviving trigger phrase
    intact and matchable, which a character cut would not.
    """
    if len(text) <= limit:
        return text
    if limit < 12:
        return ""
    kept: list[str] = []
    used = 0
    for part in (p for p in re.split(r",\s*", text) if p):
        cost = len(part) + (2 if kept else 0)
        if used + cost + 2 > limit:
            break
        kept.append(part)
        used += cost
    if not kept:
        return _clip_words(text, limit)
    return ", ".join(kept) + f", {GLOSS_ELLIPSIS}"


# The destination half of a redirect: "(use admin/duplicate-management)",
# "- use data/soql-query-optimization", "use the async-selection decision tree".
# This is the single highest-value token on a roster line, because it is the
# only part that tells a reader WHERE TO GO instead.
_REDIRECT_TARGET_RE = re.compile(
    r"[-—–(]?\s*use\s+(?:the\s+)?(?:`?[a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*`?"
    r"|[a-z][a-z0-9-]*\s+decision\s+tree)\)?",
    re.IGNORECASE,
)


def _redirect_target(clause: str) -> str:
    """The trailing `use <target>` of a NOT-for clause, normalised, else ''."""
    matches = list(_REDIRECT_TARGET_RE.finditer(clause))
    if not matches:
        return ""
    return matches[-1].group(0).strip(" -—–()").rstrip(".")


def _clip_clauses(text: str, limit: int) -> str:
    """Truncate a run of `NOT for …` clauses at a WHOLE-CLAUSE boundary.

    A half-clause redirect ("NOT for duplicate rule config (use admin/dup…")
    is worse than none: it names a destination the reader cannot resolve. So
    clauses are kept whole or dropped whole.

    When even the FIRST clause overflows, the word-clip fallback used to cut
    the clause's tail — which is exactly where the `use <target>` lives. On the
    1,027 shipped glosses that destroyed the redirect target on 55% of the
    lines that had one, in a file whose own header tells the reader that
    "a `NOT for X - use Y` clause is the most useful thing on the line". So the
    target is now re-attached after clipping: the reader loses some of the
    subject list, never the destination.
    """
    if len(text) <= limit:
        return text
    if limit < 20:
        return ""
    bounds = [m.start() for m in _NOTFOR_RE.finditer(text)] + [len(text)]
    clauses = [text[bounds[i]: bounds[i + 1]].strip() for i in range(len(bounds) - 1)]
    kept: list[str] = []
    used = 0
    for clause in clauses:
        cost = len(clause) + (1 if kept else 0)
        if used + cost > limit:
            break
        kept.append(clause)
        used += cost
    if kept:
        return " ".join(kept)

    # Even the first clause overflows. Word-clip its subject, but keep the
    # destination — dropping "use X" is what makes a redirect unresolvable.
    first = clauses[0]
    target = _redirect_target(first)
    if not target:
        return _clip_words(first, limit)
    tail = f" {GLOSS_ELLIPSIS} {target}"
    head = _clip_words(first, max(0, limit - len(tail)))
    if not head:
        # No room for both; the destination alone still routes the reader.
        return target if len(target) <= limit else _clip_words(first, limit)
    return head[: -len(f" {GLOSS_ELLIPSIS}")].rstrip(" ,;:-—") + tail if head.endswith(GLOSS_ELLIPSIS) else head + tail


def build_gloss(description: str, limit: int = MAX_GLOSS_CHARS) -> str:
    """The one-line roster gloss for a skill package.

    Priority order — triggers, then the NOT-for redirect, then the lead out of
    whatever is left. See the MAX_GLOSS_CHARS block for the measurements behind
    that order and behind `limit`.
    """
    lead, triggers, notfor = split_description(description)
    remaining = limit

    trigger_part = ""
    if triggers:
        # 11 = len("Triggers: ") + the joining space.
        trigger_part = _clip_keywords(
            triggers, min(GLOSS_TRIGGER_CAP, max(0, remaining - 11))
        )
        if trigger_part:
            remaining -= len(trigger_part) + 11

    notfor_part = ""
    if notfor:
        notfor_part = _clip_clauses(
            notfor, min(GLOSS_NOTFOR_CAP, max(0, remaining - 1))
        )
        if notfor_part:
            remaining -= len(notfor_part) + 1

    lead_part = ""
    if lead and remaining - 1 >= GLOSS_LEAD_MIN:
        lead_part = _clip_words(lead, min(GLOSS_LEAD_CAP, remaining - 1))

    parts = []
    if lead_part:
        parts.append(lead_part.rstrip(" .") + ".")
    if trigger_part:
        parts.append("Triggers: " + trigger_part.rstrip(" .") + ".")
    if notfor_part:
        parts.append(notfor_part)
    return " ".join(parts)


def yaml_quote(value: str) -> str:
    """Double-quoted YAML scalar. Descriptions contain colons and commas, so
    they must be quoted; ``name`` is never quoted because Claude Code compares
    it to the directory name."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def lookup_block(domain: str | None) -> list[str]:
    """The three-mechanism lookup instructions every router carries.

    Ordered by reliability on a fresh install, not by speed. ``vector_index/``
    is gitignored (chunks.jsonl, lexical.sqlite and embeddings.jsonl total
    ~800 MB), so a GitHub-sourced install has no search index and mechanism 3
    fails until it is rebuilt. The shipped roster always works.
    """
    flag = f" --domain {domain}" if domain else ""
    if domain:
        roster = [
            "**1. The shipped roster (always works, no setup).**",
            "Read `references/skill-index.md` next to this file. It lists every",
            f"`{domain}` skill package with a one-line gloss, generated from",
            "`registry/skills.json`. Scan it and pick by name.",
        ]
    else:
        roster = [
            "**1. The shipped rosters (always work, no setup).**",
            "Hand off to the domain router below; each one ships a complete",
            "`references/skill-index.md` roster of its packages, generated from",
            "`registry/skills.json`. To read one directly, open",
            "`${CLAUDE_PLUGIN_ROOT}/.claude/skills/salesforce-<domain>/references/skill-index.md`.",
        ]
    lines = [
        "## How to find the right skill",
        "",
        "Three mechanisms, listed in order of reliability on a fresh install.",
        "Use the first one that is available; do not stop at a guess.",
        "",
        *roster,
        "",
        "**2. The MCP server (fast, needs the `sfskills-mcp` server connected).**",
        "Call the `search_skill` tool with the user's phrasing"
        + (f" and `domain: \"{domain}\"`" if domain else "")
        + ". It returns",
        "ranked skill ids. `get_skill` then returns the package contents.",
        "",
        "**3. The search CLI (fast, needs a locally built index).**",
        "",
        "```bash",
        f'python3 "${{CLAUDE_PLUGIN_ROOT}}/scripts/search_knowledge.py" "<the user\'s question>"{flag} --json',
        "```",
        "",
        "This needs `vector_index/`, which is **not shipped** — it is gitignored",
        "and must be built once per clone:",
        "",
        "```bash",
        'cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m pip install -r requirements.txt && python3 scripts/build_index.py',
        "```",
        "",
        "If the command errors or reports `Coverage: NONE`, fall back to",
        "mechanism 1 rather than telling the user the topic is uncovered.",
        "",
        "**Then read the package.** Open the exact",
        "`${CLAUDE_PLUGIN_ROOT}/skills/<domain>/<slug>/SKILL.md` the lookup",
        "returned, plus its `references/gotchas.md` and",
        "`references/llm-anti-patterns.md`. Do not answer from this router:",
        "it is a map, not the territory.",
        "",
    ]
    return lines


# ── Renderers ─────────────────────────────────────────────────────────────────

def render_top_router(registry: dict, agents: list[dict], commands: list[tuple[str, str]]) -> str:
    counts = registry["domain_counts"]
    total = registry["skill_count"]

    description = (
        f"Entry point for the SfSkills Salesforce library: {total:,} skill "
        f"packages across {len(DOMAIN_ORDER)} domains ({', '.join(DOMAIN_ORDER)}), "
        f"{len(agents)} run-time agents and {len(commands)} slash commands. Use for any "
        "Salesforce, Force.com or Lightning Platform question — Apex, SOQL, "
        "SOSL, triggers, Flow, LWC, sObject, custom field, permission set, "
        "profile, sharing rule, validation rule, deployment, sandbox, "
        "Agentforce, OmniStudio, org setup. This skill does not answer "
        "Salesforce questions itself; it routes to the specific skill package "
        "that does, then hands off to a domain router."
    )
    if len(description) > MAX_DESCRIPTION_CHARS:
        raise SystemExit(
            f"ERROR: description for salesforce is {len(description)} chars, "
            f"over the {MAX_DESCRIPTION_CHARS} cap"
        )

    lines = [
        "---",
        "name: salesforce",
        f"description: {yaml_quote(description)}",
        "---",
        "",
        "# Salesforce — SfSkills library router",
        "",
        "You are working with a Salesforce library that is far too large to",
        "load. This file tells you how to reach the one page you need.",
        "",
        "**Generated by `scripts/build_plugin.py`. Do not hand-edit.**",
        "",
        "## What is in the library",
        "",
        f"- **{total:,} skill packages** under `${{CLAUDE_PLUGIN_ROOT}}/skills/<domain>/<slug>/`.",
        "  Each is a `SKILL.md` plus `references/examples.md`, `gotchas.md`,",
        "  `well-architected.md` and `llm-anti-patterns.md`.",
        f"- **{len(agents)} run-time agents** under `${{CLAUDE_PLUGIN_ROOT}}/agents/<id>/AGENT.md`,",
        "  exposed as subagents (see the roster at the bottom of this file).",
        f"- **{len(commands)} slash commands** under `${{CLAUDE_PLUGIN_ROOT}}/commands/`.",
        "- **Decision trees** under `${CLAUDE_PLUGIN_ROOT}/standards/decision-trees/`,",
        "  which route between technologies *before* a skill is opened.",
        "- **Canonical templates** under `${CLAUDE_PLUGIN_ROOT}/templates/`.",
        "",
        "Skill counts by domain:",
        "",
        "| Domain | Skills | Router |",
        "|---|---:|---|",
    ]
    for domain in DOMAIN_ORDER:
        lines.append(f"| `{domain}` | {counts[domain]:,} | `salesforce-{domain}` |")
    lines += [
        f"| **total** | **{total:,}** | |",
        "",
    ]

    lines += lookup_block(None)

    lines += [
        "## Domain routers",
        "",
        "Hand off to the router for the domain the request lands in. Each one",
        "carries that domain's featured skills, decision trees and templates.",
        "",
    ]
    for domain in DOMAIN_ORDER:
        scope = " ".join(DOMAIN_META[domain][0].split())
        lines.append(f"- **`salesforce-{domain}`** ({counts[domain]} skills) — {scope}")
    lines += [
        "",
        "## Decision trees — read before choosing a technology",
        "",
        "When a request straddles more than one technology, read the tree",
        "*before* activating any skill, and cite the branch that decided it.",
        "",
    ]
    for tree in sorted(p.name for p in TREES_DIR.glob("*.md") if p.name != "README.md"):
        lines.append(f"- `${{CLAUDE_PLUGIN_ROOT}}/standards/decision-trees/{tree}`")
    lines += [
        "- `${CLAUDE_PLUGIN_ROOT}/standards/decision-trees/README.md` — the index,",
        "  with the rule for when a tree outranks a retrieval tie",
        "",
        "## Cross-domain entry points",
        "",
        "If you need a place to start before running a lookup, these are the",
        "highest-traffic packages in the library:",
        "",
    ]
    for skill_id, why in ENTRY_SKILLS:
        lines.append(f"- `${{CLAUDE_PLUGIN_ROOT}}/skills/{skill_id}/SKILL.md` — {why}")

    lines += [
        "",
        "## Run-time agents",
        "",
        "For a whole workflow rather than a single question, invoke the",
        "matching subagent. Each reads its full `AGENT.md` playbook, cites",
        "every skill it consulted, and never deploys to an org.",
        "",
    ]
    for domain in DOMAIN_ORDER:
        in_domain = [a for a in agents if a["domain"] == domain]
        if not in_domain:
            continue
        lines.append(f"- **{domain}** — " + ", ".join(f"`{a['id']}`" for a in in_domain))
    unclassified = [a for a in agents if a["domain"] not in DOMAIN_ORDER]
    if unclassified:
        lines.append("- **other** — " + ", ".join(f"`{a['id']}`" for a in unclassified))

    lines += [
        "",
        "## Rules",
        "",
        "1. Never answer a Salesforce behaviour, limit or API question from",
        "   this file. Route, open the package, then answer from it.",
        "2. Cite every skill id, template path and decision-tree branch you",
        "   used. The library's value is that its claims are traceable.",
        "3. Never claim the library lacks coverage without having run a",
        "   lookup and pasted its output.",
        "4. Never deploy to an org and never write outside the paths the user",
        "   gave you.",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_domain_router(domain: str, registry: dict, agents: list[dict]) -> str:
    count = registry["domain_counts"][domain]
    scope, vocab = DOMAIN_META[domain]
    scope = " ".join(scope.split())
    vocab = " ".join(vocab.split())

    description = (
        f"Router for the {count} SfSkills `{domain}` skill packages. {scope} "
        f"Use when the request mentions {vocab}. Finds and opens the exact "
        f"skill package to read; it does not contain the guidance itself."
    )
    if len(description) > MAX_DESCRIPTION_CHARS:
        raise SystemExit(
            f"ERROR: description for salesforce-{domain} is "
            f"{len(description)} chars, over the {MAX_DESCRIPTION_CHARS} cap"
        )

    lines = [
        "---",
        f"name: salesforce-{domain}",
        f"description: {yaml_quote(description)}",
        "---",
        "",
        f"# Salesforce {domain} — SfSkills domain router",
        "",
        f"{scope}",
        "",
        f"**{count} skill packages** live under",
        f"`${{CLAUDE_PLUGIN_ROOT}}/skills/{domain}/<slug>/SKILL.md`. They are not",
        "loaded — reach them by path, on demand.",
        "",
        "**Generated by `scripts/build_plugin.py`. Do not hand-edit.**",
        "",
    ]

    lines += lookup_block(domain)

    lines += [
        "## Featured entry points",
        "",
        "Curated starting points when the request is broad or the lookup is",
        "ambiguous. This is a shortlist, not the catalogue — the roster at",
        f"`references/skill-index.md` has all {count}.",
        "",
    ]
    for skill_id, why in FEATURED_SKILLS[domain]:
        lines.append(f"- `${{CLAUDE_PLUGIN_ROOT}}/skills/{skill_id}/SKILL.md` — {why}")

    lines += [
        "",
        "## Decision trees",
        "",
        "Read the tree *before* activating a skill when the request could be",
        "solved more than one way, and cite the branch that decided it.",
        "",
    ]
    for tree, why in DOMAIN_TREES[domain]:
        lines.append(f"- `${{CLAUDE_PLUGIN_ROOT}}/standards/decision-trees/{tree}` — {why}")

    template_dir = TEMPLATES_DIR / domain
    if template_dir.is_dir():
        lines += [
            "",
            "## Canonical templates",
            "",
            f"Do not hand-roll an idiom that already exists. Copy from",
            f"`${{CLAUDE_PLUGIN_ROOT}}/templates/{domain}/` and rename in the consuming",
            "project; never edit the template in place.",
            "",
        ]
        for hint in DOMAIN_TEMPLATE_HINTS.get(domain, []):
            lines.append(f"- `${{CLAUDE_PLUGIN_ROOT}}/templates/{domain}/{hint}`")
        lines.append(f"- `${{CLAUDE_PLUGIN_ROOT}}/templates/{domain}/README.md` — the full list")

    domain_agents = [a for a in agents if a["domain"] == domain]
    if domain_agents:
        lines += [
            "",
            "## Run-time agents for this domain",
            "",
            "Invoke one of these subagents when the ask is a whole workflow",
            "rather than a single question:",
            "",
        ]
        for agent in domain_agents:
            lines.append(f"- `{agent['id']}` — {agent['title']}")

    lines += [
        "",
        "## Rules",
        "",
        f"1. Answer from the opened `{domain}` package, never from this router.",
        "2. Cite the skill id and, where one applied, the decision-tree branch.",
        "3. Never claim a topic is uncovered without pasting lookup output.",
        "4. Never deploy to an org.",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_roster(domain: str, registry: dict) -> str:
    entries = sorted(
        (s for s in registry["skills"] if s["category"] == domain),
        key=lambda s: s["name"],
    )
    lines = [
        f"# SfSkills — `{domain}` skill roster ({len(entries)} packages)",
        "",
        "The zero-setup lookup path: this file ships with the plugin and needs",
        "no search index. Scan it, pick a package by name, then read that",
        "package from the repository root under `${CLAUDE_PLUGIN_ROOT}`.",
        "",
        "Generated from `registry/skills.json` by `scripts/build_plugin.py`.",
        "Do not hand-edit.",
        "",
        f"**How to read a gloss.** The package id is on the line already, so the",
        "gloss does not repeat it. It carries what the id cannot, in this order:",
        "the package's own **trigger vocabulary** (the phrasings that should",
        f"land here), then its **`NOT for …` redirect** (which names the package",
        "to use instead), then a short scope phrase if there is room. A",
        f"`{GLOSS_ELLIPSIS}` marks a truncation, always at a word, keyword or",
        f"whole-clause boundary. Budget: {MAX_GLOSS_CHARS} characters.",
        "",
        "**A `NOT for X - use Y` clause is the most useful thing on the line.**",
        "If your question is X, stop and open Y instead of this package.",
        "",
    ]
    for skill in entries:
        gloss = build_gloss(skill.get("description", ""))
        lines.append(f"- `skills/{domain}/{skill['name']}/SKILL.md` — {gloss}")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_subagent(agent: dict) -> str:
    """One flat subagent loader. Also the single largest always-on line item.

    THE DESCRIPTION IS A BUDGET DECISION. An agent's `name` + `description` is
    always-on, at 0.25 tok/char, in every session — 48 of these were 3,229 of
    the plugin's 6,118 tokens (53%). Measured on the previous wording, the 48
    descriptions shared a 188-character longest-common-suffix: 188 x 48 = 9,024
    chars = 2,256 tok = 37% of the ENTIRE always-on bill, spent on text that is
    the same on every line and therefore discriminates between nothing.
    (The docs previously said 203 chars / 9,744 / 2,436; 188 is the measured
    figure. It is a suffix, not a byte-identical string, because `{domain}`
    takes 10 distinct values.)

    So the boilerplate is cut to the shortest form that still states the
    contract, and part of the saving is spent BACK on discrimination: the slash
    command is now named. `/refactor-apex` and the agent id `apex-refactorer`
    are different strings, and the command is what a user actually types, so
    naming it makes the agent findable by a phrasing the name does not carry.
    Shortening all 48 into interchangeability would trade a budget win for a
    routing loss; the title, domain and command are what keep them apart.
    """
    domain = agent["domain"] or "platform"
    invocation = f", /{agent['command']}" if agent["command"] else ""
    # A placeholder title ("Run the SfSkills audit-router run-time agent")
    # would only restate the agent id and the sentence that follows it, so it
    # is dropped rather than shipped as filler.
    lead = "" if _is_untitled(agent["title"]) else f"{agent['title']}. "
    description = (
        f"{lead}SfSkills {domain} workflow agent{invocation}: "
        f"reads its AGENT.md playbook, cites its sources, never deploys."
    )
    lines = [
        "---",
        f"name: {agent['id']}",
        f"description: {yaml_quote(description)}",
        "---",
        "",
        f"# {agent['id']}",
        "",
        f"{agent['title']}",
        "",
        "**Generated by `scripts/build_plugin.py`. Do not hand-edit.**",
        "",
        "This file is a loader. The agent itself is the checked-in playbook.",
        "",
        "## Before you do anything",
        "",
        "Read both of these in full. Paths are relative to the SfSkills",
        "repository root — the same path prefixed with `${CLAUDE_PLUGIN_ROOT}/`",
        "when this file is loaded as a plugin component.",
        "",
        f"1. `agents/{agent['dir']}/AGENT.md` — the playbook: inputs, mandatory",
        "   reads, procedure, output contract and refusal conditions.",
        "2. `agents/_shared/AGENT_CONTRACT.md` — the 8-section AGENT.md shape",
        "   every run-time agent must obey, including the mandatory",
        "   **Process Observations** block.",
        "",
        "Then read every skill, template and decision tree the playbook lists",
        "under Mandatory Reads before producing output. If a cited path does",
        "not resolve, say so instead of substituting a guess.",
        "",
        "## Non-negotiables",
        "",
        "- Cite every skill id, template path and decision-tree branch you",
        "  consulted, in a Citations block.",
        "- Return a confidence score (HIGH / MEDIUM / LOW) and list the",
        "  ambiguities that reduced it.",
        "- Process exactly one target per invocation.",
        "- Never deploy to an org. Never mutate files outside the paths the",
        "  user supplied.",
        "- Never print a secret; redact as `[REDACTED]`.",
        "- Recommend other agents by name, but never auto-chain to them.",
        "",
    ]
    router = f"salesforce-{domain}" if domain in DOMAIN_ORDER else "salesforce"
    lines += ["## Related", ""]
    if agent["command"]:
        lines.append(
            f"- Slash command: `/{agent['command']}` (`commands/{agent['command']}.md`)"
        )
    lines += [f"- Domain router skill: `{router}`", ""]
    return "\n".join(lines) + "\n"


def _inventory_phrase(
    registry: dict, commands: list[tuple[str, str]], shipped: list[str]
) -> str:
    """The one sentence every manifest description is built from.

    Every number here is DERIVED from what an install actually exposes:
    `registry['skill_count']` for the on-demand packages, `len(commands)` for
    the files the declared `commands` path loads, and `shipped` — the flat
    `agents/*.md` loaders this build emits, per
    `shipped_agents_in_build()` — for the agents the default scan can see.
    The agent clause is omitted entirely while that set is empty, so the
    manifest never claims a component the plugin cannot deliver.
    `--audit-install` is the gate.
    """
    parts = [f"{registry['skill_count']:,} grounded Salesforce skill packages"]
    if shipped:
        parts.append(f"{len(shipped)} run-time agents")
    parts.append(f"{len(commands)} slash commands")
    return ", ".join(parts[:-1]) + f" and {parts[-1]}"


def render_plugin_manifest(registry: dict, shipped: list[str], commands: list[tuple[str, str]]) -> str:
    """`.claude-plugin/plugin.json`.

    Declares `skills` and `commands`. Deliberately omits `agents`:

    - `commands` REPLACES the default `commands/` scan, so naming `./commands/`
      explicitly is a no-op behaviourally and a statement of intent
      editorially — the manifest now says what it ships instead of relying on
      an implicit default. Measured on 2.1.209: all 66 files still load.
    - `agents` also REPLACES its default scan, and on Claude Code 2.1.209
      every custom-path form loads ZERO agents while suppressing the one scan
      that works. See the `AGENT_LOADING_MATRIX` comment at the top of this
      file for the full probe results. Declaring it is strictly worse than
      omitting it — the 48 loaders ship through the DEFAULT scan of the flat
      `agents/*.md` files this build emits, which no manifest key improves on.
    """
    manifest = {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": PLUGIN_NAME,
        "displayName": "SfSkills — Salesforce AI Skill Library",
        "version": PLUGIN_VERSION,
        "description": (
            f"{_inventory_phrase(registry, commands, shipped)}, reached through 12 "
            "lightweight router skills instead of a flat index."
        ),
        "author": {"name": AUTHOR_NAME, "url": REPO_URL},
        "homepage": f"{REPO_URL}#readme",
        "repository": REPO_URL,
        "license": "PolyForm-Small-Business-1.0.0",
        "keywords": [
            "salesforce",
            "apex",
            "soql",
            "lightning-web-components",
            "flow",
            "agentforce",
            "omnistudio",
            "admin",
            "devops",
            "well-architected",
        ],
        "skills": [PLUGIN_SKILLS_PATH],
        "commands": [PLUGIN_COMMANDS_PATH],
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def render_marketplace_manifest(registry: dict, shipped: list[str], commands: list[tuple[str, str]]) -> str:
    """`.claude-plugin/marketplace.json` — the repo is its own marketplace.

    `source: "./"` plus an entry-level `skills` override is the documented
    marketplace-root exception (plugin-marketplaces, "Advanced plugin
    entries"): "With a marketplace-root `source`, the listed paths are the
    complete set for that entry, and other directories in the shared
    `skills/` folder don't load." That is the only mechanism that keeps the
    1,027 Tier-2 packages out of the always-on index.

    `source: "./"` is also what puts the whole repo in the plugin cache, so
    `${CLAUDE_PLUGIN_ROOT}/skills/`, `/scripts/`, `/standards/` and
    `/templates/` all resolve. A narrower source would leave the routers
    pointing at nothing.
    """
    entry = {
        "name": PLUGIN_NAME,
        "source": "./",
        "displayName": "SfSkills — Salesforce AI Skill Library",
        "description": (
            "Tiered Salesforce library: 12 router skills up front, "
            f"{_inventory_phrase(registry, commands, shipped)} reached on demand."
        ),
        # Must equal plugin.json's version — `claude plugin tag` enforces it.
        "version": PLUGIN_VERSION,
        "author": {"name": AUTHOR_NAME, "url": REPO_URL},
        "homepage": f"{REPO_URL}#readme",
        "repository": REPO_URL,
        "license": "PolyForm-Small-Business-1.0.0",
        "category": "development",
        "keywords": ["salesforce", "apex", "flow", "lwc", "agentforce", "well-architected"],
        "tags": ["salesforce", "crm", "apex", "soql", "admin", "architecture"],
        # LOAD-BEARING — see the docstring. Do not remove, and do not add an
        # `agents` key alongside it (variants F/G in AGENT_LOADING_MATRIX).
        "skills": [PLUGIN_SKILLS_PATH],
        "commands": [PLUGIN_COMMANDS_PATH],
    }
    manifest = {
        "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
        "name": MARKETPLACE_NAME,
        "description": (
            "Salesforce skills, run-time agents and slash commands from the "
            "SfSkills library."
        ),
        "owner": {"name": AUTHOR_NAME, "url": REPO_URL},
        "plugins": [entry],
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


# ── Build ─────────────────────────────────────────────────────────────────────

def verify_seeds(registry: dict) -> list[str]:
    """Resolve every curated seed against the registry and the filesystem."""
    known = {s["id"] for s in registry["skills"]}
    problems: list[str] = []

    seen_domains = set(FEATURED_SKILLS) | set(DOMAIN_META) | set(DOMAIN_TREES)
    for domain in sorted(seen_domains):
        if domain not in registry["domain_counts"]:
            problems.append(f"seed domain {domain!r} is not in the registry")
    for domain in DOMAIN_ORDER:
        if domain not in registry["domain_counts"]:
            problems.append(f"DOMAIN_ORDER lists {domain!r}, absent from the registry")
        for table, label in ((FEATURED_SKILLS, "FEATURED_SKILLS"),
                             (DOMAIN_META, "DOMAIN_META"),
                             (DOMAIN_TREES, "DOMAIN_TREES")):
            if domain not in table:
                problems.append(f"{label} has no entry for domain {domain!r}")
    if sorted(registry["domain_counts"]) != sorted(DOMAIN_ORDER):
        problems.append(
            "DOMAIN_ORDER disagrees with registry domain_counts: "
            f"{sorted(set(registry['domain_counts']) ^ set(DOMAIN_ORDER))}"
        )

    for domain in sorted(FEATURED_SKILLS):
        entries = FEATURED_SKILLS[domain]
        if not 5 <= len(entries) <= 10:
            problems.append(
                f"FEATURED_SKILLS[{domain!r}] has {len(entries)} entries; must be 5-10"
            )
        slugs = [sid for sid, _ in entries]
        if len(set(slugs)) != len(slugs):
            problems.append(f"FEATURED_SKILLS[{domain!r}] has duplicate ids")
        for skill_id, _ in entries:
            if not skill_id.startswith(f"{domain}/"):
                problems.append(f"{skill_id} is featured under the wrong domain {domain!r}")
            problems += _resolve_skill(skill_id, known, f"FEATURED_SKILLS[{domain!r}]")

    for skill_id, _ in ENTRY_SKILLS:
        problems += _resolve_skill(skill_id, known, "ENTRY_SKILLS")
    entry_domains = {sid.split("/")[0] for sid, _ in ENTRY_SKILLS}
    missing = sorted(set(DOMAIN_ORDER) - entry_domains)
    if missing:
        problems.append(f"ENTRY_SKILLS covers no skill for domain(s): {missing}")

    for domain in sorted(DOMAIN_TREES):
        if not DOMAIN_TREES[domain]:
            problems.append(f"DOMAIN_TREES[{domain!r}] cites no decision tree")
        for tree, _ in DOMAIN_TREES[domain]:
            if not (TREES_DIR / tree).exists():
                problems.append(f"DOMAIN_TREES[{domain!r}] cites missing tree {tree}")

    for domain, hints in sorted(DOMAIN_TEMPLATE_HINTS.items()):
        for hint in hints:
            if not (TEMPLATES_DIR / domain / hint).exists():
                problems.append(f"DOMAIN_TEMPLATE_HINTS[{domain!r}] cites missing {hint}")

    return problems


def _resolve_skill(skill_id: str, known: set[str], label: str) -> list[str]:
    problems = []
    if skill_id not in known:
        problems.append(f"{label}: {skill_id} is not in registry/skills.json")
    if not (SKILLS_DIR / skill_id / "SKILL.md").exists():
        problems.append(f"{label}: skills/{skill_id}/SKILL.md does not exist on disk")
    return problems


def build_outputs() -> dict[Path, str]:
    """Every managed artifact, keyed by repo-relative path. Pure function of
    the repo's committed inputs, so ``--check`` is a true drift gate."""
    registry = load_registry()
    problems = verify_seeds(registry)
    if problems:
        raise SystemExit(
            "ERROR: curated seeds do not resolve — refusing to ship dead paths:\n  "
            + "\n  ".join(problems)
        )

    agents = runtime_agents()
    commands = command_index()

    out: dict[Path, str] = {}

    # Subagent loaders FIRST: the manifest description is derived from the
    # flat `agents/*.md` set this build emits, so that set has to exist before
    # the manifests are rendered. One render, two destinations, byte-identical
    # — see PLUGIN_AGENT_SCAN_DIR for why both are needed and why generating
    # them together is the only thing that makes drift detectable.
    for agent in agents:
        loader = render_subagent(agent)
        out[SUBAGENT_ROOT / f"{agent['id']}.md"] = loader
        out[PLUGIN_AGENT_SCAN_DIR / f"{agent['id']}.md"] = loader

    shipped = shipped_agents_in_build(out)
    out[PLUGIN_MANIFEST_DIR / "plugin.json"] = render_plugin_manifest(registry, shipped, commands)
    out[PLUGIN_MANIFEST_DIR / "marketplace.json"] = render_marketplace_manifest(registry, shipped, commands)
    out[ROUTER_ROOT / "salesforce" / "SKILL.md"] = render_top_router(registry, agents, commands)

    for domain in DOMAIN_ORDER:
        base = ROUTER_ROOT / f"salesforce-{domain}"
        out[base / "SKILL.md"] = render_domain_router(domain, registry, agents)
        roster = render_roster(domain, registry)
        size = len(roster.encode("utf-8"))
        if size > MAX_ROSTER_BYTES:
            raise SystemExit(
                f"ERROR: roster for {domain} is {size} bytes, over the "
                f"{MAX_ROSTER_BYTES}-byte cap"
            )
        out[base / "references" / "skill-index.md"] = roster

    _self_check(out, registry)
    return out


def _self_check(out: dict[Path, str], registry: dict) -> None:
    """Fail the build if a generated router would cite a path that does not
    resolve, or would break one of the shape invariants."""
    problems: list[str] = []
    skill_path_re = re.compile(r"skills/([a-z]+)/([a-z0-9][a-z0-9-]*)/SKILL[.]md")
    tree_re = re.compile(r"standards/decision-trees/([a-z-]+[.]md)")

    for rel, content in sorted(out.items()):
        if rel.suffix != ".md":
            continue
        for domain, slug in skill_path_re.findall(content):
            if not (SKILLS_DIR / domain / slug / "SKILL.md").exists():
                problems.append(f"{rel}: cites missing skills/{domain}/{slug}/SKILL.md")
        for tree in tree_re.findall(content):
            if not (TREES_DIR / tree).exists():
                problems.append(f"{rel}: cites missing decision tree {tree}")
        for agent_ref in re.findall(r"`agents/([a-z0-9][a-z0-9_-]*)/([A-Z_]+\.md)`", content):
            if not (AGENTS_DIR / agent_ref[0] / agent_ref[1]).exists():
                problems.append(f"{rel}: cites missing agents/{agent_ref[0]}/{agent_ref[1]}")
        for cmd_ref in re.findall(r"`commands/([a-z0-9][a-z0-9-]*\.md)`", content):
            if not (COMMANDS_DIR / cmd_ref).exists():
                problems.append(f"{rel}: cites missing commands/{cmd_ref}")

    for rel, content in sorted(out.items()):
        if rel.parent.parent != ROUTER_ROOT or rel.name != "SKILL.md":
            continue
        meta = content.split("---")[1]
        name = (re.search(r"^name: *(.+)$", meta, re.M) or [None, ""])[1].strip()
        desc = (re.search(r"^description: *(.+)$", meta, re.M) or [None, ""])[1].strip()
        if name != rel.parent.name:
            problems.append(f"{rel}: frontmatter name {name!r} != directory {rel.parent.name!r}")
        if not 0 < len(desc) <= MAX_DESCRIPTION_CHARS:
            problems.append(f"{rel}: description is {len(desc)} chars")
        for needle in ("CLAUDE_PLUGIN_ROOT}/scripts/search_knowledge.py",
                       "search_skill", "skill-index.md"):
            if needle not in content:
                problems.append(f"{rel}: router does not teach {needle!r}")
        if not tree_re.search(content):
            problems.append(f"{rel}: router cites no decision tree")
        if rel.parent.name != "salesforce":
            domain = rel.parent.name[len("salesforce-"):]
            own = {s for d, s in skill_path_re.findall(content) if d == domain}
            if not 5 <= len(own) <= 10:
                problems.append(
                    f"{rel}: names {len(own)} skills from its own domain; must be 5-10"
                )

    for domain, count in sorted(registry["domain_counts"].items()):
        rel = ROUTER_ROOT / f"salesforce-{domain}" / "references" / "skill-index.md"
        listed = len(skill_path_re.findall(out[rel]))
        if listed != count:
            problems.append(f"{rel}: lists {listed} skills, registry says {count}")

    # The two subagent loader sets must stay the same set, with the same
    # bytes. They are consumed by two different mechanisms (plugin scope vs
    # project scope) and the project copy overrides the plugin copy inside a
    # clone, so a divergence would be invisible to anyone testing from the
    # repo. Catch it here rather than in the field.
    project_scope = {p.stem for p in out if p.parent == SUBAGENT_ROOT and p.suffix == ".md"}
    plugin_scope = {p.stem for p in out if p.parent == PLUGIN_AGENT_SCAN_DIR and p.suffix == ".md"}
    for missing in sorted(project_scope - plugin_scope):
        problems.append(f"agents/{missing}.md: project-scope loader has no plugin-scope twin")
    for missing in sorted(plugin_scope - project_scope):
        problems.append(f"{SUBAGENT_ROOT}/{missing}.md: plugin-scope loader has no project-scope twin")
    for agent_id in sorted(project_scope & plugin_scope):
        if out[SUBAGENT_ROOT / f"{agent_id}.md"] != out[PLUGIN_AGENT_SCAN_DIR / f"{agent_id}.md"]:
            problems.append(
                f"{agent_id}: the project-scope and plugin-scope loaders differ; "
                "they must be byte-identical"
            )

    if problems:
        raise SystemExit(
            "ERROR: generated output failed self-check:\n  " + "\n  ".join(problems)
        )


# Directories this script owns OUTRIGHT: everything under them is generated,
# so anything the build did not just write is stale and gets pruned.
FULLY_MANAGED_DIRS = (PLUGIN_MANIFEST_DIR, ROUTER_ROOT, SUBAGENT_ROOT)

# `agents/` is NOT fully managed. It is shared: the build owns the flat
# `agents/<id>.md` loaders, while the hand-authored `agents/<id>/AGENT.md`
# packages and `agents/_shared/` belong to humans. So the sweep here is
# deliberately non-recursive and restricted to top-level `*.md` — a
# `rglob("*")` prune over this directory would delete the entire agent
# library.
#
# The glob alone is still too wide: it would make the build own EVERY
# top-level `agents/*.md`, so a hand-authored `agents/README.md` would be
# silently unlinked by the next build. Nothing is at risk today (no such file
# exists) and the docs already describe the narrower ownership the build was
# supposed to have — so the code is narrowed to match, rather than the doc
# widened to excuse it. Silently deleting a contributor's file is a far worse
# failure mode than leaving a stale loader behind, which `--check` reports
# anyway. A candidate is therefore pruned only if it carries the marker line
# that render_subagent() stamps into every loader it writes.
SHARED_MANAGED_GLOBS = ((PLUGIN_AGENT_SCAN_DIR, "*.md"),)
GENERATED_MARKER = "**Generated by `scripts/build_plugin.py`. Do not hand-edit.**"


def _is_build_output(path: Path) -> bool:
    """True only for a file this script wrote, identified by its own marker."""
    try:
        return GENERATED_MARKER in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def _stale_managed_files(root: Path, keep: set[Path]) -> list[Path]:
    """Every file under a managed location that this build did not produce."""
    stale: list[Path] = []
    for managed in FULLY_MANAGED_DIRS:
        base = root / managed
        if not base.exists():
            continue
        stale += [
            p for p in sorted(base.rglob("*"))
            if p.is_file() and p.relative_to(root) not in keep
        ]
    for managed, pattern in SHARED_MANAGED_GLOBS:
        base = root / managed
        if not base.is_dir():
            continue
        stale += [
            p for p in sorted(base.glob(pattern))
            if p.is_file()
            and p.relative_to(root) not in keep
            and _is_build_output(p)  # never touch a hand-authored file here
        ]
    return stale


def write_outputs(out: dict[Path, str], root: Path) -> tuple[int, int]:
    """Write every artifact under ``root``, pruning stale managed files."""
    written = 0
    for rel, content in sorted(out.items()):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8", newline="\n")
        written += 1

    keep = set(out)
    pruned = 0
    for path in _stale_managed_files(root, keep):
        path.unlink()
        pruned += 1

    # Only the fully-managed trees get their empty directories reaped;
    # `agents/` keeps its package dirs.
    for managed in FULLY_MANAGED_DIRS:
        base = root / managed
        if not base.exists():
            continue
        for path in sorted(base.rglob("*"), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    return written, pruned


# ── Modes ─────────────────────────────────────────────────────────────────────

def run_build() -> int:
    out = build_outputs()
    written, pruned = write_outputs(out, REPO_ROOT)
    print(f"Wrote {written} plugin artifact(s) under {REPO_ROOT}")
    routers = sum(1 for p in out if p.name == "SKILL.md")
    rosters = sum(1 for p in out if p.name == "skill-index.md")
    subagents = sum(1 for p in out if p.parent == SUBAGENT_ROOT)
    plugin_agents = len(shipped_agents_in_build(out))
    print(f"  {routers} router skill(s)   → {ROUTER_ROOT}/")
    print(f"  {rosters} domain roster(s)  → {ROUTER_ROOT}/salesforce-*/references/")
    print(f"  {subagents} subagent(s)      → {SUBAGENT_ROOT}/          (project scope)")
    print(f"  {plugin_agents} subagent(s)      → {PLUGIN_AGENT_SCAN_DIR}/<id>.md    (plugin scope, identical bytes)")
    print(f"  2 manifest(s)       → {PLUGIN_MANIFEST_DIR}/")
    if pruned:
        print(f"  pruned {pruned} stale file(s)")
    print("\nNext: python3 scripts/build_plugin.py --measure")
    return 0


def run_check() -> int:
    """Rebuild into a TemporaryDirectory and diff against the working tree."""
    out = build_outputs()
    with tempfile.TemporaryDirectory(prefix="sfskills-plugin-check-") as scratch:
        scratch_root = Path(scratch)
        write_outputs(out, scratch_root)

        drift: list[str] = []
        for rel in sorted(out):
            live = REPO_ROOT / rel
            fresh = scratch_root / rel
            if not live.exists():
                drift.append(f"missing: {rel}")
            elif live.read_bytes() != fresh.read_bytes():
                drift.append(f"differs: {rel}")

        for path in _stale_managed_files(REPO_ROOT, set(out)):
            drift.append(f"unmanaged: {path.relative_to(REPO_ROOT)}")

    if not drift:
        print(f"OK: {len(out)} plugin artifact(s) match a fresh build — no drift")
        return 0
    print("DRIFT: the committed plugin artifacts do not match a fresh build:")
    for item in drift:
        print(f"  - {item}")
    print("\nTo fix: python3 scripts/build_plugin.py")
    return 1


def _frontmatter(content: str) -> tuple[str, str]:
    """A component's `name` and `description` — the only part loaded up front."""
    meta = content.split("---")[1]
    name = (re.search(r"^name: *(.+)$", meta, re.M) or [None, ""])[1].strip()
    desc = (re.search(r"^description: *(.+)$", meta, re.M) or [None, ""])[1].strip()
    # Strip the YAML quoting: the model sees the value, not the delimiters.
    if len(desc) >= 2 and desc[0] == '"' and desc[-1] == '"':
        desc = desc[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return name, desc


def measure() -> dict:
    """The always-on cost of an install, from the closed form at the top.

    Subagents are NOT free. Their `name` + `description` frontmatter loads up
    front exactly like a skill's — the total rose from ~2,889 to ~6,118 when
    the 48 loaders started shipping. So they are counted in `tier1_tokens`;
    leaving them out would make this gate cheerfully report half the bill.

    Three billing details, each established by a probe rather than assumed:
    skills and commands are billed under their `<plugin>:<name>` qualified
    name while agents are billed bare; a command's description is its FULL H1,
    not the `/slug — ` stripped subtitle; and that H1 is hard-truncated at 100
    characters. `tier1_tokens` is the model's exact prediction of what
    `claude plugin details` will print — the gate runs against
    `tier1_tokens_padded`, which adds the single SAFETY_MARGIN_RATIO.
    """
    registry = load_registry()
    commands = command_index()
    out = build_outputs()

    router_tokens = 0.0
    router_skills = 0
    for rel, content in sorted(out.items()):
        if rel.parent.parent != ROUTER_ROOT or rel.name != "SKILL.md":
            continue
        name, desc = _frontmatter(content)
        router_tokens += always_on_tokens(qualified_skill_name(name), desc)
        router_skills += 1

    # Agents are NOT namespaced — probes B1/B2 at the top of this file: the
    # same 10 agents billed 258 tok under an 8-char and a 12-char plugin name.
    agent_ids = shipped_agents_in_build(out)
    agent_tokens = 0.0
    for agent_id in agent_ids:
        name, desc = _frontmatter(out[PLUGIN_AGENT_SCAN_DIR / f"{agent_id}.md"])
        agent_tokens += always_on_tokens(name, desc)

    # The WHOLE H1, truncated at 100 — probes C1-C4. Charging the stripped
    # subtitle (as this did until 2026-08-07) under-reads by ~1.5 tok/command.
    command_tokens = sum(
        always_on_tokens(qualified_skill_name(stem), heading[:COMMAND_DESCRIPTION_CHARS])
        for stem, heading in commands
    )
    tier1 = router_tokens + command_tokens + agent_tokens
    tier1_rounded = round(tier1)
    padded = math.ceil(tier1 * (1 + SAFETY_MARGIN_RATIO))

    # Apples to apples: a flat export would be billed under the same model,
    # every package namespaced, so compare it that way rather than by chars/4.
    flat_tokens = round(sum(
        always_on_tokens(qualified_skill_name(s["name"]), s["description"])
        for s in registry["skills"]
    ))
    ratio = round(padded / flat_tokens, 4) if flat_tokens else 0.0

    return {
        "model": "0.25 * (len(qualified_name) + len(description)) + 0.25 per "
                 "component; skills and commands qualified as "
                 f"'{PLUGIN_NAME}:<name>', agents bare; a command's description "
                 f"is its full H1 truncated at {COMMAND_DESCRIPTION_CHARS} chars",
        "router_skills": router_skills,
        "router_tokens": round(router_tokens, 1),
        "commands": len(commands),
        "command_tokens": round(command_tokens, 1),
        "agents": len(agent_ids),
        "agent_tokens": round(agent_tokens, 1),
        "tier1_tokens": tier1_rounded,
        "tier1_tokens_exact": round(tier1, 1),
        "safety_margin_ratio": SAFETY_MARGIN_RATIO,
        "tier1_tokens_padded": padded,
        "flat_export_skills": registry["skill_count"],
        "flat_export_tokens": flat_tokens,
        "ratio": ratio,
        "budget_tier1_tokens": BUDGET_TIER1_TOKENS,
        "over_budget_by_tokens": max(0, padded - BUDGET_TIER1_TOKENS),
        "within_budget": padded <= BUDGET_TIER1_TOKENS and ratio <= BUDGET_TIER1_RATIO,
        "measured_reference": MEASURED_REFERENCE,
    }


def run_measure() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    if result["within_budget"]:
        return 0
    print(
        f"\nOVER BUDGET by {result['over_budget_by_tokens']} tok "
        f"({result['tier1_tokens_padded']} padded, {result['tier1_tokens']} "
        f"predicted, vs {result['budget_tier1_tokens']}).\n"
        f"This is not a modelling artifact. The model is the closed form at "
        f"the top of scripts/build_plugin.py, validated against a full-replica "
        f"install on Claude Code {result['measured_reference']['claude_code_version']} "
        f"to within a tenth of a token — verify it yourself with the probe "
        f"procedure in docs/installing-the-plugin.md.\n"
        f"Fix the COST, not the ceiling. Largest line items: agent loaders "
        f"{result['agent_tokens']} tok, commands {result['command_tokens']} "
        f"tok, routers {result['router_tokens']} tok. Look first for text that "
        f"is REPEATED across components — identical text carries no routing "
        f"signal and is pure always-on cost.\n"
        f"Raising BUDGET_TIER1_TOKENS is not a fix; the budget is the only "
        f"thing standing between this plugin and the flat export it exists "
        f"to avoid.",
        file=sys.stderr,
    )
    return 1


def audit_install() -> dict:
    """What an INSTALLED plugin exposes vs what this repo contains.

    Answers the only question that matters for shippability: after
    `claude plugin install sfskills@sfskills`, which components does Claude
    Code actually load? Each projection below is the mechanism proven by the
    `AGENT_LOADING_MATRIX` probe, not an inference from the manifest.
    """
    registry = load_registry()
    commands = command_index()
    routers = 1 + len(DOMAIN_ORDER)
    shipped = shipped_agents_on_disk()
    projected = {
        # `skills` on a marketplace-root entry replaces the default scan, so
        # only the routers load — the 1,027 packages stay on-demand by path.
        "skills_routers": routers,
        # `commands` names ./commands/, one flat skill per file.
        "skills_from_commands": len(commands),
        # Only flat agents/*.md load. Custom paths load zero.
        "agents": len(shipped),
    }
    projected["skills_total"] = projected["skills_routers"] + projected["skills_from_commands"]
    repo = {
        "skill_packages": registry["skill_count"],
        "runtime_agents": len(runtime_agents()),
        "commands": len(commands),
    }
    gaps: list[str] = []
    if projected["agents"] != repo["runtime_agents"]:
        gaps.append(
            f"agents: the repo defines {repo['runtime_agents']} run-time agent(s) but an "
            f"install exposes {projected['agents']}. Only flat "
            f"`{PLUGIN_AGENT_SCAN_DIR}/<id>.md` files load — the `<id>/AGENT.md` packages "
            f"are skipped, and `{SUBAGENT_ROOT}/` is PROJECT-LOCAL state Claude Code reads "
            "for anyone whose cwd is this repo, not a plugin component. Fix: re-run "
            "`python3 scripts/build_plugin.py`, which emits both loader sets."
        )
    if projected["skills_from_commands"] != repo["commands"]:
        gaps.append(
            f"commands: {repo['commands']} file(s) in {COMMANDS_DIR.name}/ but "
            f"{projected['skills_from_commands']} projected."
        )
    # The plugin-scope and project-scope loaders must be the same set with the
    # same bytes. Inside a clone the project copy overrides the plugin copy
    # (https://code.claude.com/docs/en/plugins), so a divergence cannot be
    # noticed by testing from the repo — only by comparing the files.
    project_side = sorted(
        p.stem for p in (REPO_ROOT / SUBAGENT_ROOT).glob("*.md")
    ) if (REPO_ROOT / SUBAGENT_ROOT).is_dir() else []
    if project_side != shipped:
        only_plugin = sorted(set(shipped) - set(project_side))
        only_project = sorted(set(project_side) - set(shipped))
        gaps.append(
            f"loader sets diverge: {len(only_plugin)} only under "
            f"{PLUGIN_AGENT_SCAN_DIR}/ ({', '.join(only_plugin) or '—'}), "
            f"{len(only_project)} only under {SUBAGENT_ROOT}/ "
            f"({', '.join(only_project) or '—'}). Re-run the build."
        )
    else:
        differing = [
            name for name in shipped
            if (REPO_ROOT / PLUGIN_AGENT_SCAN_DIR / f"{name}.md").read_bytes()
            != (REPO_ROOT / SUBAGENT_ROOT / f"{name}.md").read_bytes()
        ]
        if differing:
            gaps.append(
                f"loader bytes diverge for {len(differing)} agent(s) "
                f"({', '.join(differing[:5])}{', …' if len(differing) > 5 else ''}). "
                f"The {SUBAGENT_ROOT}/ copy overrides the {PLUGIN_AGENT_SCAN_DIR}/ copy "
                "inside a clone, so this is invisible from here. Re-run the build."
            )
    return {"projected": projected, "repo": repo, "gaps": gaps}


def run_audit_install() -> int:
    result = audit_install()
    projected, repo = result["projected"], result["repo"]
    print("Projected inventory of an INSTALLED sfskills plugin")
    print(f"  Skills  {projected['skills_total']:>5}   "
          f"({projected['skills_routers']} router(s) from {PLUGIN_SKILLS_PATH} + "
          f"{projected['skills_from_commands']} command(s) from {PLUGIN_COMMANDS_PATH})")
    print(f"  Agents  {projected['agents']:>5}   "
          f"(flat *.md under {PLUGIN_AGENT_SCAN_DIR}/, the only form that loads)")
    print("\nRepo inventory")
    print(f"  skill packages    {repo['skill_packages']:>5}   reached on demand by path, not loaded up front")
    print(f"  run-time agents   {repo['runtime_agents']:>5}")
    print(f"  slash commands    {repo['commands']:>5}")
    print(f"\nProbe baseline: Claude Code {AGENT_LOADING_MATRIX_VERSION}. Verify against the "
          "real CLI with:\n"
          "  claude plugin validate .\n"
          "  claude plugin details sfskills   # run from OUTSIDE this repo")
    if not result["gaps"]:
        print("\nOK: every component this repo defines is reachable through the plugin.")
        return 0
    print(f"\n{len(result['gaps'])} component(s) the plugin cannot deliver:")
    for gap in result["gaps"]:
        print(f"  - {gap}")
    return 1


def run_verify_seeds() -> int:
    problems = verify_seeds(load_registry())
    total = sum(len(v) for v in FEATURED_SKILLS.values()) + len(ENTRY_SKILLS)
    if not problems:
        print(f"OK: {total} curated seed(s) resolved, 0 unresolved")
        return 0
    print(f"{len(problems)} unresolved seed reference(s):")
    for problem in problems:
        print(f"  - {problem}")
    return 1


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the SfSkills Claude Code plugin (tiered routers).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/build_plugin.py                 # build every artifact in place
  python3 scripts/build_plugin.py --check         # drift gate; exit 1 on any diff
  python3 scripts/build_plugin.py --measure       # token-budget JSON; exit 1 if over
  python3 scripts/build_plugin.py --verify-seeds  # resolve the curated seed table
  python3 scripts/build_plugin.py --audit-install # what an INSTALL exposes; exit 1 on a gap

After a build, verify against the real CLI (from OUTSIDE this repo, so a pass
cannot come from project-local .claude/ loading):
  claude plugin validate .
  claude plugin details sfskills
        """,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Non-destructive. Rebuild into a temp dir and diff against the "
             "working tree. Exit 1 on any drift or unmanaged file.",
    )
    mode.add_argument(
        "--measure",
        action="store_true",
        help="Emit the Tier-1 token budget as JSON and exit 1 if it is over "
             "budget or over the flat-export ratio cap.",
    )
    mode.add_argument(
        "--verify-seeds",
        action="store_true",
        help="Resolve every curated featured-skill, decision-tree and template "
             "seed against the registry and the filesystem. Exit 1 on any "
             "unresolved reference.",
    )
    mode.add_argument(
        "--audit-install",
        action="store_true",
        help="Report the component inventory an INSTALLED plugin exposes, "
             "beside the repo's own inventory. Exit 1 when the repo defines a "
             "component the plugin cannot deliver.",
    )
    args = parser.parse_args()

    if args.check:
        return run_check()
    if args.measure:
        return run_measure()
    if args.verify_seeds:
        return run_verify_seeds()
    if args.audit_install:
        return run_audit_install()
    return run_build()


if __name__ == "__main__":
    sys.exit(main())
