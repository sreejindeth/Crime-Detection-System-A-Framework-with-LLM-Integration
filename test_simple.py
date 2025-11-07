import sys
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings

print("Quick test starting...")

try:
    print("Importing cv2...")
    import cv2
    print("✓ OpenCV OK")
    
    print("Importing detection...")
    from detection import AccidentDetectionModel
    print("✓ Detection module OK")
    
    print("Loading model (this may take a moment)...")
    import os
    os.chdir(r"D:\SET\Accident-Detection-System-main")
    model = AccidentDetectionModel("model.json", "model_weights.keras")
    print("✓ Model loaded!")
    
    print("\nTesting video...")
    video_path = r"D:\SET\Accident-Detection-System-main\Bike.mp4"
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✓ Video OK - Frame shape: {frame.shape}")
            cap.release()
        else:
            print("✗ Cannot open video")
    else:
        print(f"✗ Video not found: {video_path}")
    
    print("\nAll tests passed!")
    
except Exception as e:
    import traceback
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()















