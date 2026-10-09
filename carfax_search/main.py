import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def log_progress(message):
    print(message, flush=True)

def configure_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # Uncomment for debugging (removes headless mode)
    # chrome_options.add_argument("--headless")
    service = Service(executable_path="./chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def process_carfax(driver, vin, mileage):
    try:
        log_progress(f"Processing VIN: {vin} with Mileage: {mileage}")

        # Enter VIN
        vin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "vin"))
        )
        vin_input.clear()
        vin_input.send_keys(vin)
        
        # Check "I own this car"
        owner_checkbox = driver.find_element(By.CSS_SELECTOR, "label.checkbox-input input")
        driver.execute_script("arguments[0].click();", owner_checkbox)

        # Click "Get CARFAX Value"
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-theme='blue']"))
        )
        submit_button.click()
        
        time.sleep(1)  # Allow page to load

        # Enter Odometer
        odometer_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "odometer"))
        )
        odometer_input.clear()
        odometer_input.send_keys(mileage)
        
        time.sleep(1)  # Allow processing

        # Extract Private Party Value
        private_party_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.pricesStyle_results__prices__list-item__price__LxsIf span"))
        )
        private_party_value = private_party_element.text.replace("$", "").replace(",", "").strip()
        log_progress(f"Private Party Value: {private_party_value}")
        return private_party_value

    except Exception as e:
        log_progress(f"Error processing VIN {vin}: {e}")
        return None

def process_excel(file_path, driver):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=["VIN", "Odometer"]).reset_index(drop=True)
    except Exception as e:
        log_progress(f"Error reading Excel file: {e}")
        return

    total_rows = len(df)
    log_progress(f"Total valid rows to process: {total_rows}")

    try:
        driver.get("https://www.carfax.com/value/")
        
        log_progress("Please log in manually. Once logged in, press ENTER in the console to continue...")
        input("Waiting for manual login. Press ENTER when ready to proceed.")
        
        # Enter ZIP code
        zip_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "zip"))
        )
        zip_input.clear()
        zip_input.send_keys("08857")
        zip_input.send_keys(Keys.RETURN)
        
        for index, row in df.iterrows():
            vin = str(row["VIN"])
            mileage = str(row["Odometer"])
            
            private_party_value = process_carfax(driver, vin, mileage)
            if private_party_value:
                df.at[index, "MSRP"] = private_party_value
                
            if index < total_rows - 1:
                # Click "Change Car"
                change_car_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.vehicleIdCardStyle_vehicle-id-card__button__eqPj_"))
                )
                change_car_button.click()
                time.sleep(1)

    finally:
        driver.quit()

    output_path = file_path.replace(".xlsx", "_updated.xlsx")
    df.to_excel(output_path, index=False)
    log_progress(f"Updated Excel saved to: {output_path}")

if __name__ == "__main__":
    input_file = "./test-test.xlsx"
    driver = configure_driver()
    process_excel(input_file, driver)
