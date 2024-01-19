from datetime import timezone
import datetime

class PriceStats():
    def __init__(self, id, ecommerce_name, lowest, highest, median, mean) -> None:
        self.query_id = id
        self.ecommerce_name = ecommerce_name
        self.lowest = lowest
        self.highest = highest
        self.median = median
        self.mean = mean

    def __repr__(self):
        return f'   Taken from {self.ecommerce_name}: \
                    Query ID: {self.query_id}, \
                    Highest Price: {self.highest}, \
                    Lowest Price: {self.lowest}, \
                    Median Price: {self.median}, \
                    Mean Price: {self.mean}'
    

def price_stats_to_prices_row_entry(stat: PriceStats):
    return {
        'query_id': stat.query_id,
        'ecommerce_name': stat.ecommerce_name,
        'query_dt': datetime.datetime.now(timezone.utc).isoformat(),
        'median_price': stat.median,
        'lowest_price': stat.lowest,
        'highest_price': stat.highest,
        'mean_price': stat.mean
    }