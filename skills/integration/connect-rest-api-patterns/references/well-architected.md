# Well-Architected Notes — Connect REST API Patterns

**Reliability:** Connect encodes the business operation — post with a mention, publish
content, moderate — where raw SObject access encodes only the row that results. The gap
between the two is where silent failures live: a `FeedItem` insert succeeds and produces
a post with no mention and no notification, and nothing about the successful DML says the
requirement was missed.

**Performance:** inside Apex, the `ConnectApi` namespace is the same capability
in-process — no callout, no API allocation consumed, strongly typed. Raw Connect REST is
for callers outside the org. Feed pagination is cursor-based because feeds mutate while
you read them; offset arithmetic duplicates and skips.

## Official Sources Used

- ConnectApi Namespace overview — the Apex surface for Chatter, communities and CMS — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/connectapi_namespace_overview.htm
- ConnectApi.ChatterFeeds class — postFeedElement and feed retrieval — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/connectapi_class_chatterfeeds.htm
- Connect REST API Developer Guide — resources, cursor pagination and response shapes — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Network class — getNetworkId() for the current community context — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Network.htm
- FeedItem object reference — what the raw SObject can and cannot represent — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_feeditem.htm
