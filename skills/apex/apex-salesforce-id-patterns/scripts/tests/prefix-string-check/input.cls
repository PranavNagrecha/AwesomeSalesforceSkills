public class BadIdRouting {
    public static String classify(String rawId) {
        if (rawId.startsWith('001')) { return 'Account'; }
        if (rawId.startsWith('003')) { return 'Contact'; }
        return 'Unknown';
    }
}
