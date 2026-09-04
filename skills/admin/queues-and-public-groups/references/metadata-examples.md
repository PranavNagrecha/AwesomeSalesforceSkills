# Metadata Examples — Queues and Public Groups

Deployable shapes taken from the Metadata API Developer Guide (v62 PDF, `Queue` and `Group` types). Queues are the routing targets every assignment rule, escalation action, and Omni-Channel routing configuration names by developer name, so they deploy **first** (`admin/assignment-rules` → `references/migration-and-sandbox.md`).

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Queue | `Queue` (wildcard `*` allowed) | `queues/Tier_1_Support.queue-meta.xml` | 24.0+; `queueMembers` and `queueRoutingConfig` 42.0+; `doesIncludeBosses` 67.0+ |
| Public group | `Group` | `groups/Support_Agents_EMEA.group-meta.xml` | 24.0+ |

The developer name is the file name; `name` inside the file is the label.

## Case queue with mixed membership and an Omni-Channel routing configuration

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Queue xmlns="http://soap.sforce.com/2006/04/metadata">
    <doesIncludeBosses>true</doesIncludeBosses>
    <doesSendEmailToMembers>false</doesSendEmailToMembers>
    <email>tier1-support@acme.example</email>
    <name>Tier 1 Support</name>
    <queueMembers>
        <publicGroups>
            <publicGroup>Support_Agents_EMEA</publicGroup>
        </publicGroups>
        <roleAndSubordinatesInternal>
            <roleAndSubordinateInternal>Support_Manager</roleAndSubordinateInternal>
        </roleAndSubordinatesInternal>
        <roles>
            <role>Support_Agent</role>
        </roles>
        <users>
            <user>jane.doe@acme.example</user>
        </users>
    </queueMembers>
    <queueRoutingConfig>Case_Routing_Least_Active</queueRoutingConfig>
    <queueSobject>
        <sobjectType>Case</sobjectType>
    </queueSobject>
</Queue>
```

How to read it:

- `queueSobject` lists every object the queue may own. The guide enumerates `Case`, `ContactRequest`, `Lead`, `ServiceContract`, `Task` (48.0+), and custom objects (`ObjA__c`). A rule that targets a queue whose list omits the object fails at deploy or at routing time.
- `queueMembers` accepts four member sources. `users/user` is a **username**, which differs per org after a sandbox refresh; prefer roles and public groups, which deploy by developer name (`roleAndSubordinatesInternal` is the current internal-only shape; see gotchas #6 for the rename).
- `email` plus `doesSendEmailToMembers`: with `false`, only the queue address is notified when a record lands in the queue (gotchas #5). With `true`, every member is emailed on every arrival.
- `doesIncludeBosses` is the "Grant Access Using Hierarchies" checkbox. Leave it `true` unless managers must not see queue-owned records.
- `queueRoutingConfig` is the developer name of a `QueueRoutingConfig`. Omitting it on an Omni-Channel org means the queue is never pushed (`admin/omni-channel-routing-setup` gotchas #1). Deploy the routing configuration before the queue.

## Lead queue for assignment-rule targets (no Omni-Channel)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Queue xmlns="http://soap.sforce.com/2006/04/metadata">
    <doesSendEmailToMembers>true</doesSendEmailToMembers>
    <email>west-sales@acme.example</email>
    <name>West Region Queue</name>
    <queueMembers>
        <roles>
            <role>West_Sales_Rep</role>
        </roles>
    </queueMembers>
    <queueSobject>
        <sobjectType>Lead</sobjectType>
    </queueSobject>
</Queue>
```

`assignedTo` in the Lead assignment rule is `West_Region_Queue`, the file name, not the label.

## Public group used as a queue member and a sharing-rule target

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Group xmlns="http://soap.sforce.com/2006/04/metadata">
    <doesIncludeBosses>true</doesIncludeBosses>
    <name>Support Agents EMEA</name>
</Group>
```

Group **membership** is not part of `Group` metadata; add members in Setup or with `GroupMember` records via the API after deploy. Deploy the group before any queue or sharing rule that names it.

## package.xml and CLI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Support_Agents_EMEA</members>
        <name>Group</name>
    </types>
    <types>
        <members>Tier_1_Support</members>
        <members>West_Region_Queue</members>
        <name>Queue</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
sf project retrieve start --metadata Queue --target-org my-sandbox
python3 skills/admin/queues-and-public-groups/scripts/check_queues.py --help
sf project deploy start --source-dir force-app/main/default/queues --target-org my-sandbox
```

Verify after deploy:

```sql
SELECT Queue.DeveloperName, Queue.Email, SobjectType FROM QueueSobject WHERE SobjectType IN ('Case','Lead')
SELECT GroupId, Group.DeveloperName, UserOrGroupId FROM GroupMember WHERE Group.Type = 'Queue'
```
