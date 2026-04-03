# Well-Architected Notes - Static Resources In LWC

## Relevant Pillars

### Performance

Static resources affect page weight and initialization time directly. Controlled loading, smaller payloads, and avoiding duplicate initialization keep components responsive.

### Operational Excellence

Versioned resource names, documented internal paths, and consistent loading patterns make upgrades and rollback safe. Asset sprawl and ad hoc naming do the opposite.

## Architectural Tradeoffs

- **Library convenience vs platform fit:** a third-party dependency can accelerate delivery, but it adds security and lifecycle review cost.
- **Single-file uploads vs zipped packages:** separate resources are simple at first, while zipped packs scale better for coordinated assets.
- **Overwrite-in-place vs versioned names:** overwriting is convenient short term, but versioned names give clearer rollback and deployment behavior.

## Anti-Patterns

1. **Remote CDN loading in LWC** - the deployment model escapes Salesforce asset governance.
2. **Repeated script loads per rerender** - library initialization multiplies with every component update.
3. **Undocumented zip path contracts** - resource consumers break on package refresh because internal file paths changed silently.

## Official Sources Used

- Access Static Resources - https://developer.salesforce.com/docs/platform/lwc/guide/create-resources.html
- platformResourceLoader - https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-platform-resource-loader.html
- StaticResource Metadata Type - https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_staticresource.htm
