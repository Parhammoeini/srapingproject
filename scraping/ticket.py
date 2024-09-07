from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException
import time
import random
import pandas as pd
import openpyxl
from .rentseekers import rentseekers as rs



def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scroll_down(driver, scroll_pause_time=2, scroll_increment=500):
    """
    Scroll down the page gradually to simulate human-like scrolling.
    :param driver: The Selenium WebDriver instance
    :param scroll_pause_time: Time to wait after each scroll
    :param scroll_increment: Number of pixels to scroll down in each increment
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        # Scroll down by a certain increment
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(scroll_pause_time)  # Wait to let the new content load
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Break the loop if the page height doesn't change
        if new_height == last_height:
            break
        
        last_height = new_height

def fetch_rentseeker_data(driver,wait,max_pages=2):
    price_list = []
    address_list = []
    phone_list = []
    for attemp in range(max_pages):
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
    return price_list,address_list,phone_list

def fetch_zumper_data(driver, wait, max_pages=4):
    price_list, address_list, phone_list = [], [], []

    for page in range(max_pages):
        # Wait for elements to be present on the page
        try:
            addresses = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="ListingCardContentSection_addressContainer__1nQm9"]/p')))
            prices = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ListingCardContentSection_longTermPrice__2ub_C.ListingCardContentSection_longTermPriceLargeCard__1RLuX")))
            phone_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@class="buttons_mdButton__3vI2N buttons_linkButton__p6n-G ListingCardCallButton_callBtn__2rorX"]')))
            
            for price, address, phone_element in zip(prices, addresses, phone_elements):
                price_list.append(price.text.strip())
                address_list.append(address.text.strip())
                phone_list.append(phone_element.get_attribute('href').replace('tel:', ''))

            # Find and scroll to the "Next" button, then click
            for attempt in range(3):  # Retry up to 3 times
                try:
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, f'//a[contains(@class, "chakra-button css-1ta7ioi e1k4it830") and contains(@href, "page={page}")]')))
                    element.click()
                    break  # Exit loop if click is successful
                except ElementClickInterceptedException:
                    time.sleep(1)  # Wait a bit before retrying

        except (TimeoutException, NoSuchElementException):
            print(f"Encountered an issue on page {page + 1}.")
            break

    return price_list, address_list, phone_list

def fetch_apartments_data(driver, wait, max_pages=4):
    price_list, beds_list, phones_list, address_list = [], [], [], []

    for page in range(max_pages):
        try:
            # Ensure all elements are loaded
            prices = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "property-pricing")))
            beds = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "property-beds")))
            phones = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".phone-link.js-phone.js-student-housing")))
            addresses = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "property-address.js-url")))

            # Extract text from the elements
            for price, bed, phone, address in zip(prices, beds, phones, addresses):
                price_list.append(price.text.strip())
                beds_list.append(bed.text.strip() if bed.text.strip() else "Not Available")
                phones_list.append(phone.text.strip())
                address_list.append(address.text.strip())

            # Find and interact with the "Next" button
            
            for attempt in range(3):  # Retry up to 3 times
                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, f'//nav[@id="paging"]//a[@data-page="{page+1}"]//span[@class="pagingBtn"]')))
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)  # Ensure the button is scrolled into view
                    next_button.click()
                    time.sleep(random.uniform(2, 5))  # Wait for the next page to load
                    break  # Exit loop if click is successful
                except ElementClickInterceptedException:
                    # If click intercepted, try again after a short delay
                    print("Element click intercepted, retrying...")
                    time.sleep(1)
                except TimeoutException:
                    print("Timeout while trying to find the next button.")
                    break  # Exit loop if button cannot be found
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Encountered an issue on page {page + 1}: {str(e)}")
            break

    return price_list, beds_list, phones_list, address_list
def search_city(city, country):
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)

    prices_zumper, addresses_zumper, phones_zumper = [], [], []
    price_apartments, beds_apartments, phones_apartments, addresses_apartments = [], [], [], []
    prices_seeker, addresses_seeker, phone_seekers = [], [], []

    try:
        if country == "Canada":
            # Rentseeker scraping
            url = "https://www.rentseeker.ca/"
            driver.get(url)
            searchbar = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "pac-target-input")))
            driver.execute_script("arguments[0].scrollIntoView();", searchbar)
            searchbar.send_keys(city)
            searchbar.send_keys(Keys.ARROW_DOWN)
            searchbar.send_keys(Keys.ENTER)
            time.sleep(10)
            prices_seeker, addresses_seeker, phone_seekers = fetch_rentseeker_data(driver, wait)

            # Zumper scraping
            zumper_url = "https://www.zumper.com/"
            driver.get(zumper_url)
            searchbar = wait.until(EC.visibility_of_element_located((By.ID, "autocomplete-search-input__")))
            searchbar.send_keys(city)
            time.sleep(random.uniform(1, 3))
            searchbar.send_keys(Keys.ENTER)
            time.sleep(random.uniform(2, 5))
            scroll_down(driver, scroll_pause_time=3)
            prices_zumper, addresses_zumper, phones_zumper = fetch_zumper_data(driver, wait)

            # Apartments.com scraping
            apartments_url = "https://www.apartments.com/"
            driver.get(apartments_url)
            search_bar = wait.until(EC.element_to_be_clickable((By.ID, "quickSearchLookup")))
            search_bar.send_keys(city)
            time.sleep(random.uniform(2, 5))
            search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.go.btn.btn-lg.btn-primary")))
            search_button.click()
            time.sleep(random.uniform(2, 5))
            price_apartments, beds_apartments, phones_apartments, addresses_apartments = fetch_apartments_data(driver, wait)

        elif country == "USA":
            # Zumper scraping
            zumper_url = "https://www.zumper.com/"
            driver.get(zumper_url)
            searchbar = wait.until(EC.visibility_of_element_located((By.ID, "autocomplete-search-input__")))
            searchbar.send_keys(city)
            time.sleep(random.uniform(1, 3))
            searchbar.send_keys(Keys.ENTER)
            time.sleep(random.uniform(2, 5))
            scroll_down(driver, scroll_pause_time=3)
            prices_zumper, addresses_zumper, phones_zumper = fetch_zumper_data(driver, wait)

            # Apartments.com scraping
            apartments_url = "https://www.apartments.com/"
            driver.get(apartments_url)
            search_bar = wait.until(EC.element_to_be_clickable((By.ID, "quickSearchLookup")))
            search_bar.send_keys(city)
            time.sleep(random.uniform(2, 5))
            search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.go.btn.btn-lg.btn-primary")))
            search_button.click()
            time.sleep(random.uniform(2, 5))
            price_apartments, beds_apartments, phones_apartments, addresses_apartments = fetch_apartments_data(driver, wait)

    finally:
        driver.quit()

    # Prepare data for Excel
    if country == "Canada":
        data_apartment = {
            "Address": addresses_apartments,
            "Price": price_apartments,
            "Beds": beds_apartments,
            "Phone Number": phones_apartments
        }
        data_zumper = {
            "Address": addresses_zumper,
            "Price": prices_zumper,
            "Phone Number": phones_zumper
        }
        data_rentseekers = {
            "Address": addresses_seeker,
            "Price": prices_seeker,
            "Phone Number": phone_seekers
        }
        df1 = pd.DataFrame(data_apartment)
        df2 = pd.DataFrame(data_zumper)
        df3 = pd.DataFrame(data_rentseekers)

        with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='Apartments', index=False)
            df2.to_excel(writer, sheet_name='Zumper', index=False)
            df3.to_excel(writer, sheet_name='Rentseekers', index=False)

        return (prices_zumper, addresses_zumper, phones_zumper), (price_apartments, beds_apartments, phones_apartments, addresses_apartments), (prices_seeker, addresses_seeker, phone_seekers)

    elif country == "USA":
        data_apartment = {
            "Address": addresses_apartments,
            "Price": price_apartments,
            "Beds": beds_apartments,
            "Phone Number": phones_apartments
        }
        data_zumper = {
            "Address": addresses_zumper,
            "Price": prices_zumper,
            "Phone Number": phones_zumper
        }
        df1 = pd.DataFrame(data_apartment)
        df2 = pd.DataFrame(data_zumper)

        with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='Apartments', index=False)
            df2.to_excel(writer, sheet_name='Zumper', index=False)

        return (prices_zumper, addresses_zumper, phones_zumper), (price_apartments, beds_apartments, phones_apartments, addresses_apartments)