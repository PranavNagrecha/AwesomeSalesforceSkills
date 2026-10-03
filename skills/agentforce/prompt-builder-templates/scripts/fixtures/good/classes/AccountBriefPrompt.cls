public with sharing class AccountBriefPrompt {
    // Field Generation grounding; see the guide's OpenCasesPrompt example.
    @InvocableMethod(label='Account Brief' CapabilityType='PromptTemplateType://einstein_gpt__fieldCompletion')
    public static List<Response> run(List<Request> requests) {
        Response r = new Response();
        r.Prompt = 'Industry: ' + requests[0].RelatedEntity.Industry;
        return new List<Response>{ r };
    }
    public class Request {
        @InvocableVariable(required=true)
        public Account RelatedEntity;
    }
    public class Response {
        @InvocableVariable
        public String Prompt;
    }
}
