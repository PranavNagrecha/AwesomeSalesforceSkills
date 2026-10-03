public with sharing class NoRelated {
    @InvocableMethod(CapabilityType='PromptTemplateType://einstein_gpt__fieldCompletion')
    public static List<Response> run(List<Request> requests) { return new List<Response>(); }
    public class Request { @InvocableVariable public Account acct; }
    public class Response { @InvocableVariable public String Prompt; }
}
