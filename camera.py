import json
import os
import time
from typing import Any, Dict, Optional

import cv2
import numpy as np
import requests

from detection import AccidentDetectionModel
from config import TELEGRAM_SETTINGS, LLM_SETTINGS
from llm_analyzer import LLMAnalyzer, LLMAnalysisResult, LLMAnalyzerError

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
font = cv2.FONT_HERSHEY_SIMPLEX
model: Optional[AccidentDetectionModel] = None
llm_analyzer_instance: Optional[LLMAnalyzer] = None
report_sent = False  # Flag to ensure the report is sent only once per session

# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------
def send_telegram_message(message: str, chat_id: str, parse_mode: Optional[str] = "Markdown") -> None:
    if not TELEGRAM_SETTINGS.enable_notifications or not TELEGRAM_SETTINGS.bot_token:
        print("Telegram notifications disabled or bot token missing. Skipping message send.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_SETTINGS.bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}

    if parse_mode:
        params["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=params, timeout=15)
        response.raise_for_status()
        print(f"Telegram message sent to {chat_id}.")
    except requests.exceptions.RequestException as exc:
        print(f"Failed to send Telegram message: {exc}")


def send_telegram_image(image_path: str, chat_id: str) -> None:
    if not TELEGRAM_SETTINGS.enable_notifications or not TELEGRAM_SETTINGS.bot_token:
        print("Telegram notifications disabled or bot token missing. Skipping image send.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_SETTINGS.bot_token}/sendPhoto"

    try:
        with open(image_path, "rb") as image:
            files = {"photo": image}
            data = {"chat_id": chat_id}
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            print(f"Telegram image sent to {chat_id}.")
    except FileNotFoundError:
        print(f"Failed to send Telegram image: file not found at {image_path}")
    except requests.exceptions.RequestException as exc:
        print(f"Failed to send Telegram image: {exc}")


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------
def generate_basic_insurance_report(
    location: str,
    vehicle_id: str,
    timestamp: str,
    accident_type: str = "Hit-and-run",
    other_vehicle_id: str = "Unknown",
    driver_name: str = "Unknown",
    driver_contact: str = "Unknown",
    insurance_provider: str = "Unknown",
) -> str:
    return (
        "Accident Report (For Insurance Claim):\n\n"
        "**Incident Details:**\n"
        f"Incident Type: {accident_type}\n"
        f"Date and Time: {timestamp}\n"
        f"Location: {location}\n\n"
        "**Your Vehicle Details:**\n"
        f"Vehicle ID: {vehicle_id}\n\n"
        "**Other Vehicle Details (if applicable):**\n"
        f"Other Vehicle ID: {other_vehicle_id}\n\n"
        "**Other Driver Details (if available):**\n"
        f"Driver's Name: {driver_name}\n"
        f"Driver's Contact: {driver_contact}\n"
        f"Insurance Provider: {insurance_provider}\n\n"
        "**Additional Information:**\n"
        "Please use this report for your insurance claim.\n"
        "A photo of the accident scene is attached (if available).\n\n"
        "**Disclaimer:** This report is generated automatically and may not include all details. "
        "Please consult with relevant authorities and insurance providers for complete assessment.\n"
    )


def format_structured_info(structured: Dict[str, Any]) -> str:
    if not structured:
        return "No structured data available."
    try:
        return json.dumps(structured, indent=2)
    except (TypeError, ValueError):
        return str(structured)


def ensure_llm_analyzer() -> Optional[LLMAnalyzer]:
    global llm_analyzer_instance
    if not LLM_SETTINGS.enabled:
        return None

    if llm_analyzer_instance is None:
        try:
            llm_analyzer_instance = LLMAnalyzer()
        except Exception as exc:  # pylint: disable=broad-except
            raise LLMAnalyzerError(f"Failed to initialise LLM analyzer: {exc}") from exc

    return llm_analyzer_instance


def dispatch_llm_results(result: LLMAnalysisResult, metadata: Dict[str, Any]) -> None:
    """Send LLM outputs to the configured Telegram recipients."""
    structured_summary = format_structured_info(result.structured_info)

    if result.scene_description:
        send_telegram_message(
            "Accident Scene Analysis\n\n" + result.scene_description,
            TELEGRAM_SETTINGS.chat_id_report,
            parse_mode=None,
        )

    if result.structured_info:
        send_telegram_message(
            "Structured Findings:\n" + structured_summary,
            TELEGRAM_SETTINGS.chat_id_report,
            parse_mode=None,
        )
    else:
        send_telegram_message(
            "Structured Findings:\nNo structured information detected.",
            TELEGRAM_SETTINGS.chat_id_report,
            parse_mode=None,
        )

    if result.safety_recommendations:
        send_telegram_message(
            "Safety Recommendations\n\n" + result.safety_recommendations,
            TELEGRAM_SETTINGS.chat_id_report,
            parse_mode=None,
        )
        send_telegram_message(
            "Safety Recommendations Update\n\n" + result.safety_recommendations,
            TELEGRAM_SETTINGS.chat_id_alert,
            parse_mode=None,
        )

    if result.insurance_report:
        send_telegram_message(
            "Enhanced Insurance Report\n\n" + result.insurance_report,
            TELEGRAM_SETTINGS.chat_id_report,
            parse_mode=None,
        )

    if result.police_report:
        send_telegram_message(
            "AI Police Briefing\n\n" + result.police_report,
            TELEGRAM_SETTINGS.chat_id_alert,
            parse_mode=None,
        )

    if result.safety_report:
        send_telegram_message(
            "Safety Analysis Summary\n\n" + result.safety_report,
            TELEGRAM_SETTINGS.chat_id_report,
            parse_mode=None,
        )
        send_telegram_message(
            "Safety Analysis Summary\n\n" + result.safety_report,
            TELEGRAM_SETTINGS.chat_id_alert,
            parse_mode=None,
        )


# ---------------------------------------------------------------------------
# Main entry point for detection
# ---------------------------------------------------------------------------
def startapplication() -> None:
    global report_sent, model

    if model is None:
        print("Loading accident detection model from disk...")
        print("   This includes loading the CNN architecture and weights.")
        try:
            model = AccidentDetectionModel("model.json", "model_weights.keras")
            print("   ✓ Model loaded successfully!")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"ERROR: Failed to load model: {exc}")
            import traceback

            traceback.print_exc()
            return

    video_path = r"D:\SET\Accident-Detection-System-main\Car 2.mp4"
    print(f"Opening video: {video_path}")

    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found at {video_path}")
        return

    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        print(f"ERROR: Could not open video file: {video_path}")
        return

    print("Video opened successfully. Starting detection...")
    print("Press 'q' in the video window to quit.")

    accident_detected = False
    last_accident_frame: Optional[np.ndarray] = None
    consecutive_failures = 0
    max_consecutive_failures = 10

    while True:
        ret, frame = video.read()
        if not ret or frame is None:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"Error: Failed to read {max_consecutive_failures} consecutive frames. Video may have ended or is corrupted.")
                break
            continue
        
        consecutive_failures = 0  # Reset counter on successful frame read

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        roi = cv2.resize(gray_frame, (250, 250))

        pred, prob = model.predict_accident(roi[np.newaxis, :, :, :])
        print(f"Raw Prediction Output: {pred}, Probability: {prob}")

        accident_threshold = 95
        accident_prob = prob[0][0]
        no_accident_prob = prob[0][1]

        if accident_prob > no_accident_prob and accident_prob * 100 > accident_threshold:
            confidence = round(accident_prob * 100, 2)
            cv2.rectangle(frame, (0, 0), (280, 40), (0, 0, 0), -1)
            cv2.putText(frame, f"{pred} {confidence}%", (20, 30), font, 1, (255, 255, 0), 2)
            accident_detected = True
            last_accident_frame = frame.copy()
        else:
            if accident_detected:
                print("Accident detected previously. Preparing AI reports...")
                location = "Boston"
                vehicle_id = "XYZ123"
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                metadata = {
                    "location": location,
                    "vehicle_id": vehicle_id,
                    "timestamp": timestamp,
                }

                if not report_sent:
                    detailed_report = generate_basic_insurance_report(location, vehicle_id, timestamp)
                    send_telegram_message(detailed_report, TELEGRAM_SETTINGS.chat_id_report)
                    report_sent = True

                alert_message = (
                    "URGENT: Accident Detected!\n"
                    f"Location: {location}\n"
                    f"Vehicle ID: {vehicle_id}\n"
                    f"Timestamp: {timestamp}\n"
                    "Immediate action required!"
                )

                if last_accident_frame is not None:
                    image_path = "last_accident_frame.jpg"
                    cv2.imwrite(image_path, last_accident_frame)

                    send_telegram_message(alert_message, TELEGRAM_SETTINGS.chat_id_alert, parse_mode=None)
                    send_telegram_image(image_path, TELEGRAM_SETTINGS.chat_id_alert)
                    send_telegram_image(image_path, TELEGRAM_SETTINGS.chat_id_report)

                    if LLM_SETTINGS.enabled:
                        try:
                            analyzer = ensure_llm_analyzer()
                        except LLMAnalyzerError as exc:
                            print(exc)
                            send_telegram_message(
                                "AI analysis could not be initialised. Basic reports only.",
                                TELEGRAM_SETTINGS.chat_id_report,
                                parse_mode=None,
                            )
                            analyzer = None

                        if analyzer:
                            if TELEGRAM_SETTINGS.send_analysis_progress:
                                send_telegram_message(
                                    "AI accident analysis in progress (expected < 1 minute)...",
                                    TELEGRAM_SETTINGS.chat_id_report,
                                    parse_mode=None,
                                )
                                send_telegram_message(
                                    "AI accident analysis in progress (expected < 1 minute)...",
                                    TELEGRAM_SETTINGS.chat_id_alert,
                                    parse_mode=None,
                                )
                            try:
                                analysis_result = analyzer.run_full_analysis(image_path, metadata)
                                dispatch_llm_results(analysis_result, metadata)
                            except LLMAnalyzerError as exc:
                                error_msg = str(exc)
                                print(f"LLM analysis failed: {error_msg}")
                                
                                # Provide helpful error message
                                if "memory" in error_msg.lower():
                                    failure_msg = (
                                        "AI analysis unavailable: Insufficient system memory. "
                                        "The LLM model requires more RAM than currently available. "
                                        "Basic accident detection and reports are still available."
                                    )
                                else:
                                    failure_msg = "AI analysis failed. Please rely on the attached evidence."
                                
                                send_telegram_message(
                                    failure_msg,
                                    TELEGRAM_SETTINGS.chat_id_report,
                                    parse_mode=None,
                                )

                accident_detected = False
                last_accident_frame = None

        if cv2.waitKey(100) & 0xFF == ord("q"):
            break

        cv2.imshow("Video", frame)

    video.release()
    cv2.destroyAllWindows()