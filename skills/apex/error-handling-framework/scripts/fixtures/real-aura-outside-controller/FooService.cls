public with sharing class FooService {
    public static void run() {
        throw new AuraHandledException('x');
    }
}
