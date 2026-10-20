# Well-Architected Notes — Apex Connect Api Chatter

## Relevant Pillars

### Security

Chatter posts inherit the feed parent's sharing, but the author of the post is still the running user. Posting as a System Administrator to a record the user-in-question can't see creates an information leak in notifications. Always consider who the running user is, and prefer mentioning users who have legitimate access to the parent.

### Reliability

Chatter can be disabled, rate-limited, or experience transient outages. A Chatter post failing should never abort the primary business transaction (a trigger that escalates the case and posts to Chatter should not un-escalate the case because the post failed).

## Architectural Tradeoffs

- **ConnectApi vs FeedItem DML:** ConnectApi supports the full capability set (mentions, files, polls, links). DML supports plain-text posts only, and does not produce notifications on mentions. Use ConnectApi unless you have a proven reason not to.
- **Sync vs async posting:** Sync posts inside a trigger add governor cost and failure-mode coupling to the primary transaction. Async posting (Queueable) decouples reliability but adds enqueue limits. For critical notifications, use `apex-custom-notifications-from-apex` rather than Chatter.
- **Chatter vs Custom Notifications:** Chatter is a collaboration feed; Custom Notifications are directed bell/mobile alerts. For guaranteed-delivery notifications, use Custom Notifications. For collaboration context ("here's what I just did, team"), use Chatter.

## Anti-Patterns

1. **Literal `@` strings in FeedItem DML** — looks right in UI, doesn't notify anyone.
2. **Hardcoded Network Id** — breaks when the community Id differs between sandbox and prod.
3. **ConnectApi in tests without `SeeAllData=true` or a `setTest*` registration** — the test fails (Apex Developer Guide 264 L26331-26335); keep the `SeeAllData` tests few and test payload assembly in isolation.
4. **Per-record ConnectApi call in a trigger** — governor-limit disaster at bulk sizes.

## Official Sources Used

- Apex Reference — ConnectApi Namespace: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_namespace_ConnectApi.htm
- Apex Reference — ConnectApi.ChatterFeeds: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ConnectAPI_ChatterFeeds_static_methods.htm
- Chatter REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/intro.htm
- Apex Reference — Testing ConnectApi: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_connectapi_test_methods.htm
- Apex Developer Guide, Winter '27 (264) — Connect in Apex testing: most methods need `@IsTest(SeeAllData=true)`, some need `setTest*` registration stated in the method's Usage section (L26331-26335, example L26360-26377), runs as the context user without `runAs` (L26329-26330); supports Gotcha 2, anti-patterns 3 and 5, and Example 3
- Apex Developer Guide, Winter '27 (264) — "Total heap size" 10 MB sync / 25 MB async (L19780) and the uncatchable `System.LimitException` footnote (L19853), supporting Gotcha 7; Metadata API 264 `ApexSettings.enableEnforceSummer26ApexHeapLimit` (L113855-113862) for the Winter '27-only nonproduction opt-out
- Salesforce Help — Chatter feed tracking: https://help.salesforce.com/s/articleView?id=sf.collab_feed_tracking_overview.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
