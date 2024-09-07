from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException
from selenium_stealth import stealth
import time
import random

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver

def scroll_down(driver, scroll_pause_time=2):
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with the last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Break the loop if no more scrolling possible
        last_height = new_height

def fetch_data(driver, wait, price_list, address_list, phone_list):
    try:
        addresses = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="ListingCardContentSection_addressContainer__1nQm9"]/p')))
        prices = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ListingCardContentSection_longTermPrice__2ub_C.ListingCardContentSection_longTermPriceLargeCard__1RLuX")))
        phone_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@class="buttons_mdButton__3vI2N buttons_linkButton__p6n-G ListingCardCallButton_callBtn__2rorX"]')))

        for price, address, phone_element in zip(prices, addresses, phone_elements):
            price_list.append(price.text.strip())
            address_list.append(address.text.strip())
            phone_list.append(phone_element.get_attribute('href').replace('tel:', ''))  # Extract phone number from href

    except TimeoutException:
        print("Data fetch timeout.")
    except ElementNotInteractableException:
        print("Element not interactable during data fetch.")
    except StaleElementReferenceException:
        print("Stale element reference during data fetch.")

def search_machine(city, max_pages=3):
    url = "https://www.zumper.com/"
    driver = setup_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 30)
    price_list, address_list, phone_list = [], [], []

    try:
        # Wait for the search bar to be visible href="/apartments-for-rent/austin-tx?page=2"
        searchbar = wait.until(EC.visibility_of_element_located((By.ID, "autocomplete-search-input__")))
        driver.execute_script("arguments[0].scrollIntoView();", searchbar)  # Scroll element into view if necessary
        time.sleep(2)  # Adding a small delay to ensure the element is ready

        searchbar.click()
        attempts = 3
        while attempts > 0:
            try:
                searchbar.send_keys(city)
                time.sleep(random.uniform(1, 3))  # Add some delay to mimic human interaction
                searchbar.send_keys(Keys.ENTER)
                break  # If successful, break out of the loop
            except StaleElementReferenceException:
                attempts -= 1
                searchbar = wait.until(EC.visibility_of_element_located((By.ID, "autocomplete-search-input-top-search")))

        # Loop through the pages
        for page_number in range(max_pages):
            print(f"Fetching data from page {page_number + 1}...")

            # Scroll down to load more results
            scroll_down(driver, scroll_pause_time=3)

            # Fetch data from the current page
            fetch_data(driver, wait, price_list, address_list, phone_list)

            # Navigate to the next page if it exists
            try:
                next_page = wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "chakra-button") and contains(@href, "/apartments-for-rent/")]')))
                driver.execute_script("arguments[0].scrollIntoView();", next_page)
                time.sleep(1)  # Wait a bit to ensure it's in view
                driver.execute_script("arguments[0].click();", next_page)
                time.sleep(random.uniform(2, 5))  # Wait for the next page to load
            except TimeoutException:
                print("No more pages to navigate to.")
                break

    except TimeoutException as e:
        print(f"Timeout occurred: {e}")
    except ElementNotInteractableException as e:
        print(f"Element not interactable: {e}")

    finally:
        time.sleep(random.uniform(2, 5))  # Wait to observe results
        driver.quit()  # Ensure the browser is closed

    # Print out the collected data
    for price, address, phone in zip(price_list, address_list, phone_list):
        print(f"{price:<10} | {address:<40} | {phone:<15}")

search_machine("San francisco")
