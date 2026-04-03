

Chat REST API Developer Guide
## Version 66.0, Spring ’26
Last updated: January 30, 2026

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
Chapter  1:  Overview. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Chapter 2: Getting Started with the Chat REST API. . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
Chapter 3: Request Headers. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
Chapter 4: Your Message Long Polling Loop. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
Chapter 5: Using Estimated Wait Time Instead of Queue Position for a Chat Session
(Beta). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
Chapter 6: Chat REST API Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
Create  a  Chat  Session. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
SessionId. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
Create a Chat Visitor Session. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
ChasitorInit. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
ReconnectSession. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
ChasitorResyncState. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
Monitor  Chat  Activity. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
ChasitorNotTyping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
ChasitorSneakPeek. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
ChasitorTyping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
ChatEnd. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
ChasitorIdleTimeoutWarningEvent. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
ChatMessage. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
CustomEvent. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
Messages. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
MultiNoun. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
Customize the Chat Visitors’ Experience. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
Settings. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
Availability. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
Breadcrumb. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
VisitorId. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
SensitiveDataRuleTriggered for Agents. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
SensitiveDataRuleTriggered  for  Chasitors. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
Chapter 7: Request Bodies for Chat REST API. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Chapter 8: Response Bodies for Chat REST API . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37
Chapter 9: Chat REST API Data Types. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 52
Chapter 10: Status Codes and Error Responses. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61

Index. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
## Contents

CHAPTER 1Overview
## EDITIONS
Available in: Salesforce
Classic and Lightning
## Experience
Available in: Performance
Editions and in Developer
Edition orgs that were
created after June 14, 2012
Available in: Essentials,
Unlimited, and Enterprise
Editions with Service Cloud
or Sales Cloud
Take Chat to a native mobile app or a custom client using the Chat REST API.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in
maintenance mode until then. During this phase, you can continue to use chat, but we no
longer recommend that you implement new chat channels. To avoid service interruptions
to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the
chat features that you love plus asynchronous conversations that can be picked back up at
any time. Learn about chat retirement in Help.
You don’t have to rely on Visualforce to develop customized chat windows. With the REST resources
in this guide, you can extend the functionality of chat windows beyond simple HTML and JavaScript
environments that merge seamlessly into your company’s own applications.
Note:  Chat REST API doesn’t support building custom clients that work with Einstein Bots.
See Einstein Bots API and SDK.
## SEE ALSO:
Embedded Service SDK for iOS Developer Guide
Embedded Service SDK for Android Developer Guide
## 1

CHAPTER 2Getting Started with the Chat REST API
Learn how to start, confirm, and end a Chat session with the Chat REST API.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in maintenance mode until then. During
this phase, you can continue to use chat, but we no longer recommend that you implement new chat channels. To avoid service
interruptions to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features that you
love plus asynchronous conversations that can be picked back up at any time. Learn about chat retirement in Help.
Retrieve Your Chat API Endpoint
Your Chat API endpoint is a unique URL that lets you access data from your organization’s Chat sessions. To find your organization’s Chat
API endpoint:
1.From Setup, in the Quick Find box, enter ChatSettings, and then select Chat Settings.
2.Retrieve the hostname from the Chat API Endpoint. The hostname is the URL without “/chat/rest/” at the end, for example,
“https://yourChatApiEndpoint.com”. Substitute hostname in the Chat API endpoints with this URL.
Start a Chat Session
To start a Chat session, send a SessionId request. Replace hostname with the URL that you retrieved from Chat API Endpoint.
GET https://hostname/chat/rest/System/SessionId/
Use these Request Headers.
## •
## X-LIVEAGENT-AFFINITY
## •
## X-LIVEAGENT-API-VERSION
Confirm the Chat Session Started
A ChatRequestSuccess response tells you that the Chat session started.
## {
queuePosition:1,
estimatedWaitTime:120,
## 2

geoLocation:{
countryCode:"US",
countryName:"UnitedStatesof America",
region:"CA",
city:"SanFrancisco",
organization:Salesforce,
latitude:37.793880,
longitude:-122.395114
## },
url:"http://yoursite",
oref:"http://www.google.com?q=yoursite",
postChatUrl:"http://yoursite/postchat",
customDetails:[
## {
label:"E-mailAddress",
value:"jon@example.com",
transcriptFields:[
"c__EmailAddress"
## ],
displayToAgent:true
## }
## ],
visitorId:"acd47048-bd80-476e-aa33-741bd5cb05d3"
## }
Then wait for a ChatEstablished on page 22 response. That response tells you that an agent accepted the chat session.
## {
name:"AndyL.",
userId:"f1dda237-57f8-4816-b8e8-59775f1e44c8",
sneakPeekEnabled:true
## }
Now you’re ready to send, for example, Messages requests. Before you send further requests, wait until you receive the ChatRequestSuccess
and ChatEstablished responses, otherwise the API throws a NullPointer exception, and you receive a 500 error.
End the Chat Session
The Chat session ends when you send a ChatEnd request or send a DELETESessionId request. In both request types,
X-LIVEAGENT-SESSION-KEY is the unique ID of the Chat session that you want to end.
Here’s the ChatEnd request.
https://hostname/chat/rest/Chasitor/ChatEnd
Use these Request Headers.
## •
## X-LIVEAGENT-AFFINITY
## •
## X-LIVEAGENT-API-VERSION
## •
## X-LIVEAGENT-SESSION-KEY
## •
## X-LIVEAGENT-SEQUENCE
## 3
Getting Started with the Chat REST API

Here’s the SessionId request.
DELETEhttps://hostname/chat/rest/System/SessionId/X-LIVEAGENT-SESSION-KEY
Use these Request Headers.
## •
## X-LIVEAGENT-AFFINITY
## •
## X-LIVEAGENT-API-VERSION
## 4
Getting Started with the Chat REST API

CHAPTER 3Request Headers
Each Chat REST API resource requires one or more headers to make a request.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in maintenance mode until then. During
this phase, you can continue to use chat, but we no longer recommend that you implement new chat channels. To avoid service
interruptions to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features that you
love plus asynchronous conversations that can be picked back up at any time. Learn about chat retirement in Help.
Not all resources require all of the available request headers. Each resource indicates which headers are required to make a request.
The following headers are available:
DescriptionHeader Syntax
The Salesforce API version for the request.X-LIVEAGENT-API-VERSION
The system-generated ID used to identify the Chat session on the Chat servers. This
affinity token is included in the response body of the SessionId request.
## X-LIVEAGENT-AFFINITY
The unique ID associated with your Chat session.X-LIVEAGENT-SESSION-KEY
Note:  Your session key shouldn’t be shared or sent over insecure channels, as it
allows access to potentially sensitive chat information.
The sequence of messages you have sent to the Chat server to help the Chat server avoid
processing duplicate messages. This number should be increased by one with every
new request.
## X-LIVEAGENT-SEQUENCE
## 5

CHAPTER 4Your Message Long Polling Loop
Message long polling notifies you of events that occur on the Chat server for your Chat session.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in maintenance mode until then. During
this phase, you can continue to use chat, but we no longer recommend that you implement new chat channels. To avoid service
interruptions to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features that you
love plus asynchronous conversations that can be picked back up at any time. Learn about chat retirement in Help.
When you start a request, all pending messages get immediately delivered to your session. If there are no pending messages, the
connection to the server will remain open. The Messages poll will return one payload of messages from the server when they become
available, and you’ll have to open a new Messages connection to receive future data.
You’ll receive a 200 (“OK”) response code and a resource that contains an array of the remaining messages. If no messages were received,
you will receive a 204 (“No Content”) response code.
When you receive a 200 (“OK”) or 204 (“No Content”) response code, immediately perform another Messages request to continue
to retrieve messages that are registered on the Chat server.
Warning:  If you don’t make another Messages request to continue the messaging loop, your session will end after a system
timeout on the Chat server.
If you don’t receive a response within the number of seconds indicated by the clientPollTimeout property in your SessionId
request, your network connection to the server is likely experiencing an error, so you should terminate the request.
To initiate a long polling loop, perform a Messages request.
## SEE ALSO:
## Messages
SessionId
Status Codes and Error Responses
## 6

CHAPTER 5Using Estimated Wait Time Instead of
Queue Position for a Chat Session (Beta)
By default, the Chat API returns queue position information that you can relay to customers. However,
you can also receive the estimated wait time in addition to the queue position. Sometimes, the estimated
wait time more effectively conveys the right information to customers than a queue position number.
This feature is available in API version 47.0 and later.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in
maintenance mode until then. During this phase, you can continue to use chat, but we no longer
recommend that you implement new chat channels. To avoid service interruptions to your
customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features
that you love plus asynchronous conversations that can be picked back up at any time. Learn about
chat retirement in Help.
Note:  As a beta feature, Estimated Wait Time is a preview and isn’t part of the “Services” under
your main subscription agreement with Salesforce. Use this feature at your sole discretion, and
make your purchase decisions only on the basis of generally available products and features.
Salesforce doesn’t guarantee general availability of this feature within any particular time frame
or at all, and we can discontinue it at any time. This feature is for evaluation purposes only, not for
production use. It’s offered as is and isn’t supported, and Salesforce has no liability for any harm
or damage arising out of or in connection with it. All restrictions, Salesforce reservation of rights,
obligations concerning the Services, and terms for related Non-Salesforce Applications and Content
apply equally to your use of this feature.
The following algorithm is used to calculate the wait time:
## A = (0.9* A′) + (0.1* W)
## Where:
## •
A′ is the previous value for A. If no previous value exists, this value is W.
## •
W is the wait time of the chat that has most recently been accepted.
The value returned is the value of A minus the time already spent waiting.
Additional algorithm details:
## •
This value is calculated separately for each chat button.
## •
A is recalculated each time a chat is accepted.
## •
0 is returned if the result is less than 0.
## •
-1 is returned when the value cannot be calculated.
To use this feature, specify that you want the estimated wait time from the Settings request (by setting
Settings.needEstimatedWaitTime to 1) and the Availability request (by setting
Availability.needEstimatedWaitTime to 1). When this value is set to 1, the response
includes the estimated wait time for each button ID requested.
If receiveQueueUpdates is set when initializing the session, ChatRequestSuccess and QueueUpdate
will both contain the estimated wait time (in seconds) in their responses.
## 7

CHAPTER 6Chat REST API Resources
To perform a POST or GET request, create and send an HTTP request with the appropriate parameters or request body.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in maintenance mode until then. During
this phase, you can continue to use chat, but we no longer recommend that you implement new chat channels. To avoid service
interruptions to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features that you
love plus asynchronous conversations that can be picked back up at any time. Learn about chat retirement in Help.
The Chat REST API requests let you begin new chat sessions between agents and chat visitors and monitor the chat activity that occurs.
## IN THIS SECTION:
Create a Chat Session
To create a new Chat session, you must call the SessionId request.
Create a Chat Visitor Session
To create or reestablish a chat visitor session using the Chat REST API, you must make certain requests.
## Monitor Chat Activity
Chat requests indicate when certain activities occurred during a chat session.
Customize the Chat Visitors’ Experience
With the Chat visitor REST API resources, you can establish your chat visitors’ experience with Chat in custom mobile applications.
Create a Chat Session
To create a new Chat session, you must call the SessionId request.
## IN THIS SECTION:
SessionId
Establishes a new Chat session. The SessionId request is required as the first request to create every Chat session.
SessionId
Establishes a new Chat session. The SessionId request is required as the first request to create every Chat session.
## Syntax
## URI
https://hostname/chat/rest/System/SessionId/
https://hostname/chat/rest/System/SessionId/X-LIVEAGENT-SESSION-KEY
Available since release
This resource is available in API versions 29.0 and later.
## 8

## Formats
## JSON
HTTP methods
GET—Creates a session. Don't pass X-LIVEAGENT-SESSION-KEY to the URL.
DELETE—Deletes the session. Pass X-LIVEAGENT-SESSION-KEY, the session key, to the URL.
Request headers
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-API-VERSION
Request body
## None
Request parameters
## None
## Response Body
SessionId response
## SEE ALSO:
## Your Message Long Polling Loop
Create a Chat Visitor Session
To create or reestablish a chat visitor session using the Chat REST API, you must make certain requests.
## IN THIS SECTION:
ChasitorInit
Initiates a new chat visitor session. The ChasitorInit request is always required as the first POST request in a new chat session.
ReconnectSession
Reconnect a customer’s chat session on a new server if the session is interrupted and the original server is unavailable.
ChasitorResyncState
Reestablishes the chat visitor’s state, including the details of the chat, after a ReconnectSessionrequest is completed.
ChasitorInit
Initiates a new chat visitor session. The ChasitorInit request is always required as the first POST request in a new chat session.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChasitorInit
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
## 9
Create a Chat Visitor SessionChat REST API Resources

HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
ChasitorInit request
Response body
## None
ReconnectSession
Reconnect a customer’s chat session on a new server if the session is interrupted and the original server is unavailable.
This request should only be made if you receive a 503 response status code, indicating that the affinity token has changed for your Chat
session. When you receive a 503 response status code, you must cancel any existing inbound or outbound requests.
The data in outbound requests will be temporarily stored and resent once the session is reestablished. Upon receiving the response for
the ReconnectSession request, you can start polling for messages.
The first response will be a ChasitorSessionData message containing the data from the previous session that will be restored once the
session is reestablished. After receiving that message, you can proceed to send the existing messages that were canceled upon receiving
the 503 response status code.
## Syntax
## URI
https://hostname/chat/rest/System/ReconnectSession
Available since release
This resource is available in API versions 37.0 and later.
## Formats
## JSON
HTTP methods
## GET
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## 10
ReconnectSessionChat REST API Resources

Request parameters
DescriptionTypeName
The event offset from the most recent Messages request that your
client received.
NumberReconnectSession.offset
Query parameters
## None
Request body
## None
Response body
ReconnectSession
Example: Your REST client can get a 503 Invalid Affinity Token response, for example, to a long poll request
(/chat/rest/System/Messages).
No matter which kind of request gets the 503 response, you must send a /chat/rest/System/ReconnectSession
request to finish the handover process.
Method:GET
## URL:
<!--Changethe liveagentpoolto the correctone for yourorg.-->
https://LiveAgentPool.salesforceliveagent.com/chat/rest/System/
ReconnectSession?ReconnectSession.offset=54647226
## Headers:
## X-LIVEAGENT-AFFINITY:
null[theliteralstring“null”]
## X-LIVEAGENT-API-VERSION:
## 42
## X-LIVEAGENT-SESSION-KEY:
4eb90106-3410-4dd0-8f04-c4facf90a929!1519169434766!IbjEwmJkIIyqalZS3YBU8WO3nSM=
The ReconnectSession.offset query parameter has to be set to the “offset” parameter of the most recent long poll
response that actually contained messages. Empty long poll responses don’t come with an “offset”.
The response to this ReconnectSession request looks like this:
## {
## "messages":[
## {
"type":"ReconnectSession",
## "message":{
"resetSequence":true,[Thismay be undefined]
"affinityToken":"efae1fa0"
## }
## }
## ]
## }
## 11
ReconnectSessionChat REST API Resources

The resetSequence is always set to true. Therefore, reset the sequence number of the next request and store the value in
affinityToken to use in the X-LIVEAGENT-AFFINITY header for all future requests. Once another handover process
occurs the resetSequence is updated again.
## Testing
To test that your client handles this process correctly, check that your client sends a ReconnectSession request when it receives a 503
response from the server. You can use a proxy tool of your choice to mimic the 503 response or you can wait until the Salesforce server
sends one. When the proxy tool sends a 503 response, you can test that your client sends the ReconnectSession request and reconnects
the chat session to a new server, as expected. To get an actual 503 response from the server, you can leave a session connected and
wait until the server is restarted during scheduled maintenance. Then see if the chat session reconnects to a new server. However, the
maintenance schedule is not announced in advance.
## SEE ALSO:
Status Codes and Error Responses
ChasitorSessionData
ChasitorResyncState
Status Codes and Error Responses
ChasitorResyncState
Reestablishes the chat visitor’s state, including the details of the chat, after a ReconnectSessionrequest is completed.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChasitorResyncState
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
Request parameters
## None
Query parameters
## None
Request body
ChasitorResyncState
## 12
ChasitorResyncStateChat REST API Resources

Response body
## None
## SEE ALSO:
ReconnectSession
## Monitor Chat Activity
Chat requests indicate when certain activities occurred during a chat session.
## IN THIS SECTION:
ChasitorNotTyping
Indicates that the chat visitor is not typing in the chat window.
ChasitorSneakPeek
Provides a chat visitor’s message that was viewable through Sneak Peek.
ChasitorTyping
Indicates that a chat visitor is typing a message in the chat window.
ChatEnd
Indicates that a chat visitor has ended the chat.
ChasitorIdleTimeoutWarningEvent
Informs the server when a warning is shown or cleared so that a transcript event can be created.
ChatMessage
Returns the body of the chat message sent by the chat visitor.
CustomEvent
Indicates a custom event was sent from the chat visitor during the chat.
## Messages
Returns all messages that were sent between agents and chat visitors during a chat session.
MultiNoun
Batches multiple POST requests together if you’re sending multiple messages at the same time.
ChasitorNotTyping
Indicates that the chat visitor is not typing in the chat window.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChasitorNotTyping
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
## 13
Monitor Chat ActivityChat REST API Resources

HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
## None
Response body
## None
ChasitorSneakPeek
Provides a chat visitor’s message that was viewable through Sneak Peek.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChasitorSneakPeek
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
ChasitorSneakPeek request
## 14
ChasitorSneakPeekChat REST API Resources

Response body
## None
ChasitorTyping
Indicates that a chat visitor is typing a message in the chat window.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChasitorTyping
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
## None
Response body
## None
ChatEnd
Indicates that a chat visitor has ended the chat.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChatEnd
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
## 15
ChasitorTypingChat REST API Resources

HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
ChatEndReason—Include the ChatEndReason parameter in the request body of your request to specify the reason that
the chat ended. This parameter is required. For example: {reason:“client”}.
Response properties
attachedRecords—Includes attached record IDs. You can use this Visualforce component to display the attached record IDs
in the post-chat page: <apex:outputTextvalue=”{!$CurrentPage.parameters.attachedRecords}”/><br
## />.
ChasitorIdleTimeoutWarningEvent
Informs the server when a warning is shown or cleared so that a transcript event can be created.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChasitorIdleTimeoutWarningEvent
Available since release
This resource is available in API versions 35.0 and later.
Response body
ChasitorIdleTimeoutWarningEvent response
ChatMessage
Returns the body of the chat message sent by the chat visitor.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/ChatMessage
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
## 16
ChasitorIdleTimeoutWarningEventChat REST API Resources

HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
ChatMessage request
Response body
## None
CustomEvent
Indicates a custom event was sent from the chat visitor during the chat.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/CustomEvent
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
CustomEvent request
## 17
CustomEventChat REST API Resources

Response body
## None
## Messages
Returns all messages that were sent between agents and chat visitors during a chat session.
For a complete list of responses for the Messages resource, see Chat REST API Messages Response Objects.
## Syntax
## URI
https://hostname/chat/rest/System/Messages
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## GET
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
Request parameters
## None
Query parameters
ack—The ack query parameter is a sequencing mechanism that allows you to poll for messages on the Live Agent server. The
first time you make the Messages request, the ack parameter is set to –1. To guarantee that you receive the messages from
the server in the correct order, update the ack value in the next request with the sequence value from the preceding response.
You receive a sequence value only if the response code is 200, which is the response if there are new messages. If the response
code is 204, there are no messages and the client doesn't provide a sequence value. In this case, run the Messages request
with the same ack value as the previous request.
Request body
## None
Response body
Messages response
## Troubleshooting
If your request doesn’t receive an HTTP response and fails, retry the request. If you don’t retry the request before the chat session times
out, the session expires. The timeout value that determines how long you have to attempt to send requests before the server expires
the session is configured in Chat Deployment in Salesforce Setup.
## 18
MessagesChat REST API Resources

## IN THIS SECTION:
Chat REST API Messages Response Objects Response Objects
The Messages request returns an array of objects that represent all the events that occurred during an agent’s chat with a chat
customer.
## SEE ALSO:
## Your Message Long Polling Loop
Chat REST API Messages Response Objects Response Objects
The Messages request returns an array of objects that represent all the events that occurred during an agent’s chat with a chat
customer.
This request can return several subtypes with unique response bodies, depending on the events that occurred within the chat.
Here is an example of the structure of a Messages response array:
## {
## "messages":{
## "type":"array",
"description":"Themessagessentoverthe courseof a chat.",
## "items":{
"name":"Message",
## "type":"object",
## "properties":{
## "type":{
## "type":"string",
"description":"Thetypeof messagethatwas received.",
## "required":true,
## "version":29.0
## },
## "message":{
## "type":"object",
"description":"Aplaceholderobjectfor the messagethatwas received.
Can returnany of the responsesavailablefor the Messagesrequest.",
## "required":true,
## "version":29.0
## }
## }
## },
## "required":true,
## "version":29.0
## },
## "sequence":{
## "type":"integer",
"description":"Thesequenceof the messageas it was receivedover
the courseof a chat.",
## "required":true,
## "version":29.0
## }
## }
## 19
MessagesChat REST API Resources

## IN THIS SECTION:
AgentDisconnect
Indicates that the agent has been disconnected from the chat.
AgentNotTyping
Indicates that the agent is not typing a message to the chat visitor.
AgentTyping
Indicates that the agent is typing a message to the chat visitor.
ChasitorSessionData
Returns the current chat session data for the chat visitor. This request is used to restore the session data for a chat visitor’s chat session
after a ReconnectSessionrequest is sent.
ChatEnded
Indicates that the chat has ended.
ChatEstablished
Indicates that an agent has accepted a chat request and is engaged in a chat with a visitor.
ChatMessage
Indicates a new chat message has been sent from an agent to a chat visitor.
ChatRequestFail
Indicates that the chat request was not successful.
ChatRequestSuccess
Indicates that the chat request was successful and routed to available agents.
ChatTransferred
Indicates the chat was transferred from one agent to another.
CustomEvent
Indicates a custom event was sent from an agent to a chat visitor during a chat.
NewVisitorBreadcrumb
Indicates the URL of the Web page the chat visitor is currently viewing.
QueueUpdate
Indicates the new position of the chat visitor in the chat queue when the visitor’s position in the queue changes.
SensitiveDataRules
Lists the sensitive data rules.
AgentDisconnect
Indicates that the agent has been disconnected from the chat.
Note:  Though the agent has been disconnected from the chat, the chat session is still active on the server. A new agent may
accept the chat request and continue the chat.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
## 20
MessagesChat REST API Resources

Response body
## None
Response properties
## None
AgentNotTyping
Indicates that the agent is not typing a message to the chat visitor.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
## None
Response properties
## None
AgentTyping
Indicates that the agent is typing a message to the chat visitor.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
## None
Response properties
## None
ChasitorSessionData
Returns the current chat session data for the chat visitor. This request is used to restore the session data for a chat visitor’s chat session
after a ReconnectSessionrequest is sent.
The ChasitorSessionData request is the first message sent after a ReconnectSession request is delivered.
Note:  No messages should be sent after a 503 status code is encountered until this message is processed.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
## 21
MessagesChat REST API Resources

Response body
ChasitorSessionData request
## SEE ALSO:
ReconnectSession
Status Codes and Error Responses
Status Codes and Error Responses
ChatEnded
Indicates that the chat has ended.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
ChatEndReason on page 39 response
Response properties
## None
ChatEstablished
Indicates that an agent has accepted a chat request and is engaged in a chat with a visitor.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
ChatEstablished response
## SEE ALSO:
ChatRequestSuccess
ChatMessage
Indicates a new chat message has been sent from an agent to a chat visitor.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
ChatMessage response
## 22
MessagesChat REST API Resources

ChatRequestFail
Indicates that the chat request was not successful.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
ChatRequestFail response
ChatRequestSuccess
Indicates that the chat request was successful and routed to available agents.
Note:  The ChatRequestSuccess response only indicates that a request has been routed to available agents. The chat hasn’t been
accepted until the ChatEstablished response is received.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
ChatRequestSuccess response
## SEE ALSO:
ChatEstablished
ChatTransferred
Indicates the chat was transferred from one agent to another.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
ChatTransferred response
CustomEvent
Indicates a custom event was sent from an agent to a chat visitor during a chat.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
CustomEven response
## 23
MessagesChat REST API Resources

NewVisitorBreadcrumb
Indicates the URL of the Web page the chat visitor is currently viewing.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
NewVisitorBreadcrumb response
QueueUpdate
Indicates the new position of the chat visitor in the chat queue when the visitor’s position in the queue changes.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
QueueUpdate response
SensitiveDataRules
Lists the sensitive data rules.
## Syntax
Available since release
This resource is available in API versions 29.0 and later.
Response body
SensitiveDataRules response
Response properties
## None
MultiNoun
Batches multiple POST requests together if you’re sending multiple messages at the same time.
## Syntax
## URI
https://hostname/chat/rest/System/MultiNoun
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
## 24
MultiNounChat REST API Resources

HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## X-LIVEAGENT-AFFINITY
## X-LIVEAGENT-SESSION-KEY
## X-LIVEAGENT-SEQUENCE
Request parameters
## None
Query parameters
## None
Request body
MultiNoun request
Response body
## None
Customize the Chat Visitors’ Experience
With the Chat visitor REST API resources, you can establish your chat visitors’ experience with Chat in custom mobile applications.
## IN THIS SECTION:
## Settings
Retrieves all settings information about the Chat deployment that’s associated with your chat session. The Settings request is
required as the first request to establish a chat visitor’s session.
## Availability
Indicates whether a chat button is available to receive new chat requests.
## Breadcrumb
Sets a breadcrumb value to the URL of the Web page that the chat visitor is viewing as the visitor chats with an agent. The agent
can then see the value of the breadcrumb to determine the page the chat visitor is viewing.
VisitorId
Generates a unique ID to track a chat visitor when they initiate a chat request and tracks the visitor’s activities as the visitor navigates
from one Web page to another.
SensitiveDataRuleTriggered for Agents
Sets the sensitive data rules for the chat agent, such as blocking the agent’s credit card, Social Security, phone and account numbers,
or even profanity.
SensitiveDataRuleTriggered for Chasitors
Sets the sensitive data rules for the chat visitor, such as blocking the visitor’s credit card, Social Security, phone and account numbers,
or even profanity.
## 25
Customize the Chat Visitors’ ExperienceChat REST API Resources

## Settings
Retrieves all settings information about the Chat deployment that’s associated with your chat session. The Settings request is
required as the first request to establish a chat visitor’s session.
## Syntax
## URI
https://hostname/chat/rest/Visitor/Settings
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## GET
Request headers
## X-LIVEAGENT-API-VERSION
Request parameters
## None
Query parameters
org_id
The ID of the Salesforce organization that’s associated with the Live Agent deployment.
deployment_id
The ID of the Chat deployment that the chat request was initiated from.
Settings.buttonIds
An array of chat button IDs for which to retrieve settings information.
Settings.needEstimatedWaitTime
Indicates whether the estimatedWaitTime property should be filled. Specify a value of 1 to request the estimated wait
time.
Settings.updateBreadcrumb
Indicates whether to update the chat visitor’s location with the URL of the Web page that the visitor is viewing.
Request body
## None
Response body
Settings response on page 47
## Availability
Indicates whether a chat button is available to receive new chat requests.
## Syntax
## URI
https://hostname/chat/rest/Visitor/Availability
## 26
SettingsChat REST API Resources

Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## GET
Request headers
## X-LIVEAGENT-API-VERSION
Request parameters
## None
Query parameters
org_id
The ID of the Salesforce organization that’s associated with the Live Agent deployment.
deployment_id
The 15-digit ID of the Chat deployment that the chat request was initiated from.
## Availability.ids
An array of object IDs for which to verify availability.
Availability.needEstimatedWaitTime
Indicates whether the estimatedWaitTime property should be filled. Specify a value of 1 to request the estimated wait
time.
Request body
## None
Response body
Availability response
## Breadcrumb
Sets a breadcrumb value to the URL of the Web page that the chat visitor is viewing as the visitor chats with an agent. The agent can
then see the value of the breadcrumb to determine the page the chat visitor is viewing.
## Syntax
## URI
https://hostname/chat/rest/Visitor/Breadcrumb
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
## 27
BreadcrumbChat REST API Resources

Request parameters
## None
Query parameters
## None
Request body
Breadcrumb request
Response body
## None
VisitorId
Generates a unique ID to track a chat visitor when they initiate a chat request and tracks the visitor’s activities as the visitor navigates
from one Web page to another.
## Syntax
## URI
https://hostname/chat/rest/Visitor/VisitorId
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## GET
Request headers
## X-LIVEAGENT-API-VERSION
Request parameters
## None
Query parameters
org_id
The Salesforce organization ID
deployment_id
The ID of the Chat deployment that the chat request was initiated from
Request body
## None
Response body
VisitorId response
SensitiveDataRuleTriggered for Agents
Sets the sensitive data rules for the chat agent, such as blocking the agent’s credit card, Social Security, phone and account numbers,
or even profanity.
## 28
VisitorIdChat REST API Resources

## Syntax
## URI
https://hostname/chat/rest/Agent/SensitiveDataRuleTriggered
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
Request parameters
## None
Query parameters
## None
Request body
SensitiveDataRuleTriggered for Agents request
Response body
## None
SensitiveDataRuleTriggered for Chasitors
Sets the sensitive data rules for the chat visitor, such as blocking the visitor’s credit card, Social Security, phone and account numbers,
or even profanity.
## Syntax
## URI
https://hostname/chat/rest/Chasitor/SensitiveDataRuleTriggered
Available since release
This resource is available in API versions 29.0 and later.
## Formats
## JSON
HTTP methods
## POST
Request headers
## X-LIVEAGENT-API-VERSION
Request parameters
## None
Query parameters
## None
Request body
SensitiveDataRuleTriggered for Chasitors request
## 29
SensitiveDataRuleTriggered for ChasitorsChat REST API Resources

Response body
## None
## SEE ALSO:
Salesforce Help: Block Sensitive Data in Chats
## 30
SensitiveDataRuleTriggered for ChasitorsChat REST API Resources

CHAPTER 7Request Bodies for Chat REST API
To perform a POST or GET request, pass query parameters or create a request body that’s formatted in JSON. Request bodies can contain
one or more other request bodies that are nested inside. Each request body can contain unique request properties.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in maintenance mode until then. During
this phase, you can continue to use chat, but we no longer recommend that you implement new chat channels. To avoid service
interruptions to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features that you
love plus asynchronous conversations that can be picked back up at any time. Learn about chat retirement in Help.
## Breadcrumb
Request properties
Available VersionsDescriptionTypeProperty Name
29.0The URL of the web page that the chat
visitor is viewing.
## Stringlocation
Request body
## "location":{
## "type":"string",
"description":"Thecurrentlocationor URL of the visitor",
## "required":true,
## "version":29.0
## }
ChasitorInit
Request properties
Available VersionsDescriptionTypeProperty Name
29.0The chat visitor’s Salesforce organization
## ID.
StringorganizationId
29.0The ID of the deployment from which
the chat originated.
StringdeploymentId
29.0The ID of the button from which the
chat originated.
StringbuttonId
29.0The ID of the agent of a direct-to-agent
chat request. For normal chat requests,
leave this field empty.
StringagentId
## 31

Available VersionsDescriptionTypeProperty Name
29.0Specifies the fallback mode if
agentId is present. If the value is
BooleandoFallback
false, it attempts to route the chat
session back to that specific agent. If
the value is true, it attempts to route
the chat session back to the specific
agent first but, if the agent is
unavailable, it attempts to route to the
button next.
29.0The chat visitor’s Chat session ID.StringsessionId
29.0The chat visitor’s browser user agent.StringuserAgent
29.0The chat visitor’s spoken language.Stringlanguage
29.0The resolution of the chat visitor’s
computer screen.
StringscreenResolution
29.0The chat visitor’s custom name.StringvisitorName
29.0The pre-chat information that was
provided by the chat visitor.
Array of CustomDetail
objects
prechatDetails
29.0The records created, searched for, or
both depending on what
Array of Entity objectsprechatEntities
EntityFieldsMaps on page 56 has
enabled.
## 29.0
The button override is an ordered list of
routing targets and overrides the
Array of StringsbuttonOverrides
buttonId, agentId, and doFallback
modes. The possible options are:
## •
buttonId—Normal routing
## •
agentId—Direct-to-agent
routing with no fallback
## •
agentId_buttonId—Direct-to-agent
routing with fallback to the button
You can list one or more of these
options, where the order specifies the
routing target order. The second or third
target is attempted only if the previous
one fails.
29.0Indicates whether the chat visitor
receives queue position updates
(true) or not (false).
BooleanreceiveQueueUpdates
## 32
Request Bodies for Chat REST API

Available VersionsDescriptionTypeProperty Name
29.0Indicates whether the chat request was
made properly through a POST request
(true) or not (false).
BooleanisPost
Request body
## {
organizationId:"00DD0000000JVXs",
deploymentId:"572D000000000J6",
buttonId:"573D000000000OC",
agentId:"005B0000000F3b2",
doFallback:true,
sessionId:"5503f854-0203-4324-8ed5-f793a367426f",
userAgent:"Mozilla/5.0(Macintosh;IntelMac OS X 10_6_8)AppleWebKit/537.36
(KHTML,likeGecko)Chrome/28.0.1500.95Safari/537.36",
language:"en-US",
screenResolution:"2560x1440",
visitorName:"JonA.",
prechatDetails:[
## {
label:"E-mailAddress",
value:"jon@example.com",
entityFieldMaps:[
## {
entityName:"Contact",
fieldName:"Email",
isFastFillable:false,
isAutoQueryable:true,
isExactMatchable:true
## }
## ],
transcriptFields:[
"c__EmailAddress"
## ],
displayToAgent:true
## }
## ],
prechatEntities:[],
buttonOverrides:[
## "573D000000000OD"
## ],
receiveQueueUpdates:true,
isPost:true
## }
## 33
Request Bodies for Chat REST API

ChasitorResyncState
Request properties
Available VersionsDescriptionTypeProperty Name
29.0The chat visitor’s Salesforce organization
## ID.
StringorganizationId
Request body
## {
organizationId:"00DD0000000JVXs"
## }
ChasitorSneakPeek
Request properties
Available VersionsDescriptionTypeProperty Name
29.0The position of the Sneak Peek update in the chat.integerposition
29.0The text that the chat visitor is typing in the text input
area of the chat window.
## Stringtext
Request body
## {
position:3,
text:"Hi there."
## }
ChatMessage
Request properties
Available VersionsDescriptionTypeProperty Name
29.0The text of the chat visitor’s message to the agent.Stringtext
Request body
## {
text:"I havea questionaboutmy account."
## }
## 34
Request Bodies for Chat REST API

CustomEvent
Request properties
Available VersionsDescriptionTypeProperty Name
29.0The type of custom event that occurred, used for adding the event
listener on the agent’s side.
## Stringtype
29.0Data that’s relevant to the event that was sent to the agent.Stringdata
Request body
## {
type:"PromptForCreditCard",
data:"Visa"
## }
MultiNoun
Request properties
Available VersionsDescriptionTypeName
29.0An array of noun objects and their properties that are batched
in the MultiNoun request.
Array of
NounWrapper
objects
nouns
Request body
## {
nouns:[
## {
prefix:"Chasitor",
noun:"ChatMessage",
object:{
text:"Goodbye"
## }
## },
## {
prefix:"Chasitor",
noun:"ChatEnd",
object:{}
## }
## ]
## }
## 35
Request Bodies for Chat REST API

SensitiveDataRuleTriggered for Agents
Request properties
Available VersionsDescriptionTypeProperty Name
29.0A list of sensitive data rules applied to the
chat session.
Array of Rule
objects
rules
The ID of the chat session.StringchatId
Request body
## {
## "rules":[
## {
"name":"Replace-Bad-Word"
## },
## {
"name":"Filter-Out-Digits"
## }
## ],
"chatId":"1a240b1a-f60e-456d-9f77-41cbfa7b9159"
## }
SensitiveDataRuleTriggered for Chasitors
Request properties
Available VersionsDescriptionTypeProperty Name
29.0A list of sensitive data rules applied to
the chat session.
Array of Rule
objects
rules
Request body
## {
## "rules":[
## {
"id":"0GORM00000001dM",
"name":"Replace-Bad-Word"
## },
## {
"id":"0GORM00000001dW",
"name":"Filter-Out-Digits"
## }
## ]
## }
## 36
Request Bodies for Chat REST API

CHAPTER 8Response Bodies for Chat REST API
A request to a Chat REST API resource returns a response code. The successful execution of a resource request can also return a response
body in JSON format.
Note:  The legacy chat product is scheduled for retirement on February 14, 2026, and is in maintenance mode until then. During
this phase, you can continue to use chat, but we no longer recommend that you implement new chat channels. To avoid service
interruptions to your customers, migrate to Messaging for In-App and Web. Messaging offers many of the chat features that you
love plus asynchronous conversations that can be picked back up at any time. Learn about chat retirement in Help.
## Availability
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0A list of Salesforce IDs that
correspond to agents and chat
Array of Result objectsresults
buttons and their respective
availability to receive new chat
requests.
Response body
## {
## "results":{
## "type":"array",
"description":"Listof validpatternsof IDs and theiravailability.",
## "items":{
## "name":"result",
## "type":"object",
## "properties":{
## "id":{
## "type":"string",
"description":"IDof the entity.",
## "required":true,
## "version":29.0
## },
"isAvailable":{
## "type":"boolean",
"description":"Whetheror not the entityis availablefor chat.",
## "version":29.0
## }
## }
## },
## "required":true,
## 37

## "version":29.0
## }
## }
ChasitorSessionData
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0The position of the chat visitor
in the chat queue.
integerqueuePosition
29.0The chat visitor's location,
based on the IP address from
which the request originated.
GeoLocation objectgeoLocation
29.0The URL that the chat visitor is
visiting.
## Stringurl
29.0The original URL that the chat
request came from.
## Stringoref
29.0The URL to which to redirect
the chat visitor after the chat
has ended.
StringpostChatUrl
29.0Whether Sneak Peek is enabled
for the agent who accepts the
chat.
BooleansneakPeekEnabled
29.0The chat message structure
that’s synchronized across the
agent.js and chasitor.js files.
Array of
TranscriptEntry
objects
chatMessages
Response body
## {
queuePosition:1,
geoLocation:{
countryCode:"US",
countryName:"UnitedStatesof America",
region:"CA",
city:"SanFrancisco",
organization:Salesforce,
latitude:37.793880,
longitude:-122.395114
## },
url:"http://yoursite",
oref:"http://www.google.com?q=yoursite",
postChatUrl:"http://yoursite/postchat",
sneakPeekEnabled:true,
## 38
Response Bodies for Chat REST API

chatMessages:[
## {
type:"Agent",
name:"AndyL.",
content:"Hello,how can I helpyou?",
timestamp:1376596367548,
sequence:1
## },
## {
type:"Chasitor",
name:"JonA.",
content:"I havea questionfor you.",
timestamp:1376596349132
sequence:2
## }
## ]
## }
ChasitorIdleTimeoutWarningEvent
Response properties
Available VersionsDescriptionTypeProperty Name
35.0Informs the server when a
warning is triggered or cleared.
StringidleTimeoutWarningEvent
Possible values: triggered
and cleared.
ChatEndReason
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The reason that the chat ended.Stringreason
## 29.0
Returns a list of record IDs
mapped to the chat's transcript
StringattachedRecords
object with the corresponding
transcript field names
containing those mappings.
This mapping data is useful for
enhancing your post chat
implementation.
Available if post-chat is enabled
on the chat button. If the client
uses attachedRecords
## 39
Response Bodies for Chat REST API

post chat and a chasitor ends
the chat without the client
receiving the ChatEnded
response, call Messages again
after calling ChatEnd.
ChatEstablished
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The name of the agent who is
engaged in the chat.
## Stringname
29.0The user ID of the agent who is
engaged in the chat.
StringuserId
29.0Whether Sneak Peek is enabled
for the agent who accepts the
chat.
BooleansneakPeekEnabled
35.0Gives the settings for chat
visitor idle time-out.
ChasitorIdleTimeoutSettingschasitorIdletimeout
Response body
## {
name:"AndyL.",
userId:"f1dda237-57f8-4816-b8e8-59775f1e44c8",
sneakPeekEnabled:true
## }
ChatMessage
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The name of the agent who is
engaged in the chat.
## Stringname
29.0The text of the chat message
that the agent sent to the chat
visitor.
## Stringtext
## 40
Response Bodies for Chat REST API

Response body
## {
name:"AndyL."
text:"Hello,how can I helpyou?"
## }
ChatRequestFail
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The reason why the chat
request failed—for example,
## Stringreason
no agents were available to
chat or an internal error
occurred.
29.0The URL of the post-chat page
to which to redirect the chat
visitor after the chat has ended.
StringpostChatUrl
Response body
## {
reason:"Unavailable",
postChatUrl:"http://yoursite/postChat"
## }
ChatRequestSuccess
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The position of the chat visitor
in the chat queue.
integerqueuePosition
47.0The estimated wait time for the
button in seconds. If the server
numberestimatedWaitTime
cannot retrieve the wait time,
this property returns -1.
29.0The chat visitor's location,
based on the IP address from
which the request originated.
GeoLocation objectgeoLocation
29.0The URL that the chat visitor is
visiting.
## Stringurl
## 41
Response Bodies for Chat REST API

Available VersionsDescriptionTypeProperty Name
29.0The original URL that the chat
request came from.
## Stringoref
29.0The URL to which to redirect
the chat visitor after the chat
has ended.
StringpostChatUrl
29.0The custom details of the
deployment from which the
chat request was initiated.
Array of CustomDetail
objects
customDetails
29.0The ID of the chat visitor.StringvisitorId
Response body
## "{
queuePosition:1,
estimatedWaitTime:120,
geoLocation:{
countryCode:"US",
countryName:"UnitedStatesof America",
region:"CA",
city:"SanFrancisco",
organization:Salesforce,
latitude:37.793880,
longitude:-122.395114
## },
url:"http://yoursite",
oref:"http://www.google.com?q=yoursite",
postChatUrl:"http://yoursite/postchat",
customDetails:[
## {
label:"E-mailAddress",
value:"jon@example.com",
transcriptFields:[
"c__EmailAddress"
## ],
displayToAgent:true
## }
## ],
visitorId:"acd47048-bd80-476e-aa33-741bd5cb05d3"
## }"
## 42
Response Bodies for Chat REST API

ChatTransferred
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The name of the agent to
whom the chat was transferred.
## Stringname
29.0The ID of the chat visitor.StringuserId
29.0Whether Sneak Peek is enabled
for the agent to whom the chat
was transferred.
BooleansneakPeekEnabled
35.0Gives the settings for chat
visitor idle time-out.
ChasitorIdleTimeoutSettingschasitorIdletimeout
Response body
## {
name:"RyanS.",
userId:"edacfa56-b203-43d5-9e1b-678278b61263",
sneakPeekEnabled:false
## }
CustomEvent
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The type of custom event that
occurred, used for adding the
## Stringtype
event listener on the chat
visitor’s side.
29.0Data that’s relevant to the
event that was sent to the chat
visitor.
## Stringdata
Response body
## {
type:"CreditCardEntered",
data:"5105105105105100"
## }
## 43
Response Bodies for Chat REST API

## Messages
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0The messages that were sent
over the course of a chat.
Array of Message objectsmessages
29.0An internal number to be used
with a ReconnectSession
integeroffset
request that tracks which
messages your client has
received.
29.0The sequence of the message
as it was received over the
course of a chat.
integersequence
Response body
## {
messages:[
## {
type:"ChatEstablished",
message:{
name:"AndyL.",
userId:"f1dda237-57f8-4816-b8e8-59775f1e44c8",
sneakPeekEnabled:true
## }
## }
## ],
sequence:1,
offset:1234567890
## }
NewVisitorBreadcrumb
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The URL of the web page that
the chat visitor is viewing.
## Stringlocation
## 44
Response Bodies for Chat REST API

Response body
## {
location:"http://yoursite/page2"
## }
QueueUpdate
Response properties
Available VersionsDescriptionTypeProperty Name
29.0The updated position of the
chat visitor in the chat queue.
integerposition
47.0The estimated wait time for the
button in seconds. If the server
numberestimatedWaitTime
cannot retrieve the wait time,
this property returns -1.
Response body
## {
position:3,
estimatedWaitTime:120
## }
ReconnectSession
Response properties
Available VersionsDescriptionTypeProperty Name
37.0If true, the sequence for the
next request should be reset.
BooleanresetSequence
37.0The affinity token for the
session that’s passed in the
header for all future requests.
StringaffinityToken
Response body
## {
resetSequence:true,
affinityToken:"73061fa0"
## }
## 45
Response Bodies for Chat REST API

SensitiveDataRules
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0List of sensitive data rules and
their details.
SensitiveDataRule
object
sensitiveDataRules
Response body
## {
"sensitiveDataRules":[
## {
"name":"Replace-Bad-Word",
## "pattern":"bad",
"id":"0GORM00000001dM",
## "replacement":"badword",
"actionType":"Replace"
## },
## {
"name":"Filter-Out-Digits",
## "pattern":"[0-9]+",
"id":"0GORM00000001dW",
"replacement":"<DIGIT>",
"actionType":"Replace"
## }
## ]
## }
SessionId
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0The session ID for the new
session.
## Stringid
29.0The session key for the new
session.
## Stringkey
29.0The affinity token for the session
that’s passed in the header for all
future requests.
StringaffinityToken
29.0The number of seconds before
you must make a Messages
integerclientPollTimeout
request before your Messages
long polling loop times out and
is terminated.
## 46
Response Bodies for Chat REST API

Response body
## {
id: "241590f5-2e59-44b5-af89-9cae83bb6947",
key:
## "f6c1d699-84c7-473f-b194-abf4bf7cccf8!b65b13c7-f597-4dd2-aa3a-cbe01e69f19c",
affinityToken:"73061fa0"
clientPollTimeout:"30"
## }
## Settings
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0The rate at which the visitor must
ping the server to maintain the
Chat visitor session.
numberpingrate
29.0The URL of the content server.StringcontentServerUrl
29.0A list of chat buttons, along with
their settings information, that
Array of button objectsbuttons
were specified when you made
the Settings request.
Response body
## {
"pingRate":{
## "type":"number",
"description":"Therateat whichthe visitorshouldpingthe serverto
maintainpresence",
## "required":true,
## "version":29.0
## },
"contentServerUrl":{
## "type":"string",
"description":"ThecontentserverURL",
## "required":true,
## "version":29.0
## },
## "buttons":{
## "type":"array",
"description":"Thelistof buttons",
## "items":{
## "name":"button",
## "type":"object",
## "properties":{
## "id":{
## "type":"string",
## 47
Response Bodies for Chat REST API

"description":"Theid of the button",
## "required":true,
## "version":29.0
## },
## "type":{
## "type":"string",
"description":"Thetypeof the button",
## "required":true,
## "version":29.0,
"enum":["Standard","Invite","ToAgent"]
## },
"endpointUrl":{
## "type":"string",
"description":"Thecustomchatwindowurl of the button",
## "required":false,
## "version":29.0
## },
"prechatUrl":{
## "type":"string",
"description":"Theprechaturl of the button",
## "required":false,
## "version":29.0
## },
## "language":{
## "type":"string",
"description":"Thelanguagesettingof the button",
## "required":false,
## "version":29.0
## },
"isAvailable":{
## "type":"boolean",
"description":"Whetheror not the buttonis availablefor chat",
## "version":29.0
## },
## /* Inviterelatedsettings*/
"inviteImageUrl":{
## "type":"string",
"description":"Theimageof the button",
## "required":false,
## "version":29.0
## },
"inviteImageWidth":{
## "type":"number",
"description":"Thewidthof the buttonimage",
## "required":false,
## "version":29.0
## },
"inviteImageHeight":{
## "type":"number",
"description":"Theheightof the buttonimage",
## "required":false,
## "version":29.0
## },
## 48
Response Bodies for Chat REST API

"inviteRenderer":{
## "type":"string",
"description":"Theanimationoptionof the invite",
## "required":false,
## "version":29.0,
"enum":["Slide","Fade","Appear","Custom"]
## },
"inviteStartPosition":{
## "type":"string",
"description":"Thestartpositionof the animation",
## "required":false,
## "version":29.0,
"enum":["TopLeft","TopLeftTop","Top","TopRightTop","TopRight",
"TopRightRight","Right","BottomRightRight","BottomRight",
"BottomRightBottom","Bottom","BottomLeftBottom","BottomLeft",
"BottomLeftLeft","Left","TopLeftLeft"]
## },
"inviteEndPosition":{
## "type":"string",
"description":"Theend positionof the animation",
## "required":false,
## "version":29.0,
"enum":["TopLeft","Top","TopRight","Left","Center","Right","BottomLeft","Bottom","BottomRight"]
## },
"hasInviteAfterAccept":{
## "type":"boolean",
"description":"Whetheror not invitewilltriggerafteraccepting",
## "required":false,
## "version":29.0
## },
"hasInviteAfterReject":{
## "type":"boolean",
"description":"Whetheror not invitewilltriggerafterrejecting",
## "required":false,
## "version":29.0
## },
"inviteRejectTime":{
## "type":"number",
"description":"Theautorejectsettingof the invite",
## "required":false,
## "version":29.0
## },
"inviteRules":{
## "type":"object",
"description":"Therulesof the invite",
## "required":false,
## "version":29.0
## }
## 49
Response Bodies for Chat REST API

## /* Inviterelatedsettings*/
## }
## },
## "required":true,
## "version":29.0
## }
## }
SwitchServer
This response is returned for requests to Visitor resources if the Live Agent instance URL is not correct for the Organization ID provided.
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0The new Chat API endpoint for
your org if your org is moved. It
StringnewUrl
can be moved due to a planned
org migration or during a Site
Switch to a different instance.
Response body
## {
## "messages":[
"type":"SwitchServer"
## "message":{
"newUrl":"https://LiveAgentPool.salesforceliveagent.com/chat"
## }
## ]
## }
VisitorId
## Response Properties
Available VersionsDescriptionTypeProperty Name
29.0The session ID for the new
session.
StringsessionId
Response body
"sessionId":{
## "type":"string",
"description":"Thesessionid of the visitor",
## "required":true,
## 50
Response Bodies for Chat REST API

## "version":29.0
## }
## SEE ALSO:
Status Codes and Error Responses
## 51
Response Bodies for Chat REST API

CHAPTER 9Chat REST API Data Types
A request to a Chat REST API resource returns a response code. The successful execution of a resource request can also return a response
body in JSON format. Some response bodies return data types that contain their own properties. All property values that refer to a name
of an entity or field are case-sensitive.
## Button
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe ID of the chat
button object.
## Stringid
29.0TRUEThe button type. Valid
values are:
## Stringtype
## •
## Standard
## •
## Invite
## •
ToAgent
29.0FALSEThe URL of the custom
chat window that’s
StringendpointUrl
assigned to the chat
button.
29.0FALSEThe URL of the pre-chat
form that’s assigned to
the button.
StringprechatUrl
29.0FALSEThe chat button’s
default language.
## Stringlanguage
29.0FALSESpecifies whether the
chat button is available
BooleanisAvailable
to receive new chat
requests (true) or not
(false). If you don’t
see this property, the
value is false.
29.0FALSEThe URL to the
automated invitation’s
static image resource.
StringinviteImageUrl
(for automated chat
invitations only)
## 52

Available VersionsRequiredDescriptionTypeProperty Name
29.0FALSEThe width in pixels of
the automated chat
invitation’s image.
numberinviteImageWidth
(for automated chat
invitations only)
29.0FALSEThe height in pixels of
the automated chat
invitation’s image.
numberinviteImageHeight
(for automated chat
invitations only)
29.0FALSEThe animation option
that’s assigned to the
StringinviteRenderer
(for automated chat
invitations only)
automated chat
invitation. Valid values
are:
## •
## Slide
## •
## Fade
## •
## Appear
## •
## Custom
29.0FALSEThe position at which
the automated chat
StringinviteStartPosition
(for automated chat
invitations only)
invitation begins its
animation. Valid values
are:
## •
TopLeft
## •
TopLeftTop
## •
## Top
## •
TopRightTop
## •
TopRight
## •
TopRightRight
## •
## Right
## •
BottomRightRight
## •
BottomRight
## •
BottomRightBottom
## •
## Bottom
## •
BottomLeftBottom
## •
BottomLeft
## •
BottomLeftLeft
## •
## Left
## •
TopLeftLeft
29.0FALSEThe position at which
the automated chat
StringinviteEndPosition
(for automated chat
invitations only)
invitation begins its
## 53
Chat REST API Data Types

Available VersionsRequiredDescriptionTypeProperty Name
animation. Valid values
are:
## •
TopLeft
## •
## Top
## •
TopRight
## •
## Left
## •
## Center
## •
## Right
## •
BottomLeft
## •
## Bottom
## •
BottomRight
29.0FALSESpecifies whether the
automated chat
BooleanhasInviteAfterAccept
(for automated chat
invitations only)
invitation can be sent
again after the customer
accepted a previous
chat invitation (true)
or not (false).
29.0FALSESpecifies whether the
automated chat
BooleanhasInviteAfterReject
(for automated chat
invitations only)
invitation can be sent
again after the customer
rejected a previous chat
invitation (true) or not
## (false).
29.0FALSEThe amount of time in
seconds that the
numberinviteRejectTime
(for automated chat
invitations only)
invitation appears on a
customer’s screen
before the invitation is
automatically rejected.
29.0FALSEThe custom rules that
govern the behavior of
ObjectinviteRules (for
automated chat
invitations only)
the automated chat
invitation, as defined in
your custom Apex class.
## 47.0FALSE
The estimated wait time
for the button in
numberestimatedWaitTime
seconds. If the server
cannot retrieve the wait
## 54
Chat REST API Data Types

Available VersionsRequiredDescriptionTypeProperty Name
time, this property
returns -1.
CustomDetail
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe customized label for
the detail.
## Stringlabel
29.0TRUEThe customized value for
the detail.
## Stringvalue
29.0TRUEThe names of fields to
which to save the
Array of StringstranscriptFields
customer’s details on the
chat transcript.
29.0FALSESpecifies whether to
display the customized
BooleandisplayToAgent
detail to the agent
(true) or not (false).
## Entity
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe record to search for
or create.
StringentityName
29.0FALSESpecifies whether to
display the record after
BooleanshowOnCreate
it’s created (true) or
not (false).
29.0FALSEThe name of the record
to which to link the
detail.
StringlinkToEntityName
29.0FALSEThe field within the
record to which to link
the detail.
StringlinkToEntityField
## 55
Chat REST API Data Types

Available VersionsRequiredDescriptionTypeProperty Name
29.0FALSEThe name of the
transcript field to which
to save the record.
StringsaveToTranscript
29.0TRUEThe fields to which to
associate the detail on a
record.
Array of EntityFieldsMaps
objects
entityFieldsMaps
EntityFieldsMaps
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe name of the field to
which to associate the
detail.
StringfieldName
29.0TRUEThe customized label for
the detail.
## Stringlabel
29.0TRUESpecifies whether to use
the field fieldName
BooleandoFind
to perform a search for
matching records
(true) or not (false).
29.0TRUESpecifies whether to
only search for records
BooleanisExactMatch
that have fields that
exactly match the field
fieldName (true)
or not (false).
29.0TRUESpecifies whether to
create a record based on
BooleandoCreate
the field fieldName
if one doesn’t exist
(true) or not (false).
## 56
Chat REST API Data Types

GeoLocation
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe ISO 3166-1 alpha-2
country code for the
chat visitor's location.
StringcountryCode
29.0TRUEThe name of the country
that’s associated with
StringcountryName
the chat visitor’s
location.
29.0FALSEThe principal
administrative division
## Stringregion
associated with the chat
visitor's location—for
example, the state or
province.
29.0FALSEThe name of the city
associated with the chat
visitor’s location.
## Stringcity
29.0FALSEThe name of the
organization associated
## Stringorganization
with the chat visitor’s
location.
29.0FALSEThe latitude associated
with the chat visitor’s
location.
numberlatitude
29.0FALSEThe longitude associated
with the chat visitor’s
location.
numberlongitude
## Message
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe type of message that was
received.
## Stringtype
29.0TRUEA placeholder object for the
message that was received. Can
## Objectmessage
## 57
Chat REST API Data Types

Available VersionsRequiredDescriptionTypeProperty Name
return any of the responses that are
available for the Messages request.
NounWrapper
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe prefix of the resource.Stringprefix
29.0TRUEThe name of the resource.Stringnoun
29.0FALSEThe data to post to the resource.Stringdata
## Result
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe Salesforce ID of the agent or
chat button.
## Stringid
29.0FALSEIndicates whether the entity that’s
associated with the Salesforce ID
BooleanisAvailable
id is available to receive new chat
requests (true) or not (false).
If you don’t see this property, the
value is false.
## 47.0FALSE
The estimated wait time for the
button in seconds. If the server
numberestimatedWaitTime
cannot retrieve the wait time, this
property returns -1.
## Rule
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0FALSEThe ID of the sensitive data rule
record. Applies to
## Stringid
## 58
Chat REST API Data Types

Available VersionsRequiredDescriptionTypeProperty Name
SensitiveDataRuleTriggered for
Chasitors only.
29.0TRUEThe name of the sensitive data rules
applied to the chat session. This
## Stringname
property applies to both agent and
chasitor.
SensitiveDataRule
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe name of the sensitive data rule.Stringname
29.0TRUEThe pattern of the sensitive data rule
pattern definition.
## Stringpattern
29.0FALSEThe ID of the sensitive data rule.Stringid
29.0FALSEThe replacement of the pattern in the
message if actionType is
## Replace.
## Stringreplacement
29.0FALSEThe action type if the message matches
the pattern.
StringactionType
TranscriptEntry
## Properties
Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe type of message in the chat
transcript. Valid values are:
Enumeration of type
## String
type
## •
Agent: a message from an
agent to a chat visitor
## •
Chasitor: a message from a
chat visitor to an agent
## •
OperatorTransferred:
A request to transfer a chat to
another agent
29.0TRUEThe name of the person who sent
the chat message.
## Stringname
## 59
Chat REST API Data Types

Available VersionsRequiredDescriptionTypeProperty Name
29.0TRUEThe body of the message.Stringcontent
29.0TRUEThe date and time when the
message was sent.
numbertimestamp
29.0TRUEThe sequence in which the
message was received in the chat.
numbersequence
## SEE ALSO:
Status Codes and Error Responses
Salesforce Help: Block Sensitive Data in Chats
## 60
Chat REST API Data Types

CHAPTER 10Status Codes and Error Responses
Each request returns a status code or error response to indicate whether the request was successful.
When an error occurs or when a response is successful, the response header contains an HTTP code, and the response body usually
contains:
## •
The HTTP response code
## •
The message accompanying the HTTP response code
DescriptionHTTP response
code
“OK” success code.200
“Accepted” success code, for POST request.202
“No Content” success code for Message request; resend the request as part of the message loop.204
The request couldn’t be understood, usually because the JSON body contains an error.400
The request has been refused because the session isn’t valid.403
The requested resource couldn’t be found. Check the URI for errors.404
The method specified in the Request-Line isn’t allowed for the resource specified in the URI.405
A duplicate long poll using the same session ID has caused the chat to terminate. Reestablish the chat in a
new session.
## 409
An error has occurred within the Chat server, so the request couldn’t be completed. Contact Customer Support.500
The affinity token has changed. Make a ReconnectSession request to get a new affinity token, then make a
ChasitorSessionData request to reestablish the chat visitor’s data within the new session.
## 503
## SEE ALSO:
## Your Message Long Polling Loop
ReconnectSession
ChasitorSessionData
Response Bodies for Chat REST API
Chat REST API Data Types
ReconnectSession
ChasitorSessionData
## 61

## INDEX
## A
AgentDisconnect20
AgentNotTyping21
AgentTyping21
## Availability26
## B
## Breadcrumb27
## C
ChasitorIdleTimeoutWarningEvent16
ChasitorNotTyping13
ChasitorResyncState12
ChasitorSessionData21
ChasitorSneakPeek14
ChasitorTyping15
ChatEnd15
ChatEnded22
ChatEstablished22
ChatMessage16, 22
ChatRequestFail23
ChatRequestSuccess23
ChatTransferred23
CustomEvent17, 23
## D
## Data Types52
## E
Error responses61
## M
## Messages18
MultiNoun24
## N
NewVisitorBreadcrumb24
## Q
QueueUpdate24
## R
## Requests
## Headers5
## Resources
AgentDisconnect20
AgentNotTyping21
AgentTyping21
## Availability26
## Breadcrumb27
ChasitorIdleTimeoutWarningEvent16
ChasitorNotTyping13
ChasitorResyncState12
ChasitorSessionData21
ChasitorSneakPeek14
ChasitorTyping15
ChatEnd15
ChatEnded22
ChatEstablished22
ChatMessage16, 22
ChatRequestFail23
ChatRequestSuccess23
ChatTransferred23
CustomEvent17, 23
## Data Types52
## Long Polling6
## Messages18–19
MultiNoun24
NewVisitorBreadcrumb24
QueueUpdate24
Request headers5
## Requests8–9, 13, 25, 31
SensitiveDataRules24
SensitiveDataRuleTriggered28–29
SessionId8
## Settings26
VisitorId28
## Responses
## Data Types52
## S
SensitiveDataRules24
SensitiveDataRuleTriggered28–29
SessionId8
## Settings26
Status codes61
## V
VisitorId28
## 62