from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from supabase import Client

from context import QueryContext, get_query_context_list
from db import get_db_connection

import statistics
import os

BASE_URL_AMAZON = 'https://www.amazon.sg/s?k='
DELIMITER_AMAZON = '+'

BASE_URL_LAZADA = 'https://www.lazada.sg/catalog/?q='
DELIMITER_LAZADA = '%20'

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class PriceStats():
    def __init__(self, id, lowest, highest, median, mean) -> None:
        self.query_id = id
        self.lowest = lowest
        self.highest = highest
        self.median = median
        self.mean = mean

    def __repr__(self):
        return f'Query ID: {self.query_id}, \
                    Highest Price: {self.highest}, \
                    Lowest Price: {self.lowest}, \
                    Median Price: {self.median}, \
                    Mean Price: {self.mean}'
        
def init_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
    driver.set_page_load_timeout(10)
    return driver

def get_full_query_url(base_url, delimiter, query_terms):
    query_params = ''
    for term in query_terms:
        query_params += f'{term}{delimiter}'
    query_params = query_params[:-(len(delimiter))]
    return base_url + query_params

def scrape_lazada(driver: webdriver.Chrome, context: QueryContext, client: Client) -> PriceStats:
    full_query_url = get_full_query_url(BASE_URL_LAZADA, DELIMITER_LAZADA, context.query_terms)
    try:
        driver.get(full_query_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'products'))
        )
        
    except TimeoutException:
        print("Timeout Occured when scraping Lazada!")

    finally:
        elements = driver.find_elements(By.CSS_SELECTOR, f'[data-qa-locator="product-item"]')
        if len(elements) == 0:
            print("Empty List!")
        else:
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
                lowest=min(prices), 
                highest=max(prices), 
                median=round(statistics.median(prices), 2), 
                mean=statistics.mean(prices))
            
            print('Lazada:')
            print(stats)
            
            return stats
                

def scrape_amazon(driver: webdriver.Chrome, context: QueryContext, client: Client) -> PriceStats:
    full_query_url = get_full_query_url(BASE_URL_AMAZON, DELIMITER_AMAZON, context.query_terms)
    try:
        driver.get(full_query_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 's-skipLinkTargetForMainSearchResults'))
        )

    except TimeoutException:
        print("Timeout Occured when scraping Amazon!")
          
    finally:
        elements = driver.find_elements(By.CSS_SELECTOR, f'[data-cy="price-recipe"]')
        if len(elements) == 0:
            print("Empty List!")
        else:
            prices = []
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
                lowest=min(prices), 
                highest=max(prices), 
                median=round(statistics.median(prices), 2), 
                mean=statistics.mean(prices))
            
            print('Amazon: ')
            print(stats)
            
            return stats
            
if __name__ == '__main__':
    try:
        client = get_db_connection(url=SUPABASE_URL, key=SUPABASE_KEY)
        context_list = get_query_context_list(client)
        driver: webdriver.Chrome = init_driver()
        stats_list = []
        for ctx in context_list:
            stats_list.append(scrape_lazada(driver, ctx, client))
            stats_list.append(scrape_amazon(driver, ctx, client))
        print(stats_list)
    finally:
        driver.quit()