![WhatsApp Image 2024-11-05 at 04 11 07_b1b9d4e2](https://github.com/user-attachments/assets/8af27ad1-df8e-4a74-b3b8-234d9ab90283)
![WhatsApp Image 2024-11-05 at 04 11 06_8b9df3f3](https://github.com/user-attachments/assets/57154278-926c-4e24-a5ee-270be57cfa7a)

**Impartus View Automation and Summarizer**
This project automates view adjustments and summarizes lecture content from Impartus video lectures. By detecting the professor's presence using YOLOv5 and capturing lecture slides, this tool provides both an optimized viewing experience and a summary of key topics discussed.
Video-Capture-Yolo.py - This file captures screenshots of impartus videos and detects professors using Yolo v5 model and changes view accordingly.

**Features**
**Automated View Adjustment:** Detects the professor in the video and automatically switches views to ensure they remain in frame. This is ideal for maintaining focus during lectures.
Lecture Summarization: Captures slides and generates a summary of the lecture content using an LLM (Large Language Model). The summary is displayed alongside the video for easy reference.
**Downloadable Slides:** Option to download relevant lecture slides with extraneous slides (like blank screens or desktop views) filtered out.


Requirements
Install necessary libraries with the following commands:

pip install ultralytics
pip install git+https://github.com/ultralytics/ultralytics.git@main

Ensure you also download the YOLOv5 model for professor detection.

git clone https://github.com/yourusername/impartus-view-automation.git
cd impartus-view-automation

IMPARTUS_USERNAME=your_username

IMPARTUS_PASSWORD=your_password

GROQ_API_KEY=your_groq_api_key

*note:groq does not work on bits wifi

python Video-Capture-Yolo.py
python Summary.py





Automated View: The Video-Capture-Yolo.py script will run in the background, adjusting views automatically based on the professor's position.
Generate Summary: Running Summary.py will generate a short summary alongside the video. The summary is based on captured slides and audio.
Download Relevant Slides: After summarization, irrelevant slides (such as blank or desktop views) will be excluded, providing a clean set of downloadable lecture slides.
