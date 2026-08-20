# Salesforce platform landscape — August 2026

## Official Salesforce DX MCP

The official Salesforce DX MCP server exposes more than sixty tools grouped into toolsets and supports individual-tool configuration. Its documentation explicitly warns that enabling all tools can overwhelm model context and offers experimental dynamic discovery. The surface includes both observational and mutating operations such as deploy, test execution, user/permission management, and org management.

### Framework decision

SfSkills does not recreate the official surface and never exposes it unrestricted in product mode. It pins explicit orgs, enables the minimum read operations, normalizes upstream variants, assigns evidence IDs, enforces a separate deny-by-default broker, and preserves upstream version/provenance.

Sources: `SRC-SF-DX-MCP`.

## Headless 360

Salesforce’s Headless 360 beta presents four stable tools—discovery, description, dispatch, and read-only dispatch—backed by a growing skill library. The product rationale is directly relevant: thousands of individual operations create context and scaling problems, while a compact discovery surface can scale independently. The server also supports mutating Salesforce tasks, so “read-only dispatch” or a separate restricted upstream path is essential for SfSkills product authority.

### Framework decision

Use the same small-surface principle for discovery and a brokered evidence interface. SfSkills adds user-job products, evidence/claim contracts, context telemetry, independent review, replay, and known-truth QA rather than copying Headless 360 operations.

Sources: `SRC-SF-HEADLESS-360`, `SRC-SF-HEADLESS-360-BLOG`.

## Skills as the workflow layer

Salesforce Code Analyzer documentation describes skills as folders of instructions, scripts, and resources that load dynamically and explain how to do a job, while tools provide raw system interaction. The documentation also records a June 2026 transition away from the standalone Code Analyzer MCP workflow toward skills.

### Framework decision

Preserve SfSkills packages as governed knowledge/workflow units and use official deterministic tools beneath them. Avoid an MCP-only architecture; adapters need native skills plus a restricted evidence surface.

Sources: `SRC-SF-CODE-ANALYZER-SKILLS`, `SRC-SF-CODE-ANALYZER-MCP-TRANSITION`.

## Agentforce Builder, testing, and observability

The new Agentforce Builder is graph-based, with subagents as nodes, transitions, state variables, routing, and per-subagent evolution. Salesforce provides command-line and API testing/evaluation workflows, and tools such as AgentLens demonstrate graph and finite-state-machine observability over traces.

### Framework decision

SfSkills’ Agentforce Quality Engineer should inspect current Agent Script/subagent/action/test artifacts and use official test results where available. Its own runtime should use explicit state and structured handoffs without pretending to be Agentforce Builder.

Sources: `SRC-SF-AGENTFORCE-BUILDER-2026`, `SRC-SF-AGENT-TESTING-CLI`, `SRC-SF-AGENT-TEST-RUN-EVAL`, `SRC-SF-AGENTLENS`.

## Salesforce Well-Architected

Salesforce Well-Architected provides Trusted, Easy, and Adaptable dimensions and platform-specific patterns/anti-patterns.

### Framework decision

Use these as governed architecture guidance and finding tags where relevant. Do not reduce concrete evidence to a generic score or claim Well-Architected compliance without complete assessment scope.

Sources: `SRC-SF-WAF`.

## Deterministic Salesforce tools remain authoritative

Deployment/test reports, Code Analyzer, metadata APIs, CLI commands, and formal testing systems should parse and observe. Models should interpret, synthesize, prioritize, and explain—not recreate deterministic outputs in prose.
