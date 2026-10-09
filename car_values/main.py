import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from difflib import SequenceMatcher

def log_progress(message):
    """Print progress message for logging."""
    print(message, flush=True)

def find_closest_option(select_element, target_value):
    """
    Finds and selects the best matching option in a dropdown based on the target value.
    """
    target_value = target_value.strip().lower()
    best_match = None
    best_ratio = 0

    for option in select_element.options:
        option_text = option.text.strip().lower()
        if "select" in option_text:
            continue
        if target_value in option_text:
            log_progress(f"Exact substring match found: '{option.text}'")
            option.click()
            return option.text
        similarity_ratio = SequenceMatcher(None, target_value, option_text).ratio()
        if similarity_ratio > best_ratio:
            best_match = option
            best_ratio = similarity_ratio

    if best_match:
        log_progress(f"Best similarity match: '{best_match.text}'") 
        best_match.click()
        return best_match.text
    log_progress("No match found.")
    return None

def configure_driver():
    """Configures the Selenium WebDriver to block images, videos, and CSS."""
    chrome_options = webdriver.ChromeOptions()

    # Disable loading of images, videos, and CSS
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.plugins": 2,  # Blocks videos and plugins
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(executable_path="./chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def run_appraisal(driver, vin_var, mileage_var, style_var):
    """Runs the Selenium automation for car appraisal."""
    try:
        log_progress(f"Opening Edmunds appraisal page for VIN: {vin_var}")
        driver.get("https://www.edmunds.com/appraisal/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        log_progress("Entering VIN...")
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='tab-VIN']"))
        )
        ActionChains(driver).move_to_element(button).click(button).perform()

        vin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='vin-number']"))
        )
        vin_input.clear()
        vin_input.send_keys(vin_var)

        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='appraise-btn-by-vin']"))
        )
        ActionChains(driver).move_to_element(submit_button).click(submit_button).perform()

        log_progress("Selecting style...")
        style_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[data-tracking-id='style_select']"))
        )
        find_closest_option(Select(style_select), style_var)

        log_progress("Proceeding with appraisal steps...")
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-id='submit_location_style']"))
        )
        ActionChains(driver).move_to_element(continue_button).click(continue_button).perform()

        log_progress("Selecting exterior and interior colors...")
        exterior_color = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.colors-section.exteriorColor .color-item"))
        )
        ActionChains(driver).move_to_element(exterior_color).click(exterior_color).perform()

        interior_color = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.colors-section:not(.exteriorColor) .color-item"))
        )
        ActionChains(driver).move_to_element(interior_color).click(interior_color).perform()

        colors_continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-id='submit_colors_options']"))
        )
        ActionChains(driver).move_to_element(colors_continue_button).click(colors_continue_button).perform()

        log_progress("Entering mileage...")
        mileage_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#mileage"))
        )
        mileage_input.clear()
        mileage_input.send_keys(mileage_var)

        mileage_continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-id='submit_condition_mileage']"))
        )
        ActionChains(driver).move_to_element(mileage_continue_button).click(mileage_continue_button).perform()

        log_progress("Answering condition questions...")
        questions_sections = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.questions-section"))
        )
        for section in questions_sections:
            child_divs = section.find_elements(By.CSS_SELECTOR, "div[tabindex='-1']")
            for child in child_divs:
                try:
                    first_label = child.find_element(By.CSS_SELECTOR, "div.radio-group-wrapper label")
                    ActionChains(driver).move_to_element(first_label).click(first_label).perform()
                except Exception as e:
                    log_progress(f"Error clicking label: {e}")
        try:
            continue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#cta-offer-conditions-step"))
            )
            ActionChains(driver).move_to_element(continue_button).click(continue_button).perform()
            log_progress("Clicked Continue button after questions.")
        except Exception as e:
            log_progress(f"Failed to click Continue button after questions: {e}")

        # log_progress("Handling modal-backdrop...")
        # try:
        #     modal_backdrop = WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal-backdrop"))
        #     )
        #     ActionChains(driver).move_to_element(modal_backdrop).click(modal_backdrop).perform()
        # except Exception as e:
        #     log_progress(f"No modal-backdrop found: {e}")

        # log_progress("Selecting Private Party option...")
        # private_buttons = driver.find_elements(By.CSS_SELECTOR, "button.transaction-type-select-button")
        # for button in private_buttons:
        #     if button.text.strip() == "Private Party":
        #         ActionChains(driver).move_to_element(button).click(button).perform()
        #         break

        log_progress("Handling modal-backdrop...")
        try:
            modal_backdrop = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal-backdrop"))
            )
            ActionChains(driver).move_to_element(modal_backdrop).click(modal_backdrop).perform()
        except Exception as e:
            log_progress(f"No modal-backdrop found: {e}")
        # time.sleep(1)
        # Check if the "Edmunds Appraisal Report" button exists and click it
        log_progress("Checking for Edmunds Appraisal Report button...")
        try:
            appraisal_report_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "APPRAISAL_REPORT_TAB_ID"))
            )
            log_progress("Edmunds Appraisal Report button found. Clicking...")
            ActionChains(driver).move_to_element(appraisal_report_button).click(appraisal_report_button).perform()
        except Exception as e:
            log_progress("Edmunds Appraisal Report button not found, skipping...")
        # time.sleep(1)

        log_progress("Selecting Private Party option...")
        private_buttons = driver.find_elements(By.CSS_SELECTOR, "button.transaction-type-select-button")
        for button in private_buttons:
            if button.text.strip() == "Private Party":
                ActionChains(driver).move_to_element(button).click(button).perform()
                break




        log_progress("Extracting final value...")
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.text-gray-darker"))
        )
        last_row = table.find_element(By.CSS_SELECTOR, "tbody > tr:last-of-type")
        first_td = last_row.find_elements(By.TAG_NAME, "td")[0]
        second_td = last_row.find_elements(By.TAG_NAME, "td")[1]

        def clean_and_convert(value):
            try:
                # Remove dollar sign and commas, then convert to float
                return float(value.replace('$', '').replace(',', ''))
            except ValueError:
                print(f"Error: Unable to convert '{value}' to float.")
                return 0.0  # Default value in case of conversion error

        # Clean and convert the text to float
        first_value = clean_and_convert(first_td.text)
        second_value = clean_and_convert(second_td.text)

        average = (first_value + second_value) / 2
        # value = average
        value = second_value


        # log_progress(f"first value: {first_value}")
        # log_progress(f"second value: {second_value}")

        log_progress(f"Final Private Party value: {value}")
        return value

    except Exception as e:
        log_progress(f"Error: {e}")
        return str(e)

def process_excel(file_path):
    """Processes the Excel file row by row."""
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        log_progress(f"Error reading Excel file: {e}")
        return

    total_rows = len(df)
    log_progress(f"Total rows to process: {total_rows}")

    driver = configure_driver()

    try:
        for index, row in df.iterrows():
            vin = row["VIN"]
            style = row["Series"]
            mileage = row["Odometer"]
            msrp = run_appraisal(driver, vin, mileage, style)
            df.at[index, "MSRP"] = msrp
            log_progress(f"Processed {index + 1}/{total_rows}")
    finally:
        driver.quit()

    output_path = file_path.replace(".xlsx", "_updated.xlsx")
    df.to_excel(output_path, index=False)
    log_progress("Excel file updated successfully.")
    return output_path

if __name__ == "__main__":
    excel_file = "./test-watchlist.xlsx"
    process_excel(excel_file)
