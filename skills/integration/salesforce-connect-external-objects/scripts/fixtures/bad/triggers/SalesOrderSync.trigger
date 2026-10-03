trigger SalesOrderSync on SalesOrder__x (after update) {
    System.debug(Trigger.new.size());
}
