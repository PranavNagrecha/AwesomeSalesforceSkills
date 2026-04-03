

Place Order REST API Developer
## Guide
## Version 66.0, Spring ’26
Last updated: January 23, 2026

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
Place Order REST API Developer Guide Developer Guide. . . . . . . . . . . . . . . . . . . . . . . . 1
Requirements and Limitations. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Authorization Through External Client Apps or Connected Apps and OAuth 2.0. . . . . . . . . . . . 2
Understanding Place Order REST API Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Add a Contract and Orders to an Existing Account. . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Add an Order to an Existing Account. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
Add  Orders  to  an  Existing  Contract. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
Add Order Products to an Existing Order. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
Get  Details  About  a  Contract. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
Get Details About an Order. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
Filter  Details  About  a  Contract. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
Filter Details About an Order. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
Salesforce Place Order REST API Resource Reference. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
Create Contract-based Orders. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
Contract-based Orders. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
Create  Order. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
Order. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23



## PLACE ORDER REST API DEVELOPER GUIDE DEVELOPER
## GUIDE
Access your organization's order and contract data programmatically with the Salesforce Place Order REST API.
The Salesforce Place Order REST API is a composite API that gives programmatic access to contract, order, and order product data, as
well as child custom object data of contracts and orders in Salesforce. With this composite API, you can create contract, order, order
product, and custom object records in a single call. Any organization that has orders and API enabled can use the Place Order REST API.
Use the Place Order REST API, a REST-based composite application programming interface, to:
## •
Add orders to a new or existing contract, and add order products to those orders.
## •
Add order products to a new or existing order.
## •
Add custom objects to a new or existing contract or order.
## •
Retrieve order records under a given contract, plus those orders’ custom objects and order products.
## •
Retrieve order product records under a given order, plus custom object records under the order and its order products.
## •
Retrieve a filtered list of orders under a given contract or order products under a given order.
## IN THIS SECTION:
Requirements and Limitations
Authorization Through External Client Apps or Connected Apps and OAuth 2.0
For a client application to access REST API resources, it must be authorized as a safe visitor. To implement this authorization, use
either an external client app or a connected app and an OAuth 2.0 authorization flow.
Understanding Place Order REST API Resources
Integrate your order creation system with Salesforce by using the Place Order REST API.
Salesforce Place Order REST API Resource Reference
Each Salesforce Place Order REST API resource is a URI used with an HTTP method (such as GET).
Requirements and Limitations
To access the Salesforce Place Order REST API, you must establish a secure OAuth session ID.
Consider these limitations and general limits when using the Salesforce Place Order REST API.
Limits and Limitations
## •
2000 records per request or the API maximum limit for your organization—whichever is lower.
## •
Responses and requests are in JSON.
When using Salesforce Place Order REST API resources that require a request or response body, use Content-Type: application/json.
## •
Each call can only affect one top-level entity.
For orders under a contract, you need one call for each new or existing contract you’re adding orders, order products, or custom
objects to. For orders not under a contract, you need one call for each new or existing order you’re adding order products or
custom objects to.
## •
In each resource, you can create custom objects at a depth of one level below the top-level entity.
## 1

/services/data/latestAPI version/commerce/sale supports custom object records on contracts and
orders.
## –
## –
/services/data/latestAPI version/commerce/sale/order supports custom object records on
orders and order products.
## •
Custom objects are not supported as children of other custom objects.
## •
To filter GET results, query parameters must be a fully qualified field name. The parent entity must be lower-cased (such as
order), and the field must match the defined relationship name (such as orders.StatusCode).
For example, to get a list of all orders with a draft status under a given contract, you must use
contract.orders.StatusCode='Draft'.
## •
When you create a new order, the StatusCode must be Draft and the Status must be any value that corresponds to a
StatusCode of Draft.
## •
You can’t update existing records.
Authorization Through External Client Apps or Connected Apps and
OAuth 2.0
For a client application to access REST API resources, it must be authorized as a safe visitor. To implement this authorization, use either
an external client app or a connected app and an OAuth 2.0 authorization flow.
Important:  Creating connected apps is restricted as of Spring ‘26. You can continue to use existing connected apps during and
after Spring ‘26. However, we recommend using external client apps instead. If you must continue creating connected apps,
contact Salesforce Support.
See New connected apps can no longer be created in Spring ‘26 for more details.
Configure an External Client App or a Connected App
Both external client apps and connected apps request access to REST API resources on behalf of the client application. For an external
client app or connected app to request access, it must be integrated with your org’s REST API using the OAuth 2.0 protocol. OAuth 2.0
is an open protocol that authorizes secure data sharing between applications through the exchange of tokens.
For instructions to configure an external client app, see Create an External Client App or Enable OAuth Settings for API Integration in
Salesforce Help. For more information about connected apps, see Connected Apps in Salesforce Help.
Apply an OAuth Authorization Flow
OAuth authorization flows grant a client app restricted access to REST API resources on a resource server. Each OAuth flow offers a
different process for approving access to a client application, but in general the flows consist of three main steps.
1.To initiate an authorization flow, a connected app on behalf of a client app requests access to a REST API resource.
2.In response, an authorizing server grants access tokens to the external client app or connected app.
3.A resource server validates these access tokens and approves access to the protected REST API resource.
After reviewing and selecting an OAuth authorization flow, apply it to your external client app or connected app. For details about each
supported flow, see OAuth Authorization Flows in Salesforce Help.
## 2
Authorization Through External Client Apps or Connected
Apps and OAuth 2.0
Place Order REST API Developer Guide Developer Guide

## More Resources
Salesforce offers the following resources to help you navigate connected apps and OAuth:
## •
## Salesforce Help: External Client Apps
## •
Salesforce Help: Authorize Apps with OAuth
## •
Salesforce Help: OpenID Connect Token Introspection
## •
## Trailhead: Build Integrations Using External Client Apps
Understanding Place Order REST API Resources
Integrate your order creation system with Salesforce by using the Place Order REST API.
Use this API to:
## IN THIS SECTION:
Add a Contract and Orders to an Existing Account
Add an Order to an Existing Account
Add Orders to an Existing Contract
Add Order Products to an Existing Order
Get Details About a Contract
Get Details About an Order
Filter Details About a Contract
Filter Details About an Order
Add a Contract and Orders to an Existing Account
Here’s an example of a POST request using the Create Contract-based Orders resource to create a contract—with child orders, order
products, and custom objects—to an existing account.
Example usage
## /services/data/v30.0/commerce/sale
Example request body
## {
## "contract":[
## {
## "attributes":{
"type":"Contract"
## },
"AccountId":"001D000000JRDAv",
"StartDate":"2013-08-01",
"Status":"Draft",
"ContractTerm":"1",
"Test_Contract1__r":{
## "records":[
## 3
Understanding Place Order REST API ResourcesPlace Order REST API Developer Guide Developer Guide

## {
## "attributes":{
"type":"Test_Contract1__c"
## },
"Name":"ContractCustomObject"
## }
## ]
## },
"Orders":{
## "records":[
## {
## "attributes":{
"type":"Order"
## },
"EffectiveDate":"2013-08-11",
"Status":"Draft",
"billingCity":"SFO-Inside-OrderEntity-1",
"Pricebook2Id":"01sD0000000G2NjIAK",
"OrderItems":{
## "records":[
## {
## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001c5toIAA",
## "quantity":"1",
"UnitPrice":"10"
## }
## ]
## }
## }
## ]
## }
## }
## ]
## }
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Contract",
"url": "/services/data/v30.0/sobjects/Contract/800D0000000PIcMIAW"
## },
"Id": "800D0000000PIcMIAW",
"Orders": {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000G0ylIAC"
## 4
Add a Contract and Orders to an Existing AccountPlace Order REST API Developer Guide Developer Guide

## },
"Id": "801D0000000G0ylIAC",
"OrderItems": {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CKoyIAG"
## },
"Id": "802D0000000CKoyIAG"
## } ]
## }
## } ]
## },
"Test_Contract1__r": {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Test_Contract1__c",
"url": "/services/data/v30.0/sobjects/Test_Contract1__c/a02D0000006YYKZIA4"
## },
"Id": "a02D0000006YYKZIA4"
## } ]
## }
## } ]
## }
Add an Order to an Existing Account
Here’s an example of a POST request using the Create Order resource to create an order with order products for an existing account.
Example usage
## /services/data/v30.0/commerce/sale/order
Example request body
## {
## "order":[
## {
## "attributes":{
"type":"Order"
## },
"EffectiveDate":"2013-07-11",
"Status":"Draft",
"billingCity":"SFO-Inside-OrderEntity-1",
"accountId":"001D000000JRDAv",
"Pricebook2Id":"01sD0000000G2NjIAK",
"OrderItems":{
## "records":[
## {
## "attributes":{
"type":"OrderItem"
## 5
Add an Order to an Existing AccountPlace Order REST API Developer Guide Developer Guide

## },
"PricebookEntryId":"01uD0000001c5toIAA",
## "quantity":"1",
"UnitPrice":"15.99"
## }
## ]
## }
## }
## ]
## }
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000G0ySIAS"
## },
"Id": "801D0000000G0ySIAS",
"OrderItems": {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CKp8IAG"
## },
"Id": "802D0000000CKp8IAG"
## } ]
## }
## } ]
## }
Add Orders to an Existing Contract
Here’s an example of a PATCH request using the Contract-based Orders resource to add new orders and order products to an existing
contract.
Example usage
/services/data/v30.0/commerce/sale/800D0000000PFL8IAO
Example request body
## {
## "contract":[
## {
## "attributes":{
"type":"Contract"
## },
"Id": "800D0000000PFL8IAO",
"Orders":{
## 6
Add Orders to an Existing ContractPlace Order REST API Developer Guide Developer Guide

## "records":[
## {
## "attributes":{
"type":"Order"
## },
"EffectiveDate":"2013-08-11",
"Status":"Draft",
"billingCity":"SFO-Inside-OrderEntity-1",
"contractId":"800D0000000PFL8IAO",
"pricebook2Id":"01sD0000000G2JbIAK",
"OrderItems":{
## "records":[
## {
## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001c5tjIAA",
## "quantity":"12",
"UnitPrice":"10"
## },
## {
## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001cAkMIAU",
## "quantity":"2",
"UnitPrice":"20"
## }
## ]
## }
## },
## {
## "attributes":{
"type":"Order"
## },
"EffectiveDate":"2013-10-11",
"Status":"Draft",
"billingCity":"SFO-Inside-OrderEntity-1",
"contractId":"800D0000000PFL8IAO",
"pricebook2Id":"01sD0000000G2JbIAK",
"OrderItems":{
## "records":[
## {
## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001cAkRIAU",
## "quantity":"11",
"UnitPrice":"10"
## },
## {
## "attributes":{
"type":"OrderItem"
## },
## 7
Add Orders to an Existing ContractPlace Order REST API Developer Guide Developer Guide

"PricebookEntryId":"01uD0000001cAkWIAU",
## "quantity":"2",
"UnitPrice":"20"
## },
## {
## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001cAkgIAE",
## "quantity":"14",
"UnitPrice":"10"
## }
## ]
## }
## }
## ]
## }
## }
## ]
## }
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Contract"
## },
"Orders": {
"totalSize": 2,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v29.0/sobjects/Order/801D0000000G0xsIAC"
## },
"Id": "801D0000000G0xsIAC",
"OrderItems": {
"totalSize": 2,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v29.0/sobjects/OrderItem/802D0000000CKoPIAW"
## },
"Id": "802D0000000CKoPIAW"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v29.0/sobjects/OrderItem/802D0000000CKoQIAW"
## },
"Id": "802D0000000CKoQIAW"
## } ]
## 8
Add Orders to an Existing ContractPlace Order REST API Developer Guide Developer Guide

## }
## }, {
## "attributes": {
"type": "Order",
"url": "/services/data/v29.0/sobjects/Order/801D0000000G0xtIAC"
## },
"Id": "801D0000000G0xtIAC",
"OrderItems": {
"totalSize": 3,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v29.0/sobjects/OrderItem/802D0000000CKoRIAW"
## },
"Id": "802D0000000CKoRIAW"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v29.0/sobjects/OrderItem/802D0000000CKoSIAW"
## },
"Id": "802D0000000CKoSIAW"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v29.0/sobjects/OrderItem/802D0000000CKoTIAW"
## },
"Id": "802D0000000CKoTIAW"
## } ]
## }
## } ]
## }
## } ]
## }
Add Order Products to an Existing Order
Here’s an example of a PATCH request using the Order resource to add order products to an existing order.
Example usage
/services/data/v30.0/commerce/sale/order/801D0000000Frh8
Example request body
## {
## "order":[
## {
## "attributes":{
"type":"Order"
## },
"Id":"801D0000000Frh8",
"OrderItems":{
## "records":[
## {
## 9
Add Order Products to an Existing OrderPlace Order REST API Developer Guide Developer Guide

## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001cCd1",
## "quantity":"1",
"UnitPrice":"100",
"orderId":"801D0000000Frh8"
## },
## {
## "attributes":{
"type":"OrderItem"
## },
"PricebookEntryId":"01uD0000001cCd1",
## "quantity":"2",
"UnitPrice":"200",
"orderId":"801D0000000Frh8"
## }
## ]
## }
## }
## ]
## }
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order"
## },
"OrderItems": {
"totalSize": 2,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CJtMIAW"
## },
"Id": "802D0000000CJtMIAW"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CJtNIAW"
## },
"Id": "802D0000000CJtNIAW"
## } ]
## }
## } ]
## }
## 10
Add Order Products to an Existing OrderPlace Order REST API Developer Guide Developer Guide

Get Details About a Contract
Here’s an example of a GET request using the Contract-based Orders resource to query details about a contract and its child orders, order
products, and custom objects.
Example usage
/services/data/v30.0/commerce/sale/800D0000000PFHp
Example request body
## None
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Contract",
"url": "/services/data/v30.0/sobjects/Contract/800D0000000PFHpIAO"
## },
"Id": "800D0000000PFHpIAO",
"Orders": {
"totalSize": 4,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FqzsIAC"
## },
"Id": "801D0000000FqzsIAC",
"OrderItems": {
"totalSize": 3,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CJX0IAO"
## },
"Id": "802D0000000CJX0IAO"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CJYDIA4"
## },
"Id": "802D0000000CJYDIA4"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CKFCIA4"
## },
"Id": "802D0000000CKFCIA4"
## } ]
## },
"Custom_Objects__r": null
## 11
Get Details About a ContractPlace Order REST API Developer Guide Developer Guide

## }, {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FpNEIA0"
## },
"Id": "801D0000000FpNEIA0",
"OrderItems": {
"totalSize": 3,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CIWBIA4"
## },
"Id": "802D0000000CIWBIA4"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CIWCIA4"
## },
"Id": "802D0000000CIWCIA4"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CIWDIA4"
## },
"Id": "802D0000000CIWDIA4"
## } ]
## },
"Custom_Objects__r": null
## }, {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FqztIAC"
## },
"Id": "801D0000000FqztIAC",
"OrderItems": null,
"Custom_Objects__r": null
## }, {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FpkNIAS"
## },
"Id": "801D0000000FpkNIAS",
"OrderItems": null,
"Custom_Objects__r": null
## } ]
## },
"Test_Contract1__r": null
## } ]
## }
## 12
Get Details About a ContractPlace Order REST API Developer Guide Developer Guide

Get Details About an Order
Here’s an example of a GET request using the Order resource to query details about an order and its order products and custom object
records.
Example usage
/services/data/v30.0/commerce/sale/order/801D0000000FzsM
Example request body
## None
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FzsMIAS"
## },
"Id": "801D0000000FzsMIAS",
"OrderItems": {
"totalSize": 2,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CKIHIA4"
## },
"Id": "802D0000000CKIHIA4"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CKIGIA4"
## },
"Id": "802D0000000CKIGIA4"
## } ]
## },
"Custom_Objects__r": null
## } ]
## }
Filter Details About a Contract
Here’s an example of a GET request using the Contract-based Orders resource to query a given contract’s activated orders.
Example usage
/services/data/v30.0/commerce/sale/800D0000000PFL8?contract.orders.StatusCode='Activated'
Example request body
## None
## 13
Get Details About an OrderPlace Order REST API Developer Guide Developer Guide

Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Contract",
"url": "/services/data/v30.0/sobjects/Contract/800D0000000PFHpIAO"
## },
"Id": "800D0000000PFHpIAO",
"Orders": {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FpNEIA0"
## },
"Id": "801D0000000FpNEIA0",
"OrderItems": {
"totalSize": 3,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CIWBIA4"
## },
"Id": "802D0000000CIWBIA4"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CIWCIA4"
## },
"Id": "802D0000000CIWCIA4"
## }, {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CIWDIA4"
## },
"Id": "802D0000000CIWDIA4"
## } ]
## },
"Custom_Objects__r": null
## } ]
## },
"Test_Contract1__r": null
## } ]
## }
Filter Details About an Order
Here’s an example of a GET request using the Order resource to query details for order products with a certain start date for a given order.
## 14
Filter Details About an OrderPlace Order REST API Developer Guide Developer Guide

Example usage
/services/data/v30.0/commerce/sale/order/801D0000000FzsM?order.orderItems.effectivedate=2013-08-05
Example request body
## None
Example JSON response body
## {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "Order",
"url": "/services/data/v30.0/sobjects/Order/801D0000000FzsMIAS"
## },
"Id": "801D0000000FzsMIAS",
"OrderItems": {
"totalSize": 1,
"done": true,
## "records": [ {
## "attributes": {
"type": "OrderItem",
"url": "/services/data/v30.0/sobjects/OrderItem/802D0000000CKIHIA4"
## },
"Id": "802D0000000CKIHIA4"
## }]
## },
"Custom_Objects__r": null
## } ]
## }
Salesforce Place Order REST API Resource Reference
Each Salesforce Place Order REST API resource is a URI used with an HTTP method (such as GET).
Resources for the Salesforce Place Order REST API are:
DescriptionSupported
HTTP Method
## Resource
Add new orders, order products, and custom objects to
a new contract.
POST/services/data/latestAPI
version/commerce/sale
Add new orders, order products, and custom objects to
an existing contract. Retrieve a contract’s child orders,
order products, and custom objects.
PATCH, GET/services/data/latestAPI
version/commerce/sale/contractID
Add new order products and custom objects to a new
order.
POST/services/data/latestAPI
version/commerce/sale/order
## 15
Salesforce Place Order REST API Resource ReferencePlace Order REST API Developer Guide Developer Guide

DescriptionSupported
HTTP Method
## Resource
Add new order products and custom objects to an
existing order. Retrieve an order’s child order products
and custom objects.
PATCH, GET/services/data/latestAPI
version/commerce/sale/order/orderID
## Create Contract-based Orders
With this resource, you can create a new contract with orders and order products, as well as custom object records on the contract or
order level.
## Syntax
## URI
/services/data/latestAPI version/commerce/sale
Available since release
## 30.0
## Formats
## JSON
HTTP methods
## POST
Request body
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the new contract.Attributesattributes
30.0Unique record identifier for the parent account.StringAccountId
30.0Status of the contract.StringStatus
30.0Child orders of the new contract.Orders[]Orders
30.0Child custom object records of the new contract.Custom
## Objects[]
CustomObject__r
## Attributes
## Since
## Version
DescriptionTypeProperty
30.0Format of the resource.Stringtype
## 16
Create Contract-based OrdersPlace Order REST API Developer Guide Developer Guide

## Orders
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the new order record.Attributesattributes
30.0Status of the order.StringStatus
30.0Unique record identifier for the associated price book.StringPricebook2Id
30.0Child order products of the new order.Order Products[]OrderItems
30.0Child custom object records of the new order.Custom Objects[]CustomObject__r
## Custom Object Records
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the custom object record.Attributesattributes
30.0Unique record identifier.StringId
## Order Products
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the order product record.Attributesattributes
30.0Unique record identifier for the associated price book entry.StringPricebookEntryId
30.0Number of units of the order product.Numberquantity
30.0The unit price for the order product.CurrencyUnitPrice
Request parameters
## None
Response body
DescriptionTypeProperty
Total number of records added.NumbertotalSize
When true, the operation was successful.Booleandone
Attributes and IDs of records.Records[]records
## 17
Create Contract-based OrdersPlace Order REST API Developer Guide Developer Guide

## Records
DescriptionTypeProperty
Type and URL for the new record.Attributesattributes
Unique identifier for the new record.StringId
## Attributes
DescriptionTypeProperty
Format of the resource.Stringtype
Resource URL.Stringurl
## Example
See Add a Contract and Orders to an Existing Account on page 3.
## Usage
You can only create one contract at a time. You can’t POST new orders onto an existing contract. For that, see the Contract-based Orders
resource.
## Contract-based Orders
With this resource, you can add one or more new orders to an existing contract, as well as order products and custom object records
for each order, or you can retrieve data for a specific contract.
If available, GET method retrieves the contract’s child orders and order products, as well as custom objects under the contract and orders.
## Syntax
## URI
/services/data/latestAPI version/commerce/sale/contractId
For retrieving filtered data:
/services/data/latestAPI version/commerce/sale/contractID?contract.orders.field
name=value
Available since release
## 30.0
## Formats
## JSON
HTTP methods
## PATCH, GET
## 18
Contract-based OrdersPlace Order REST API Developer Guide Developer Guide

Request parameters
## •
You can use parameters for all standard and custom fields on contracts, orders, order products, and any custom objects directly
related to these objects.
## •
The parameters must be fully qualified. For example: objectname.relationshipname.fieldname=value.
## –
Object name must be all lower-case.
## –
Relationship name must match what is defined on the object and is case-sensitive.
## –
Field name isn’t case sensitive.
## –
If the value is a string, it must be encased in single quotation marks. If the value is a number, it must not be encased. If the
value is a date, it should be in the YYYY-MM-DD format.
## •
You can use multiple parameter fields, separated by "&", to make more detailed filters.  For example:
/services/data/v30.0/commerce/sale/{contractId}?contract.status='Activated'
&contract.Orders.status='Draft'&contract.Orders.OrderItems.unitprice=300
The following aren’t supported:
## •
Arrays of values. For example: contract.orders.Status='Activated','Draft'.
## •
Operators: >, >=, < and <=
## •
The OR condition
## Since
## Version
DescriptionParameters
30.0The object name of the record being filtered. In this resource, this is always
contract.
contract
30.0The relationship name of the field that the order’s data will be filtered by.
In this resource, this is always orders.
orders
30.0The field whose value to filter by. For example, if you want to only retrieve
orders with a status category, the field name is StatusCode.
field name
30.0The value to filter by. For example, if you want to only retrieve orders
with a status category of Activated, the value is Activated.
value
Request body
## Since
## Version
DescriptionTypeProperty
30.0Type of the contract.Attributesattributes
30.0Unique contract identifier.StringId
30.0Child orders of the contract.Orders[]Orders
## 19
Contract-based OrdersPlace Order REST API Developer Guide Developer Guide

## Attributes
## Since
## Version
DescriptionTypeProperty
30.0Format of the resource.Stringtype
## Order Records
## Since
## Version
DescriptionTypeProperty
30.0Type of the order record.Attributesattributes
30.0Status of the order.StringStatus
30.0Unique record identifier for the parent contract.StringcontractId
30.0Unique record identifier for the associated price book.Stringpricebook2Id
30.0Child order products of the order.Order Products[]OrderItems
30.0Child custom object records of the order.Custom
## Objects[]
CustomObject__r
## Order Products
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the order product.Attributesattributes
30.0Unique record identifier for the associated price book entry.StringPricebookEntryId
30.0Number of units of the order product.Numberquantity
30.0The unit price for the order product.CurrencyUnitPrice
## Custom Objects
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the custom object.Attributesattributes
30.0Unique custom object identifier.StringId
## 20
Contract-based OrdersPlace Order REST API Developer Guide Developer Guide

Response body
DescriptionTypeProperty
Total number of records retrieved.NumbertotalSize
When true, the operation was successful.Booleandone
Attributes and ID of contract record.Records[]records
## Records
DescriptionTypeProperty
Type and URL of the record.Attributesattributes
Unique contract identifier.StringId
## Attributes
DescriptionTypeProperty
Format of the resource.Stringtype
Resource URL.Stringurl
## Examples
## •
Add Orders to an Existing Contract on page 6
## •
Get Details About a Contract on page 11
## •
Filter Details About a Contract on page 13
## Create Order
With this resource, you can create a new order with order products and custom objects.
If you don’t want to add the order to a contract, you can add it directly to an account. You can only create one new order per call. The
request body must have either an account or a contract as its parent record, and it must have a reference to a price book.
## Syntax
## URI
/services/data/latestAPI version/commerce/sale/order
Available since release
## 30.0
## Formats
## JSON
## 21
Create OrderPlace Order REST API Developer Guide Developer Guide

HTTP methods
## POST
Request body
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the new order.Attributesattributes
30.0Child order products of the new order.Order Products[]OrderItems
30.0Child custom object records of the new order.Custom Objects[]CustomObject__r
## Attributes
## Since
## Version
DescriptionTypeProperty
30.0Format of the resource.Stringtype
30.0Resource URL.Stringurl
## Order Products
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the order product.Attributesattributes
30.0Unique record identifier for the associated price book entry.StringPricebookEntryId
30.0Number of units of the order product.Numberquantity
30.0The unit price for the order product.CurrencyUnitPrice
30.0Unique order product identifier.StringId
## Custom Objects
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the custom object.Attributesattributes
30.0Unique custom object identifier.StringId
Request parameters
## None
## 22
Create OrderPlace Order REST API Developer Guide Developer Guide

Response body
DescriptionTypeProperty
Total number of records retrieved.NumbertotalSize
When true, the operation was successful.Booleandone
Attributes and ID of contract record.Records[]records
## Records
DescriptionTypeProperty
Type and URL of the record.Attributes on page
## 23
attributes
Unique contract identifier.StringId
## Attributes
DescriptionTypeProperty
Format of the resource.Stringtype
Resource URL.Stringurl
## Example
See Add an Order to an Existing Account on page 5.
## Order
Use this resource to add one or more new order products and custom object records to an existing order or to retrieve data for a specific
order.
You can only PATCH one order at a time.
If available, GET method retrieves the orders’ child order products and custom objects under the order or order products.
## Syntax
## URI
/services/data/latestAPI version/commerce/sale/order/orderID
For retrieving filtered data:
/services/data/latestAPI version/commerce/sale/order/orderID?order.orderItems.field
name=value
## 23
OrderPlace Order REST API Developer Guide Developer Guide

Available since release
## 30.0
## Formats
## JSON
HTTP methods
## POST
Request body
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the order.Attributesattributes
30.0Child order products of the new order.Order
## Products
OrderItems
30.0Child custom object records of the new order.Custom
## Object
CustomObject__r
## Attributes
## Since
## Version
DescriptionTypeProperty
30.0Format of the resource.Stringtype
## Order Products
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the order product.Attributesattributes
30.0Unique record identifier for the associated price book entry.StringPricebookEntryId
30.0Number of units of the order product.Numberquantity
30.0The unit price for the order product.CurrencyUnitPrice
30.0Unique record identifier for the parent order.StringorderId
30.0Unique order product identifier.StringId
## Custom Objects
## Since
## Version
DescriptionTypeProperty
30.0Type and URL of the custom object.Attributesattributes
## 24
OrderPlace Order REST API Developer Guide Developer Guide

## Since
## Version
DescriptionTypeProperty
30.0Unique custom object identifier.StringId
Request parameters
## •
You can use parameters for all standard and custom fields on contracts, orders, order products, and any custom objects directly
related to these objects.
## •
The parameters must be fully qualified. For example: objectname.relationshipname.fieldname=value.
## –
Object name must be all lower-case.
## –
Relationship name must match what is defined on the object and is case-sensitive.
## –
Field name isn’t case sensitive.
## –
If the value is a string, it must be encased in single quotation marks. If the value is a number, it must not be encased. If the
value is a date, it should be in the YYYY-MM-DD format.
## •
You can use multiple parameter fields, separated by "&", to make more detailed filters.  For example:
/services/data/v30.0/commerce/sale/{contractId}?contract.status='Activated'
&contract.Orders.status='Draft'&contract.Orders.OrderItems.unitprice=300
The following aren’t supported.
## •
Arrays of values. For example: order.orderItems.effectiveDate=2013–01–01,2013–01–02.
## •
Operators: >, >=, < and <=
## •
The OR condition
DescriptionParameters
The object name of the record being filtered. In this resource,
this is always order.
order
The relationship name of the field that the order’s data will be
filtered by. In this resource, this is always orderItems.
orderItems
The field whose value to filter by. For example, if you want to
only retrieve order products with a certain start date, the field
name is effectivedate.
field name
The value to filter by. For example, if you want to only retrieve
order products that started on January 1, 2013, the value is
## 2013–01–01.
value
Response body
DescriptionTypeProperty
Total number of records listed.NumbertotalSize
Attributes and IDs of the new records.Records[]records
## 25
OrderPlace Order REST API Developer Guide Developer Guide

## Records
DescriptionTypeProperty
Type and URL for the record.Attributesattributes
Unique record identifier.StringId
## Attributes
DescriptionTypeProperty
Format of the resource.Stringtype
Resource URL.URIurl
## Examples
## •
Add Order Products to an Existing Order on page 9
## •
Get Details About an Order on page 13
## •
Filter Details About an Order on page 14
## 26
OrderPlace Order REST API Developer Guide Developer Guide