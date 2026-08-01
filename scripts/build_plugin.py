#!/usr/bin/env python3
"""
build_plugin.py — Claude Code plugin packaging (tiered router architecture)

Generates every artifact needed to install SfSkills as a Claude Code plugin:

  .claude-plugin/plugin.json          plugin manifest
  .claude-plugin/marketplace.json     repo-as-its-own-marketplace manifest
  .claude/skills/salesforce/          Tier-1 top-level router
  .claude/skills/salesforce-<domain>/ Tier-1 domain routers (11) + rosters
  .claude/agents/<agent-id>.md        Tier-3 project-scope subagent wrappers

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

PLUGIN_NAME = "sfskills"
MARKETPLACE_NAME = "sfskills"
PLUGIN_VERSION = "1.0.0"
AUTHOR_NAME = "Pranav Nagrecha"
REPO_URL = "https://github.com/PranavNagrecha/AwesomeSalesforceSkills"

# The marketplace entry's `skills` field is load-bearing. Per
# plugins-reference "Path behavior rules", `skills` normally ADDS to the
# default `skills/` scan; the one exception is a marketplace entry whose
# `source` resolves to the marketplace root, where the listed paths REPLACE
# it. That exception is what keeps the 1,027 Tier-2 packages out of the
# always-on index. Do not drop either half of the (source, skills) pair.
PLUGIN_SKILLS_PATH = "./.claude/skills/"

# Token model: ceil(chars / 4), applied to name + description for skills and
# to stem + first heading for commands. Calibrated against Claude Code's own
# "Always-on" accounting, where 12 routers carrying 450-char descriptions
# measured ~1,290 tokens (~107 each).
CHARS_PER_TOKEN = 4
BUDGET_TIER1_TOKENS = 6000
BUDGET_TIER1_RATIO = 0.05

# Max characters for a router `description:` value. Claude Code has no hard
# cap, but every character here is always-on cost.
MAX_DESCRIPTION_CHARS = 900
# Max characters for a roster gloss (first sentence of the registry
# description).
MAX_GLOSS_CHARS = 120
# Roster files are on-invoke cost only, but keep them readable.
MAX_ROSTER_BYTES = 60 * 1024

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
DOMAIN_META: dict[str, tuple[str, str]] = {
    "admin": (
        "Declarative Salesforce configuration: objects, fields, record types, "
        "page layouts, permission sets, reports, and the requirements work "
        "that precedes them.",
        "custom object, custom field, picklist, record type, page layout, "
        "permission set, profile, validation rule, report, dashboard, queue, "
        "approval process, user setup",
    ),
    "agentforce": (
        "Agentforce and Einstein: agents, topics, actions, prompt templates, "
        "grounding, guardrails, evaluation and production readiness.",
        "Agentforce, agent topic, agent action, prompt builder, Einstein, "
        "Trust Layer, grounding, RAG, guardrails, agent evaluation, "
        "prompt injection",
    ),
    "apex": (
        "Apex and SOQL: triggers, governor limits, async processing, "
        "callouts, security enforcement, and the test patterns that keep "
        "them deployable.",
        "Apex, trigger, SOQL, SOSL, governor limit, batch, queueable, "
        "@future, schedulable, test class, CPU time, heap, with sharing, "
        "StripInaccessible",
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
        "query optimisation, deduplication, archival and storage.",
        "data model, data migration, data load, Data Loader, Bulk API, "
        "external id, duplicate, deduplication, skinny table, custom index, "
        "archival, data storage",
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
        "flows, plus bulkification, fault handling, testing and versioning.",
        "Flow, Flow Builder, record-triggered flow, screen flow, scheduled "
        "flow, subflow, fault path, flow element, orchestration, "
        "Process Builder migration, Workflow Rule migration",
    ),
    "integration": (
        "Inbound and outbound integration: REST and SOAP APIs, Bulk API 2.0, "
        "Platform Events, CDC, Pub/Sub, Named Credentials and middleware.",
        "integration, REST API, SOAP API, Bulk API, Platform Event, Change "
        "Data Capture, Pub/Sub, webhook, Named Credential, OAuth, MuleSoft, "
        "Salesforce Connect",
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
        "Platform security and compliance: org hardening, sharing "
        "troubleshooting, encryption, session policy, MFA, monitoring and "
        "incident response.",
        "security, org hardening, Shield, platform encryption, field audit "
        "trail, MFA, SSO, SAML, session policy, guest user, event "
        "monitoring, GDPR, XSS, injection",
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
    """
    match = re.match(r"^/\S+\s*[—–-]\s*(.+)$", heading)
    if match:
        return match.group(1).strip()
    return f"Run the SfSkills {stem} run-time agent"


DOMAIN_REF_RE = re.compile(r"\b(" + "|".join(DOMAIN_ORDER) + r")/[a-z0-9][a-z0-9-]*")


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

def tokens(text: str) -> int:
    """Token estimate: ceil(chars / 4)."""
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def first_sentence(text: str, limit: int = MAX_GLOSS_CHARS) -> str:
    """First sentence of a description, collapsed and truncated to ``limit``."""
    flat = " ".join(text.split())
    match = re.match(r"^(.*?\.)(?:\s|$)", flat)
    sentence = match.group(1) if match else flat
    if len(sentence) > limit:
        sentence = sentence[: limit - 3] + "..."
    return sentence


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
        "Do not hand-edit. Glosses are the first sentence of each package's",
        f"own description, truncated to {MAX_GLOSS_CHARS} characters.",
        "",
    ]
    for skill in entries:
        gloss = first_sentence(skill.get("description", ""))
        lines.append(f"- `skills/{domain}/{skill['name']}/SKILL.md` — {gloss}")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_subagent(agent: dict) -> str:
    domain = agent["domain"] or "platform"
    description = (
        f"{agent['title']}. SfSkills {domain} run-time agent: reads its full "
        f"AGENT.md playbook, cites every skill consulted, returns a confidence "
        f"score, and never deploys to an org. Invoke for the whole workflow, "
        f"not a single lookup."
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


def render_plugin_manifest(registry: dict, agents: list[dict], commands: list[tuple[str, str]]) -> str:
    """`.claude-plugin/plugin.json`.

    Deliberately omits `agents` and `commands`:

    - `agents` REPLACES the default `agents/` scan (plugins-reference, "Path
      behavior rules"). Measured on Claude Code v2.1.209 with a throwaway
      probe plugin: omitting the key loads the flat `agents/*.md` scan
      correctly; a custom file path loads ZERO agents; a directory value is
      rejected with `agents: Invalid input`; and pointing the key at the very
      file the default scan just loaded still yields zero. So declaring it is
      strictly worse than omitting it. The subagents ship to `.claude/agents/`
      instead, per https://code.claude.com/docs/en/sub-agents.
    - `commands` also REPLACES its default scan; omitting it lets the default
      `commands/` scan pick up every existing command file unchanged.
    """
    manifest = {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": PLUGIN_NAME,
        "displayName": "SfSkills — Salesforce AI Skill Library",
        "version": PLUGIN_VERSION,
        "description": (
            f"{registry['skill_count']:,} grounded Salesforce skill packages, "
            f"{len(agents)} run-time agents and {len(commands)} slash commands, "
            "reached through 12 lightweight router skills instead of a flat index."
        ),
        "author": {"name": AUTHOR_NAME, "url": REPO_URL},
        "homepage": f"{REPO_URL}#readme",
        "repository": REPO_URL,
        "license": "Apache-2.0",
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
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def render_marketplace_manifest(registry: dict, agents: list[dict], commands: list[tuple[str, str]]) -> str:
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
            f"Tiered Salesforce library: 12 router skills up front, "
            f"{registry['skill_count']:,} skill packages and {len(agents)} run-time "
            "agents reached on demand."
        ),
        # Must equal plugin.json's version — `claude plugin tag` enforces it.
        "version": PLUGIN_VERSION,
        "author": {"name": AUTHOR_NAME, "url": REPO_URL},
        "homepage": f"{REPO_URL}#readme",
        "repository": REPO_URL,
        "license": "Apache-2.0",
        "category": "development",
        "keywords": ["salesforce", "apex", "flow", "lwc", "agentforce", "well-architected"],
        "tags": ["salesforce", "crm", "apex", "soql", "admin", "architecture"],
        # LOAD-BEARING — see the docstring. Do not remove, and do not add an
        # `agents` key alongside it.
        "skills": [PLUGIN_SKILLS_PATH],
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

    out: dict[Path, str] = {
        PLUGIN_MANIFEST_DIR / "plugin.json": render_plugin_manifest(registry, agents, commands),
        PLUGIN_MANIFEST_DIR / "marketplace.json": render_marketplace_manifest(registry, agents, commands),
        ROUTER_ROOT / "salesforce" / "SKILL.md": render_top_router(registry, agents, commands),
    }
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
    for agent in agents:
        out[SUBAGENT_ROOT / f"{agent['id']}.md"] = render_subagent(agent)

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

    if problems:
        raise SystemExit(
            "ERROR: generated output failed self-check:\n  " + "\n  ".join(problems)
        )


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
    for managed in (PLUGIN_MANIFEST_DIR, ROUTER_ROOT, SUBAGENT_ROOT):
        base = root / managed
        if not base.exists():
            continue
        for path in sorted(base.rglob("*"), reverse=True):
            if path.is_file() and path.relative_to(root) not in keep:
                path.unlink()
                pruned += 1
            elif path.is_dir() and not any(path.iterdir()):
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
    print(f"  {routers} router skill(s)   → {ROUTER_ROOT}/")
    print(f"  {rosters} domain roster(s)  → {ROUTER_ROOT}/salesforce-*/references/")
    print(f"  {subagents} subagent(s)       → {SUBAGENT_ROOT}/")
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

        keep = set(out)
        for managed in (PLUGIN_MANIFEST_DIR, ROUTER_ROOT, SUBAGENT_ROOT):
            base = REPO_ROOT / managed
            if not base.exists():
                continue
            for path in sorted(base.rglob("*")):
                if path.is_file() and path.relative_to(REPO_ROOT) not in keep:
                    drift.append(f"unmanaged: {path.relative_to(REPO_ROOT)}")

    if not drift:
        print(f"OK: {len(out)} plugin artifact(s) match a fresh build — no drift")
        return 0
    print("DRIFT: the committed plugin artifacts do not match a fresh build:")
    for item in drift:
        print(f"  - {item}")
    print("\nTo fix: python3 scripts/build_plugin.py")
    return 1


def measure() -> dict:
    registry = load_registry()
    agents = runtime_agents()
    commands = command_index()
    out = build_outputs()

    router_tokens = 0
    router_skills = 0
    for rel, content in sorted(out.items()):
        if rel.parent.parent != ROUTER_ROOT or rel.name != "SKILL.md":
            continue
        meta = content.split("---")[1]
        name = (re.search(r"^name: *(.+)$", meta, re.M) or [None, ""])[1].strip()
        desc = (re.search(r"^description: *(.+)$", meta, re.M) or [None, ""])[1].strip()
        # Strip the YAML quoting: the model sees the value, not the delimiters.
        if len(desc) >= 2 and desc[0] == '"' and desc[-1] == '"':
            desc = desc[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        router_tokens += tokens(name + desc)
        router_skills += 1

    command_tokens = sum(tokens(stem + heading) for stem, heading in commands)
    tier1 = router_tokens + command_tokens

    flat_chars = sum(len(s["name"]) + len(s["description"]) for s in registry["skills"])
    flat_tokens = tokens_from_chars(flat_chars)
    ratio = round(tier1 / flat_tokens, 4) if flat_tokens else 0.0

    return {
        "router_skills": router_skills,
        "router_tokens": router_tokens,
        "commands": len(commands),
        "command_tokens": command_tokens,
        "agents": len(agents),
        "tier1_tokens": tier1,
        "flat_export_skills": registry["skill_count"],
        "flat_export_tokens": flat_tokens,
        "ratio": ratio,
        "budget_tier1_tokens": BUDGET_TIER1_TOKENS,
        "within_budget": tier1 <= BUDGET_TIER1_TOKENS and ratio <= BUDGET_TIER1_RATIO,
    }


def tokens_from_chars(chars: int) -> int:
    return math.ceil(chars / CHARS_PER_TOKEN)


def run_measure() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    return 0 if result["within_budget"] else 1


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

After a build, verify against the real CLI:
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
    args = parser.parse_args()

    if args.check:
        return run_check()
    if args.measure:
        return run_measure()
    if args.verify_seeds:
        return run_verify_seeds()
    return run_build()


if __name__ == "__main__":
    sys.exit(main())
