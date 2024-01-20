from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from query_context import QueryContext
from price_stats import PriceStats

import statistics

BASE_URL_AMAZON = 'https://www.amazon.sg/s?k='
DELIMITER_AMAZON = '+'

BASE_URL_LAZADA = 'https://www.lazada.sg/catalog/?q='
DELIMITER_LAZADA = '%20'

def get_full_query_url(base_url: str, delimiter: str, query_terms: list[str]) -> str:
    query_params = ''
    for term in query_terms:
        query_params += f'{term}{delimiter}'
    query_params = query_params[:-(len(delimiter))]
    return base_url + query_params

# Scraping logic designed for mobile driver
def scrape_lazada(driver: webdriver.Chrome, context: QueryContext, timeout: int) -> PriceStats | None:
    full_query_url = get_full_query_url(BASE_URL_LAZADA, DELIMITER_LAZADA, context.query_terms)
    try:
        driver.get(full_query_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-list'))
        )

    except TimeoutException:
        print("Timeout Occured when scraping Lazada!")

    finally:
        elements = driver.find_elements(By.CSS_SELECTOR, f'[data-qa-locator="product-item"]')
        
        if len(elements) == 0:
            print("Empty List from Lazada!")
            return None
     
        prices = []
        if len(context.exclude_terms) > 0:
            elements = filter(lambda e: e not in context.exclude_terms, elements)
        for e in elements:
            product_data = e.text.split('\n')
            for item in product_data:
                if item[0] != '$':
                    continue
                price_value = float(item[1:])
                prices.append(price_value)

        stats = PriceStats(
            id=context.id,
            ecommerce_name='lazada',
            lowest=min(prices), 
            highest=max(prices), 
            median=round(statistics.median(prices), 2), 
            mean=statistics.mean(prices))
        
        print(stats)
        
        return stats
                
# Scraping logic designed for web driver
def scrape_amazon(driver: webdriver.Chrome, context: QueryContext, timeout: int) -> PriceStats | None:
    full_query_url = get_full_query_url(BASE_URL_AMAZON, DELIMITER_AMAZON, context.query_terms)
    try:
        driver.get(full_query_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, 's-skipLinkTargetForMainSearchResults'))
        )

    except TimeoutException:
        print("Timeout Occured when scraping Amazon!")
          
    finally:
        elements = driver.find_elements(By.CSS_SELECTOR, f'[data-cy="price-recipe"]')

        if len(elements) == 0:
            print("Empty List from Amazon!")
            return None
      
        prices = []
        if len(context.exclude_terms) > 0:
            elements = filter(lambda e: e not in context.exclude_terms, elements)
        for e in elements:
            price_data = e.text.split('S')
            if len(price_data) < 2:
                continue
            price_string = price_data[1]
            dollars, cents, *metadata = price_string.split('\n', 2)
            price_value = int(dollars[1:]) + (int(cents[:2]) / 100)
            prices.append(price_value)
                
        stats = PriceStats(
            id=context.id,
            ecommerce_name='amazon',
            lowest=min(prices), 
            highest=max(prices), 
            median=round(statistics.median(prices), 2), 
            mean=statistics.mean(prices))
        
        print(stats)
        
        return stats