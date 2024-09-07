import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import random
import pandas as pd
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, ElementNotInteractableException
from queue import Queue

def click_next_page_with_retry(driver, wait, page_number, retries=3):
    for attempt in range(retries):
        try:
            next_page = wait.until(EC.element_to_be_clickable((By.XPATH, f'//nav[@id="paging"]//a[@data-page="{page_number}"]')))
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_page)
            return True
        except TimeoutException as e:
            print(f"TimeoutException on attempt {attempt + 1}: {str(e)}")
        except NoSuchElementException as e:
            print(f"NoSuchElementException on attempt {attempt + 1}: {str(e)}")
        except Exception as e:
            print(f"Exception on attempt {attempt + 1}: {str(e)}")
        time.sleep(2)
    print(f"Failed to navigate to page {page_number} after {retries} attempts")
    return False

def wait_for_page_load(driver, wait, page_number):
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, f'//nav[@id="paging"]//a[@data-page="{page_number}"]')))
    except TimeoutException as e:
        print(f"TimeoutException while waiting for page {page_number} to load: {str(e)}")
    except Exception as e:
        print(f"Exception while waiting for page {page_number} to load: {str(e)}")

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def save_to_excel(data_dict, filename):
    df = pd.DataFrame(data_dict)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)

def scroll_down(driver, scroll_pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
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

def search_zumber(city, output_queue, max_pages=3):
    url = "https://www.zumper.com/"
    driver = setup_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 30)
    price_list, address_list, phone_list = [], [], []

    try:
        searchbar = wait.until(EC.visibility_of_element_located((By.ID, "autocomplete-search-input__")))
        driver.execute_script("arguments[0].scrollIntoView();", searchbar)
        time.sleep(2)
        searchbar.click()
        attempts = 3
        while attempts > 0:
            try:
                searchbar.send_keys(city)
                time.sleep(random.uniform(1, 3))
                searchbar.send_keys(Keys.ENTER)
                break
            except StaleElementReferenceException:
                attempts -= 1
                searchbar = wait.until(EC.visibility_of_element_located((By.ID, "autocomplete-search-input__")))

        for page_number in range(1, max_pages + 1):
            print(f"Fetching data from page {page_number}...")
            scroll_down(driver, scroll_pause_time=3)
            fetch_data(driver, wait, price_list, address_list, phone_list)

            if page_number < max_pages:
                if not click_next_page_with_retry(driver, wait, page_number + 1):
                    break

    except TimeoutException as e:
        print(f"Timeout occurred: {e}")
    except ElementNotInteractableException as e:
        print(f"Element not interactable: {e}")
    finally:
        time.sleep(random.uniform(2, 5))
        driver.quit()

    output_queue.put(([], price_list, address_list, phone_list))

def search_apartments_com(city, output_queue):
    driver = setup_driver()
    url = "https://www.apartments.com/"
    driver.get(url)
    wait = WebDriverWait(driver, 30)

    try:
        time.sleep(random.uniform(2, 5))
        search_bar = wait.until(EC.element_to_be_clickable((By.ID, "quickSearchLookup")))
        search_bar.send_keys(city)

        time.sleep(random.uniform(2, 5))
        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.go.btn.btn-lg.btn-primary")))
        search_button.click()
        time.sleep(random.uniform(2, 5))

        price_list, phones_list, address_list = [], [], []
        i = 1

        while i <= 3:
            try:
                time.sleep(random.uniform(2, 5))

                prices = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "property-pricing")))
                phones = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".phone-link.js-phone.js-student-housing")))
                addresses = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "property-address.js-url")))

                for price, phone, address in zip(prices, phones, addresses):
                    price_list.append(price.text.strip())
                    phones_list.append(phone.text.strip())
                    address_list.append(address.text.strip())

                if i < 3:
                    wait_for_page_load(driver, wait, i + 1)
                    if not click_next_page_with_retry(driver, wait, i + 1):
                        break
                i += 1

            except TimeoutException:
                print("Timeout occurred while fetching data.")
            except NoSuchElementException:
                print("Element not found during data fetch.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    finally:
        driver.quit()

    output_queue.put((price_list, phones_list, address_list))

def main():
    city = "New York"
    output_queue = Queue()

    threads = [
        threading.Thread(target=search_zumber, args=(city, output_queue)),
        threading.Thread(target=search_apartments_com, args=(city, output_queue))
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    zumber_data = output_queue.get()
    apartments_data = output_queue.get()

    save_to_excel({
        "Zumber Prices": zumber_data[1],
        "Zumber Addresses": zumber_data[2],
        "Zumber Phones": zumber_data[3],
        "Apartments.com Prices": apartments_data[0],
        "Apartments.com Phones": apartments_data[1],
        "Apartments.com Addresses": apartments_data[2]
    }, 'apartments_data.xlsx')

if __name__ == "__main__":
    main()
