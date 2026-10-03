public with sharing class NoNullComparator implements Comparator<UnannotatedRow> {
    public Integer compare(UnannotatedRow a, UnannotatedRow b) {
        return a.amount > b.amount ? 1 : -1;
    }
}
