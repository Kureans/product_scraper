from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from supabase import Client
from dotenv import load_dotenv

from query_context import get_query_context_list
from db import get_db_connection, add_stats_to_db
from scraper import scrape_amazon, scrape_lazada
from price_stats import PriceStats, price_stats_to_prices_row_entry

import os

def init_driver(timeout=10) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('window-size=1400,2100')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
    driver.set_page_load_timeout(timeout)
    return driver

if __name__ == '__main__':
    try:
        load_dotenv()
        TIMEOUT_SECONDS = os.environ.get("WEBDRIVER_TIMEOUT_SECONDS")
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

        client = get_db_connection(url=SUPABASE_URL, key=SUPABASE_KEY)
        context_list = get_query_context_list(client)
        driver: webdriver.Chrome = init_driver(TIMEOUT_SECONDS)

        stats_list: list[PriceStats] = []

        for ctx in context_list:
            stats_list.append(scrape_lazada(driver, ctx, TIMEOUT_SECONDS))
            stats_list.append(scrape_amazon(driver, ctx, TIMEOUT_SECONDS))

        stats_list = list(map(lambda stat : price_stats_to_prices_row_entry(stat), stats_list))
        add_stats_to_db(client, stats_list)

    finally:
        driver.quit()