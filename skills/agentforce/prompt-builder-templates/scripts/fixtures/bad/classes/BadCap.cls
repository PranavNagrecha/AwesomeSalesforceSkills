public with sharing class BadCap {
    @InvocableMethod(CapabilityType='PromptTemplateType://einstein_gpt__summarize')
    public static List<Response> run(List<Request> requests) { return new List<Response>(); }
    public class Request { @InvocableVariable public Account RelatedEntity; }
    public class Response { @InvocableVariable public String Prompt; }
}
