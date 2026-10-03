public with sharing class FlexCap {
    @InvocableMethod(CapabilityType='FlexTemplate://Renewal_Outreach')
    public static List<Response> run(List<Request> requests) { return new List<Response>(); }
    public class Request { @InvocableVariable public Account account; }
    public class Response { @InvocableVariable public String Prompt; }
}
