from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from tempfile import mkdtemp
from dotenv import load_dotenv

from query_context import get_query_context_list
from db import get_db_connection, add_stats_to_db
from scraper import scrape_amazon, scrape_lazada
from price_stats import PriceStats, price_stats_to_prices_row_entry

import os
import traceback

def init_driver(timeout=10, is_mobile=False, is_dev_env=False) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    service: webdriver.ChromeService

    if is_dev_env:
        service = webdriver.ChromeService(ChromeDriverManager().install())
    else:
        service = webdriver.ChromeService("/opt/chromedriver")
        chrome_options.binary_location = '/opt/chrome/chrome'

    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--window-size=1280,1696")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-dev-tools')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-port=9222")

    if is_mobile:
        print("this is run")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; U; CPU iPhone OS 5_1_1 like Mac OS X; ar) AppleWebKit/534.46.0 (KHTML, like Gecko) CriOS/19.0.1084.60 Mobile/9B206 Safari/7534.48.3")

    driver = webdriver.Chrome(options=chrome_options, service=service)
    driver.set_page_load_timeout(timeout)
    return driver

def run():
    try:
        load_dotenv()
        TIMEOUT_SECONDS = int(os.environ.get("WEBDRIVER_TIMEOUT_SECONDS"))
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
        RUNTIME_ENV = os.environ.get("RUNTIME_ENV")
        is_dev_env = (RUNTIME_ENV == 'DEV')

        print("Initiating DB Connection...")
        client = get_db_connection(url=SUPABASE_URL, key=SUPABASE_KEY)

        print("DB Connected. Getting Context List...")
        context_list = get_query_context_list(client)

        print("Obtained List. Initalising Web Driver...")
        driver = init_driver(timeout=TIMEOUT_SECONDS, is_mobile=False, is_dev_env=is_dev_env)

        print("Web Driver Initialised. Executing scrapes...")
        
        stats_list: list[PriceStats] = []

        for ctx in context_list:
            ama_stats = scrape_amazon(driver, ctx, TIMEOUT_SECONDS)
            if ama_stats != None:
                stats_list.append(ama_stats)

        driver.quit()

        print("Finished scrapes for web driver. Initialising mobile driver...")
        mobile_driver = init_driver(timeout=TIMEOUT_SECONDS, is_mobile=True, is_dev_env=is_dev_env)

        for ctx in context_list:
            laz_stats = scrape_lazada(mobile_driver, ctx, TIMEOUT_SECONDS)
            if laz_stats != None:
                stats_list.append(laz_stats)
        
        mobile_driver.quit()

        stats_list = list(map(lambda stat : price_stats_to_prices_row_entry(stat), stats_list))
        print("Finished scraping. Adding data to DB...")
        add_stats_to_db(client, stats_list)
        print("Completed.")

    except:
        traceback.print_exc()
        # Teardown drivers if program crashes
        driver.quit()
        mobile_driver.quit()



if __name__ == '__main__':
    run()