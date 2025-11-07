"""
Feedback API - Standalone Feedback Collection System
====================================================

This module provides a REST API for collecting false positive/negative 
feedback from system users (CCTV operators, police, insurance agents).

NOTE: This is a STANDALONE demonstration module and is NOT integrated 
      with the main accident detection pipeline. It can be run separately
      to show the feedback collection mechanism.

Features:
- RESTful API for feedback submission
- Stores feedback in JSON format for future retraining
- Sends acknowledgment via Telegram
- Validates feedback data
- Exports feedback for dataset augmentation

Usage:
    python feedback_api.py
    
    Then submit feedback via POST request:
    curl -X POST http://localhost:5000/api/feedback \
         -H "Content-Type: application/json" \
         -d '{"detection_id": "123", "is_correct": false, "actual_label": "No Accident"}'
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import requests

# Configuration
FEEDBACK_STORAGE_DIR = Path("feedback_data")
FEEDBACK_FILE = FEEDBACK_STORAGE_DIR / "feedback_log.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_FEEDBACK_CHAT_ID = os.getenv("TELEGRAM_FEEDBACK_CHAT_ID", "")

# Initialize Flask app
app = Flask(__name__)

# Ensure feedback storage directory exists
FEEDBACK_STORAGE_DIR.mkdir(exist_ok=True)


def load_feedback_history() -> List[Dict[str, Any]]:
    """Load existing feedback from storage."""
    if not FEEDBACK_FILE.exists():
        return []
    
    try:
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_feedback(feedback_entry: Dict[str, Any]) -> None:
    """Save feedback entry to persistent storage."""
    history = load_feedback_history()
    history.append(feedback_entry)
    
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def send_telegram_acknowledgment(feedback_entry: Dict[str, Any]) -> bool:
    """Send Telegram notification acknowledging feedback receipt."""
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram bot token not configured. Skipping notification.")
        return False
    
    message = (
        f"✅ Feedback Received\n\n"
        f"Detection ID: {feedback_entry.get('detection_id', 'N/A')}\n"
        f"Submitted by: {feedback_entry.get('submitted_by', 'Anonymous')}\n"
        f"Correction: {feedback_entry.get('correction_type', 'N/A')}\n"
        f"Actual label: {feedback_entry.get('actual_label', 'N/A')}\n"
        f"Timestamp: {feedback_entry.get('timestamp', 'N/A')}\n\n"
        f"Thank you for improving our system!"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_FEEDBACK_CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        print(f"Telegram acknowledgment sent for detection {feedback_entry.get('detection_id')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram acknowledgment: {e}")
        return False


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback for a detection result.
    
    Expected JSON payload:
    {
        "detection_id": "unique_detection_identifier",
        "predicted_label": "Accident" or "No Accident",
        "actual_label": "Accident" or "No Accident",
        "is_correct": true or false,
        "submitted_by": "user_name or role",
        "image_path": "optional_path_to_frame",
        "comments": "optional_additional_notes",
        "location": "optional_location",
        "timestamp_original": "original_detection_timestamp"
    }
    
    Returns:
        JSON response with status and feedback_id
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['detection_id', 'is_correct', 'actual_label']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate labels
        valid_labels = ['Accident', 'No Accident']
        if data['actual_label'] not in valid_labels:
            return jsonify({
                'status': 'error',
                'message': f'Invalid actual_label. Must be one of: {valid_labels}'
            }), 400
        
        # Determine correction type
        if data['is_correct']:
            correction_type = 'True Positive Confirmation'
        else:
            predicted = data.get('predicted_label', 'Unknown')
            actual = data['actual_label']
            if predicted == 'Accident' and actual == 'No Accident':
                correction_type = 'False Positive'
            elif predicted == 'No Accident' and actual == 'Accident':
                correction_type = 'False Negative'
            else:
                correction_type = 'Correction'
        
        # Create feedback entry
        feedback_entry = {
            'feedback_id': f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data['detection_id']}",
            'detection_id': data['detection_id'],
            'predicted_label': data.get('predicted_label', 'Unknown'),
            'actual_label': data['actual_label'],
            'is_correct': data['is_correct'],
            'correction_type': correction_type,
            'submitted_by': data.get('submitted_by', 'Anonymous'),
            'image_path': data.get('image_path', ''),
            'location': data.get('location', ''),
            'comments': data.get('comments', ''),
            'timestamp_original': data.get('timestamp_original', ''),
            'timestamp_feedback': datetime.now().isoformat(),
            'status': 'pending_review'
        }
        
        # Save feedback
        save_feedback(feedback_entry)
        
        # Send acknowledgment via Telegram
        send_telegram_acknowledgment(feedback_entry)
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback_entry['feedback_id'],
            'correction_type': correction_type
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """
    Retrieve all feedback entries or filter by parameters.
    
    Query parameters:
        - correction_type: Filter by correction type (false_positive, false_negative, etc.)
        - status: Filter by status (pending_review, processed, etc.)
        - limit: Maximum number of entries to return
    
    Returns:
        JSON array of feedback entries
    """
    try:
        history = load_feedback_history()
        
        # Apply filters
        correction_type = request.args.get('correction_type')
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        
        if correction_type:
            history = [f for f in history if f.get('correction_type') == correction_type]
        
        if status:
            history = [f for f in history if f.get('status') == status]
        
        if limit:
            history = history[-limit:]
        
        return jsonify({
            'status': 'success',
            'count': len(history),
            'feedback_entries': history
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve feedback: {str(e)}'
        }), 500


@app.route('/api/feedback/export', methods=['GET'])
def export_feedback():
    """
    Export feedback for retraining purposes.
    
    Returns feedback in a format suitable for dataset augmentation.
    Only exports entries marked as corrections (is_correct=false).
    
    Returns:
        JSON with training-ready format:
        {
            "corrections": [
                {
                    "image_path": "path/to/image.jpg",
                    "label": "Accident" or "No Accident",
                    "metadata": {...}
                }
            ]
        }
    """
    try:
        history = load_feedback_history()
        
        # Filter only corrections (incorrect predictions)
        corrections = [f for f in history if not f.get('is_correct', True)]
        
        # Format for training
        training_data = []
        for correction in corrections:
            if correction.get('image_path'):
                training_data.append({
                    'image_path': correction['image_path'],
                    'label': correction['actual_label'],
                    'original_prediction': correction.get('predicted_label'),
                    'correction_type': correction.get('correction_type'),
                    'feedback_id': correction['feedback_id'],
                    'metadata': {
                        'location': correction.get('location'),
                        'comments': correction.get('comments'),
                        'submitted_by': correction.get('submitted_by'),
                        'timestamp': correction.get('timestamp_feedback')
                    }
                })
        
        return jsonify({
            'status': 'success',
            'total_corrections': len(training_data),
            'corrections': training_data,
            'export_timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to export feedback: {str(e)}'
        }), 500


@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """
    Get statistics about feedback submissions.
    
    Returns:
        JSON with statistics:
        - Total feedback count
        - False positive count
        - False negative count
        - Accuracy based on feedback
    """
    try:
        history = load_feedback_history()
        
        total = len(history)
        correct = sum(1 for f in history if f.get('is_correct', False))
        false_positives = sum(1 for f in history if f.get('correction_type') == 'False Positive')
        false_negatives = sum(1 for f in history if f.get('correction_type') == 'False Negative')
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return jsonify({
            'status': 'success',
            'statistics': {
                'total_feedback': total,
                'correct_predictions': correct,
                'false_positives': false_positives,
                'false_negatives': false_negatives,
                'user_reported_accuracy': round(accuracy, 2),
                'needs_retraining': false_positives + false_negatives > 10
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to compute statistics: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Feedback API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    print("=" * 70)
    print("FEEDBACK API - Accident Detection System")
    print("=" * 70)
    print(f"Storage directory: {FEEDBACK_STORAGE_DIR.absolute()}")
    print(f"Feedback log file: {FEEDBACK_FILE.absolute()}")
    print(f"Telegram notifications: {'Enabled' if TELEGRAM_BOT_TOKEN else 'Disabled'}")
    print()
    print("Available endpoints:")
    print("  POST   /api/feedback         - Submit new feedback")
    print("  GET    /api/feedback         - Retrieve feedback entries")
    print("  GET    /api/feedback/export  - Export for retraining")
    print("  GET    /api/feedback/stats   - Get feedback statistics")
    print("  GET    /api/health           - Health check")
    print()
    print("Starting server on http://localhost:5000")
    print("=" * 70)
    print()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)




