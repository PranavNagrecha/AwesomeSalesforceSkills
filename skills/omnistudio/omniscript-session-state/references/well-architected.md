# Well-Architected Notes — OmniScript Session State

## Relevant Pillars

- **Reliability** — session loss is a top user complaint for long
  OmniScripts.
- **User Experience** — seamless resume beats "start over."
- **Security** — PII stored mid-flow is a compliance surface.

## Architectural Tradeoffs

- **Custom object vs native tracking:** custom objects give query and
  audit power; native is simpler but opaque.
- **Short expiry vs user convenience:** short expiry reduces risk but
  increases frustration; tier by data sensitivity.
- **Big Object vs custom object:** Big Object handles volume; custom
  object handles query shape.

## Official Sources Used

- OmniScript Tracking — https://help.salesforce.com/s/articleView?id=sf.os_omniscript_tracking.htm
- OmniScript Save/Resume — https://help.salesforce.com/s/articleView?id=sf.os_use_save_for_later.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
