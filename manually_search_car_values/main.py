from selenium import webdriver
from difflib import SequenceMatcher
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, request, jsonify
import sys
import time 

app = Flask(__name__)

def log_progress(message):
    """Print progress message for frontend tracking."""
    print(message, flush=True)

def find_closest_option(select_element, target_value):
    """
    Finds and selects the best matching option in a dropdown based on the target value.
    Prioritizes options containing the target value as a substring, ignoring placeholder options.
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
        log_progress(f"Comparing '{target_value}' with '{option_text}' - Similarity: {similarity_ratio}")
        if similarity_ratio > best_ratio:
            best_match = option
            best_ratio = similarity_ratio

    if best_match:
        log_progress(f"Best similarity match: '{best_match.text}'")
        best_match.click()
        return best_match.text

    log_progress("No match found.")
    return None

def run_appraisal(vin_var, mileage_var, style_var):
    """Runs the Selenium automation for car appraisal."""
    log_progress("Setting up WebDriver...")
    service = Service(executable_path="./chromedriver")
    driver = webdriver.Chrome(service=service)

    try:
        # Open the target webpage
        log_progress("Opening Edmunds appraisal page...")
        driver.get("https://www.edmunds.com/appraisal/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # VIN Step
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

        # Style Selection
        log_progress("Selecting style...")
        style_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[data-tracking-id='style_select']"))
        )
        find_closest_option(Select(style_select), style_var)

        # Continue
        log_progress("Proceeding with appraisal steps...")
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-id='submit_location_style']"))
        )
        ActionChains(driver).move_to_element(continue_button).click(continue_button).perform()

        # Select colors
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

        # Mileage input
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

        # Handling "No" buttons
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

        # Modal-backdrop handling and extracting final value (retain time.sleep)
        log_progress("Handling modal-backdrop...")
        try:
            modal_backdrop = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal-backdrop"))
            )
            ActionChains(driver).move_to_element(modal_backdrop).click(modal_backdrop).perform()
        except Exception as e:
            log_progress(f"No modal-backdrop found: {e}")

        log_progress("Selecting Private Party option...")
        private_buttons = driver.find_elements(By.CSS_SELECTOR, "button.transaction-type-select-button")
        for button in private_buttons:
            if button.text.strip() == "Private Party":
                ActionChains(driver).move_to_element(button).click(button).perform()
                break
        time.sleep(1)

        log_progress("Extracting final value...")
        table = driver.find_element(By.CSS_SELECTOR, "table.text-gray-darker")
        last_row = table.find_element(By.CSS_SELECTOR, "tbody > tr:last-of-type")
        second_td = last_row.find_elements(By.TAG_NAME, "td")[1]
        value = second_td.text

        log_progress(f"Final Private Party value: {value}")
        return value

    except Exception as e:
        log_progress(f"Error: {e}")
        return str(e)

# Flask route for web app mode
@app.route("/", methods=["POST"])
def index():
    data = request.get_json()
    vin = data["vin"]
    mileage = data["mileage"]
    style = data["style"]

    log_progress(f"Received: VIN={vin}, Mileage={mileage}, Style={style}")
    value = run_appraisal(vin, mileage, style)
    return jsonify({"result": value})

# Main entry point
if __name__ == "__main__":
    if len(sys.argv) > 1:
        vin_var = sys.argv[1]
        mileage_var = sys.argv[2]
        style_var = sys.argv[3]
        log_progress(f"Running in CLI mode with VIN={vin_var}, Mileage={mileage_var}, Style={style_var}")
        result = run_appraisal(vin_var, mileage_var, style_var)
        log_progress(f"Final Result: {result}")
    else:
        app.run(debug=True)
