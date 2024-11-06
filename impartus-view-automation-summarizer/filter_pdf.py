import os
from groq import Groq
from pytesseract import image_to_string
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client with API key
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def extract_images_from_pdf(pdf_file):

    pdf_document = fitz.open(pdf_file)
    images = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(BytesIO(pix.tobytes("png")))  # Convert pixmap to an image
        images.append(img)
    pdf_document.close()
    return images

def extract_text_from_image(image):

    return image_to_string(image)

def classify_page_text(text):

    messages = [
        {
           "role": "system",
            "content": "You are a helpful assistant that determines the relevance of a slide to lecture content."
                       "You are given text of each page of a PDF document; your only task is to classify whether this text is related to a subject or a course lecture."
                       "If it is related to a course, label it as 'relevant'; if you don't recognize the contents, label it as 'irrelevant'."
                       "If you receive a blank, label it as 'irrelevant'."
        },
        {
            "role": "user",
            "content": f"Determine if the following slide text is relevant to a lecture:\n\n{text}\n\nAnswer with 'relevant' or 'irrelevant'."
        }
    ]
    
    # Send request to Groq API
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-70b-versatile"
    )

    # Extract and return classification result
    classification = chat_completion.choices[0].message.content.strip().lower()
    return classification

def get_relevant_pages_from_pdf(pdf_file):

    images = extract_images_from_pdf(pdf_file)
    relevant_pages = []

    for pg, img in enumerate(images):
        # Extract text from image using Tesseract OCR
        text = extract_text_from_image(img)
        
        # Send the text of each page to Groq for classification
        classification = classify_page_text(text)
        if classification == 'relevant':
            relevant_pages.append(pg)
    
    return relevant_pages

def save_relevant_pages_to_pdf(input_pdf_path, relevant_pages, output_pdf_path="filtered_lecture_slides.pdf"):

    images = extract_images_from_pdf(input_pdf_path)

    # Select only relevant pages
    relevant_images = [images[page_num] for page_num in relevant_pages]
    
    # Save selected images as a new PDF
    relevant_images[0].save(output_pdf_path, save_all=True, append_images=relevant_images[1:])
    print("Filtered PDF saved as:", output_pdf_path)

input_pdf_path = input("Enter the path to the PDF file: ")
relevant_pages = get_relevant_pages_from_pdf(input_pdf_path)
save_relevant_pages_to_pdf(input_pdf_path, relevant_pages)
