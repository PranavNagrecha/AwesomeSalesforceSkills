public class GoodRegexExample {
    private static final Pattern DIGITS = Pattern.compile('\\d+');
    public static String stripDigits(String s) {
        return DIGITS.matcher(s).replaceAll('');
    }
}
