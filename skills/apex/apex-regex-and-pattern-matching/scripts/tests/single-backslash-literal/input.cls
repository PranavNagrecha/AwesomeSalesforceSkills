public class BadRegexExample {
    public static String stripDigits(String s) {
        // Single backslash in Apex string literal — wrong. Should be '\\d+'.
        return s.replaceAll('\d+', '');
    }
}
