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
    """Logs progress messages."""
    print(message, flush=True)

def configure_driver():
    """Configures Selenium WebDriver with options."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # Uncomment below for debugging (removes headless mode)
    # chrome_options.add_argument("--headless")
    service = Service(executable_path="./chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def pause_for_debug():
    """Pause to allow manual observation of the browser."""
    input("Paused for debug. Press ENTER to continue...")

def run_mmr_appraisal(driver, vin_var, mileage_var):
    """Fetches MMR and Private Party values from the MMR site."""
    try:
        log_progress(f"Processing VIN: {vin_var} with Mileage: {mileage_var}")

        # VIN Input Field
        vin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "vinText"))
        )
        log_progress(f"VIN input - Enabled: {vin_input.is_enabled()}, Displayed: {vin_input.is_displayed()}")
        vin_input.clear()
        vin_input.send_keys(vin_var)

        # Search Button
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Search VIN']"))
        )
        log_progress(f"Search button - Enabled: {search_button.is_enabled()}, Displayed: {search_button.is_displayed()}") 
        search_button.click()

        # Wait for modal and pause if it appears
        try:
            modal = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles__modalContainer__j5Wbj"))
            )
            if modal:
                log_progress("Modal detected. Please make a selection manually and press ENTER in the terminal to continue...")
                input("Paused for manual selection. Press ENTER when ready to proceed.")
        except Exception:
            log_progress("No modal detected, continuing...")

        # Wait for Odometer input
        mileage_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "form input[type='tel'][id='Odometer']")
            )
        )
        log_progress(f"Odometer input - Enabled: {mileage_input.is_enabled()}, Displayed: {mileage_input.is_displayed()}")

        # Simulate clearing and typing the value
        mileage_input.clear()  # Clear the field explicitly
        ActionChains(driver).click(mileage_input).send_keys(mileage_var).perform()  # Simulate typing the value

        # Press Enter or Tab to confirm the input
        mileage_input.send_keys(Keys.RETURN)  # Alternatively, use Keys.TAB to move to the next element

        # Optionally, wait for the dropdown or region selection to appear before proceeding
        log_progress("Odometer value set and confirmed.")

        time.sleep(1)

        # Handle dropdown for Region selection
        region_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div#Region div.form-group"))
        )
        log_progress(f"Region dropdown - Enabled: {region_dropdown.is_enabled()}, Displayed: {region_dropdown.is_displayed()}")
        region_dropdown.click()

        # Wait for options to appear and click "Northeast"
        northeast_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button/span[text()='Northeast']"))
        )
        log_progress(f"Northeast option - Enabled: {northeast_option.is_enabled()}, Displayed: {northeast_option.is_displayed()}")
        northeast_option.click()

        # Wait for results to load
        time.sleep(2)

        # Fetch MMR value
        mmr_value_element = driver.find_element(By.CSS_SELECTOR, "div.styles__adjustmentsBoxContainer__rcnNc div.styles__currencyContainer__i1LPq div.styles__currency__EkR32")
        mmr_value = mmr_value_element.text.replace("$", "").replace(",", "").strip()
        log_progress(f"Fetched MMR value: {mmr_value}")

        # Fetch Private Party value
        private_party_element = driver.find_element(By.CSS_SELECTOR, "div.styles__estimatedRetailValue__Wkxa3 span.print--hide")
        private_party_value = private_party_element.text.replace("$", "").replace(",", "").strip()
        log_progress(f"Fetched Private Party value: {private_party_value}")

        # Fetch LOW MMR value
        low_mmr_value_element = driver.find_element(By.CSS_SELECTOR, "div.styles__adjustedMMRRange__wGmgR div.styles__adjMMRRangeValue__fOTt5 span.print--hide")
        low_mmr_value = low_mmr_value_element.text.split('-')[0].replace("$", "").replace(",", "").strip()
        log_progress(f"Fetched lowest MMR value: {low_mmr_value}")

        # Check if fetched values are valid
        if mmr_value == "--" or private_party_value == "--":
            raise ValueError("MMR or Private Party value could not be fetched. Ensure the page is loading results.")

        return mmr_value, private_party_value, low_mmr_value

    except Exception as e:
        log_progress(f"Error: {e}")
        return None, None, None

def process_excel(file_path, driver):
    """Processes Excel file and updates it with MMR and Private Party values."""
    try:
        df = pd.read_excel(file_path)
        # Drop rows where VIN or Odometer is missing
        df = df.dropna(subset=["VIN", "Odometer"]).reset_index(drop=True)
    except Exception as e:
        log_progress(f"Error reading Excel file: {e}")
        return

    total_rows = len(df)
    log_progress(f"Total valid rows to process: {total_rows}")

    try:
        for index, row in df.iterrows():
            vin = str(row["VIN"])
            mileage = str(row["Odometer"])

            mmr, private_party, low_mmr = run_mmr_appraisal(driver, vin, mileage)
            if mmr is not None and private_party is not None:
                df.at[index, "MMR"] = mmr
                df.at[index, "MSRP"] = private_party
                df.at[index, "MMR LOW"] = low_mmr


            log_progress(f"Processed {index + 1}/{total_rows}")
    finally:
        driver.quit()

    # Save updated Excel file
    output_path = file_path.replace(".xlsx", "_updated.xlsx")
    df.to_excel(output_path, index=False)
    log_progress(f"Updated Excel saved to: {output_path}")

if __name__ == "__main__":
    input_file = "./test-watchlist.xlsx"
    
    # Configure WebDriver
    driver = configure_driver()

    # Manual login and processing
    driver.get("https://mmr.manheim.com/ui-mmr/?country=US&popup=true")
    log_progress("Please log in manually in the browser. Once logged in, press ENTER to continue...")
    input("Waiting for manual login. Press ENTER when you're ready to proceed.")

    process_excel(input_file, driver)