"""import cv2

cap = cv2.VideoCapture(0)  # Change to 1 or 2 if the default camera (0) doesn't work

if not cap.isOpened():
    print("❌ Error: Could not open camera. Try changing the index (0 → 1 or 2).")
else:
    ret, frame = cap.read()
    if ret:
        print("Camera is working!")
    else:
        print("❌ Error: Frame not captured.")

cap.release() """ # Correctly release the camera after the check"""

import os

video_path = r"D:\SET\Accident-Detection-System-main\Car 3.mp4"

if os.path.exists(video_path):
    print("File found:", video_path)
else:
    print("File NOT found. Check the path!")

