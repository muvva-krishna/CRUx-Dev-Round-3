Video-Capture-Yolo.py - This file captures screenshots of impartus videos and detects professors using Yolo v5 model and changes view accordingly.

### Install the ultralytics package from GitHub

pip install ultralytics
pip install git+https://github.com/ultralytics/ultralytics.git@main

Download the yolov5 model too.

Summary.py - This file generates a summary of the video lecture by capturing the slides and injects the summary to left of the video.
This file needs llm.py and image_capture.py to run.

llm.py - This file is used to generate the summary of the video lecture by capturing the slides.

image_capture.py - This file is used to capture the slides of the video lecture.

Add a `.env ` config file with IMPARTUS_USERNAME,IMPARTUS_PASSWORD,GROQ_API_KEY
