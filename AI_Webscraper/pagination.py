import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from typing import Union,List, Dict,Tuple

from pydantic import BaseModel, Field,ValidationError

#**(prompt suggested by gpt)
pagination_prompt = """
You are an assistant specialized in extracting pagination URLs from website markdown content. Your task is to identify and capture URLs associated with pagination, regardless of the website's structure. Follow the instructions carefully to ensure accurate extraction.
1.Identifying the Next Page URL:
    *Find the URL for the primary pagination button, typically labeled "Next," "More," "See more," "Load more," or similar, which links to the subsequent page of content.
    *If multiple URLs follow the same pattern, leave this field empty.
   
2.Generating Patterned Pagination URLs:
   -Detect any URL pattern indicating a sequence of numbered pages, and generate a list of URLs based on this pattern.
   - Use the first detected URL in the sequence to create additional URLs, covering the range up to the highest page number inferred from the content.
   - Avoid non-pagination links (e.g., image sources, static assets) and focus solely on URLs providing access to content across multiple pages.
   - If URLs are partial or relative, combine them with the base URL given at the end of this prompt to form complete URLs.
   
3.Considering User-Provided Hints:
   - Take into account any hints provided at the end of this prompt regarding the pagination structure. These details can offer insights into page patterns and the expected number of pages. Use this information to refine extraction.

**Required Output Format:**
Provide the results in JSON format as follows:
```json
{
    "next_page_url": "next_page_url_here",
    "page_urls": ["url1", "url2", "url3", ..., "urlN"]
}
"""
load_dotenv()
class PaginationData(BaseModel):
    page_urls: List[str] = Field(default_factory=list)

def detect_pagination(url: str, indications: str, markdown_content: str) -> Tuple[Union[PaginationData, Dict, str], Dict, float]:
    try:
        prompt_pagination = (
            f"{pagination_prompt}\n"
            f"The URL of the page to extract pagination from: {url}\n"
            "If the URLs you find are not complete, combine them intelligently to fit the pattern. **ALWAYS GIVE A FULL URL**"
        )
        
        if indications!= "":
            prompt_pagination += f"\n\nUser's indications: {indications}\n\nMarkdown content:\n\n{markdown_content}"
        else:
            prompt_pagination += f"\nno specific user indications provided,apply the default logic.\n\nMarkdown content:\n\n{markdown_content}"
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_pagination},
                {"role": "user", "content": markdown_content},
            ],
            response_format=PaginationData
       
        )
        
        # extrac the parse the response format
        parsed_response = completion.choices[0].message.parsed
        return parsed_response
    

    except Exception as e:
        logging.error(f"An error occurred in detect_pagination_elements: {e}")
        #return default if error occurs
        return PaginationData(page_urls=[])

