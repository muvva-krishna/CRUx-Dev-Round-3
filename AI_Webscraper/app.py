import os
import pandas as pd
import json
import re
import streamlit as st
from urllib.parse import urlparse
from streamlit_tags import st_tags
from scraper import selenium_setup, parse_html,scrape_url,scrape_multiple_urls,webscrape,clicking_acceptcookies,scrape_titles_content,markdown_converter,create_dynamic_listing_model,create_listings_container_model,store_data,create_folder_name,format_data,save_formatted_data
from pydantic import BaseModel
from pagination import PaginationData,detect_pagination
from datetime import datetime
def serialize_pydantic(obj):
    if isinstance(obj, BaseModel):
        return obj.dict()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

# Initialize the Streamlit app
st.title("AI-Powered Web Scraper")

# Input fields
url = st.text_input("Enter the URL:")
show_tags = st.toggle("Enable Scraping")
tags=[]

tags = st_tags(
    label='Enter tags to extract',
    value=[],
    maxtags=-1,
    key='tag_input'
)
pagination = st.checkbox("Enable pagination")
pagination_details = None
#initialize session state variables
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'perform_scrape' not in st.session_state:
    st.session_state['perform_scrape'] = False




#**below function is suggested by GPT
def generate_folder(url):
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    parsed_url = urlparse(url)
    # Extract the domain name from the URL
    domain = parsed_url.netloc or parsed_url.path.split('/')[0]
    # Remove 'www.' if present
    domain = re.sub(r'^www\.', '', domain)
    # Remove any non-alphanumeric characters and replace with underscores
    clean_domain = re.sub(r'\W+', '_', domain)
    return f"{clean_domain}_{timestamp}"

def scrape_multiple_urls(urls, fields):
    output_folder = os.path.join('output', create_folder_name(urls[0]))
    os.makedirs(output_folder, exist_ok=True)
    
    all_data = []
    first_url_markdown = None
    for i, url in enumerate(urls, start=1):
        raw_html = webscrape(url)
        markdown = markdown_converter(raw_html)
        if i == 1:
            first_url_markdown = markdown  
        formatted_data = scrape_url(url, fields, output_folder, i, markdown)
        all_data.append(formatted_data)
    
    return output_folder, all_data, first_url_markdown


def perform_scrape():
    # Generate timestamp for file naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Step 1: Get raw HTML content and convert to markdown
    raw_html = webscrape(url)
    markdown = markdown_converter(raw_html)
    store_data(markdown, timestamp)
    
    pagination_info = None #checking for pagination
    if pagination:
        pagination_data = detect_pagination(url, pagination_details,markdown)
        pagination_info = {
            "pagination_urls": pagination_data.page_urls,
        }
    
    # Step 3: Data extraction and formatting based on provided tags
    formatted_output = None
    df = None
    if show_tags:
        # Create dynamic models for data structuring
        ListingSchema = create_dynamic_listing_model(tags)
        ListingsContainer = create_listings_container_model(ListingSchema)
        
        # Format markdown data using the listing models
        formatted_data = format_data(markdown, ListingsContainer, ListingSchema)
        
        # Save structured data in JSON and Excel formats
        df = save_formatted_data(formatted_data, timestamp)
    else:
        formatted_data = None
        df = None

    return df, formatted_data,markdown, timestamp, pagination_info

if st.button("Scrape"):
    with st.spinner('Please wait... Data is being scraped.'):
        urls = url.split()
        field_list = tags
        output_folder, all_data, first_url_markdown = scrape_multiple_urls(urls, field_list)
        pagination_info = None
        if pagination and len(urls) == 1:#only a single url should be provided
            try:
                pagination_result = detect_pagination(urls[0], pagination_details, first_url_markdown)
                
                if pagination_result is not None:
                    pagination_data = pagination_result
                    
                    # Check if pagination_data is a PaginationData object or dictionary
                    if isinstance(pagination_data, PaginationData):
                        page_urls = pagination_data.page_urls
                    elif isinstance(pagination_data, dict):
                        page_urls = pagination_data.get("page_urls", [])
                    else:
                        page_urls = []
                    
                    pagination_info = {
                        "page_urls": page_urls
                    }
                else:
                    st.warning("No pagination information available.")
            except Exception as e:
                st.error(f"An error occurred during pagination detection: {e}")
                pagination_info = {
                    "page_urls": []
                }
        
        # Store results in session state
        st.session_state['results'] = (all_data, None, first_url_markdown, output_folder, pagination_info)
        st.session_state['perform_scrape'] = True

if st.session_state['results']:
    all_data, _, _, output_folder, pagination_info = st.session_state['results']
    if all_data and show_tags:
        st.subheader("Scraped Data")
        for i, data in enumerate(all_data, start=1):
            st.write(f"Data from URL {i}:")
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    st.error(f"Failed to parse data as JSON for URL {i}")
                    continue
            
            if isinstance(data, dict):
                if 'listings' in data and isinstance(data['listings'], list):
                    df = pd.DataFrame(data['listings'])
                else:
                    df = pd.DataFrame([data]) #use the entire dict if listings is not in the dict
            elif hasattr(data, 'listings') and isinstance(data.listings, list):
                listings = [item.dict() for item in data.listings]
                df = pd.DataFrame(listings)
            else:
                st.error(f"Unexpected data format for URL {i}")
                continue
            
            # display the dataframe
            st.dataframe(df, use_container_width=True)

        #download options
        st.subheader("Download Options")
        col1, col2 = st.columns(2)
        with col1:
            json_data = json.dumps(all_data, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o), indent=4)
            st.download_button(
                "Download JSON",
                data=json_data,
                file_name="scraped_data.json"
            )
        with col2:
            # Convert all data to a single DataFrame
            all_listings = []
            for data in all_data:
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                if isinstance(data, dict) and 'listings' in data:
                    all_listings.extend(data['listings'])
                elif hasattr(data, 'listings'):
                    all_listings.extend([item.dict() for item in data.listings])
                else:
                    all_listings.append(data)
            
            combined_df = pd.DataFrame(all_listings)
            st.download_button(
                "Download CSV",
                data=combined_df.to_csv(index=False),
                file_name="scraped_data.csv"
            )

        st.success(f"Scraping completed. Results saved in {output_folder}")

    if pagination_info and pagination:
        st.markdown(f"Number of Page URLs: {len(pagination_info['page_urls'])}")
        
        st.subheader("Pagination Information")
        pagination_df = pd.DataFrame(pagination_info["page_urls"], columns=["Page URLs"])
        
        st.dataframe(
            pagination_df,
            column_config={
                "Page URLs": st.column_config.LinkColumn("Page URLs")
            },use_container_width=True
        )
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download JSON Pagination", 
                data=json.dumps(pagination_info["page_urls"], indent=4), 
                file_name=f"pagination_urls.json"
            )
        with col2:
            st.download_button(
                "Download CSV Pagination", 
                data=pagination_df.to_csv(index=False), 
                file_name=f"pagination_urls.csv"
            )
if st.button("Clear Results"):
    st.session_state['results'] = None
    st.session_state['perform_scrape'] = False
    st.rerun()