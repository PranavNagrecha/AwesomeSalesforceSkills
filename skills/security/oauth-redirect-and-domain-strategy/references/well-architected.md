# Well-Architected Notes — OAuth Redirect / Domain

## Relevant Pillars

- **Security** — strict callback matching prevents open-redirect and
  auth-code interception.
- **Reliability** — sandbox refresh + domain changes are the #1 source
  of OAuth outages; planning matters.
- **Operational Excellence** — inventory of callback URIs + audit of
  hardcoded URLs is ongoing work.

## Architectural Tradeoffs

- **login.salesforce.com vs My Domain host:** My Domain is preferred
  (fewer redirects, fewer library quirks) at the cost of per-env
  configuration.
- **Short My Domain name vs descriptive:** short wins at the cost of a
  slightly less obvious host.
- **One Connected App for all envs vs per-env Connected Apps:** one app
  with multi-env callback list is simpler; per-env apps give tighter
  blast radius at the cost of client-side app-id management.

## Hygiene

- Track Connected App + callback URI changes in source control.
- Redirect URI mismatches dashboard.
- Enhanced Domains audit on every release.

## Official Sources Used

- Connected App OAuth —
  https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm
- My Domain —
  https://help.salesforce.com/s/articleView?id=sf.domain_name_overview.htm
- Enhanced Domains —
  https://help.salesforce.com/s/articleView?id=sf.domain_name_enhanced_domains_overview.htm
