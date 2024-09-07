from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver
def rentseekers(city):
    url = "https://www.rentseeker.ca/"
    driver = setup_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 30)
    price_list = []
    address_list = []
    phone_list = []
    
    searchbar = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "pac-target-input")))
    driver.execute_script("arguments[0].scrollIntoView();", searchbar)
    time.sleep(2)
    
    searchbar.send_keys(city)
    time.sleep(2)
    searchbar.send_keys(Keys.ARROW_DOWN)
    searchbar.send_keys(Keys.ENTER)
    time.sleep(10)
    pages = 3
    
    for attemp in range(pages):
        try:
            prices = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "price")))
            addresses = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "subtitle")))
            phones = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@class="call-cta cta-button"]')))
            
            print(f"Found {len(prices)} prices, {len(addresses)} addresses, {len(phones)} phones")
            
            for price, address, phone in zip(prices, addresses, phones):
                price_list.append(price.text.strip())
                address_list.append(address.text.strip())
                phone_list.append(phone.get_attribute('href').replace('tel:', ''))
            for price, address, phone in zip(price_list, address_list, phone_list):
                print(price, " - ", address, " - ", phone)
        
        except Exception as e:
            print(f"Error accessing addresses or data extraction: {e}")
        
        try:
            next_page = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'page-item')]/a[contains(@class, 'page-link')]")))
            driver.execute_script("arguments[0].scrollIntoView();", next_page)
            time.sleep(1)
            next_page.click()
            time.sleep(2)
        except Exception as e:
            print(f"Unable to go to the next page: {e}")
            break
    
    df = pd.DataFrame({
        'Price': price_list,
        'Address': address_list,
        'Phone': phone_list
    })
    
    try:
        with pd.ExcelWriter('rentseekers.xlsx', engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='rentseekers', index=False)
        print("Excel file created successfully.")
    except Exception as e:
        print(f"Error saving to Excel: {e}")
    
    driver.quit()


