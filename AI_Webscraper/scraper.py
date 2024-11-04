import pandas as pd
import re
import time
import json
import os
import openai
import random
from urllib.parse import urlparse
from dotenv import load_dotenv
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup 
from typing import  Union ,List, Dict,Type,Tuple
from datetime import datetime
import html2text
from pydantic import BaseModel, Field, create_model , ValidationError

user_message = f"Extract the following information from the provided text:\nPage content:\n\n"

original_system_message = (
    "You are an AI web scraper assistant. Your task is to analyze the provided context "
    "extracted from a web page and respond to the user's inquiry based on that context. "
    "Focus on providing accurate, concise, and relevant information. If the context contains "
    "specific details or data, summarize them clearly. If the context lacks sufficient information "
    "to answer the user's question, indicate that more data is needed."
)

load_dotenv()

def selenium_setup():
    options = Options()
    #options.timeouts = {'pageLoad': 5000}
    service=Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options) 
    return driver
def webscrape(url):
   
    driver = selenium_setup()
    try:
        driver.get(url)
        time.sleep(1)
        html = driver.page_source
        return html
        
    finally:
        driver.quit()
    
    
def parse_html(html_content):
    soup = BeautifulSoup(html_content,'html.parser')
    return str(soup)
    

def clicking_acceptcookies(driver):

    try:
        WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button | //a | //div")))

        text_accept = [
                "continue", "I agree","got it", "accept", "agree", "allow"
            ]
        for tag in ["button", "a", "div"]:
            for text in text_accept:
                try:
                    element = driver.find_element(By.XPATH, f"//{tag}[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                    if element:
                            element.click()
                            print(f"Clicked the '{text}' button.")
                            return
                except:
                        continue
        
    except Exception as e:
        print(f"error finding the button: {e}")


def markdown_converter(html_content):
    parsed_html = parse_html(html_content)
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    markdown_content = markdown_converter.handle(parsed_html)
    return markdown_content

def scrape_titles_content(url):
    driver  =  selenium_setup(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    titles_content = {}
    for title in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        content = []
        for sibling in title.find_next_siblings():
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break
            if sibling.text.strip():
                content.append(sibling.text.strip())
                
        titles_content[title.get_text(strip=True)] = ' '.join(content)
        
    return titles_content
def store_data(raw_data: str, output_folder: str, file_name: str):
    os.makedirs(output_folder, exist_ok=True)
    raw_output_path = os.path.join(output_folder, file_name)
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
    print(f"Raw data saved to {raw_output_path}")
    return raw_output_path
# dynamically creating a pydantisavec model
def create_dynamic_listing_model(field_names: List[str]) -> Type[BaseModel]:
    field_definitions = {field: (str, ...) for field in field_names}
    return create_model('DynamicListingModel', **field_definitions)
        
def create_listings_container_model(listing_model: Type[BaseModel]) -> Type[BaseModel]:

    return create_model('DynamicListingsContainer', listings=(List[listing_model], ...))


def create_folder_name(url):
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    try:
        url_name = urlparse(url).netloc#suggested by gpt
    except IndexError:
        raise ValueError("Invalid URL format.")
    return f"{url_name}_{timestamp}"


def generate_system_message(listing_model: BaseModel) -> str:
    schema_info = listing_model.model_json_schema()
    field_descriptions = []
    for field_name, field_info in schema_info["properties"].items():
        field_type = field_info["type"]
        field_descriptions.append(f'"{field_name}": "{field_type}"')
    schema_structure = ",\n".join(field_descriptions)

    # Generate the system message dynamically
    system_message = f"""
    You are an intelligent text extraction and conversion assistant. Your task is to extract structured information 
                        from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text, 
                        with no additional commentary, explanations, or extraneous information. 
                        You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                        Please process the following text and provide the output in pure JSON format with no words before or after the JSON:
    Please ensure the output strictly follows this schema:

    {{
        "listings": [
            {{
                {schema_structure}
            }}
        ]
    }} """

    return system_message
def format_data(data, DynamicListingsContainer, DynamicListingModel):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature= 0.5,
            messages=[
                {"role": "system", "content":original_system_message},
                {"role": "user", "content": user_message + data},
            ],
            response_format = DynamicListingsContainer
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"An error occurred: {e}")


#**below function is  generated by gpt**
def save_formatted_data(formatted_data, output_folder: str, json_file_name: str, excel_file_name: str):
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Parse the formatted data if it's a JSON string
    if isinstance(formatted_data, str):
        try:
            formatted_data_dict = json.loads(formatted_data)
        except json.JSONDecodeError:
            raise ValueError("The provided formatted data is a string but not valid JSON.")
    else:
        # Assume it's a dictionary-like object from a parsed response
        formatted_data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data

    # Save the formatted data as JSON
    json_output_path = os.path.join(output_folder, json_file_name)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data_dict, f, indent=4)
    print(f"Formatted data saved to JSON at {json_output_path}")

    # Prepare data for DataFrame
    if isinstance(formatted_data_dict, dict):
        # If the dictionary has a single key containing a list of records, use that list
        data_for_df = next(iter(formatted_data_dict.values())) if len(formatted_data_dict) == 1  else formatted_data_dict
    elif isinstance(formatted_data_dict, list):
        data_for_df = formatted_data_dict
    else:
        raise ValueError("Formatted data is neither a dictionary nor a list, cannot convert to DataFrame")

    # Create DataFrame
    try:
        df = pd.DataFrame(data_for_df)
        print("DataFrame created successfully.")

        # Save the DataFrame to an Excel file
        excel_output_path = os.path.join(output_folder, excel_file_name)
        df.to_excel(excel_output_path, index=False)
        print(f"Formatted data saved to Excel at {excel_output_path}")
        
        return df
    except Exception as e:
        print(f"Error creating DataFrame or saving Excel: {str(e)}")
        return None

def scrape_multiple_urls(urls, fields):
    output_folder = os.path.join('output', create_folder_name(urls[0]))
    os.makedirs(output_folder, exist_ok=True)
    
    all_data = []
    markdown = None
    for i, url in enumerate(urls, start=1):
        raw_html = webscrape(url)
        current_markdown = markdown_converter(raw_html)
        if i == 1:
            markdown =current_markdown  
        formatted_data = scrape_url(url, fields, output_folder, i, current_markdown)
        all_data.append(formatted_data)
    
    return output_folder, all_data, markdown


def scrape_url(url: str, fields: List[str],  output_folder: str, file_number: int, markdown: str):
    try:
        # Save raw data in Markdown format
        store_data(markdown, output_folder, f'rawData_{file_number}.md')
        DynamicListingModel = create_dynamic_listing_model(fields)
        DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
        formatted_data = format_data(markdown, DynamicListingsContainer, DynamicListingModel)
        save_formatted_data(formatted_data, output_folder, f'sorted_data_{file_number}.json', f'sorted_data_{file_number}.xlsx')
        return formatted_data

    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return None



