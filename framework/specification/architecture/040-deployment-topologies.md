# Deployment topologies

The framework defines one behavior contract across multiple deployments. A topology cannot claim a stronger guarantee than its controls prove.

## 1. Local single-user

```text
Cursor/Claude/VS Code
  -> local plugin/skills/commands
  -> local SFAEF runtime and evidence broker
  -> local Salesforce CLI and explicit authorized orgs
  -> local external DX project
  -> .sfskills/runs
```

Best for the initial product. Credentials remain in existing Salesforce CLI stores. The framework records aliases and redacted identities, not tokens. Local hooks can provide stronger shell/MCP interception where supported.

## 2. Offline fixture/replay

No network or org access. The user runs a captured fixture or replay bundle. Useful for installation, demos, deterministic regression, privacy-sensitive review, and product comparisons. It cannot claim current-org truth.

## 3. Team policy with local execution

Teams distribute signed policy/context/scenario packages while developers execute locally. Shared controls may define allowed org aliases, retention, source tiers, benchmark versions, and required review gates. Local user credentials remain outside the package.

## 4. Enterprise evidence gateway

A controlled service mediates org access with identity, RBAC, audit, rate limits, data minimization, and private retention. Hosts call the gateway rather than receiving broad Salesforce credentials. The service must return the same normalized evidence objects and must not weaken local claim/evidence semantics.

## 5. CI quality lane

Credential-free CI runs schemas, fixtures, policies, plugin generation, context tests, and package/replay verification. Protected scheduled/manual jobs may run persistent read-only org probes. No untrusted pull request receives Salesforce credentials.

## 6. Scratch-org behavioral QA

A protected runner creates a one-day disposable scratch org, installs/deploys versioned scenario setup, runs validation/tests, retrieves evidence through product read-only tools, invokes the actual host/product, grades known truth, sanitizes artifacts, and destroys the org in an unconditional cleanup block.

The setup runner and product broker are separate processes/authority profiles. The product cannot invoke scratch setup.

## 7. Host portability

Cursor is the primary V2 host because it can package native skills, subagents, commands, MCP, and hooks. Claude Code and VS Code/Copilot use the same product/evidence/context contracts through thinner adapters. Agentforce Vibes is both a host candidate and an upstream Salesforce environment.

Portable Agent Plugins may carry skills and MCP, while host-specific packages add commands, subagents, hooks, and policy UX. Portability means behavior and evidence consistency, not identical UI.
