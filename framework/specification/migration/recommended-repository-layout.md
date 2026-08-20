# Recommended V2 repository layout

```text
framework/
  spec/                    # imported numbered spec or submodule/path
  definitions/
    products/
    agents/
    commands/
    tools/
    policies/
    context-packs/
  schemas/
  core/                    # deterministic runtime modules
  adapters/
    cursor/
    claude/
    copilot/
    vibes/
  qa/
    fixtures/
    scenarios/
    scratch/
  reports/                 # generated, normally gitignored except release reports

skills/                    # existing canonical knowledge corpus
agents/                    # existing compatibility agents and migrated product agents
commands/                  # existing compatibility commands
mcp/sfskills-mcp/          # existing MCP plus normalized V2 evidence tools
integrations/cursor/       # canonical Cursor adapter source if existing convention retained
dist/                      # generated packages
```

The implementation may adapt paths to repository conventions, but it must preserve canonical-versus-generated ownership and avoid parallel hand-maintained definitions.
