public with sharing class LegacyFhirClient {
    public static HttpResponse readCondition(String id) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(URL.getOrgDomainUrl().toExternalForm() + '/services/data/v60.0/healthcare/fhir/R4/Condition/' + id);
        req.setMethod('GET');
        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() != 200) {
            throw new CalloutException('FHIR read failed: ' + res.getStatusCode());
        }
        return res;
    }
}
