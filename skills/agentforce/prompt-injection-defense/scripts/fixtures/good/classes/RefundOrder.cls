public with sharing class RefundOrder {
    // Accepts identifiers only; status is re-queried in user mode.
    @InvocableMethod(label='Refund Order')
    public static List<String> run(List<Request> reqs) {
        Set<Id> ids = new Set<Id>();
        for (Request r : reqs) { ids.add(r.orderId); }
        Map<Id, Order> byId = new Map<Id, Order>([SELECT Id, Status FROM Order WHERE Id IN :ids WITH USER_MODE]);
        List<String> out = new List<String>();
        for (Request r : reqs) {
            Order o = byId.get(r.orderId);
            out.add(o == null ? 'NOT_VISIBLE' : (o.Status == 'Delivered' ? 'OK' : 'POLICY_BLOCKED'));
        }
        return out;
    }
    public class Request {
        @InvocableVariable(required=true)
        public Id orderId;
    }
}
