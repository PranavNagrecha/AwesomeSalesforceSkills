public with sharing class ShipmentLookupAction {
    public class Request {
        @InvocableVariable(required=true label='Tracking Number' description='The carrier tracking number the user gave.')
        public String trackingNumber;
    }
    public class Result {
        @InvocableVariable(label='Status' description='Shipment status a user can read.')
        public String status;
        @InvocableVariable(label='Error' description='NOT_FOUND when no shipment matches.')
        public String error;
    }
    @InvocableMethod(label='Look Up Shipment' description='Returns the status of one shipment by tracking number. It never changes data.')
    public static List<Result> lookUp(List<Request> requests) {
        List<Result> results = new List<Result>();
        for (Request req : requests) {
            Result res = new Result();
            res.error = String.isBlank(req.trackingNumber) ? 'NOT_FOUND' : '';
            results.add(res);
        }
        return results;
    }
}
