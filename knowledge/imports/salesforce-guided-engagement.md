

Lightning Flow for Service
## Developer Guide
## Salesforce, Spring ’26
Guide your users with a list of actions
Last updated: November 17, 2025

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
SALESFORCE FLOW FOR SERVICE. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Supported Apps, Channels, and Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Example Use Case. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
Implementing  the  Example. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
Enhance the User Experience. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
Show  Recommendations. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
Resume  Paused  Flows. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
Pin  Steps. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
Complete  Mandatory  Steps. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
Hide  Remove  Option. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
Find  Another  Action. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
View  Action  History. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
Considerations. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
IMPLEMENTATION  CHECKLIST. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
CREATE ACTIONS TO SHOW. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
ASSOCIATE ACTIONS WITH RECORDS. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
Using a Deployment. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
Using Process Builder. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
Using  SOAP. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
Using Apex. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
CUSTOMIZE PAGES WITH THE COMPONENT. . . . . . . . . . . . . . . . . . . . . . . . 30
INTEGRATE WITH CHAT. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 32
INTEGRATE WITH OPEN CTI. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34
OTHER RESOURCES. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36



## SALESFORCE FLOW FOR SERVICE
## EDITIONS
Available in: Lightning
## Experience
Available in: Essentials,
## Professional, Enterprise,
## Performance, Unlimited,
and Developer Editions
Lightning console apps are
available for an extra cost to
users with Salesforce
Platform user licenses for
certain products. Some
restrictions apply. For pricing
details, contact your
Salesforce account
executive.
Give your users a list of logical next steps with Salesforce Flow for Service and the Actions &
Recommendations component. To create the list, associate actions with a record page using an
Actions & Recommendations deployment, Salesforce automation tools, or API. You can configure
default actions for specific channels, like phone or chat, and select the actions that you want users
to complete first and last.
Specify which actions to show in the component on your Lightning pages. When you set up a
deployment or use an API, you can also display the top recommendations that result from your
Einstein Next Best Action strategies.
The component shows a list of RecordAction junction objects. A RecordAction associates an action,
such as a screen flow, a field service mobile flow, an autolaunched flow, or a quick action, with the
parent record. A RecordAction is also created when a user accepts a Next Best Action
recommendation; then the RecordAction associates the flow in the recommendation with the
record.
When the user clicks a step in the list, the associated action in the RecordAction object launches.
You can also set up the first action to auto-launch when the record page opens. If the action is a
screen flow, for example, it starts in a subtab of a console app or in a window for a standard
navigation app. When the user confirms the start of an autolaunched flow, it runs in the background.
Quick actions open in a window.
The Actions & Recommendations component helps your users:
## •
Identify which steps to complete for a specific record and in which order
## •
Consider customized actions and offers that result from an Einstein Next Best Action strategy, such as a discount, a repair, or an
add-on service
## •
Restart flows that users have paused, and view stages in an active flow if stages are defined
## •
Identify and complete flows that are mandatory
## •
Find and start another action from a subset that you configure
## •
Understand the history of actions taken on a record, including when each action was started, paused, resumed, and completed and
by whom
Here’s an example of Salesforce Flow for Service set up in the Service Console app. The flow in the subtab helps agents verify the identity
of an incoming caller.
## 1

Before you add the component to your Lightning pages, first set up the flows and quick actions that you want to show. If you want to
include recommendations from Next Best Action strategies, configure them first as well.
Then create an Actions & Recommendations deployment. A deployment captures settings that you can reuse on multiple pages. Place
the component on your Lightning pages, and select the deployment in component properties.
Tip:  Learn how to put the Actions & Recommendations component to work for your agents. The Salesforce Flow for Service
module on Trailhead can help you get started.
Never heard of flows and process automation? Many of the tasks you assign, the emails you send, and other record updates are vital
parts of your standard business processes. Instead of doing this repetitive work manually, you can configure flows and processes to do
it automatically. To learn more, check out Automate Your Business Processes in Salesforce Help.
Supported Apps, Channels, Actions, and Objects in Lightning Flow for Service
Lightning Flow for Service is supported in Lightning console and standard navigation apps. You can set it up to work with Open CTI
for phone integration, including support for unknown callers, and Chat in Lightning Experience for chat integration.
Lightning Flow for Service Example Use Case
Lightning Flow for Service can help your agents follow consistent procedures when a customer calls or a support issue comes in.
You can associate actions with a new record, such as a case or contact record, and show agents a to-do list for the record page.
Implementing the Example Use Case
You can configure the Actions & Recommendations component in several ways. Creating a deployment in Setup is an easy way to
create RecordActions that appear in the list.
Enhance the User Experience
The Actions & Recommendations component gives your agents a clear set of steps to follow. Help your agents be more productive
by fine-tuning how they use the list.
## 2
Salesforce Flow for Service

Lightning Flow for Service Considerations
Learn about how packaging, change sets, and the sharing model can impact your Lightning Flow for Service implementation.
## SEE ALSO:
Trailhead module: Lightning Flow for Service
Supported Apps, Channels, Actions, and Objects in Lightning Flow for
## Service
Lightning Flow for Service is supported in Lightning console and standard navigation apps. You can set it up to work with Open CTI for
phone integration, including support for unknown callers, and Chat in Lightning Experience for chat integration.
The component can include these types of actions.
## •
Active screen flows, field service mobile flows, and autolaunched flows
Note:  Autolaunched flows run in the background without any user input. You can design an autolaunched flow to pause for
a time interval or until a condition exists. When an autolaunched flow pauses, we show a message that the flow completed.
When the flow resumes, however, it still has work to do.
## •
Quick actions that are available in the record page layout
## •
Recommendations that result from applying Next Best Action strategies
We support the Actions & Recommendations component on most Lightning pages, including custom Lightning pages. Custom sharing
rules limit support for the component on a few Lightning pages. We don’t support the component on these pages, for example.
## •
ContentDocuments
## •
## Events
## •
## Knowledge
## •
## Notes
## •
## Scorecard Associations
## •
## Scorecard Metrics
## •
## Tasks
We haven’t validated the component with these objects.
## •
AiDataset
## •
AiVisionModel
## •
CustomPersonAccountChild__p
## •
CustomPersonChild__p
## •
CustomPerson__p
## •
LiveAgentSession
## •
LiveChatVisitor
## •
OpportunityLineItem
## •
OpportunityLineItemSchedule
## •
OrderItem
## •
OrderItemTaxLineItem
## 3
Supported Apps, Channels, Actions, and Objects in Lightning
Flow for Service
Salesforce Flow for Service

## •
ProcessInstanceStep
## •
ProcessInstanceWorkitem
## •
ServiceResourceCapacity
## •
## Shift
## SEE ALSO:
Salesforce Help: Salesforce Console in Lightning Experience
## Salesforce Help: Salesforce Call Center
## Salesforce Help: Chat
Lightning Flow for Service Example Use Case
Lightning Flow for Service can help your agents follow consistent procedures when a customer calls or a support issue comes in. You
can associate actions with a new record, such as a case or contact record, and show agents a to-do list for the record page.
Let’s look at a fictional Service Cloud customer. Awesome Bank employs 20 agents who handle loan applications. Typically, agents get
calls from potential customers applying for a new loan. Agents also take calls from customers that have started the application process
online on the bank’s Experience Cloud site.
When a customer’s call is routed to the appropriate agent based on the loan type, the agent completes the loan application in the
following way.
1.The agent verifies the loan type and gathers basic information, such as the customer’s name and phone number.
2.The agent requests information that’s needed to obtain the customer’s credit score. Obtaining the credit score is a required step.
3.The agent follows a series of other steps to process the loan application.
4.When the application is processed successfully, the agent submits it for approval.
5.When the loan application is approved, the loan is sent for disbursement.
6.The agent wraps up the loan application process, and logs the call.
Meet Cyrus, the service team leader. He’s in charge of the customer service department and is looking at ways to improve agent efficiency.
He wants to streamline the following.
## •
Common steps that are applicable to all loan types
## •
Unique steps specific to the loan type
## •
A standardized way for agents to complete steps that have been started before, such as when a customer starts an application online
and later calls to complete it
In addition, Cyrus wants agents to suggest extra products and services to qualified customers. He approaches Maria, the service admin
in charge of Salesforce applications for Awesome Bank. With Lightning Flow for Service, Maria can provide Awesome Bank agents:
## •
A method of presenting agents with recommendations, such as a next step or customized offer
## •
A dynamic set of flows and quick actions associated with the record so that agents can see which steps to complete
## •
A simple way for agents to resume paused flows for a record, such as flows that customers have started on an Experience Cloud site
page and then paused
## •
An easy way for agents to find another step based on customer needs
## •
A means of seeing which actions have been started and completed on a record
## •
A reminder for agents to complete screen flows that are required, like the credit score check
## 4
Lightning Flow for Service Example Use CaseSalesforce Flow for Service

After Maria creates flows and quick actions, she can choose from several methods to set up Lightning Flow for Service. All the methods
create RecordActions so that Maria can present a list of steps to agents.
## •
Associate Actions to Records with a Deployment
## •
Associate Actions to Records with Process Builder
## •
Associate Actions to Records with SOAP
## •
Associate Actions to Records with Apex
Maria decides to configure an Actions & Recommendations deployment in Setup. A deployment lets her set up the component from
the user interface rather than using code. She can specify which channel-specific actions appear on which record pages, and give her
agents step-by-step guidance. Best of all, she can display special offers that result from applying Next Best Action strategies to a set of
recommendations.
Note:  To show recommendations from Next Best Action strategies, use a deployment or API. Process Builder lets you show flows
and quick actions on record pages when there’s a trigger condition.
## SEE ALSO:
Implementing the Example Use Case
Trailhead module: Lightning Flow for Service
Implementing the Example Use Case
You can configure the Actions & Recommendations component in several ways. Creating a deployment in Setup is an easy way to create
RecordActions that appear in the list.
Maria, the admin at Awesome Bank, is ready to set up Lightning Flow for Service for her agents. She wants to configure actions as channel
defaults so that agents see the loan application steps on a contact or case page. In addition, she wants to integrate Lightning Flow for
Service with Awesome Bank’s Open CTI implementation. That way, agents can quickly create a contact record when there's an unknown
caller.
Maria completes the following tasks.
1.Create flows in Flow Builder.
## •
To handle unknown callers, Maria builds a flow called Create Contact that walks agents through creating a contact record.
## •
To guide agents and portal customers through the loan application, she creates a flow called New Loan.
## •
To determine a customer’s credit score, she creates a flow called Check Credit Score.
## •
To let agents submit a loan application, she builds an autolaunched flow called Process Loan.
## •
To walk agents through the wrap-up steps, she creates a flow called Wrap Up Loan.
2.Update the Screen Pop Settings for the softphone layout in Setup (in Lightning Experience).
To handle unknown callers, Maria updates the No Matching Records setting to pop to the unknown caller flow, Create Contact. This
setting ensures that when an agent accepts a call from an unknown caller, the agent is presented with a flow that creates a contact
record.
3.Create an Actions & Recommendations deployment in Setup.
a.From Setup, in the Quick Find box, enter Actions& Recommendations, and select Actions & Recommendations.
b.Click New Deployment. Name your deployment.
## 5
Implementing the Example Use CaseSalesforce Flow for Service

c.Select at least one type of guidance. Select Flows and quick actions, or to display actions and offers that result from Next Best
Action strategies, select Recommendations .
Maria selects Flows and quick actions. After she gets the component to show the right steps, she can come back, edit the
deployment, and configure settings to show recommendations too.
d.Select objects to use for object-specific quick actions and Next Best Action strategies.
Maria adds the Case and Contact objects. That way, she can show agents object-specific quick actions, such as Log a Call.
Note:  To use object-specific quick actions in deployment settings, add them to the record page layout.
e.Configure channel defaults.
On each channel, select the actions to show as defaults. For example, Maria wants to configure the flows defined in Step 1 as
channel defaults. She drags those flows to the preview pane, and adds the Log a Call quick action too. She assigns attributes to
indicate which actions users can remove at run time, and which are mandatory, such as the Check Credit Score flow.
Note:  Agents see the channel defaults when no other RecordActions are defined for the record page when it opens in a
channel. If you create RecordActions using Process Builder or APIs, your users don’t see the actions that you configure as
channel defaults.
f.Define which actions are available for users to start as needed. At run time, an agent can click Add and select an action from
this subset.
4.Edit the Lightning record page, and add the Actions & Recommendations component.
To display a list of actions associated with the contact and case records, Maria adds the component to those pages. In component
properties, she selects her deployment.
## The Agent Experience
The component gives the loan agents at Awesome Bank a clear set of steps to follow when they speak to customers. Under
Recommendations (1), they see offers or actions from a Next Best Action strategy when the deployment is configured to show them.
When the record page has a paused flow, it’s listed in under Resume Paused Actions (2). If there’s a handoff between agents, an agent
can use the History tab (3) to learn which steps in the loan process have been started or completed. If agents don’t see a step, they can
click Add and find a different action (4) to run. And agents see an asterisk next to mandatory actions that are important to complete (5).
## 6
Implementing the Example Use CaseSalesforce Flow for Service

## Example Customer Scenarios
Yolanda is a business owner who is hoping to expand and open a new location. She’s looking for a small business loan to jump-start
the new venture, so she calls Awesome Bank. Yolanda has never done business with the bank before, so her phone number isn’t
recognized. Because Maria configured settings to pop to the Create Contact flow for unknown callers, the agent that takes Yolanda's
call sees the flow and completes a new contact record. The agent also sees other steps to complete for the loan application because
Maria configured default actions for the Phone channel. One of the other steps is the mandatory step to check Yolanda’s credit score.
Erika is buying a new car. She heads to Awesome Bank’s website and starts an application for an auto loan. Midway through, she realizes
that she doesn’t have the required vehicle information. She pauses the application. Later that day, Erika finds the information she needs
and calls to finish the application. Because the paused flow is associated with Erika’s contact record, when the agent takes the call, the
paused flow appears on the Actions & Recommendations component on Erika’s contact page. The agent resumes the flow, enters the
missing information, and completes the application, picking up right where Erika left off.
## SEE ALSO:
Associate Actions to Records with a Deployment
Customize Your Lightning Pages with the Component
Enhance the User Experience
The Actions & Recommendations component gives your agents a clear set of steps to follow. Help your agents be more productive by
fine-tuning how they use the list.
## 7
Enhance the User ExperienceSalesforce Flow for Service

Show Users the Top Recommendations
You can show the top recommendations from your Einstein Next Best Action strategies in the Actions & Recommendations component.
To display recommendations, configure a deployment in Setup or programmatically with the metadata type RecordActionDeployment.
Let Users Resume Paused Flows from the Actions & Recommendations Component
When you configure Process Automation Settings, you can allow users to pause flows. Show agents paused flows associated with
the current record page in the Actions & Recommendations component. When there’s a handoff or a customer calls back, the agent
can easily find and resume the paused flow. The component shows all paused flows associated with the current record, including
flows not started from the list.
Show Users Which Steps to Complete First or Last
Pin actions to the top or bottom of the Actions & Recommendations component so that users know to complete them first or last.
Remind Users to Complete Mandatory Steps
Highlight required steps by configuring them as mandatory actions. When agents try to close a flow that’s mandatory, they see a
reminder that the step is required.
Keep Steps Visible on Your List
Hide the remove option for actions that you want agents to complete. Agents can’t remove these steps, so they remain on the list
unless they’re completed.
## Find Another Action
Sometimes a customer interaction requires a step that doesn’t appear in the Actions & Recommendations component. When an
agent clicks Add, they can search for an action and start it. You can help users narrow their search by configuring a subset of actions.
View the Action History
See which actions were launched, by which agents, and when in the History tab on the Actions & Recommendations component.
The History tab also shows the state, or status, for each action, so you can see when an action was started, paused, resumed, and
completed. You also can access the action history for a record programmatically using the RecordActionHistory object.
Show Users the Top Recommendations
You can show the top recommendations from your Einstein Next Best Action strategies in the Actions & Recommendations component.
To display recommendations, configure a deployment in Setup or programmatically with the metadata type RecordActionDeployment.
For example, Awesome Bank wants to present credit card offers to customers that have good credit scores. First, Maria creates flows
that can walk agents or customers through the card application process. Maria configures those flows as Next Best Action recommendations.
To filter the right offers and present them to the right customers, Maria sets up an action strategy.
In an Actions & Recommendations deployment, Maria configures the component to show recommendations. She selects strategies that
the deployment uses, and configures how the recommendations appear.
## 8
Show Users the Top RecommendationsSalesforce Flow for Service

When a customer qualifies, the agent clicks Recommendations to see the offers. When a recommendation is accepted, the associated
flow opens.
Tip:  In your recommendation, keep the labels for the accept and reject buttons to fewer than 10 characters. Otherwise, the buttons
don’t appear side by side.
## SEE ALSO:
## Salesforce Help: Einstein Next Best Action
Let Users Resume Paused Flows from the Actions & Recommendations
## Component
When you configure Process Automation Settings, you can allow users to pause flows. Show agents paused flows associated with the
current record page in the Actions & Recommendations component. When there’s a handoff or a customer calls back, the agent can
easily find and resume the paused flow. The component shows all paused flows associated with the current record, including flows not
started from the list.
For example, Erika is a customer at the fictitious Awesome Bank. Erika is completing an online auto loan application that uses a flow. She
pauses the flow because she’s missing some required information. She calls the bank later to complete the application. Because the
current record variable in the flow is set to Erika’s contact record, when her contact page opens, the agent sees the paused flow in the
Actions & Recommendations component. To resume the flow, the agent clicks Resume Paused Actions and selects the flow.
## 9
Let Users Resume Paused Flows from the Actions &
## Recommendations Component
Salesforce Flow for Service

When an agent resumes a flow, it opens, and the list updates to include it. If the flow was started from a pinned region of the list, it’s
added at the end of that region. Otherwise, it’s added to the bottom of the unpinned region.
Note:  A flow can use the variable Flow.CurrentRecord to track the current record associated with the flow. Sometimes
API or flow logic updates this variable. For example, if a flow is associated with a lead record and the lead is converted to a contact,
the record association is updated. When a user pauses a flow, the component checks the currently associated record. If the record
context changed, the paused flow doesn’t appear on the record page’s list. Instead, to resume the flow, a message directs the user
to the new record that is associated with the flow.
## SEE ALSO:
## Salesforce Help: Let Users Pause Flow Interviews
Salesforce Help: Add Record Context to Your Flows
Show Users Which Steps to Complete First or Last
Pin actions to the top or bottom of the Actions & Recommendations component so that users know to complete them first or last.
Maria, the Salesforce admin at Awesome Bank, can assign actions to the top, bottom, or unpinned regions of the component. The method
by which she sets up RecordActions determines how she assigns an action to a region.
## •
When Maria configures channel defaults in a Actions & Recommendations deployment, she can select an action and drag it to a
region in the preview area.
## 10
Show Users Which Steps to Complete First or LastSalesforce Flow for Service

## •
If Maria uses Process Builder and creates RecordActions, she can assign the Top, Bottom, or None value to the RecordAction’s Pinned
attribute.
## •
If Maria uses an API to define RecordActions, she can set the Pinned attribute for the action.
Note:  Each step in the component has a pulldown menu. The Move Up and Move Down menu options let users reorder actions,
but only within a pinned or unpinned region.
Remind Users to Complete Mandatory Steps
Highlight required steps by configuring them as mandatory actions. When agents try to close a flow that’s mandatory, they see a reminder
that the step is required.
Maria, the Salesforce admin at Awesome Bank, wants to make sure that agents complete the Check Credit Score step. This step is required
for every loan application. To help agents remember to complete this step, Maria defines this screen flow as a mandatory action.
Note:  The reminder appears for screen flows and field service mobile flows. We don’t show the reminder for quick actions or
autolaunched flows that are marked as mandatory.
Maria can set up an action as mandatory in several ways. Which method Maria uses depends on how she creates the RecordActions that
display in the component.
## •
When Maria configures channel defaults in an Actions & Recommendations deployment, she can select an action in the preview
area and mark it as mandatory.
## •
If Maria uses Process Builder to create RecordActions, she can set the Is Mandatory attribute to True.
## 11
Remind Users to Complete Mandatory StepsSalesforce Flow for Service

## •
If Maria uses an API to define RecordActions, she can set the mandatory field for the action to True.
For example, when an agent tries to close a mandatory screen flow before completing it, a message reminds the agent that the flow is
required. Clicking Cancel dismisses the warning and continues the flow. Or, the agent can click Finish Later, which closes the tab or
window. The agent can start a new instance of the flow later.
## SEE ALSO:
Keep Steps Visible on Your List
Keep Steps Visible on Your List
Hide the remove option for actions that you want agents to complete. Agents can’t remove these steps, so they remain on the list unless
they’re completed.
By default, steps on the Actions & Recommendations component are removable. However, if you choose, you can hide the remove
option from users.
## 12
Keep Steps Visible on Your ListSalesforce Flow for Service

Maria, the Salesforce admin at Awesome Bank, wants to make sure that agents complete the Check Credit Score flow. In addition to
marking the flow mandatory, she can hide the remove option in one of these ways.
## •
When Maria configures channel defaults in a deployment, she selects the Check Credit Score flow in the preview area and marks it
as not removable.
## •
If Maria uses Process Builder and creates RecordActions, she can set the Hide Remove Action in UI attribute in the RecordAction to
## True.
## •
If Maria uses an API to define RecordActions, she can set the attribute in the RecordAction.
Note:  Even if you hide the remove option from users, actions can still be removed from the component using an API.
## Find Another Action
Sometimes a customer interaction requires a step that doesn’t appear in the Actions & Recommendations component. When an agent
clicks Add, they can search for an action and start it. You can help users narrow their search by configuring a subset of actions.
For example, Maria, the Salesforce admin at Awesome Bank, wants her agents to see only the actions that they use for loan processing.
## 13
Find Another ActionSalesforce Flow for Service

Maria configures the set of actions available to her agents.
## •
When Maria configures an Actions & Recommendations deployment in Setup, she selects which actions her agents see when they
click Add.
## •
If Maria uses Metadata API to define a deployment, she can define which actions appear for her agents.
When a user adds an action, it starts, and is added to the list above the actions pinned at the bottom.
View the Action History
## EDITIONS
Available in: Lightning
## Experience
Available in: Essentials,
## Professional, Enterprise,
## Performance, Unlimited,
and Developer Editions
Lightning console apps are
available for an extra cost to
users with Salesforce
Platform user licenses for
certain products. Some
restrictions apply. For pricing
details, contact your
Salesforce account
executive.
See which actions were launched, by which agents, and when in the History tab on the Actions &
Recommendations component. The History tab also shows the state, or status, for each action, so
you can see when an action was started, paused, resumed, and completed. You also can access
the action history for a record programmatically using the RecordActionHistory object.
Use the Component’s History to Understand Status
The History tab lists state changes for actions associated with the record. It helps agents and
supervisors grasp status so that they can quickly decide what to do next. For example, in a handoff
or escalation, an agent or supervisor can review the history to identify gaps and determine the next
step.
Here’s an example. The History tab lists the most recent 20 state changes, sorted with the most
recently logged events listed first. Click View More to see the next 20 state changes in the log.
Users can filter the list to see actions by status. The filter only applies to the last 200 actions.
## 14
View the Action HistorySalesforce Flow for Service

Use APIs to Query the Action History
You can also use APIs to query the RecordActionHistory object, which is a big object.
Note:  The RecordActionHistory object is read-only. It is available in API version 44.0 and later.
Both synchronous and asynchronous queries are supported. Using SOQL, SOAP, REST, Bulk, or Apex APIs, synchronous queries must
follow a specific pattern or they fail. See the description and examples in the Object Reference for Salesforce and Lightning Platform. To
learn more about big objects and how to query them, see the Query Big Objects module on Trailhead.
If you have access to Analytics, you can query the RecordActionHistory object and use the data to build an Analytics dashboard. For
example, the dashboard can show usage data and compare how many actions were started, paused, resumed, and completed in a given
time period.
## 15
View the Action HistorySalesforce Flow for Service

Lightning Flow for Service Considerations
Learn about how packaging, change sets, and the sharing model can impact your Lightning Flow for Service implementation.
## Packaging
When you package up your implementation, the package includes your Actions & Recommendations deployment settings. Any
processes and flows that reference flows through RecordActions are also included in the package. For example, if Flow A creates a
RecordAction that references Flow B, adding Flow A to a package also adds Flow B to the package.
When you add your app to the package, here’s what’s included:
## •
All the objects in the app
## •
For each object, the associated page layouts, Lightning pages (including the page with the component), active processes, and
quick actions. The package includes the Actions & Recommendations deployment and settings defined in the deployment.
## •
If a deployment references flow actions, those flows are included.
Note: Make sure that flows in your deployment are active before you create a package. Otherwise, inactive flows in a
deployment can cause the package not to install successfully.
## •
If a process includes flow actions, those flows are included.
## •
If an object includes flow quick actions, those flows are included
## Change Sets
You can add the RecordAction Deployment component to your change sets.
An option in Process Automation Settings determines whether flows are deployed as active or inactive (see Deploy Processes and
Flows as Active). Unless the Deploy processes and flows as active option is set, your flows are deployed as inactive. After using
a change set to move a deployment from a sandbox to production, check to make sure that your flows are active.
## 16
Lightning Flow for Service ConsiderationsSalesforce Flow for Service

## Sharing Model
Access to the RecordAction object is determined by a user’s access to the associated parent record. This sharing model applies to
access in the user interface, API, Bulk API, and Bulk API 2.0.
## •
If the user has read access on the record that the action is associated with, the user can perform all operations (create, read,
update, and delete) on the corresponding RecordAction.
## •
If the user doesn’t have read access on the record that the flow is associated with, then the user doesn’t have access to the
associated RecordAction.
Note:  When using RecordAction and Salesforce Object Query Language (SOQL), make sure that your queries filter by the
parent record. To filter by the parent record, use a where clause for users without Modify All Data permission. Otherwise, the
query doesn’t work. If the user has Modify All Data permission, a where clause isn't necessary to filter correctly.
Here’s an example of a where clause for RecordAction.
SELECTfieldsFROMRecordActionWHERERecordId=ENTITY_ID
## 17
Lightning Flow for Service ConsiderationsSalesforce Flow for Service

## LIGHTNING FLOW FOR SERVICE IMPLEMENTATION
## CHECKLIST
Review the Lightning Flow for Service checklist before you roll out your implementation.
Tip:  If you’re new to process automation, we recommend completing Automate Your Business Processes with Salesforce Flow
in Trailhead. The Lightning Flow for Service module in Trailhead can also help you prepare.
We recommend that you have a working knowledge of the following features and user interfaces.
## •
Process automation tools, like Process Builder and Flow Builder
## •
Einstein Next Best Action, if you plan to show recommendations from action strategies to your users
## •
## Lightning App Builder
## •
Lightning console or standard navigation apps
You need the following permissions to complete an end-to-end implementation.
## User Permissions Needed
Manage FlowTo create flows in Flow Builder:
Customize ApplicationTo create quick actions:
To manage deployments in Setup that include flows and quick actions:
## Modify All Data
To manage deployments in Setup that include recommendations:
## OR
## Manage Next Best Action Strategies
View Setup and ConfigurationTo view Actions & Recommendations deployments in component properties:
Manage Flow AND View All DataTo create a process in Process Builder:
Customize ApplicationTo create and save pages in the Lightning App Builder:
To create or manage Lightning apps:
To set up and configure Chat:
Manage Call CentersTo set up and configure Open CTI:
To let your users run flows from an Actions & Recommendations component, make sure that they have the correct flow permissions.
For flows that change data, users need permission to create, read, edit, and delete the relevant records and fields.
## User Permission Needed
## Flow User
To run flows:
## OR
FlowUser field enabled on the user
detail page
## 18

## User Permission Needed
## OR
## Manage Flow
## OR
If Override default behavior and restrict
access to enabled profiles or permission
sets is selected for an individual flow, access
to that flow is given to users by profile or
permission set
To set up recommendations, you need these permissions.
## User Permission Needed
Default On for Tab Setting for
Recommendations object
Display Recommendations as a tab:
Modify all data
## OR
Create and manage recommendations:
## Manage Next Best Action Recommendations
To manage or run action strategies, you need these permissions.
## User Permission Needed
## Modify All Data
## OR
To create or manage action strategies:
## Manage Next Best Action Strategies
## Run Flows
## OR
To run an action strategy:
Flow User field enabled on the user detail
page
Use the following individual setup tasks when implementing Lightning Flow for Service.
Complete If...Task
You want to create a flow, quick action, or recommendation that
shows in the component.
Create Actions to Show
You want to define component settings: what type of guidance
to show, channel defaults, and additional actions that users can
Associate Actions to Records with a Deployment
## 19
Lightning Flow for Service Implementation Checklist

Complete If...Task
start at run time. You can also create deployments
programmatically using the Metadata API.
You want to create a process for actions declaratively using Process
Builder. With Process Builder, you can automatically associate
Associate Actions to Records with Process Builder
actions with a record when the record meets criteria that you
define.
You want to associate actions to records programmatically using
## SOAP API.
Associate Actions to Records with SOAP
You want to associate actions to records programmatically using
## Apex.
Associate Actions to Records with Apex
You want to add the component to record pages in your app.Customize Your Lightning Pages with the Actions &
## Recommendations Component
You want to integrate Lightning Flow for Service with Chat.Integrate Chat with Lightning Flow for Service
You want to integrate Lightning Flow for Service with Open CTI
and configure your softphone screen pop settings.
Integrate Open CTI with Lightning Flow for Service
## 20
Lightning Flow for Service Implementation Checklist

## CREATE ACTIONS TO SHOW
Create the actions and recommendations that you want to users to start from the Actions & Recommendations component. You can
show flows, quick actions, and recommendations that result from Next Best Action strategies.
1.Create a flow.
a.To create flows that interactively guide your users, use Flow Builder, a point-and-click tool that lets you automate business
processes.
The component can show screen flows, field service mobile flows, and autolaunched flows. You can also define the flow to
include stages so that users can see where they are in a series of steps.
Note:  If you want to pass the parent record ID into a flow when it’s launched from the component, create a flow text
input variable named recordId. The name is case-sensitive. When an agent launches the flow from the component,
the parent record ID is passed into the flow variable. Your flow can then use the parent record ID to update a field in the
record, for example.
b.Test your flow
Before you activate your flow, test it and make sure that it’s working as expected.
c.Activate your flow.
To appear in the Actions & Recommendations component, your flow must be active.
2.Create a quick action.
You can create a global or object-specific quick action and show it in the component. For the quick action to appear in the component,
add it to the record page layout.
3.Create offers or actions to recommend to users using Next Best Action strategies.
a.Create recommendations.
Recommendations are customized actions and offers that you want to present to users. When you create a recommendation,
specify a screen flow that starts when the user accepts the recommendation.
b.Create an action strategy.
To determine which recommendations show in the component, create an action strategy. Action strategies use business rules,
predictive models, and other data sources to filter recommendations.
## SEE ALSO:
Associate Actions with Records
Aura Components Developer Guide: Use Aura Components with Flows
Salesforce Help: Show Users Progress Through a Flow with Stages
## Salesforce Help: Create Global Quick Actions
Salesforce Help: Create Object-Specific Quick Actions
## Salesforce Help: Einstein Next Best Action
## 21

## ASSOCIATE ACTIONS WITH RECORDS
To associate actions to records declaratively, configure channel-specific defaults in an Actions & Recommendations deployment or use
Process Builder. To associate flows to records programmatically, use SOAP or Apex. After you add the Actions & Recommendations
component to your Lightning pages, you can display RecordActions that you’ve configured.
Associate Actions to Records with a Deployment
Use an Actions & Recommendations deployment to show default actions when records open from phone screen popups, chats, list
views, or related records. A deployment also lets you show recommendations from Next Best Action strategies. After you create a
deployment, select it in the Actions & Recommendations component on your Lightning record pages.
Associate Actions to Records with Process Builder
Process Builder is a point-and-click automation tool that you can use to design processes that kick off when a new or updated record
meets specific criteria. After you create flows and quick actions, you can associate them with a record by building a process. Use
Process Builder to create a process that, when triggered, creates a RecordAction. The RecordAction represents an association between
an action and the record that kicked off the process.
Associate Actions to Records with SOAP
If your business maintains code outside the Salesforce platform, you can use SOAP API to create, retrieve, update, or delete a
RecordAction.
Associate Actions to Records with Apex
If you want to control how you trigger the creation of a RecordAction, you can use Apex to associate actions to records. The
RecordAction object is exposed as a standard object in Apex. You can trigger it before a DML operation or on delete or undelete.
You can also provide custom error handling.
## SEE ALSO:
## Developer Documentation: Process Automation Cheatsheet
Associate Actions to Records with a Deployment
Use an Actions & Recommendations deployment to show default actions when records open from phone screen popups, chats, list
views, or related records. A deployment also lets you show recommendations from Next Best Action strategies. After you create a
deployment, select it in the Actions & Recommendations component on your Lightning record pages.
When you configure an Actions & Recommendations deployment, you define these settings.
## •
Type of guidance to show—Select at least one option, Flows and quick actions or Recommendations.
## •
Context objects—Specify which objects to use for object-specific quick actions and action strategies.
## •
Channel defaults—For each channel, define the default actions that appear when a record is opened in that channel and no other
RecordAction associations exist.
## •
Additional actions—Define which actions users can launch at run time, as needed. When a user clicks Add and selects an action, it
starts. We create a RecordAction that associates the action with the current record page.
## •
Recommendation settings—Specify how Next Best Action recommendations appear, how many to show, and which action strategies
to use.
## 22

Note:  You can use Process Builder to create RecordActions that appear in the component, but to show recommendations, create
a deployment or use API.
Before you configure a deployment, first set up the flows and quick actions that you want to show in the component. If you want to
include recommendations from Next Best Action strategies, configure them first as well.
You can define a deployment in Setup, or programmatically using the metadata type RecordActionDeployment.
1.From Setup, in the Quick Find box, enter Actions& Recommendations, and select Actions & Recommendations.
2.Click New Deployment.
a.Name your deployment.
b.Select at least one type of guidance to show, for example, Flows and quick actions. To display actions and offers that result
from filtering recommendations with your Next Best Action strategies, select Recommendations.
Note:  If you edit a deployment and deselect a type of guidance, we delete the related settings.
3.Select up to 10 objects that provide context for object-specific quick actions and Next Best Action strategies.
You can associate quick actions and strategies with specific object types, giving them an object-specific, rather than global, context.
When a page for a selected object opens, the component lists the global and object-specific actions and recommendations. On
other pages, it displays only the global items.
For example, you define an object-specific quick action for the Contact object. To show this quick action in the component on
Contact pages, add Contact as a context object. Or, to filter recommendations with a strategy that uses case fields, add the Case
object as a context object. Then, in strategy settings, select a strategy that filters recommendations for cases.
Note:  To use object-specific quick actions in a deployment, add them to record page layouts for those objects. The component
shows quick actions that are available in the page layout.
4.If you selected the option to show flows and quick actions, configure a default list for each channel.
## Important:
## •
The component shows channel defaults only when no other RecordActions exist and the record page is opened in that
channel. For example, if you set up a process in Process Builder that creates RecordActions for a record page, the component
shows the RecordActions from your process instead of the channel defaults that you configure here.
## •
If a default action is added to an existing deployment, users see the action in the Actions & Recommendations component
on new records only.
a.Click a tab to configure settings for that channel.
## •
## Chat
This channel works with Chat in Lightning Experience. Use this channel to specify default actions for when agents chat with
customers. To use this channel, add the component to the chat transcript record page.
## •
## Phone
This channel works with Open CTI. Use this channel to specify default steps for when customers call and records are shown
to the agent. To use this channel, update your softphone screen pop settings for no matching records and single-matching
records.
## •
## Default
Use this channel to specify default actions for when records open from list views or related records.
The Chat and Phone channels display even if you don’t have these features in your org.
## 23
Associate Actions to Records with a DeploymentAssociate Actions with Records

You can configure multiple channels. For example, if you use Open CTI, you can configure actions for the Phone and Default
channels. That way, agents can select actions from the list when a caller’s contact record is popped. Agents can also navigate
to a contact record manually, such as when they open a record from a list view. Then they see the actions that you set up in the
Default channel.
Note:  For information about Chat and Open CTI integration, see Integrate Chat with Lightning Flow for Service and
Integrate Open CTI with Lightning Flow for Service.
b.On each channel, drag actions from All Actions to the preview area.
The preview area has three regions: Top Pinned, Unpinned, or Bottom Pinned. Use the pinned regions to specify actions that
you want your users to complete first and last. The Unpinned region is for actions that you want your users to complete during
the record’s life cycle.
c.Select actions that are important, and click Mark Mandatory.
When a user tries to close a flow that’s marked as mandatory without completing it, a reminder appears.
Note:  You don’t see a reminder for quick actions or autolaunched flows that are marked as mandatory.
d.Select actions that you don’t want users to remove at run time, and click Unmark Removable. By default, all actions are
removable.
e.Specify whether to auto-launch the first action when the record page opens.
f.Click Save.
5.If you selected the option to show flows and quick actions, narrow the list of actions that users can launch at run time. When the
user clicks Add, the component shows the subset of actions that you configure here.
6.If you selected the option to show recommendations, configure display settings and Next Best Action strategies.
a.On the General Settings tab, set up how recommendations display, and select a default strategy.
## 24
Associate Actions to Records with a DeploymentAssociate Actions with Records

Set the maximum number of recommendations to a value from 1 to 4.
b.On the Strategy Settings tab, you can select object-specific strategies that override the default strategy on those pages.
Note:  For the component to display recommendations, select a default or an object-specific strategy. A strategy loads
and filters recommendations so that your users can see the best next steps.
c.Click Save.
7.In Lightning App Builder, add the Actions & Recommendations component to a page, and select the deployment.
If you don’t select a deployment in component properties, no actions appear when the user clicks Add. In addition, the component is
empty unless other RecordActions exist for the record page.
Associate Actions to Records with Process Builder
Process Builder is a point-and-click automation tool that you can use to design processes that kick off when a new or updated record
meets specific criteria. After you create flows and quick actions, you can associate them with a record by building a process. Use Process
Builder to create a process that, when triggered, creates a RecordAction. The RecordAction represents an association between an action
and the record that kicked off the process.
RecordActions appear in the Actions & Recommendations component on the record page, ready for your users to start.
Note:  When you associate actions to records using Process Builder, you override any channel defaults that you configured in an
Actions & Recommendations deployment.
1.Define the process properties.
The process properties uniquely identify your process.
2.Configure the process trigger.
Every process includes a trigger, which tells the process when to start. How you configure that trigger depends on what type of
process you’re creating.
## 25
Associate Actions to Records with Process BuilderAssociate Actions with Records

3.Add process criteria.
Define the criteria that must be true before the process can execute the associated actions.
4.Add actions to your process and create a record from the process.
After you define a criteria node, create a record from the process when criteria are met. Actions are executed in the order in which
they appear in the Process Builder.
Note: Flows is a supported Action Type in Process Builder. This type is different from creating a RecordAction. An Action
Type of Flows supports only flows that don’t have screens, and is invoked immediately when the process is triggered.
Creating a RecordAction doesn’t invoke the flow; rather, it associates a record with the flow so that your users can run it.
Important:  To associate flows or quick actions to records, you must create a RecordAction.
Specify the following.
## •
## Action Type: Createa Record
## •
Record Type: RecordAction
Set field values for the Create a Record action.
ValueTypeField
Specify the action that you want to associate with the record.PicklistAction
Specify whether the action is a flow or a quick action.PicklistAction Type
Specify the order of the action among all actions associated with this
record. Actions are ordered in comparison to other actions in their pinned
NumberOrder
or unpinned region. If two actions have the same order, then they are
sorted by their last modified date.
Specify the record associated with the action. For most use cases, select
the ID for the object you’ve selected for your process trigger. For
Field ReferenceParent Record ID
example, if you used the contact object, set the value to
[Contact].Id.
If set to True, the flow is required. When a mandatory screen flow is
launched, if the user tries to close the tab or window, a message appears
BooleanIs Mandatory
and reminds the user to complete the flow. The reminder doesn’t appear
for quick actions or autolaunched flows.
If set to True, users can’t see the Remove option for the action in the
component. However, actions can still be deleted using the API.
BooleanHide Remove Action in UI
Specify whether the action is pinned to the top or bottom of the
component. To display the action in the unpinned region, use None.
PicklistPinned
5.Activate your process.
When your criteria are met and your process runs, the actions that you specified are associated with the parent record.
Example: Create a process that adds a required flow for users to verify a contact’s information, like an email address, when their
phone number changes.
1.Choose the contact object, and start the process when a record is created or edited.
## 26
Associate Actions to Records with Process BuilderAssociate Actions with Records

2.Create criteria for when the [Contact].MobilePhone field changes.
3.Add a Create a Record action, and specify RecordAction for the Record Type
4.Set field values for the record, pointing to your Verify_Information flow and the parent record ID. To encourage the
user to complete this flow, specify the Is Mandatory field as True.
## 27
Associate Actions to Records with Process BuilderAssociate Actions with Records

5.Activate the process.
When the contact’s MobilePhone field changes, the Verify Information flow opens as a subtab on the contact record. An asterisk
next to the flow indicates that it is mandatory.
Associate Actions to Records with SOAP
If your business maintains code outside the Salesforce platform, you can use SOAP API to create, retrieve, update, or delete a RecordAction.
Note:  RecordAction is available in API version 42.0 and later.
## SEE ALSO:
SOAP API Developer Guide: RecordAction
Associate Actions to Records with Apex
If you want to control how you trigger the creation of a RecordAction, you can use Apex to associate actions to records. The RecordAction
object is exposed as a standard object in Apex. You can trigger it before a DML operation or on delete or undelete. You can also provide
custom error handling.
Note:  RecordAction is available in API version 42.0 and later.
Here are some scenarios that Apex better accommodates.
## 28
Associate Actions to Records with SOAPAssociate Actions with Records

## •
Triggering before a DML operation rather than after
## •
Triggering on delete and undelete DML operations
## •
Validating data before the action is run
## •
Custom error handling
## •
Partial completion rather than complete failure
Example: This example uses an Apex class and trigger pair to associate a flow to a newly created account that satisfies specific
criteria. In the class, a method is defined that takes in a list of accounts and creates a RecordAction for each of them. It sets the
new account as the RecordId and the ActionDefinition as an active flow. The trigger is called after the insert of an account record.
When the criterion (type is Customer) is satisfied, the class method is executed, and it adds the defined flow to the new account.
## Apex Class
publicclassRecordActionHandler{
publicstaticvoidaddNewCustomerFlow(Account[]accts){
RecordAction[]recordActions= new List<RecordAction>();
for (Accounta : accts){
RecordActionra = new RecordAction(RecordId=a.Id,
ActionDefinition='New_Customer_Flow', Order=1,ActionType='Flow');
recordActions.add(ra);
## }
try {
insertrecordActions;
} catch(DMLExceptione) {
System.debug('An unexpectederrorhas occurred:' + e.getMessage());
## }
## }
## }
## Apex Trigger
triggerRecordActionTriggeron Account(afterinsert) {
Account[]customerAccounts= new List<Account>();
for (Accounta : Trigger.new) {
if (a.Type== 'Customer') {
customerAccounts.add(a);
## }
## }
RecordActionHandler.addNewCustomerFlow(customerAccounts);
## }
## SEE ALSO:
## Apex Developer Guide
## 29
Associate Actions to Records with ApexAssociate Actions with Records

## CUSTOMIZE YOUR LIGHTNING PAGES WITH THE ACTIONS
## & RECOMMENDATIONS COMPONENT
The Actions & Recommendations component displays RecordActions associated to the parent record. Add the component to your
Lightning pages so that users can see the actions that they can take.
Note:  You can add the Actions & Recommendations component to Lightning console and standard navigation pages for most
objects. To learn about supported objects, see Supported Apps, Channels, and Objects.
First, plan out your user’s experience. When do you want users to see the component? What records will your users be on? What other
information do you want your users to see on the page?
After you identify a record page to edit, create a custom Lightning page for it using one of the pinned region templates available in the
Lightning App Builder. The pinned region page allows you to display the Actions & Recommendations component while flows open in
subtabs for console apps.
1.Before you add the component to your record pages, create an Actions & Recommendations deployment.
2.Add the component to your pages.
In the Lightning App Builder, drag the Actions & Recommendations component to a pinned region on a page. For the Service Console
app, we recommend adding the component to the left pinned sidebar.
3.Select the deployment in component properties.
If you don’t select a deployment, no actions appear when the user clicks Add. In addition, the component is empty unless other
RecordActions exist for the record.
4.Save your Lightning page.
## 30

If needed, activate the page and assign it to your app.
## SEE ALSO:
Salesforce Help: Create and Configure Lightning Experience Record Pages
## 31
Customize Your Lightning Pages with the Actions &
## Recommendations Component

## INTEGRATE CHAT WITH LIGHTNING FLOW FOR SERVICE
Customers who chat with you are often looking for quick and immediate resolutions to their problems. Lightning Flow for Service helps
your agents provide consistent and efficient service. Agents can view your business processes in context of the customer chat because
actions are presented as subtabs of the Chat Transcript primary tab. Agents see the appropriate actions to take right up front, without
having to manually search for them.
Lightning Flow for Service supports Chat in Lightning Experience, which uses Omni-Channel routing.
1.Set up your actions.
Use Flow Builder to create individual flows. Create quick actions, and add them to the record page layout so that they can appear
in the component.
2.Create an Actions & Recommendations deployment.
In the settings for the Chat channel, specify the actions that agents see by default. Specify which actions you want agents to complete
first and last, and whether to auto-launch the first flow in the list. Optionally, select the actions that you want agents to see when
they click Add.
3.Create a Lightning console record page.
a.In Lightning App Builder, create a record page for the Chat Transcript object using the Console: Pinned Left and Right Sidebars
page template.
b.Add the Actions & Recommendations component to the left column, and specify the deployment name in component properties.
c.Place the Chat Body component in the right column.
Example: This Chat Transcript page displays the Actions & Recommendations and Chat Body components.
## 32

## SEE ALSO:
Salesforce Help: Set Up Chat in Lightning Experience
## 33
Integrate Chat with Lightning Flow for Service

## INTEGRATE OPEN CTI WITH LIGHTNING FLOW FOR SERVICE
Open CTI provides a set of APIs that enables third-party telephony services to integrate with Salesforce. Lightning Flow for Service takes
advantage of three Open CTI methods: getSoftphoneLayout(), screenPop(), and searchAndScreenPop().
1.Update your Open CTI implementation to allow incoming calls to screen-pop to flows.
You can also pass call data, such as the phone number or customer name, directly to a flow when it’s screen-popped.
Use Open CTI API version 42.0 and later with the following methods.
## •
getSoftphoneLayout()
## •
screenPop()
## •
searchAndScreenPop()
Note:  Before updating your implementation, make sure that you understand how Open CTI arguments are passed.
Flows can accept input variables, which are also called arguments. The Actions & Recommendations component on a record
page automatically attempts to pass the parent record ID to the flow. To use this information, the flow defines an input variable
called recordId of type Text. The Open CTI API allows for more complex variable passing. Single variables and collection
variables, like lists and arrays, can be passed through the flowArgs parameter available in the screenPop and
searchAndScreenPop methods.
2.Create flows.
For example, create an Unknown Caller screen flow for when there’s an incoming call and there’s no match in Salesforce for the
caller. In Flow Builder, create a screen flow to verify the caller.
## •
Add a screen with input components First Name, Last Name, Phone Number, and Address.
## •
Add the Create Records element to create a contact and set the contact fields using the screen input components.
## •
Connect the start element to the Unknown Caller screen.
In addition to the Unknown Caller flow, create other flows and actions that you want your agents to use when talking to customers
on the phone.
3.Configure screen-pop settings in the softphone layout.
From Setup, go to the Softphone Layouts page.
For No matching records, select Pop to flow. Then select the flow you created for Unknown Callers.
Note:  When you use the Pop to flow option, flows open as primary tabs in the console.
For Single-matching records, select Pop detail page. This setting allows the contact record page, for example, to be popped.
## 34

4.Create an Actions & Recommendations deployment and configure default actions for the phone channel.
5.Customize the record page.
Add the Actions & Recommendations component to a record page, such as the contact page. Select the deployment in the component
properties. When calls match a Salesforce record and users get popped to that page, they can see which actions to complete for
the call.
## SEE ALSO:
Open CTI Developer Guide
Salesforce Help: Designing a Custom Softphone Layout
Salesforce Help: Assigning a Softphone Layout to a User Profile
Lightning Components Developer Guide: Set Flow Variable Values from a Lightning Component
## 35
Integrate Open CTI with Lightning Flow for Service

## OTHER RESOURCES FOR LIGHTNING FLOW FOR SERVICE
Learn about other resources, like developer guides and Trailhead, to help you get started with Lightning Flow for Service.
## Process Automation
Trailhead: Lightning Flow for Service
Trailhead: Automate Your Business Processes with Salesforce Flow
## Trailhead: Einstein Next Best Action
## Salesforce Help: Automate Your Business Processes
## Salesforce Help: Einstein Next Best Action
## Cheatsheet: Process Automation Cheatsheet
## App
Salesforce Help: Salesforce Console in Lightning Experience
Salesforce Help: Create and Configure Lightning Experience Record Pages
## Integrations
## Salesforce Help: Salesforce Call Center
## Salesforce Help: Chat
## 36