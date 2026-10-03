public class BadAction {
    public class Request {
        @InvocableVariable(required=true)
        public Object payload;
        @InvocableVariable(label='Ids' description='Record ids')
        public List<String> recordIds;
    }
    @InvocableMethod(label='Do It')
    public static List<String> run(String single) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Vendor/orders');
        new Http().send(req);
        return new List<String>();
    }
    @InvocableMethod(label='Second' description='A second invocable in the same class, which is not allowed.')
    public static void second(List<Request> requests) {
    }
}
