import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress all TensorFlow messages
print("1. Starting...")

import sys
print(f"2. Python: {sys.version}")

try:
    print("3. Importing cv2...")
    import cv2
    print("   ✓ OpenCV imported")
    
    print("4. Importing numpy...")
    import numpy as np
    print("   ✓ NumPy imported")
    
    print("5. Importing TensorFlow (this may take 30-60 seconds)...")
    import tensorflow as tf
    print("   ✓ TensorFlow imported")
    
    print("6. Importing Keras...")
    import keras
    print("   ✓ Keras imported")
    
    print("7. Testing model loading...")
    from detection import AccidentDetectionModel
    
    print("8. Loading model (this may take a minute)...")
    model = AccidentDetectionModel("model.json", "model_weights.keras")
    print("   ✓ Model loaded!")
    
    print("\n✅ All imports successful! The issue may be with video display.")
    print("   Try running: python main.py")
    
except Exception as e:
    print(f"\n❌ ERROR at step: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter...")















