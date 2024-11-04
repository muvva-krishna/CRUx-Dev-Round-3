import cv2
import json 
import os
import time
import numpy as np
import difflib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from image_capture import capture_and_extract_text
from llm import summarize_text
from dotenv import load_dotenv
print("hello summary")
load_dotenv()

chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

def initialize_driver():
    """Initializes and returns the Chrome WebDriver."""
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver

def login(driver):
    driver.get("https://a.impartus.com/login/#/")
    wait = WebDriverWait(driver, 40)
    username = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password = wait.until(EC.presence_of_element_located((By.ID, "password")))
    username.send_keys(os.environ.get("IMPARTUS_USERNAME"))
    password.send_keys(os.environ.get("IMPARTUS_PASSWORD"))
    login_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "iu-btn")))
    login_btn.click()

def inject_js(driver):
    """Injects the summary display div with a close button into the video page."""
    driver.execute_script("""
        if (!document.getElementById('summaryDiv')) {
            let summaryDiv = document.createElement('div');
            summaryDiv.id = 'summaryDiv';
            summaryDiv.style.position = 'fixed';
            summaryDiv.style.left = '0';
            summaryDiv.style.top = '0';
            summaryDiv.style.width = '50vh';
            summaryDiv.style.height = '80vh';
            summaryDiv.style.padding = '10px';
            summaryDiv.style.backgroundColor = '#f0f0f0';
            summaryDiv.style.zIndex = '1000';
            summaryDiv.style.overflowY = 'auto';
            summaryDiv.innerHTML = '<h3>Summaries</h3>';

            let closeButton = document.createElement('span');
            closeButton.innerText = '✖';
            closeButton.style.position = 'absolute';
            closeButton.style.top = '5px';
            closeButton.style.right = '10px';
            closeButton.style.cursor = 'pointer';
            closeButton.style.fontSize = '18px';
            closeButton.style.fontWeight = 'bold';
            closeButton.onclick = function() {
                summaryDiv.remove();
            };
            summaryDiv.appendChild(closeButton);

            document.body.appendChild(summaryDiv);
        }
    """)

def remove_js(driver):
    """Removes the summary display div from the page."""
    driver.execute_script("""
        let summaryDiv = document.getElementById('summaryDiv');
        if (summaryDiv) {
            summaryDiv.remove();
        }
    """)


def main():
    previous_text = ""
    SIMILARITY_THRESHOLD = 0.7
    target_url_pattern = "https://a.impartus.com/ilc/#/video/id/"

    try:
        driver = initialize_driver()
        login(driver)
        video_page = False
        with open("summaries.txt", "a", encoding="utf-8") as summary_file:
            while True:
                if target_url_pattern in driver.current_url:
                    if not video_page:
                        print("Video page detected. Activating frame capture and injecting JS...")
                        inject_js(driver)
                        video_page = True
                    for text in capture_and_extract_text(driver, interval=40):
                        if text:
                            similarity = difflib.SequenceMatcher(None, text, previous_text).ratio()
                            if similarity < SIMILARITY_THRESHOLD:
                                summary = summarize_text(text)
                                if summary:
                                    print("Summary:", summary)
                                    summary_file.write(f"Summary:\n{summary}\n\n")
                                    summary_file.flush()
                                    previous_text = text
                                    # Properly serialize the summary for JavaScript
                                    driver.execute_script(f"""
                                        let summaryDiv = document.getElementById('summaryDiv');
                                        let newSummary = document.createElement('p');
                                        newSummary.innerText = {json.dumps(summary)};  // Serialize the summary
                                        summaryDiv.appendChild(newSummary);
                                    """)
                                    if target_url_pattern not in driver.current_url:
                                        remove_js(driver)
                else:
                    if video_page:
                        print("Exited video page. Removing injected JS...")
                        remove_js(driver)
                        video_page = False
                time.sleep(10 if not video_page else 5)

    except Exception as e:
        print(f"Error occurred: {e}. Restarting driver.")
        driver.quit()
        time.sleep(5) 

if __name__ == "__main__":
    main()
