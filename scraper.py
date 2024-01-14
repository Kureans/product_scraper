from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from supabase import create_client, Client

import statistics
import os

BASE_URL_AMAZON = 'https://www.amazon.sg/s?k='
DELIMITER_AMAZON = '+'

BASE_URL_LAZADA = 'https://www.lazada.sg/catalog/?q='
DELIMITER_LAZADA = '%20'

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class QueryContext():
    def __init__(self, query_terms: list[str], exclude_terms: list[str]) -> None:
        self.query_terms = query_terms
        self.exclude_terms = exclude_terms

def get_db_connection() -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client

def get_query_context_list(client: Client) -> list[QueryContext]:
    context_list = []
    query_strings = client.table('queries').select('query_string').execute().data
    if len(query_strings) == 0:
        print("No query strings in DB yet!")
        return
    for query in query_strings:
        query_terms = query.get('query_string', '').split(' ')
        exclude_terms = query.get('exclude_string', '').split(' ')
        context_list.append(QueryContext(query_terms, exclude_terms))
    return context_list

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

def scrape_lazada(driver: webdriver.Chrome, context: QueryContext) -> None:
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

            print('Lazada: ')
            print(f'Highest Price: {max(prices)}, \
                    Lowest Price: {min(prices)}, \
                    Median Price: {statistics.median(prices)}, \
                    Mean Price: {statistics.mean(prices)}')
                

def scrape_amazon(driver: webdriver.Chrome, context: QueryContext) -> None:
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
            
            print('Amazon: ')
            print(f'Highest Price: {max(prices)}, \
                    Lowest Price: {min(prices)}, \
                    Median Price: {statistics.median(prices)}, \
                    Mean Price: {statistics.mean(prices)}')

try:
    client = get_db_connection()
    context_list = get_query_context_list(client)
    driver: webdriver.Chrome = init_driver()
    for ctx in context_list:
        scrape_lazada(driver, ctx)
        scrape_amazon(driver, ctx)
finally:
    driver.quit()