

## Consumer Goods Cloud Real
## Time Reporting Developer
## Guide
## Version 66.0, Spring ’26
Last updated: November 17, 2025

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
Chapter  1:  Introduction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Chapter 2: Customizing Real Time Reporting (RTR) with APEX. . . . . . . . . . . . . . . . . . . 2
Create a Fund Report with Custom Apex Datasources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
Use Case: Fund Amount. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
TPM_RTRReportingWrapper_AMS  (Base  Class). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class). . . . . . . . . . . . . . . . . . . . . . . . 6
TPM_RTRFunds_AMS  (The  Logic  Class). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
Use  Case:  Fixed  Funds. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
TPM_RTRReportingWrapper_AMS  (Base  Class). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
TPM_RTRSalesforceMonthlyMeasures_AMS  (Base  Class). . . . . . . . . . . . . . . . . . . . . . . 10
TPM_RTRFixedFunds_AMS (The Logic Class). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
Create  Reports  with  Custom  Apex  Filter. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
Classes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
TPM_RTRFixedFunds_AMS. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
TPM_RTRPromoTypeFilter_AMS. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
TPM_RTRReportingParentPromoFilter. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18



CHAPTER 1Introduction
## EDITIONS
Available in: Lightning
Experience in Enterprise and
Unlimited Editions that have
## Consumer Goods Cloud
## Trade Promotion
Management enabled.
This document explains the Salesforce configurations required to
export CSV files from within Real Time Reporting (RTR) using the
Integration API, and provides information on customizing the RTR
using APEX. RTR exports support the export of BOM components.
To learn more about exporting KPIs, see Exporting the KPIs from
## Hyperforce.
## 1

CHAPTER 2Customizing Real Time Reporting (RTR) with
## APEX
You can create a fund report with custom APEX data sources to integrate KPI values that are obtained
from other sources such as a Salesforce attribute. You can also create reports with custom APEX filters,
along with the standard filters.
In this chapter ...
•Create a Fund Report
with Custom Apex
## Datasources
Although requirements vary across clients and markets, these general requirements apply for different
processes:
•Use Case: Fund
## Amount
## •
Strategic Planning: Provides flexible views on business metrics (profit, profit margin, ROI, costs,
revenue, and so on) on either a regional or national level (across many or all key accounts) to drive
•Use Case: Fixed
## Funds
future recommendations for target volumes, target revenues, marketing initiatives, brand initiatives,
and pricing.
•Create Reports with
## Custom Apex Filter
## •
Fund Management: Provides you with a hollistic view of the budgeting not only within but also
across funds prior to, during, and after a financial year, so that you can control the financials on both
an overall and granular level.
•Classes
## •
Account Planning: Provides you with flexible views on a single account to monitor business
development within the full P&L (Profit and Loss) for the relevant brands and categories and on a
detailed plan product level.
## •
Promotion Planning: Provides overviews on key promotion metrics (profit, profit margin, ROI, costs,
revenue, etc.) for a single account and time frame on both summary and detailed levels to conduct
pre-event and post-event analysis.
## •
Promotion Execution: Tracks claims against promotions or tactics in promotion-based reports and
fund reporting to be always aware of missing claim information and outstanding deductions.
## •
Post-Event Analysis: Evaluates the success of single promotional events, brand and marketing
initiatives across accounts, and the overall success rate on account-related contracts and their impact
on single accounts.
Real Time Reporting supports these requirements by providing a technical foundation to retrieve the
important business metrics and allowing flexible configurations to design reports according to client
requirements.
Example: Consider this scenario:
During an iterative planning processes, John—the Key Account Manager (KAM), identifies gaps
in promotion planning and makes the relevant changes. Real Time Reporting (RTR) helps him to
view the impact on his account directly after releasing the changes, allowing him to create a more
fruitful Account Plan for his retail partner. The immediate effect of changes that reflect in the report
helps him to act instantly and adapt promotion planning on the fly. With RTR, John can view the
impact on a summary level by either brand or category and on a detailed plan product level.
These are the five key functional benefits of RTR:
## •
Supports the full TPM closed loop with real-time insights to drive the decision-making process.
## •
Provides a consistent user experience for CG Cloud TPM users.
## •
Builds the trust of users because the numbers that are shown in RTR and other application areas (for
example, P&L sheets) are consistent.
## 2

## •
Supports the export of data in MS-Excel format for all reports that allow users to work further on
exported data.
## •
Allows you to define user-specific views so that users can switch between reports instantly.
## 3
Customizing Real Time Reporting (RTR) with APEX

Create a Fund Report with Custom Apex Datasources
The data that's required for the reports is available on a Hyperforce server and is interfaced via regular data sources such as
AccountMonthlyMeasures or AccountWeeklyMeasures.
If you want to integrate KPI values that's obtained from other sources such as a Salesforce attribute, use Real Time Report (RTR) to add
a custom datasource. A custom datasource is an Apex endpoint that delivers KPI values to the report.
RTR offers you these custom data sources:
## •
RTRSalesforceMonthlyMeasures: Used to integrate monthly values for KPIs.
## •
RTRSalesforceWeeklyMeasures: Used to integrate weekly values for KPIs.
Depending on your report, you can use either weekly or monthly custom data sources to fetch KPIs for that time level. Ensure that you
also implement an Apex endpoint that corresponds to these data sources that can deliver these KPIs in the corresponding time granularity
(week or month).
Snippet to Define Custom Datasources
## "datasources":[
## {
"name":"AccountMonthlyMeasures"
## },
## {
"name":"RTRSalesforceMonthlyMeasures"
## }
## ],
In addition to defining the datasource in the report configuration, ensure that you also create a base Apex class (based on your use case)
and a logic Apex class.
## Use Case: Fund Amount
The Fund object stores the fund amount in Salesforce. To show a fund amount for a particular category or brand, fetch it from the
Salesforce database by using custom data sources.
## Prerequisites
1.Create a KPI definition for the fund amount. For this KPI definition, ensure that the object scope is Account and it has the writeback
feature enabled.
Note:  This KPI definition only provides a name for the external KPI. The Apex class defines how to input values in this KPI.
2.Enter the name of the datasource table as AccountMeasure.
3.Add the KPI to the Reporting KPI set that's used in the report.
## 4
Create a Fund Report with Custom Apex DatasourcesCustomizing Real Time Reporting (RTR) with APEX

## Report Configuration
Apart from defining RTRSalesforceMonthlyMeasures as an additional datasource in the report configuration, ensure that you add the
newly created KPI to the list of measures.
## {
"label":"FundAmount",
"name":"myFndAmount"
## },
## Apex Classes
The custom data sources are related to two base Apex classes. You can use both classes only for code-routing and not to perform any
actual logic, queries, or calculations; this is because all reports share these classes.
Note:  In RTR, integration users run both the Apex classes, not the user who opens the report. As a result, integration users must
have access permissions to the used Apex classes.
TPM_RTRReportingWrapper_AMS (Base Class)
TPM_RTRReportingWrapper_AMS is a base Apex class that receives the payload that's constructed by filter selection in the
report. The payload contains the KPIs that are defined in the report, the customer, dates, and other important attributes. It then
deserializes the payload into an object that can be used in all other related classes.
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)
TPM_RTRSalesforceMonthlyMeasures_AMS is one of the base classes that's used for code-routing and is required to
retrieve the information by a Salesforce REST endpoint (/services/apexrest/RTRSalesforceMonthlyMeasures).
TPM_RTRFunds_AMS (The Logic Class)
Use RTRSalesforceMonthlyMeasures as the datasource to execute the base classes by every report.
TPM_RTRReportingWrapper_AMS (Base Class)
TPM_RTRReportingWrapper_AMS is a base Apex class that receives the payload that's constructed by filter selection in the
report. The payload contains the KPIs that are defined in the report, the customer, dates, and other important attributes. It then deserializes
the payload into an object that can be used in all other related classes.
Note:  Ensure that this wrapper class name is the same as the one in the Fund Amount use case. However, to incorporate this
class with the fund amount scenario, modify the class.
SampleCode
globalwithsharingclassTPM_RTRReportingWrapper_AMS{
globalclassPeriodmonth{
globalIntegeryear;
globalIntegerstart;
globalIntegertotal;
## }
globalclassInputPayload{
globalList<String>accountsfids;
globalList<String>productsfids;
globalPeriodmonthperiodmonth;
globalStringtimelevel;
## 5
TPM_RTRReportingWrapper_AMS (Base Class)Customizing Real Time Reporting (RTR) with APEX

globalList<String>readproductsfids;
globalList<String>kpis;
globalStringresponsetype;
globalBooleanerror;
## }
globalclassOutputRecord{
globalStringpdim;
globalStringkdim;
globalStringtdim;
globalDoublev;
globalOutputRecord(Stringpdim,Stringkdim,Stringtdim,Doublev) {
this.pdim= pdim;
this.kdim= kdim;
this.tdim= tdim;
this.v= v;
## }
## }
## }
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)
TPM_RTRSalesforceMonthlyMeasures_AMS is one of the base classes that's used for code-routing and is required to retrieve
the information by a Salesforce REST endpoint (/services/apexrest/RTRSalesforceMonthlyMeasures).
The system sends the selected filter criteria and the list of KPIs as input payload to the REST endpoint. The APEX REST method then
returns the fund amounts as output records to show in the report.
The fund values are returned by a function that's executed when a POST request is sent.
These steps are run within the Apex function:
1.The payload with filter values is converted into a format that can be used in the Apex code.
2.The time range (start and end date) is built by the selected month information.
3.The function that contains the logic for this use case is invoked.
SampleCode
@RestResource(urlMapping='/RTRSalesforceMonthlyMeasures/*')
globalwithsharingclassTPM_RTRSalesforceMonthlyMeasures
## {
@httpPost
globalstaticList<TPM_RTRReportingWrapper_AMS.OutputRecord>doPost(){
StringrequestBody= RestContext.request.requestbody.tostring();
TPM_RTRReportingWrapper_AMS.InputPayloadpayload= (TPM_RTRReportingWrapper_AMS.InputPayload)
JSON.deserialize(requestBody, TPM_RTRReportingWrapper_AMS.InputPayload.class);
DateinputDateBegin= Date.newInstance(payload.periodmonth.year,payload.periodmonth.start,1);
DateinputDateEnd= inputDateBegin.addMonths(payload.periodmonth.total);
returnTPM_RTRFunds_AMS.doPost(inputDateBegin, inputDateEnd,payload);
## }
## }
TPM_RTRFunds_AMS (The Logic Class)
Use RTRSalesforceMonthlyMeasures as the datasource to execute the base classes by every report.
## 6
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)Customizing Real Time Reporting (RTR) with APEX

This function performs these steps:
1.Defines a list of output record items.
2.Retrieves the fund amounts from Salesforce data by using SOQL, depending on the use case. In this example, only funds at the
category level are shown. You can use the category filter as the selection criterion. The funds are also limited to the account and
time frame that's selected in the filter.
3.For every result record, the function creates an output record and adds it to the list of results.
globalwithsharingclassTPM_RTRFunds_AMS{
globalstaticList<TPM_RTRReportingWrapper_AMS.OutputRecord>
doPost(DateinputDateBegin, DateinputDateEnd,
TPM_RTRReportingWrapper_AMS.InputPayloadpayload){
List<TPM_RTRReportingWrapper_AMS.OutputRecord>output=
new List<TPM_RTRReportingWrapper_AMS.OutputRecord>();
## Stringpdim;
## Stringkdim;
## Stringtdim;
## Doublev ;
AggregateResult[]groupedResults= [SELECTcgcloud__Anchor_Product__c,
sum (cgcloud__Deposits_Approved__c) sumValue
fromcgcloud__Fund__c
WHEREcgcloud__Anchor_Product__cIN :payload.productsfids
AND cgcloud__Anchor_Account__cIN :payload.accountsfids
AND ((cgcloud__Valid_From__c<= :inputDateEnd
AND cgcloud__Valid_From__c>= :inputDateBegin)
OR (cgcloud__Valid_Thru__c<= :inputDateEnd
AND cgcloud__Valid_Thru__c>= :inputDateBegin))
groupby cgcloud__Anchor_Product__c
## ];
for(Integeri=0;i < groupedResults.size();i++){
v =(Double)groupedResults[i].get('sumValue');
pdim=(String)groupedResults[i].get('cgcloud__Anchor_Product__c');
kdim= 'myFndAmount';
tdim= 'Total';
output.add(newTPM_RTRReportingWrapper_AMS.OutputRecord(pdim,kdim,tdim,v));
## }
returnoutput;
## }
## }
## Use Case: Fixed Funds
In this use case, the custom datasource is used to include a fixed fund KPI in Real Time Report (RTR). As a result, the fixed funds are
aggregated on both category and brand levels. One visualization option is this report, in which a brand value is only available for one
brand. However, this value is not summed up to the category level. For the calculation of category levels, the data that's stored on
Salesforce and Processing Services is used.
## Prerequisites
1.Create a KPI definition for the fund amount. For this KPI definition, ensure that the object scope is Account and it has the writeback
feature enabled.
## 7
Use Case: Fixed FundsCustomizing Real Time Reporting (RTR) with APEX

Note:  This KPI definition only provides a name for the external KPI. The Apex class defines how to enter values in this KPI.
2.Enter the name of the datasource table as AccountMeasure.
3.Add the KPI to the Reporting KPI set that's used in the report.
1.Create new KPI definitions for each use case, such as Fixed RDF Brand. Ensure that the object scope of these KPI definitions is Account.
2.Enter the name of the datasource table as AccountMeasure.
3.Define these KPI definitions in the report configuration
4.Create a custom metadata type, TPM_RTRRouting__mdt, which is linked to the KPI definition, sales organization, fund template,
and KPI levels.
DescriptionTypeField API Name
Determines the KPI to which the fixed funds are to be attributed.
For example, All Transaction Row Records, in which the target fund
has the RDF Brand Fund that belongs to the Fixed RDF KPI.
TextFund_Template__c
Name of the Fixed Funds KPI (such as FXDR and FTDR) that
determines the data which should be returned from the logic in the
Apex class.
TextKPI_Definition__c
Fixed funds can be stored on different levels (currently, category
and brand). This is needed to determine the method that should
be run. (category and brand use different logic.)
TextKPI_Level__c
Sales organization to which the record belongs.TextSales_Org__c
5.On the cgcloud__Fund_Transaction_Row__c object, add a new field.
FormulaDescriptionTypeField API Name
## IF(ISPICKVAL(
cgcloud__Transaction_Type__c
Fixed Funds for Brands are
calculated based on the value
Formula (Double)TPM_RTRAmount__c
, 'Withdraw'),of the Amount field on the
cgcloud__Amount__c * (-1),
cgcloud__Amount__c )
transaction record. Depending
on the transaction type
(withdraw or deposit), the sum
of the aggregated amounts
either increases (deposit) or
decreases (withdraw).
The formula field turns the
amounts of records with
transaction type = deposit to
negative values. Instead of
aggregating the amount field,
you can aggregate the
TPM_RTR_Amount__c field.
## 8
Use Case: Fixed FundsCustomizing Real Time Reporting (RTR) with APEX

6.On the cgcloud__Fund_Transaction_Header__c object, add a new field.
DescriptionTypeField API Name
Used to link products to the Multi-Fund
Transaction object.
Lookup(Product)TPM_Product__c
7.On the cgcloud__Fund_Template__c object, add a new field.
DescriptionTypeField API Name
Used to filter fund template records. The
picklist values of this field are fund
template record names.
PicklistTPM_RTRRoutingFundType__c
Note:  Ensure that you create new fund templates for each case, such as RDF Brand Fund. Maintain the newly created
TPM_RTRRoutingFundType__c field on the fund template.
## Apex Classes
Custom data sources are related to two base Apex classes. Because all reports share these classes, you can use both classes only for
code-routing, not to perform any actual logic, queries, or calculations.
Note:  In RTR, the integration user runs both Apex classes, not the user who opens the report. As a result, the integration user
must have access permissions for the used Apex classes.
TPM_RTRReportingWrapper_AMS (Base Class)
TPM_RTRReportingWrapper_AMS is a base class that contains the structures to load the input. This class contains the list
of KPIs and filter criteria that you chose in the report—selected time frame or the list of customers and products. Depending on
various use cases, the payload method can contain different attributes.
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)
TPM_RTRSalesforceMonthlyMeasures_AMS is the second base class that's used for code-routing and is required to
retrieve the information by a Salesforce REST endpoint (/services/apexrest/RTRSalesforceMonthlyMeasures).
TPM_RTRFixedFunds_AMS (The Logic Class)
The actual logic is defined in this class. The benefit of routing to a separate third class is that the code runs only when needed.
TPM_RTRReportingWrapper_AMS (Base Class)
TPM_RTRReportingWrapper_AMS is a base class that contains the structures to load the input. This class contains the list of KPIs
and filter criteria that you chose in the report—selected time frame or the list of customers and products. Depending on various use
cases, the payload method can contain different attributes.
The OutputRecord method returns product(pdim), KPI (kdim), time(tdim), and values(v). The values are
defined in the actual logic class, which is TPM_RTRFunds_AMS in this use case. For example, you can use tdim to display values on
a more granular view—weeks, months, or quarters. If a report meta has monthly values, the external datasource can also provide monthly
values.
## 9
TPM_RTRReportingWrapper_AMS (Base Class)Customizing Real Time Reporting (RTR) with APEX

Note:  Ensure that kdim contains the name of the fund KPI.
SampleCode
globalwithsharingclassTPM_RTRReportingWrapper_AMS
## {
globalclassPeriodMonth{
globalIntegeryear;
globalIntegerstart;
globalIntegertotal;
## }
globalclassInputPayload{
globalList<String>accountsfids;
globalList<String>productsfids;
globalPeriodMonthperiodmonth;
globalList<String>kpis;
globalStringresponsetype;
globalStringcallingsfuser;
## }
globalclassOutputRecord{
globalStringpdim;
globalStringkdim;
globalStringtdim;
globalDoublev;
globalOutputRecord(Stringpdim,Stringkdim, Stringtdim, Doublev){
this.pdim= pdim;
this.kdim= kdim;
this.tdim= tdim;
this.v= v;
## }
## }
## }
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)
TPM_RTRSalesforceMonthlyMeasures_AMS is the second base class that's used for code-routing and is required to retrieve
the information by a Salesforce REST endpoint (/services/apexrest/RTRSalesforceMonthlyMeasures).
@RestResource(urlMapping='/RTRSalesforceMonthlyMeasures')
globalwithsharingclassTPM_RTRSalesforceMonthlyMeasures_AMS{
@HttpGet
globalstaticStringdoGet(){
return'Helloworld!';
## }
@HttpPost
globalstaticList<TPM_RTRReportingWrapper_AMS.OutputRecord>doPost(){
RestContext.response.statuscode= 200;
These are the code details:
## 10
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)Customizing Real Time Reporting (RTR) with APEX

1.The payload is received, and is then turned into an object of our wrapper class. The payload contains the KPIs that are defined in the
report configuration.
StringrequestBody= RestContext.request.requestBody.toString();
TPM_RTRReportingWrapper_AMS.InputPayloadpayload=
(TPM_RTRReportingWrapper_AMS.InputPayload)JSON.deserialize(requestBody,
TPM_RTRReportingWrapper_AMS.InputPayload.class);
## System.debug(payload);
if(payload.error== true){
RestContext.response.statuscode= 500;
returnnull;
## }
2.The integration user runs the base classes, not the user who opens the report. As a result, ensure that you query an account on the
payload that the user selected to retrieve the actual user's sales org.
//GetSalesOrg of the userwho initiatedthe report
Accountacc = [SELECTId, cgcloud__Sales_Org__cFROMAccountWHEREId IN
:payload.accountsfidsLIMIT1];
StringuserSFOrg= acc.cgcloud__Sales_Org__c;
3.Helper maps and lists are created.
//HelperMaps/List
List<TPM_RTRReportingWrapper_AMS.OutputRecord>output= new
List<TPM_RTRReportingWrapper_AMS.OutputRecord>();
Map<String,TPM_RTRRouting__mdt>categoryKPIs= New Map<String,TPM_RTRRouting__mdt>();
Map<String,TPM_RTRRouting__mdt>brandKPIs= New Map<String,TPM_RTRRouting__mdt>();
4.The dates from the payload are converted to a workable format.
//Loadingand transformingthe datesselectedin the filter
DateinputDateBegin= Date.newInstance(payload.periodmonth.year,
payload.periodmonth.start+1,1);
DateinputDateEnd= inputDateBegin.addMonths(payload.periodmonth.total).addDays(-1);
5.The Apex class contains use case-specific code. Here, you can query all custom metadata records that were defined earlier and that
belong to the sales org of the user. Then you can check whether the payload contains any KPIs in the custom metadata records. If
it does, verify the level on which those KPIs are available and then add them to a dedicated map (category KPIs or brand KPIs map).
//Checkagainstcustommetadataif payloadcontainsrelevantKPIsand sortthem
For(TPM_RTRRouting__mdtkpi : [SELECTId, KPI_Definition__c,KPI_Level__c,
Fund_Template__c,Sales_Org__cFROMTPM_RTRRouting__mdtWHERESales_Org__c= :userSFOrg]){
If(payload.kpis.contains(kpi.KPI_Definition__c)){
If(kpi.KPI_Level__c== 'Category'){
categoryKPIs.put(kpi.KPI_Definition__c,kpi);
## }
ElseIf(kpi.KPI_Level__c== 'Brand'){
brandKPIs.put(kpi.KPI_Definition__c,kpi);
## }
## }
## }
## 11
TPM_RTRSalesforceMonthlyMeasures_AMS (Base Class)Customizing Real Time Reporting (RTR) with APEX

6.You can check whether the two maps (brandKPIs and categoryKPIs) contain any values — if not, nothing happens. If they do, the
actual class where all the logic happens is called and parameters such as the payload are passed.
//Runlogic
try{
If(!categoryKPIs.isEmpty()){
TPM_RTRFixedFunds_AMS.getCategory(inputDateBegin,inputDateEnd,payload,output,
categoryKPIs);
## }
If(!brandKPIs.isEmpty()){
TPM_RTRFixedFunds_AMS.getBrand(inputDateBegin,inputDateEnd,payload,output,brandKPIs);
## }
## }
catch(Exceptionex){
RestContext.response.statuscode= 400;
## System.debug(ex);
## }
returnoutput;
## }
## }
TPM_RTRFixedFunds_AMS (The Logic Class)
The actual logic is defined in this class. The benefit of routing to a separate third class is that the code runs only when needed.
For example, the Apex classes run only when the report contains the custom datasource and any of the KPIs defined in the custom
metadata. If the report contains fixedfunds KPIs only on the brand level, then only that particular method is run while the method
that's related to categories is skipped. Also if the report contains fixed funds on brand level for only one particular template, then only
this particular KPI is aggregated, calculated, and returned.
It’s important to see how to write back values to the report. For the fixed funds logic, grouping, aggregations, and calculations are
performed. And when that logic is performed, the values are written back to the report. This is done by adding the values to the output
list and then returning it.
The OutputRecord method in the wrapper class creates the output list and contains product, KPI, time, and value.
Create Reports with Custom Apex Filter
Along with standard filters, you can also define custom Apex filters that reference the attributes of the Promotion object.
Core examples are filtering by the promotion type and phase of the promotion. A custom example is linking one promotion to one
specific event.
With that, the main benefit of a custom Apex filter is to offer the opportunity to filter promotions by promotion attributes that aren’t
covered by standard filters. In addition to that, if all the values of the standard filter aren’t visible, you can limit the available filter values
of a promotion attribute for a specific real-time report.
Note:  Custom Apex filters work only with single-select picklists, not with multi-select picklists.
## Report Configuration
In the report configuration, ensure that you define the custom Apex filters in the same section as standard filters.
## 12
TPM_RTRFixedFunds_AMS (The Logic Class)Customizing Real Time Reporting (RTR) with APEX

Note:  You can't use a standard and custom filter with the same name (for example, promo_templatesfid) in the same report
configuration.
## Example: Sample Code
## {
## "type":"singleselect",
"label":"PromotionType",
## "name":"promo_templatesfid",
## "source":{
"class":"TPM_RTRPromoTypeFilter_AMS",
"method":"Event"
## },
"defaultValue":"<<FIRST_VALUE>>"
Here, method is the name of a parameter. This parameter is the Developer_Name__c field of a metadata type record.
However, you can also write a filter without parameters and discard the method line and modify the Apex code accordingly.
## Apex Class
To implement the new filter logic, create an Apex class. You can construct the code for all Apex filters as specified here:
1.Implement System.Callable.
2.Retrieve the user's sales organization for later use.
3.Define the custom logic that returns a map with values.
4.Define a public object call that the report always initially calls. When the public object is called, it calls the method with the custom
logic and passes a string parameter (based on the value of method in the report configuration).
## Classes
Detailed samples of the classes that are used in report configurations.
TPM_RTRFixedFunds_AMS
Sample of the TPM_RTRFixedFunds_AMS class.
TPM_RTRPromoTypeFilter_AMS
Sample of the TPM_RTRPromoTypeFilter_AMS class.
TPM_RTRReportingParentPromoFilter
Sample of the TPM_RTRReportingParentPromoFilter class.
TPM_RTRFixedFunds_AMS
Sample of the TPM_RTRFixedFunds_AMS class.
globalclassTPM_RTRFixedFunds_AMS{
globalstaticList<TPM_RTRReportingWrapper_AMS.OutputRecord>getBrand(DateinputDateBegin,
DateinputDateEnd,TPM_RTRReportingWrapper_AMS.InputPayloadpayload,
List<TPM_RTRReportingWrapper_AMS.OutputRecord>output,Map<String,TPM_RTRRouting__mdt>
fixedFunds){
## 13
ClassesCustomizing Real Time Reporting (RTR) with APEX

//Thiscodecreatesa listbasedon the map thatwas passedintothe method.In thisList
onlythe FundTemplate
//Namesare storedso thatthe listcan be usedin the AggregateResultquery(whereclause).
The goalis to onlyloadrecordsthat
//arerelatedto the FundTemplateswe'relookingat.
List<String>FundTemplateTypes= New List<String>();
StringSalesOrg;
For(StringcmID: fixedFunds.keyset()){
FundTemplateTypes.add(fixedFunds.get(cmID).Fund_Template__c);
if(Salesorg== Null){
Salesorg= fixedFunds.get(cmID).Sales_Org__c;
## }
## }
//ThequeryreturnsFund_Transaction_Rowrecordsbasedon the selectedtimeframe,customer,
categoryand templates
//Theresultsare aggregatedTPM_RTR_Amountvaluesgroupedby BRAND,FUNDTEMPLATE
AggregateResult[]groupedResults= [SELECTSUM(TPM_RTRAmount__c)amount,
cgcloud__Target_Fund__r.cgcloud__Fund_Template__r.Nametemplate,
cgcloud__Target_Fund__r.cgcloud__Fund_Template__r.TPM_RTRRoutingFundType__c
RTRRoutingFundType,
cgcloud__Fund_Transaction__r.cgcloud__Fund_Transaction_Header__r.TPM_Product__cbrand
FROMcgcloud__Fund_Transaction_Row__c
WHEREcgcloud__Target_Fund__r.cgcloud__Fund_Template__r.TPM_RTRRoutingFundType__cin
:FundTemplateTypes
AND cgcloud__Target_Fund__r.cgcloud__Sales_Org__c=:SalesOrg
## AND
cgcloud__Fund_Transaction__r.cgcloud__Fund_Transaction_Header__r.TPM_Product__r.cgcloud__Criterion_1_Product__c
IN :payload.productsfids
AND cgcloud__Target_Fund__r.cgcloud__Anchor_Account__cIN :payload.accountsfids
AND cgcloud__Transaction_Type__cIN ('Deposit','Withdraw')
AND ((cgcloud__Target_Fund__r.cgcloud__Valid_From__c<= :inputDateEnd
AND cgcloud__Target_Fund__r.cgcloud__Valid_From__c>= :inputDateBegin)OR
(cgcloud__Target_Fund__r.cgcloud__Valid_Thru__c<= :inputDateEnd
AND cgcloud__Target_Fund__r.cgcloud__Valid_Thru__c>= :inputDateBegin))
GROUPBY cgcloud__Fund_Transaction__r.cgcloud__Fund_Transaction_Header__r.TPM_Product__c,
cgcloud__Target_Fund__r.cgcloud__Fund_Template__r.Name,
cgcloud__Target_Fund__r.cgcloud__Fund_Template__r.TPM_RTRRoutingFundType__c];
Stringbrand,template,RTRRoutingFundType;
## Doubleamount;
Map<String,Decimal>templateMap;
Map<String,Map<String,Decimal>>cmap= New Map<String,Map<String,Decimal>>();
Map<String,String>RTRRoutingFundTypeMap= New Map<String,String>();
//ThisFor-Loopworkson the aggregateResultsand allocatesall the recordsto their
respective"place"-
//itbasicallysortsall dataintothe rightmaps
For(AggregateResultar : groupedResults){
brand= String.valueOf(ar.get('brand'));//thelastpartof thislineretrievedthe brand
id of our query(brandis an alias)
template= String.valueOf(ar.get('template'));//thelastpartof thislineretrievedthe
templateNameof our query(templateis an alias)
RTRRoutingFundType= String.valueOf(ar.get('RTRRoutingFundType'));//thelastpartof this
lineretrievedthe RTR RoutingFundTypeof our query(RTRRoutingFundTypeis an alias)'));
amount= Double.valueOf(ar.get('amount'));//thelastpartof thislineretrievedthe
aggregatedamountof our query(amountis an alias)
## 14
TPM_RTRFixedFunds_AMSCustomizing Real Time Reporting (RTR) with APEX

templateMap= New Map<String,Decimal>();
If(!cmap.containsKey(brand)){
templateMap.put(template,amount);
cmap.put(brand,templateMap);
## }
else{
templateMap= cmap.get(brand);
if(!templateMap.containsKey(template)){
templateMap.put(template,amount);
cmap.put(brand,templateMap);
## }
## }
if(!RTRRoutingFundTypeMap.containskey(RTRRoutingFundType)){
RTRRoutingFundTypeMap.put(RTRRoutingFundType,template);
## }
## }
//Onceall the resultsof our queryare allocatedand sorted,the dataneedsto be written
backto the report
//Foreachbrandin cmap,
For(StringbrandId: cmap.keyset()){
//andeachtemplatefor thatbrand,
For(StringtemplateId: cmap.get(brandId).keyset()){
//Nowwe looptroughthe map thatwas passedto thismethod
For(StringffID: fixedFunds.keyset()){
//tocheckto whichKPI the map we'recurrentlyin is corrospondingto
If(templateId== RTRRoutingFundTypeMap.get(fixedFunds.get(ffID).Fund_Template__c)){
//Ifthe map we'reworkingon rightnow has the RDF FundTemplate,and one of the records
in our map has
//theRDF FundTemplateassigned,we writebackthisKPI to the corrospondingKPI Definition
of the CustomMetaData
output.add(newTPM_RTRReportingWrapper_AMS.OutputRecord(String.valueOf(brandId),
String.valueOf(fixedFunds.get(ffID).KPI_Definition__c),'Total',
Double.valueOf(cmap.get(brandId).get(templateId))));
## }
## }
## }
## }
returnoutput;
## }
globalstaticList<TPM_RTRReportingWrapper_AMS.OutputRecord>getCategory(DateinputDateBegin,
DateinputDateEnd,TPM_RTRReportingWrapper_AMS.InputPayloadpayload,
List<TPM_RTRReportingWrapper_AMS.OutputRecord>output,Map<String,TPM_RTRRouting__mdt>
fixedFunds){
//Thiscodecreatesa listbasedon the map thatwas passedintothe method.In thisList
onlythe FundTemplate
//Namesare storedso thatthe listcan be usedin the AggregateResultquery.The goalis
to onlyloadrecordsthat
//arerelatedto the FundTemplateswe'relookingat.
List<String>FundTemplateTypes= New List<String>();
StringSalesOrg;
For(StringcmID: fixedFunds.keyset()){
FundTemplateTypes.add(fixedFunds.get(cmID).Fund_Template__c);
if(SalesOrg== Null){
SalesOrg= fixedFunds.get(cmID).Sales_Org__c;
## 15
TPM_RTRFixedFunds_AMSCustomizing Real Time Reporting (RTR) with APEX

## }
## }
//Calculationof the currentweeknumber
DatetodaysDate= date.today();
DatetodaysDateInstance= date.newInstance(todaysdate.year(),todaysdate.month(),
todaysdate.day());
todaysdate.day();
Integercurrentyear= todaysdate.year();
DatestartDate= date.newInstance(currentyear,1,1);
IntegernumberDaysDue= startDate.daysBetween(todaysDateInstance);
IntegernumberOfWeek= math.mod(Integer.valueOf(math.floor((numberDaysDue))/7),52)+1;
//SupportMap for NA_REP_FixedFund_ACalculation
Map<String,Decimal>mPrdAmounts= new Map<String,Decimal>();
//Query
AggregateResult[]groupedResults= [SELECTSUM(cgcloud__Deposits_Approved__c)sumValue,
cgcloud__Anchor_Product__c,
cgcloud__Fund_Template__c,
cgcloud__Fund_Template__r.NametmplName,
cgcloud__Fund_Template__r.TPM_RTRRoutingFundType__cRTRRoutingFundType
FROMcgcloud__Fund__c
WHEREcgcloud__Fund_Template__r.TPM_RTRRoutingFundType__cIN :FundTemplateTypes
AND cgcloud__Sales_Org__c=:SalesOrg
AND cgcloud__Anchor_Product__cIN :payload.productsfids
AND cgcloud__Anchor_Account__cIN :payload.accountsfids
AND ((cgcloud__Valid_From__c<= :inputDateEnd
AND cgcloud__Valid_From__c>= :inputDateBegin)
OR (cgcloud__Valid_Thru__c<= :inputDateEnd
AND cgcloud__Valid_Thru__c>= :inputDateBegin))
GROUPBY cgcloud__Anchor_Product__c,cgcloud__Fund_Template__c,
cgcloud__Fund_Template__r.Name,cgcloud__Fund_Template__r.TPM_RTRRoutingFundType__c];
For (AggregateResultar : groupedResults){
//Checkif currentproductis not alreadyin the map,if so, add to the map withvalue0
If(!mPrdAmounts.containsKey(String.valueOf(ar.get('cgcloud__Anchor_Product__c')))){
mPrdAmounts.put(String.valueOf(ar.get('cgcloud__Anchor_Product__c')),0);
## }
//Addthe sum of the aggregateResultto the existingvaluein map for currentproduct
mPrdAmounts.put(String.valueOf(ar.get('cgcloud__Anchor_Product__c')),
mPrdAmounts.get(String.valueOf(ar.get('cgcloud__Anchor_Product__c')))+
Double.valueOf(ar.get('sumValue')));
//CheckFundTemplateand add KPI
For(StringqKPI: fixedFunds.keyset()){
If(String.valueOf(ar.get('RTRRoutingFundType'))== fixedFunds.get(qKPI).Fund_Template__c){
output.add(new
TPM_RTRReportingWrapper_AMS.OutputRecord(String.valueOf(ar.get('cgcloud__Anchor_Product__c')),
String.valueOf(fixedFunds.get(qKPI).KPI_Definition__c),'Total',
Double.valueOf(ar.get('sumValue'))));
## }
## }
## }
//AddNA_REP_FixedFund_Aif required
If(fixedFunds.containsKey('NA_REP_FixedFund_A')){
For(Stringcdr : mPrdAmounts.keyset()){
output.add(newTPM_RTRReportingWrapper_AMS.OutputRecord(String.valueOf(cdr),
'NA_REP_FixedFund_A','Total',Double.valueOf((mPrdAmounts.get(cdr)*numberOfWeek/52))));
## 16
TPM_RTRFixedFunds_AMSCustomizing Real Time Reporting (RTR) with APEX

## }
## }
returnoutput;
## }
## }
TPM_RTRPromoTypeFilter_AMS
Sample of the TPM_RTRPromoTypeFilter_AMS class.
publicwithsharingclassTPM_RTRPromoTypeFilter_AMSimplementsSystem.Callable{
publicclassTPM_RTRPromotionsCallableExceptionextendsException{}
privatestaticStringuserSalesOrgName= null;
## //GETSF ID
static{
List<User>users= [SELECTcgcloud__Sales_Org__cFROMUserWHEREId =
:String.escapeSingleQuotes(UserInfo.getUserId())LIMIT1];
userSalesOrgName= users[0].cgcloud__Sales_Org__c;
## }
@testVisibleprivatestaticList<Map<String,Object>>getPromotionTypes(Stringdevname){
StringmyCM;
1.Query the custom metadata record based on the parameter, and then perform workarounds for the test classes.
## //GETCUSTOMMETADATATYPEPROMOTYPEGROUPINGS(BASEDON ARGUMENTOF REPORT)
if(!Test.isRunningTest()){
TPM_RTRPromoTypes__mdtcustomMetaData= [SELECTPromo_Types__cFROMTPM_RTRPromoTypes__mdt
WHEREDeveloperName= :devnameLIMIT1];
myCM= customMetaData.Promo_Types__c;
## }
## //WORKAROUNDFOR TESTCLASS(CUSTOMMETADATATYPE)
else{
myCM= devname;
## }
2.From the custom metadata record, split the value of the Promo_Types__c field into individual values and then parse them into
a new list type called groups.
List<String>splitGrouping= myCM.split(';');
List<String>typeGroups= New List<String>();
For(Stringitem: splitGrouping){
typeGroups.add(item.trim());
## }
3.Create a new list that you can later use to store the value of results= List<Map<String,Object>>. You can also
query promotion templates into another active list that has the same sales org as the user and whose name matches the values in
the Groups list type.
List<Map<String,Object>>result= new List<Map<String,Object>>();
List<cgcloud__Promotion_Template__c>prmTmpl= New List<cgcloud__Promotion_Template__c>();
prmTmpl= [SELECTId, NameFROMcgcloud__Promotion_Template__cWHEREcgcloud__Active__c
= trueAND cgcloud__Sales_Org__c= :userSalesOrgNameAND NameIN :typeGroups];
Map<String,String>outP= New Map<String,String>();
## 17
TPM_RTRPromoTypeFilter_AMSCustomizing Real Time Reporting (RTR) with APEX

4.Return the result.
for(cgcloud__Promotion_Template__ctmpl: prmTmpl){
If(!outP.containsKey(tmpl.Name)){
outP.put(String.valueOf(tmpl.Id),String.valueOf(tmpl.Name));
## }
## }
for(StringtypeId: outP.keyset()){
result.add(newMap<String,Object>{
'label'=> outP.get(typeId),
'value'=> typeId
## });
## }
returnresult;
## }
publicObjectcall(Stringmethod,Map<String,Object>args){
returngetPromotionTypes(method);
## }
## }
TPM_RTRReportingParentPromoFilter
Sample of the TPM_RTRReportingParentPromoFilter class.
publicwithsharingclassTPM_RTRReportingParentPromoFilterimplementsSystem.Callable{
publicclassTPM_RTRPromotionsCallableExceptionextendsException{}
privatestaticList<User>users= [SELECTcgcloud__Sales_Org__cFROMUserWHEREId =
:String.escapeSingleQuotes(UserInfo.getUserId())LIMIT1];
privatestaticStringuserSalesOrgName= users[0].cgcloud__Sales_Org__c;
1.Create a new list that you can later use to store the value of results= List<Map<String,Object>>.
@TestVisibleprivatestaticList<Map<String,Object>>getParentPromotion(){
List<Map<String,Object>>result= new List<Map<String,Object>>();
2.Query the Promotion object on all records templates that have the CustomerEvents picklist value selected on the
TPM_Promo_Type_ControlView__c field for the appropriate sales org ad user.
List<cgcloud__Promotion__c>prmTmpl= [SELECTID, Name,cgcloud__Slogan__c,
cgcloud__Anchor_Account__c,cgcloud__Anchor_Account__r.Name,cgcloud__Promotion_Template__r.cgcloud__Description__c,cgcloud__Promotion_Template__r.cgcloud__Sales_Org__c,cgcloud__Promotion_Template__r.TPM_Promo_Type_ControlView__c
FROMcgcloud__Promotion__cWHERE
cgcloud__Promotion_Template__r.TPM_Promo_Type_ControlView__c='CustomerEvent'and
cgcloud__Promotion_Template__r.cgcloud__Sales_Org__c=: userSalesOrgName];
Map<ID,String>outP= New Map<ID,String>();
for(cgcloud__Promotion__ctempl: prmTmpl){
If(!outP.containsKey(templ.ID)){
outP.put(String.valueOf(templ.Id),String.valueOf(templ.cgcloud__Slogan__c));
## }
## }
3.Return the list.
for(StringstatusTo: outP.keyset()){
result.add(newMap<String,Object>{
## 18
TPM_RTRReportingParentPromoFilterCustomizing Real Time Reporting (RTR) with APEX

'label'=> outP.get(statusTo),
'value'=> statusTo
## });
## }
system.debug(json.serialize(result));
returnresult;
## }
publicObjectcall(Stringmethod,Map<String,Object>args){
returngetParentPromotion();
## }
## }
## 19
TPM_RTRReportingParentPromoFilterCustomizing Real Time Reporting (RTR) with APEX