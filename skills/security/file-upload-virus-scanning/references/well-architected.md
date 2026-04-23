# Well-Architected Notes — File Upload Virus Scanning

## Relevant Pillars

- **Security** — scan is a primary defense for any multi-tenant upload surface; absence is a Critical finding for customer-facing orgs.
- **Reliability** — explicit states and rescan strategy prevent silent failures.
- **User Experience** — honest pending/infected messaging beats silent blocking.

## Architectural Tradeoffs

- **Pre-save block vs post-save async:** pre-save is safer but blocks the user; post-save is smoother but opens a pending window.
- **In-platform scan vs middleware:** in-platform keeps architecture simple; middleware keeps untrusted bytes out of storage.
- **Fail-open vs fail-closed on scanner error:** fail-open favors availability; fail-closed favors security.

## Anti-Patterns

1. Scanning only some surfaces.
2. Deleting infected files (audit trail loss).
3. No scheduled rescan for files uploaded before newer signatures.

## Official Sources Used

- Salesforce Files Connect / ContentVersion docs — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_objects_contentversion.htm
- Salesforce Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/trusted/secure
- Common scanning services: ClamAV, Cloudmersive, OPSWAT MetaDefender (vendor docs)
