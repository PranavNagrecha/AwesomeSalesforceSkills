/**
 * Actions:
 *   'bar': args { } -> String
 */
global with sharing class MissingWhenElseExample implements Callable {
    global Object call(String action, Map<String, Object> args) {
        switch on action {
            when 'bar' { return 'baz'; }
        }
        return null;
    }
}
