global class ErpConnection extends DataSource.Connection {
    override global List<DataSource.Table> sync() {
        insert new Account(Name = 'adapter log');
        return new List<DataSource.Table>();
    }
    override global DataSource.TableResult query(DataSource.QueryContext c) {
        return null;
    }
    override global List<DataSource.TableResult> search(DataSource.SearchContext c) {
        return null;
    }
}
