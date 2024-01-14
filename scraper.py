from time import sleep
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

URL_LAZADA = 'https://www.lazada.sg/catalog/?q=whey%20protein%202.5kg%20myprotein'

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('headless')
driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
query_terms = ['whey', 'protein', '2.5kg']

def scrape_amazon(driver, query_terms):
    query_params = ''
    for term in query_terms:
        query_params += f'{term}{DELIMITER_AMAZON}'
    query_params = query_params[:-1]
    full_query_url = BASE_URL_AMAZON + query_params
    driver.get(full_query_url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 's-skipLinkTargetForMainSearchResults'))
        )
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
            print(f'Highest Price: {max(prices)}, \
                    Lowest Price: {min(prices)}, \
                    Median Price: {statistics.median(prices)}, \
                    Mean Price: {statistics.mean(prices)}')
    except TimeoutException:
        print("Timeout Occured")
    finally:
        driver.quit()

scrape_amazon(driver, query_terms)