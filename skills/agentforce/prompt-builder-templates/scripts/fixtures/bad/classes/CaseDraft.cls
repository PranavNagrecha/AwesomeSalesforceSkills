public with sharing class CaseDraft {
    @InvocableMethod(CapabilityType='PromptTemplateType://einstein_gpt__caseEmailDraft')
    public static List<Response> run(List<Request> requests) { return new List<Response>(); }
    public class Request { @InvocableVariable public Case CaseObject; }
    public class Response { @InvocableVariable public String Prompt; }
}
