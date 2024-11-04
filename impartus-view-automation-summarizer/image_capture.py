import time
from PIL import Image
from io import BytesIO
import pytesseract
import time

def capture_and_extract_text(driver, interval=20):
    time.sleep(60)
    while True:
        try:

            screenshot = driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot)).convert("L")
            text = pytesseract.image_to_string(image).strip()

            yield text

            
            time.sleep(interval)

        except Exception as e:
            print(f"Error capturing or processing screenshot: {e}")
