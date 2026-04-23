/**
 * Actions:
 *   'bar': args { 'key': String } -> String
 *   'baz': args { } -> Boolean
 */
global with sharing class CleanCallableExample implements Callable {
    global Object call(String action, Map<String, Object> args) {
        switch on action {
            when 'bar' {
                if (!args.containsKey('key')) { throw new IllegalArgumentException('key required'); }
                return (String) args.get('key');
            }
            when 'baz' { return true; }
            when else { throw new NoSuchElementException('Unknown action: ' + action); }
        }
    }
}
