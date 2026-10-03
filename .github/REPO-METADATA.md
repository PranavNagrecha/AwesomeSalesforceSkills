# Proposed GitHub repository metadata

For the owner to paste (gh is not authenticated in the release worktree).
Repository: `PranavNagrecha/AwesomeSalesforceSkills`.

## Description (283 characters, limit 350)

```
Salesforce AI skill library: 1,040 skill packages, 70 run-time agents and an MCP server that give Claude Code and other AI assistants senior-practitioner Apex, LWC, Flow, Agentforce and admin judgment, grounded in official Salesforce docs. Source-available (PolyForm Small Business).
```

## Topics (20)

```
salesforce
salesforce-apex
lwc
salesforce-flow
agentforce
claude-code
claude-code-plugin
mcp
mcp-server
ai-agents
skills-library
salesforce-devops
sfdx
salesforce-admin
well-architected
knowledge-base
python
developer-tools
salesforce-architect
prompt-engineering
```

## Apply

```bash
gh repo edit PranavNagrecha/AwesomeSalesforceSkills \
  --description "Salesforce AI skill library: 1,040 skill packages, 70 run-time agents and an MCP server that give Claude Code and other AI assistants senior-practitioner Apex, LWC, Flow, Agentforce and admin judgment, grounded in official Salesforce docs. Source-available (PolyForm Small Business)." \
  --homepage "https://pranavnagrecha.github.io/AwesomeSalesforceSkills/" \
  --add-topic salesforce,salesforce-apex,lwc,salesforce-flow,agentforce,claude-code,claude-code-plugin,mcp,mcp-server,ai-agents,skills-library,salesforce-devops,sfdx,salesforce-admin,well-architected,knowledge-base,python,developer-tools,salesforce-architect,prompt-engineering
```

The counts in the description (1,040 skills, 70 run-time agents) match
`python3 scripts/check_doc_counts.py` at release/1.3.0; update them if the
corpus changes before you apply this. The `--homepage` value assumes GitHub
Pages is enabled (Settings > Pages > Source: GitHub Actions); drop that flag
otherwise.
