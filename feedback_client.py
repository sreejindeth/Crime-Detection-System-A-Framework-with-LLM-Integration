"""
Feedback Client - Submit Feedback to the Feedback API
======================================================

This is a demonstration client that shows how users (CCTV operators, 
police, insurance agents) can submit feedback about detection results.

NOTE: This is a STANDALONE demonstration script. It does NOT modify
      the main accident detection pipeline.

Usage:
    1. First start the Feedback API: python feedback_api.py
    2. Then run this client: python feedback_client.py
"""

import requests
import json
from datetime import datetime
from typing import Optional


class FeedbackClient:
    """Client for submitting feedback to the Feedback API."""
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url.rstrip('/')
        self.feedback_endpoint = f"{self.api_url}/api/feedback"
    
    def submit_feedback(
        self,
        detection_id: str,
        predicted_label: str,
        actual_label: str,
        submitted_by: str,
        image_path: Optional[str] = None,
        location: Optional[str] = None,
        comments: Optional[str] = None
    ) -> dict:
        """
        Submit feedback for a detection result.
        
        Args:
            detection_id: Unique identifier for the detection
            predicted_label: What the model predicted ("Accident" or "No Accident")
            actual_label: What actually happened ("Accident" or "No Accident")
            submitted_by: Name or role of person submitting (e.g., "CCTV_Operator_1")
            image_path: Optional path to the accident frame
            location: Optional location information
            comments: Optional additional comments
        
        Returns:
            API response as dictionary
        """
        is_correct = predicted_label == actual_label
        
        payload = {
            "detection_id": detection_id,
            "predicted_label": predicted_label,
            "actual_label": actual_label,
            "is_correct": is_correct,
            "submitted_by": submitted_by,
            "timestamp_original": datetime.now().isoformat()
        }
        
        if image_path:
            payload["image_path"] = image_path
        if location:
            payload["location"] = location
        if comments:
            payload["comments"] = comments
        
        try:
            response = requests.post(
                self.feedback_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def get_feedback_stats(self) -> dict:
        """Get feedback statistics from the API."""
        try:
            response = requests.get(f"{self.feedback_endpoint}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def export_for_retraining(self) -> dict:
        """Export feedback data for model retraining."""
        try:
            response = requests.get(f"{self.feedback_endpoint}/export", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}


def demo_false_positive():
    """Demonstrate reporting a false positive (model said accident, but wasn't)."""
    print("\n" + "="*70)
    print("DEMO 1: False Positive - Model incorrectly detected accident")
    print("="*70)
    
    client = FeedbackClient()
    
    result = client.submit_feedback(
        detection_id="DET_20251106_143022_001",
        predicted_label="Accident",
        actual_label="No Accident",
        submitted_by="CCTV_Operator_1",
        image_path="last_accident_frame.jpg",
        location="Pollachi Main Road, Camera #5",
        comments="Heavy rain caused glare on windshield, triggering false positive. No actual collision."
    )
    
    print("Feedback submission result:")
    print(json.dumps(result, indent=2))


def demo_false_negative():
    """Demonstrate reporting a false negative (model missed an accident)."""
    print("\n" + "="*70)
    print("DEMO 2: False Negative - Model missed an actual accident")
    print("="*70)
    
    client = FeedbackClient()
    
    result = client.submit_feedback(
        detection_id="DET_20251106_150815_002",
        predicted_label="No Accident",
        actual_label="Accident",
        submitted_by="Police_Officer_Dept_A",
        image_path="data/test/Accident/test2_7.jpg",
        location="NH-47 Junction, Camera #12",
        comments="Minor collision between two bikes. Low impact, model confidence was below threshold."
    )
    
    print("Feedback submission result:")
    print(json.dumps(result, indent=2))


def demo_true_positive():
    """Demonstrate confirming a correct detection."""
    print("\n" + "="*70)
    print("DEMO 3: True Positive - Model correctly detected accident")
    print("="*70)
    
    client = FeedbackClient()
    
    result = client.submit_feedback(
        detection_id="DET_20251106_153045_003",
        predicted_label="Accident",
        actual_label="Accident",
        submitted_by="Insurance_Agent_XYZ",
        image_path="data/test/Accident/test4_40.jpg",
        location="City Center, Camera #8",
        comments="Confirmed: Car collision. Good detection. Used for insurance claim processing."
    )
    
    print("Feedback submission result:")
    print(json.dumps(result, indent=2))


def demo_statistics():
    """Show feedback statistics."""
    print("\n" + "="*70)
    print("DEMO 4: Feedback Statistics")
    print("="*70)
    
    client = FeedbackClient()
    stats = client.get_feedback_stats()
    
    print("System Statistics:")
    print(json.dumps(stats, indent=2))


def demo_export():
    """Export feedback for retraining."""
    print("\n" + "="*70)
    print("DEMO 5: Export Feedback for Retraining")
    print("="*70)
    
    client = FeedbackClient()
    export_data = client.export_for_retraining()
    
    print("Exported data for retraining:")
    print(json.dumps(export_data, indent=2))


def interactive_mode():
    """Interactive mode for manual feedback submission."""
    print("\n" + "="*70)
    print("INTERACTIVE FEEDBACK SUBMISSION")
    print("="*70)
    
    client = FeedbackClient()
    
    detection_id = input("Detection ID: ").strip()
    predicted = input("Predicted label (Accident/No Accident): ").strip()
    actual = input("Actual label (Accident/No Accident): ").strip()
    submitted_by = input("Your name/role: ").strip()
    location = input("Location (optional): ").strip()
    comments = input("Comments (optional): ").strip()
    
    result = client.submit_feedback(
        detection_id=detection_id,
        predicted_label=predicted,
        actual_label=actual,
        submitted_by=submitted_by,
        location=location if location else None,
        comments=comments if comments else None
    )
    
    print("\nFeedback submission result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("=" * 70)
    print("FEEDBACK CLIENT - Accident Detection System")
    print("=" * 70)
    print()
    print("This demonstrates how users can submit feedback about detections.")
    print("Make sure the Feedback API is running (python feedback_api.py)")
    print()
    
    while True:
        print("\nSelect demo:")
        print("  1. Demo: False Positive")
        print("  2. Demo: False Negative")
        print("  3. Demo: True Positive (Confirmation)")
        print("  4. Demo: View Statistics")
        print("  5. Demo: Export for Retraining")
        print("  6. Interactive Mode")
        print("  7. Run All Demos")
        print("  0. Exit")
        
        choice = input("\nYour choice: ").strip()
        
        if choice == '1':
            demo_false_positive()
        elif choice == '2':
            demo_false_negative()
        elif choice == '3':
            demo_true_positive()
        elif choice == '4':
            demo_statistics()
        elif choice == '5':
            demo_export()
        elif choice == '6':
            interactive_mode()
        elif choice == '7':
            demo_false_positive()
            demo_false_negative()
            demo_true_positive()
            demo_statistics()
            demo_export()
        elif choice == '0':
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")




