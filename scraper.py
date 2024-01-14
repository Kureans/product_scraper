from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import statistics

BASE_URL_AMAZON = 'https://www.amazon.sg/s?k='
DELIMITER_AMAZON = '+'

BASE_URL_LAZADA = 'https://www.lazada.sg/catalog/?q='
DELIMITER_LAZADA = '%20'

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('headless')
driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
driver.set_page_load_timeout(10)
query_terms = ['whey', 'protein', '2.5kg']

def get_full_query_url(base_url, delimiter, query_terms):
    query_params = ''
    for term in query_terms:
        query_params += f'{term}{delimiter}'
    query_params = query_params[:-(len(delimiter))]
    return base_url + query_params

def scrape_lazada(driver: webdriver.Chrome, query_terms: list):
    full_query_url = get_full_query_url(BASE_URL_LAZADA, DELIMITER_LAZADA, query_terms)
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
                

def scrape_amazon(driver: webdriver.Chrome, query_terms: list):
    full_query_url = get_full_query_url(BASE_URL_AMAZON, DELIMITER_AMAZON, query_terms)
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
    scrape_lazada(driver, query_terms)
    scrape_amazon(driver, query_terms)
finally:
    driver.quit()
