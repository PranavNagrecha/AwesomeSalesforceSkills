/**
 * MockHttpResponseGenerator — reusable HttpCalloutMock.
 *
 * Supports three modes:
 *  1. Single canned response for any endpoint.
 *  2. Per-endpoint routing (path substring → response).
 *  3. Sequence mode — pops one response per call (simulates retries).
 *
 *     Test.setMock(HttpCalloutMock.class,
 *         new MockHttpResponseGenerator()
 *             .withResponse(200, '{"ok":true}')
 *             .routeByPathContains('/v1/accounts', 200, '{"id":"A-1"}')
 *             .pushSequence(503, '')
 *             .pushSequence(200, '{"ok":true}')
 *     );
 */
@IsTest
global class MockHttpResponseGenerator implements HttpCalloutMock {

    private Integer defaultStatus = 200;
    private String defaultBody = '{}';
    private Map<String, Integer> routeStatus = new Map<String, Integer>();
    private Map<String, String> routeBody = new Map<String, String>();
    private List<Integer> sequenceStatus = new List<Integer>();
    private List<String> sequenceBody = new List<String>();

    public MockHttpResponseGenerator withResponse(Integer status, String body) {
        this.defaultStatus = status;
        this.defaultBody = body == null ? '' : body;
        return this;
    }

    public MockHttpResponseGenerator routeByPathContains(String needle, Integer status, String body) {
        routeStatus.put(needle, status);
        routeBody.put(needle, body == null ? '' : body);
        return this;
    }

    public MockHttpResponseGenerator pushSequence(Integer status, String body) {
        sequenceStatus.add(status);
        sequenceBody.add(body == null ? '' : body);
        return this;
    }

    global HttpResponse respond(HttpRequest req) {
        HttpResponse res = new HttpResponse();
        res.setHeader('Content-Type', 'application/json');

        if (!sequenceStatus.isEmpty()) {
            res.setStatusCode(sequenceStatus.remove(0));
            res.setBody(sequenceBody.remove(0));
            return res;
        }

        String endpoint = req.getEndpoint();
        for (String needle : routeStatus.keySet()) {
            if (endpoint.contains(needle)) {
                res.setStatusCode(routeStatus.get(needle));
                res.setBody(routeBody.get(needle));
                return res;
            }
        }

        res.setStatusCode(defaultStatus);
        res.setBody(defaultBody);
        return res;
    }
}
