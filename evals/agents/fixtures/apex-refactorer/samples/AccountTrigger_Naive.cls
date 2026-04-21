trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
    if (Trigger.isBefore && Trigger.isInsert) {
        for (Account a : Trigger.new) {
            if (a.BillingCountry == null) {
                a.BillingCountry = 'US';
            }
            System.debug('Stamped default country on ' + a.Id);
        }
    }

    if (Trigger.isAfter && Trigger.isUpdate) {
        List<Contact> related = [
            SELECT Id, AccountId, MailingCountry
            FROM Contact
            WHERE AccountId IN :Trigger.newMap.keySet()
        ];
        for (Contact c : related) {
            Account parent = Trigger.newMap.get(c.AccountId);
            if (parent != null && parent.BillingCountry != null) {
                c.MailingCountry = parent.BillingCountry;
            }
        }
        update related;

        Http http = new Http();
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://erp.example.com/api/sync');
        req.setMethod('POST');
        req.setBody(JSON.serialize(Trigger.new));
        HttpResponse res = http.send(req);
        System.debug('ERP sync status: ' + res.getStatusCode());
    }
}
