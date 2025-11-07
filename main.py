import sys
import traceback
import os

# Suppress TensorFlow verbose output and disable GPU if not available
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress ALL TensorFlow messages for faster startup
os.environ['CUDA_VISIBLE_DEVICES'] = ''   # Disable GPU if causing issues

# Change to script directory to ensure relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    print("=" * 50)
    print("Initializing Accident Detection System...")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    print()

    # Quick LLM check (with shorter timeout for faster startup)
    print("[1/3] Checking LLM availability...", end=" ", flush=True)
    from config import LLM_SETTINGS  # noqa: E402
    from llm_analyzer import is_llm_available  # noqa: E402

    if LLM_SETTINGS.enabled:
        if is_llm_available(LLM_SETTINGS):
            if LLM_SETTINGS.provider == "gemini":
                print(f"✓ LLM enabled (Gemini API: {LLM_SETTINGS.gemini_model})")
            else:
                print(f"✓ LLM enabled (Ollama: {LLM_SETTINGS.model})")
        else:
            if LLM_SETTINGS.provider == "gemini":
                print("✗ Gemini API key not set - LLM disabled")
            else:
                print("✗ Ollama not reachable - LLM disabled")
            LLM_SETTINGS.enabled = False
    else:
        print("✗ LLM disabled via configuration")
    print()

    # Import camera module (will load TensorFlow/Keras here - this takes time)
    print("[2/3] Loading detection system (this may take 30-60 seconds)...")
    print("      Loading TensorFlow/Keras and accident detection model...")
    from camera import startapplication  # noqa: E402
    print("      ✓ Detection system loaded!")
    print()

    print("[3/3] Starting video processing...")
    print("=" * 50)
    print()
    startapplication()

except KeyboardInterrupt:
    print("\n\nApplication stopped by user.")
except Exception as e:
    print(f"\n\nERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)