import time
import os
import sys
sys.path.insert(0, './yolov5')
import torch
import cv2
import numpy as np
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device
import base64
from dotenv import load_dotenv
print("hello yolo")

load_dotenv()

# Load YOLO model
device = select_device('cpu')
model_path = Path("yolov5/yolov5n.pt")
model = DetectMultiBackend(model_path, device=device)
model.eval()

# Initialize global count and other constants
count = 0
PROFESSOR_MIN_Y_THRESHOLD = 400  # Adjusted threshold
current_view = 1

chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
driver.get("https://a.impartus.com/login/#/")

wait = WebDriverWait(driver, 20)

# Log in to the platform
try:
    username = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password = wait.until(EC.presence_of_element_located((By.ID, "password")))
    username.send_keys(os.environ.get("IMPARTUS_USERNAME"))
    password.send_keys(os.environ.get("IMPARTUS_PASSWORD"))
    login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "iu-btn")))
    login_button.click()
    print("Login successful.")
except TimeoutException as e:
    print(f"Login failed: {e}")

target_url_pattern = "https://a.impartus.com/ilc/#/video/id/"
while True:
    if target_url_pattern in driver.current_url:
        print("Video page detected. Starting YOLO detection...")
        break
    time.sleep(5)

def hover_over_video():
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        ActionChains(driver).move_to_element(video_element).perform()
    except Exception as e:
        print(f"Hover over video failed: {e}")

def switch_view(view_number):
    try:
        #Xpath for dropdown
        dropdown_xpath = "/html/body/div[1]/ui-view/div[1]/div[1]/ui-view/div/div/div[3]/div/ng-include/div/div[2]/div/div[2]/md-input-container[1]/md-select"
        wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath))).click()

        #selecting the view number
        view_xpath = f"/html/body/div[4]/md-select-menu/md-content/md-option[{view_number}]"
        wait.until(EC.element_to_be_clickable((By.XPATH, view_xpath))).click()
        print(f"Switched to View {view_number}.")
    except Exception as e:
        print(f"Error switching to view {view_number}: {e}")

def detect_person_in_frame(frame):
    global count, current_view
    resized_frame = cv2.resize(frame, (640, 640))
    img_tensor = torch.from_numpy(resized_frame).to(device).float() / 255.0
    img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)

    person_detected = False
    lowest_y = float('inf')

    with torch.no_grad():
        pred = model(img_tensor, augment=False)
    pred = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45)

    for det in pred:
        if len(det):
            det[:, :4] = scale_boxes(img_tensor.shape[2:], det[:, :4], frame.shape).round()
            for *xyxy, conf, cls in det:
                if int(cls) == 0:  # Person class
                    person_detected = True
                    y_min = xyxy[1]
                    if y_min < lowest_y:
                        lowest_y = y_min
                    label = f"Person {conf:.2f}"
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
                    cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    cv2.line(frame, (0, PROFESSOR_MIN_Y_THRESHOLD), (frame.shape[1], PROFESSOR_MIN_Y_THRESHOLD), (0, 255, 255), 2)

    if lowest_y >= PROFESSOR_MIN_Y_THRESHOLD:
        print("Professor not in view. Switching view.")
        hover_over_video()
        current_view = 2 if current_view == 1 else 1
        switch_view(current_view)

    return person_detected

def capture_video_frame():
    try:
        js_code = """
            let video = document.querySelector('video');
            let canvas = document.createElement('canvas');
            canvas.width = '640';
            canvas.height = '640';
            let ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL('image/png').substring(22);
        """
        frame_b64 = driver.execute_script(js_code)

        frame_data = base64.b64decode(frame_b64)
        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame

    except Exception as e:
        print(f"Frame capture failed: {e}")
        return None

frame_width, frame_height = 640, 640
out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 1, (frame_width, frame_height))

try:
    while True:
        frame = capture_video_frame()
        if frame is not None and detect_person_in_frame(frame):
            print(f"Person detected in frame {count}.")
            count += 1
            out.write(frame)
        else:
            print("No person detected.")
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping detection.")
finally:
    out.release()
    driver.quit()
