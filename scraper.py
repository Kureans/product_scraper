from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

URL_SHOPEE = 'shopee.sg/search'
DELIMITER_SHOPEE = '%20'
test_string = 'https://shopee.sg/search?keyword=myprotein%20whey%20protein%202.5kg'
test_string_2 = 'https://google.com'
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
driver.implicitly_wait(5)
driver.get(test_string)
res = driver.find_element(By.CLASS_NAME, 'search-items-container')
print(res)