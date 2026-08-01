# Well-Architected Notes — Flow Data Tables

**User Experience:** the component covers display-and-select declaratively, which is the
majority of screen-flow table requirements. The two configuration decisions that most
affect the experience are the selection mode — which determines the output type, not just
the interaction — and the empty-state branch, whose absence turns a legitimate "nothing
matched" into a screen that reads as broken.

**Reliability:** there is no server-side paging, so the rows displayed are the rows the
source collection holds and the collection has to be bounded deliberately. Downstream, a
multi-select table feeds a collection: assemble it in a Loop and issue one DML statement
afterwards, rather than one per row, so the flow does not consume the per-transaction
limit of 150 DML statements as a function of user selection.

## Official Sources Used

- Flow screen component reference — Data Table configuration, selection modes and column types — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp.htm
- Flow Builder — Get Records element, filters, sort and record limits — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_getrecords.htm
- Flow limits and considerations — the per-transaction limits a running flow shares with Apex — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_limit.htm
- Apex Governor Limits — 150 DML statements and 50,000 records retrieved by SOQL queries per transaction, which apply to a flow transaction too — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Flow metadata — recordLookups, decisions and screen element structure — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
