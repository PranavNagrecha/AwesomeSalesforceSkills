public without sharing class RefundAnything {
    @InvocableMethod(label='Refund Anything')
    public static List<String> run(List<Request> reqs) {
        List<Order> orders = [SELECT Id, Status FROM Order WHERE Id = :reqs[0].orderId WITH SYSTEM_MODE];
        return new List<String>{ reqs[0].isEligible ? 'REFUNDED' : 'NO' };
    }
    public class Request {
        @InvocableVariable public Id orderId;
        @InvocableVariable public Boolean isEligible;
    }
}
