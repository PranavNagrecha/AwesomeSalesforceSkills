---
name: connect-rest-api-patterns
description: "Use Connect REST API for Chatter, feeds, communities, and CMS content instead of querying underlying SObjects. NOT for custom business object CRUD."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "connect rest api chatter"
  - "post feed item api"
  - "experience cloud cms api"
  - "connect api salesforce"
tags:
  - connect-rest
  - chatter
  - cms
inputs:
  - "feature area (Chatter, CMS, Communities)"
  - "required payload"
outputs:
  - "REST call examples + Apex ConnectApi equivalents"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Connect REST API Patterns

Connect REST API exposes Chatter feeds, CMS content, Experience Cloud, and moderation APIs with richer shapes and side-effects than raw SObject access. Use it when the business operation is 'post a feed item with mentions' or 'publish CMS content' rather than 'insert FeedItem row'.

## When to Use

Chatter posts with mentions / rich text, CMS content authoring, community moderation, reports filters at scale.

Typical trigger phrases that should route to this skill: `connect rest api chatter`, `post feed item api`, `experience cloud cms api`, `connect api salesforce`.

## Recommended Workflow

1. Identify the Connect resource (`/connect/communities/{id}/chatter/feed-elements`).
2. Prefer `ConnectApi` Apex namespace over REST when inside Apex — same capability, better typing.
3. Pagination via `nextPageUrl` — don't compute offsets manually.
4. Authenticate with Named Credential + OAuth for external callers.
5. Test with low-privilege users to catch perm gaps before go-live.

## Key Considerations

- Connect API respects sharing; raw SObject queries as System Admin can mask issues.
- Response payloads are verbose; request only the fields you need via `?include` where supported.
- CMS endpoints require Experience Cloud license.
- Chatter posts via Connect create notifications — posting from a trigger can cascade.

## Worked Examples (see `references/examples.md`)

- *Post feed item with mention* — Notify record owner
- *CMS content publish* — Publish a Knowledge article

## Common Gotchas (see `references/gotchas.md`)

- **Missing community context** — Post appears in wrong feed.
- **Sharing mismatch** — Integration user can't post on behalf of another.
- **Verbose payload bloat** — Response 500kB.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Inserting FeedItem directly when mentions matter
- Manual pagination math
- Missing community context

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
