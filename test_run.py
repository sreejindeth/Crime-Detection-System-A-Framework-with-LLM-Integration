import sys
import traceback

print("Starting test...")
print("Python version:", sys.version)

try:
    print("\n1. Testing imports...")
    import cv2
    print("   - OpenCV imported successfully")
    
    import numpy as np
    print("   - NumPy imported successfully")
    
    import keras
    print("   - Keras imported successfully")
    
    print("\n2. Testing detection module...")
    from detection import AccidentDetectionModel
    print("   - AccidentDetectionModel imported successfully")
    
    print("\n3. Testing model loading...")
    model = AccidentDetectionModel("model.json", "model_weights.keras")
    print("   - Model loaded successfully!")
    
    print("\n4. Testing camera module...")
    import camera
    print("   - Camera module imported successfully")
    
    print("\n5. Testing video file...")
    import os
    video_path = r"D:\SET\Accident-Detection-System-main\Bike.mp4"
    if os.path.exists(video_path):
        print(f"   - Video file found: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            print("   - Video file can be opened!")
            ret, frame = cap.read()
            if ret:
                print(f"   - Frame read successfully: {frame.shape}")
            else:
                print("   - Warning: Could not read frame")
            cap.release()
        else:
            print("   - Error: Video file cannot be opened")
    else:
        print(f"   - Error: Video file not found at {video_path}")
    
    print("\nAll tests passed! You can run main.py now.")
    
except Exception as e:
    print(f"\n❌ ERROR OCCURRED:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)















