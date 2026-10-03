public class RateLoader implements Schedulable {
    public void execute(SchedulableContext ctx) {
        List<DatedConversionRate> rates = new List<DatedConversionRate>();
        rates.add(new DatedConversionRate(IsoCode = 'EUR', ConversionRate = 0.91, StartDate = Date.today()));
        insert rates;
    }
}
