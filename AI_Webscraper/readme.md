**AI-Powered Web Scraper******
This AI-powered web scraping tool enables users to extract data from web pages based on specific tags or structures. The application is built using Streamlit for the user interface, Selenium for web automation, and OpenAI for intelligent parsing. This tool allows users to extract structured information, including pagination handling, and export data in JSON or CSV formats.

**Features**

**Automated Web Scraping:** Uses Selenium to automate the extraction of HTML content from a given URL.
**Data Structuring:** Enables users to define specific tags or fields to target in the scraped data, making data extraction flexible and tailored.
**Pagination Support:** Detects and navigates pagination links automatically, allowing continuous scraping across multiple pages.
**Data Export**: Supports exporting data in JSON or CSV formats for easy download.
User-friendly Interface: Built with Streamlit, offering a clear and interactive interface.

**Requirements**
Ensure that the following dependencies are listed in your requirements.txt:

Getting Started

**1. Clone the Repository**

git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

**2. Set Up Environment Variables**

Create a .env file in the root directory of the project:
plaintext
OPENAI_API_KEY=your_openai_api_key

Replace your_openai_api_key with your actual OpenAI API key.

**3. Install Dependencies**

Make sure you have Python and pip installed. Install all dependencies from requirements.txt:

pip install -r requirements.txt

**4. Start the Application**

In the command prompt or terminal, run the following command to start the Streamlit application:

streamlit run app.py
