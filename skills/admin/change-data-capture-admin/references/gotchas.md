# Gotchas — Change Data Capture Admin

## Gotcha 1: Data Cloud Silently Manages CDC Entity Selections

**What happens:** An admin reviewing CDC entity selection finds objects they did not configure. Alternatively, an admin removes objects from CDC selection and finds that Data Cloud data ingestion for those objects breaks silently — data in Data Cloud becomes stale without any error in Salesforce setup or logs.

**When it occurs:** Any org with active Data Cloud and CRM Data Streams. Data Cloud creates `PlatformEventChannelMember` records for its internal `DataCloudEntities` channel when CRM Data Streams are configured. These appear in the standard CDC Setup UI alongside admin-configured entities.

UNVERIFIED (2026-09-04): the `DataCloudEntities` channel name and the automatic-selection behaviour are not stated in the Metadata API guide, the Object Reference, or the App Limits cheat sheet — those documents describe only `ChangeEvents` and custom `__chn` channels. Confirm the channel name against the org's own retrieved `platformEventChannelMembers/` folder before writing any automation that keys on it. The safe half of this gotcha needs no source: a wildcard retrieve of `PlatformEventChannelMember` returns members that features other than your own created, and re-deploying that folder is what deletes or overwrites them.

**How to avoid:** Before modifying any CDC entity selections in an org with Data Cloud active, review which objects have active CRM Data Streams in Data Cloud Admin. Do not remove or modify any `PlatformEventChannelMember` records on the `DataCloudEntities` channel via Metadata API or Tooling API. Manage Data Cloud CDC requirements through the Data Cloud Admin interface. Document which objects are Data Cloud-managed vs. admin-managed.

---

## Gotcha 2: Enrichment Cannot Be Added to Single-Entity Per-Object Channels

**What happens:** An admin or developer attempts to enrich per-object CDC events (e.g., add `Account.Owner.Region` to `/data/AccountChangeEvent` events). The Tooling API returns an error, or the configuration appears to save but enriched fields never appear in the event payload.

**When it occurs:** Any attempt to add `EnrichedField` records to `PlatformEventChannelMember` records on system-generated per-object channels. Per-object channels are managed by the platform and do not support enrichment configuration.

Grounded part: `enrichedFields` is a field of `PlatformEventChannelMember`, available in API version 51.0 and later, and every enrichment sample in the Metadata API guide (v62 PDF, `PlatformEventChannelMember`, lines ~96047 and ~96150) places it on a member of a custom `__chn` channel. Change events also exclude "any field whose value isn't on the record and is derived from another record or from a formula, except roll-up summary fields" (Object Reference, `StandardObjectNameChangeEvent` > Change Event Fields, lines 5160–5166) — which is why a formula field has nothing to enrich with.

UNVERIFIED (2026-09-04): the Metadata API guide does not state that a member of the standard `ChangeEvents` channel *rejects* `enrichedFields`; it simply never shows one. Treat "custom channel required for enrichment" as the safe design and confirm in a sandbox before telling a subscriber team the standard channel cannot be enriched.

**How to avoid:** For enrichment, create a custom `PlatformEventChannel` (multi-entity channel) via Tooling API or metadata. Add the target objects as `PlatformEventChannelMember` records on this custom channel. Add `EnrichedField` records on the channel member. Subscribe the integration to the custom channel URL. The subscriber will now receive enriched events. Formula fields cannot be enriched fields — only stored persistent fields.

---

## Gotcha 3: CDC Daily Event Limits Are Silently Enforced Without Admin Notification

**What happens:** CDC event delivery silently stops for the remainder of the day once the edition's daily limit is reached. Downstream subscribers continue to be connected but receive no new events. No email, setup alert, or API error notifies the admin that events are being dropped. The gap in change events is discovered later when downstream data is found to be stale.

**When it occurs:** High-volume orgs that enable CDC for many objects or that experience unexpected high-volume periods (month-end, marketing campaigns, large data imports). Enterprise orgs are most at risk with the 25,000 event daily limit.

UNVERIFIED (2026-09-04): the per-edition numbers (50,000 / 25,000 / 10,000) are not printed in the App Limits cheat sheet — its "Platform Event Allocations" section (lines 1244–1252) names a "Change Data Capture Allocations" set covering "the number custom channels, selected entities in a channel, and event delivery" and links out instead of listing values. Read the org's own allocation figures before sizing a design; the mechanism below (delivery stops, nothing tells you) is the part to act on.

**How to avoid:** Monitor `PlatformEventUsageMetric` regularly. Create a scheduled Apex job or Salesforce Flow that queries daily CDC usage and sends an alert email when usage exceeds 70% of the edition limit. For high-volume orgs, estimate CDC event volume before enabling objects for CDC (multiply average daily record modifications by the number of enabled objects). If usage consistently approaches the limit, reduce the number of CDC-enabled objects or upgrade to Performance/Unlimited edition for the higher 50,000 event limit.

---

## Gotcha 4: The Standard `ChangeEvents` Channel Cannot Be Deployed or Retrieved — Only Its Members Can

**What happens:** A team tries to source-control CDC entity selection by retrieving `PlatformEventChannel:ChangeEvents`. The retrieve comes back empty, or a hand-written `ChangeEvents.platformEventChannel-meta.xml` fails to deploy. The team concludes CDC entity selection is click-only and starts configuring it by hand in every sandbox.

**When it occurs:** Any API version 47.0 or later. The Metadata API guide states it plainly: "In API version 47.0 and later, you can't deploy or retrieve the `ChangeEvents` standard channel." (v62 PDF, `PlatformEventChannel` > Usage, line 95918.) The selection itself is fully deployable — it just lives in `PlatformEventChannelMember` components, one per selected entity, each carrying `<eventChannel>ChangeEvents</eventChannel>`.

**How to avoid:** Never ship a channel file for `ChangeEvents`. Ship one member file per entity — `ChangeEvents_LeadChangeEvent.platformEventChannelMember-meta.xml` — and list them under `PlatformEventChannelMember` in package.xml. Only *custom* channels get a `PlatformEventChannel` file. Shapes are in `references/metadata-examples.md`.

---

## Gotcha 5: Channel Member Full Names Collapse Double Underscores, So the File Name Is Not `Channel + Entity`

**What happens:** A member for the custom channel `SalesEvents__chn` is filed as `SalesEvents__chn_AccountChangeEvent`. The deploy fails, or the component is created under a name the manifest does not match, and a later retrieve does not bring it back.

**When it occurs:** Every custom channel (their names always end in `__chn`) and every custom-object change event (`MyObject__ChangeEvent`). The rule is a platform-wide naming constraint, not a CDC one: "Two consecutive underscores in full names designate either a component name suffix or a namespace prefix. In all other cases, two consecutive underscores aren't supported in full names… the member name would be `SalesEvents_chn_AccountChangeEvent` and not `SalesEvents__chn_AccountChangeEvent`." (v62 PDF, `PlatformEventChannelMember` > Underscores in Channel Member Full Names, line ~96190.)

**How to avoid:** Build the full name as `ChannelName_EventName` and then collapse every doubled underscore to a single one — in the file name and in the `<members>` entry only. The element values inside the file keep their real names: `<eventChannel>SalesEvents__chn</eventChannel>`, `<selectedEntity>MyObject__ChangeEvent</selectedEntity>`. The checker in `scripts/` flags a member file whose `eventChannel` has no matching channel in the tree, which is what a mis-collapsed name usually looks like.

---

## Gotcha 6: A Channel Definition Written Before API 47.0 Cannot Be Deployed With a Newer API Version

**What happens:** An older repo (or an org migration from a pre-47.0 package) carries a `PlatformEventChannel` file containing `<channelMembers>` elements. Deployed with a current API version, it fails — the field no longer exists.

**When it occurs:** The `channelMembers` field "is removed in API version 47.0 and later and is available only in API versions 45.0 and 46.0… PlatformEventChannel components created in prior versions can't be deployed using a later API version but you can deploy them in the same API version they were created with." (v62 PDF, `PlatformEventChannel` > Upgrading to Version 47.0 or Later, line ~96003.)

**How to avoid:** Strip every `<channelMembers>` block from the channel file, leaving `channelType` and `label`, and create one `PlatformEventChannelMember` component per entity that was listed inside. For a pre-47.0 `ChangeEvents` channel file, delete the file entirely — that channel can no longer be deployed at all.

---

## Gotcha 7: Deselecting an Object Is a Destructive Deploy, Not an Absent File

**What happens:** An admin removes a member file from source, deploys, and assumes CDC is now off for that object. It is still on, still publishing, and still spending event delivery allocation. The org and the repo have silently diverged.

**When it occurs:** Any CDC entity removal handled as a source diff. The Metadata API guide: "The `createMetadata()` and `deleteMetadata()` calls aren't supported with the `PlatformEventChannelMember` metadata type. To delete a channel member from a channel, deploy `destructiveChanges.xml` for this type and specify the full name of the member." (v62 PDF, `PlatformEventChannelMember` > Usage, line ~96088.) The `ChangeEvents` channel itself can never be deleted, only emptied of members.

**How to avoid:** Turn CDC off with an explicit `destructiveChanges.xml` listing the member full names, and treat "CDC disabled" as a deploy artifact, not a deletion in git. Deleting a *custom* channel is enough on its own — all of its member components go with it. After the destructive deploy, confirm the entity has stopped publishing with the `CHANGE_EVENTS_PUBLISHED` metric.

---

## Gotcha 8: The Obvious `PlatformEventUsageMetric` Query Does Not Compile, and the Per-Object Breakdown Needs a Feature Turned On

**What happens:** A monitoring query invents fields — `UsageCount`, `UsageDate`, `EventType = 'ChangeDataCapture'` — and fails, or returns nothing. A query that does compile still returns org-wide totals when the admin wanted "how many events is Account generating?"

**When it occurs:** Always, for the first query. `PlatformEventUsageMetric` (Object Reference, API 50.0+) exposes `Name` as a *restricted picklist* whose CDC values are `CHANGE_EVENTS_PUBLISHED` and `CHANGE_EVENTS_DELIVERED`; the count field is `Value` (long); `StartDate` and `EndDate` are hourly-granular UTC datetimes used to scope the query. `EventName`, `EventType`, `Client`, `UsageType` and `TimeSegment` "are available only when Enhanced Usage Metrics is enabled" (API 58.0+), and a query using `EventName` or `EventType` must also put `UsageType` in the `SELECT` or `WHERE`. The maximum span between `StartDate` and `EndDate` is 60 days.

**How to avoid:** Start from the query in `references/metadata-examples.md`, which uses only the always-available fields. Before promising per-object CDC reporting, confirm Enhanced Usage Metrics is enabled in the org — without it the answer is org-wide totals and nothing finer, and no amount of query rewriting changes that.

---

## Gotcha 9: `EventBusSubscriber` Sees Only In-Org Subscribers, and Its Backlog Column Is Always `-1` for Change Events

**What happens:** An admin builds a "who is listening to CDC?" inventory from `EventBusSubscriber` and reports that nothing consumes `AccountChangeEvent` — while a middleware Pub/Sub client has been consuming it for months. A second attempt computes subscriber lag as `Tip - Position` (or `LastPublished - LastProcessed`) and gets a nonsense number.

**When it occurs:** Always for external subscribers: `EventBusSubscriber` "represents a trigger, process, or flow that's subscribed to a platform event or a change data capture event. Doesn't include CometD or Pub/Sub API subscribers." (Object Reference, line 131273.) And always for the backlog math: "For high-volume platform events and change events, the value for `Tip` isn't available and is always -1" — the same note carries onto `LastPublished`, which replaces `Tip` as of API 66.0.

**How to avoid:** Treat `EventBusSubscriber` as the *Apex trigger and Flow* inventory only, filtered by `Topic = 'AccountChangeEvent'`, and read `Status` (`Running`, `Error`, `Suspended`, `Repartitioning`) rather than deriving lag. Get the external subscriber list from the integration owners — `integration/change-data-capture-integration` covers that side — and measure external consumption through the `CHANGE_EVENTS_DELIVERED` metric instead.

---

## Gotcha 10: `GAP_` Is a Change Type Your Subscriber Must Handle, and Replaying From `EARLIEST` to Recover Burns Delivery Allocation

**What happens:** A downstream system that switches on `changeType` and only handles `CREATE` / `UPDATE` / `DELETE` / `UNDELETE` silently drops every event that arrives as `GAP_UPDATE` or `GAP_OVERFLOW`, because no branch matches. The integration team's fix — reconnect from the earliest stored event and reprocess — then drives delivery usage far above the normal daily curve.

**When it occurs:** Gap events are a documented change type, not an error state: "For gap events, the change type starts with the `GAP_` prefix" — `GAP_CREATE`, `GAP_UPDATE`, `GAP_DELETE`, `GAP_UNDELETE` — "For overflow events, the change type is `GAP_OVERFLOW`." (Apex Reference Guide, `ChangeEventHeader.changetype`, lines 157299–157304.) The replay window is 72 hours: subscribing with `EARLIEST` "sends new events and any other events less than 72 hours old… Use this option sparingly. Subscribing with the `EARLIEST` option when a large number of event messages are stored can slow performance and exhaust the event delivery allocation." (Metadata API guide, `ManagedEventSubscription`, lines 86615–86629.)

**How to avoid:** Make gap handling a stated acceptance criterion when you hand a channel to a subscriber team: every `GAP_` change type needs an explicit branch, and the safe branch is to re-query the record by `recordIds` rather than act on the event body. UNVERIFIED (2026-09-04): the Apex Reference Guide enumerates the `GAP_` change types but does not describe what a gap event's payload contains, so treat "re-query rather than trust the payload" as the conservative design and confirm against the Change Data Capture Developer Guide before documenting it as platform behaviour. Keep replay-from-`EARLIEST` as an approved incident action with an owner, not a default reconnect setting, and watch `CHANGE_EVENTS_DELIVERED` while a replay runs. Beyond 72 hours there is no replay at all — the recovery path is a data reconciliation, which is why enabling CDC does not remove the need for a periodic full sync.
