# Claude Code adapter

Preserve the existing SfSkills tiered router and plugin compatibility while adding V2 products incrementally.

Use:

- Agent Skills for progressive product/domain knowledge;
- focused plugin agents for isolated evidence/review roles;
- hooks/permissions where supported;
- restricted SfSkills MCP broker;
- generated product commands or skills consistent with current Claude guidance.

Do not rewrite all current Claude agents during V2. Migrate a product path and compare behavior against the existing route. Record plugin version, MCP configuration, and host limitations in every smoke run.
