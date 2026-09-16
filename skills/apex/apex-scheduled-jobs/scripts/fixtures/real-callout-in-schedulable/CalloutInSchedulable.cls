public with sharing class CalloutInSchedulable implements Schedulable {
    public void execute(SchedulableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Foo');
    }
}
