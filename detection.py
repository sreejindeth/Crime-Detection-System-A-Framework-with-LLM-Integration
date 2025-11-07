import numpy as np
import os

# Try Keras 3 first, fallback to older API
try:
    from keras.models import model_from_json
    try:
        from keras.saving import load_model
        KERAS_VERSION = 3
        USE_LOAD_MODEL = True
    except ImportError:
        try:
            from keras.models import load_model
            KERAS_VERSION = 3
            USE_LOAD_MODEL = True
        except ImportError:
            USE_LOAD_MODEL = False
            KERAS_VERSION = 3
except ImportError:
    try:
        from tensorflow.keras.models import model_from_json, load_model
        KERAS_VERSION = 2
        USE_LOAD_MODEL = True
    except ImportError:
        from keras.models import model_from_json
        USE_LOAD_MODEL = False
        KERAS_VERSION = 2

class AccidentDetectionModel(object):

    class_nums = ['Accident', "No Accident"]

    def __init__(self, model_json_file, model_weights_file):
        # Get absolute paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_json_path = os.path.join(script_dir, model_json_file) if not os.path.isabs(model_json_file) else model_json_file
        model_weights_path = os.path.join(script_dir, model_weights_file) if not os.path.isabs(model_weights_file) else model_weights_file
        
        # Try loading from .keras file directly first (Keras 3 format)
        if model_weights_file.endswith('.keras') and os.path.exists(model_weights_path):
            if USE_LOAD_MODEL:
                try:
                    print(f"Attempting to load model from .keras file: {model_weights_path}")
                    self.loaded_model = load_model(model_weights_path)
                    print("Model loaded successfully from .keras file!")
                    return
                except Exception as e:
                    print(f"Direct .keras load failed: {e}")
                    print("Trying JSON + weights approach...")
        
        # Fallback: Load from JSON + weights
        if not os.path.exists(model_json_path):
            raise FileNotFoundError(f"Model JSON file not found: {model_json_path}")
        
        print(f"Loading model from JSON: {model_json_path}")
        with open(model_json_path, "r") as json_file:
            loaded_model_json = json_file.read()
            self.loaded_model = model_from_json(loaded_model_json)
        
        # Load weights if provided
        if model_weights_file and os.path.exists(model_weights_path):
            print(f"Loading weights from: {model_weights_path}")
            self.loaded_model.load_weights(model_weights_path)
        elif model_weights_file:
            print(f"Warning: Weights file not found: {model_weights_path}")

        # make_predict_function() is not needed in newer Keras versions
        try:
            self.loaded_model.make_predict_function()
        except:
            pass  # Not available in newer versions, but not required

    def predict_accident(self, img):
        self.preds = self.loaded_model.predict(img, verbose=0)
        return AccidentDetectionModel.class_nums[np.argmax(self.preds)], self.preds