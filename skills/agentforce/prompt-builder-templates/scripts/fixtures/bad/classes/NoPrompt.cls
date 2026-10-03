public with sharing class NoPrompt {
    @InvocableMethod(CapabilityType='PromptTemplateType://einstein_gpt__salesEmail')
    public static List<Response> run(List<Request> requests) { return new List<Response>(); }
    public class Request { @InvocableVariable public Contact Recipient; }
    public class Response { @InvocableVariable public String body; }
}
