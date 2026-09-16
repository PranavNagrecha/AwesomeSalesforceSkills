trigger RealLogicCase on Case (after update) {
    for (Case c : Trigger.new) {
        update c;
    }
}
