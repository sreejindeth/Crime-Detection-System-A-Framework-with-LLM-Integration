# Feedback Mechanism Documentation

## Overview

The Feedback Mechanism is a standalone system that allows users (CCTV operators, police officers, insurance agents) to report incorrect detections (false positives and false negatives) to improve the accident detection model through retraining.

**IMPORTANT**: This is a **demonstration module** that operates independently from the main accident detection system. It does not modify or interfere with the existing codebase.

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Layer 1: Input Layer                       │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │CCTV Operator  │  │Police Officer│  │ Insurance Agent    │  │
│  └───────┬───────┘  └──────┬───────┘  └─────────┬──────────┘  │
└──────────┼──────────────────┼────────────────────┼─────────────┘
           │                  │                    │
           │     [Submit false positive/negative]  │
           └──────────────────┼────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 3: Cloud Services                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Feedback API (feedback_api.py)            │    │
│  │  - POST   /api/feedback         (Submit)               │    │
│  │  - GET    /api/feedback         (Retrieve)             │    │
│  │  - GET    /api/feedback/export  (Export)               │    │
│  │  - GET    /api/feedback/stats   (Statistics)           │    │
│  └───────────────┬──────────────────────┬─────────────────┘    │
│                  │                      │                       │
│  ┌───────────────▼──────┐       ┌──────▼───────────────┐      │
│  │   Telegram Bot       │       │   (Main System)      │      │
│  │  [Acknowledge]       │       │   NOT INTEGRATED     │      │
│  └──────────────────────┘       └──────────────────────┘      │
└──────────────────┼──────────────────────────────────────────────┘
                   │
                   │ [Store feedback data]
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 5: Storage Layer                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  feedback_data/feedback_log.json                         │  │
│  │  - Detection ID                                          │  │
│  │  - Predicted vs Actual Label                            │  │
│  │  - Correction Type (False Positive/Negative)            │  │
│  │  - User comments and metadata                           │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              │ [Export for retraining]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                Layer 4: Training & Evaluation                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Dataset Augmentation                                    │  │
│  │  - Add corrected samples to training set                │  │
│  │  - Retrain model with feedback data                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Feedback Submission Flow

```
User observes incorrect detection
           ↓
Uses Feedback Client (feedback_client.py)
           ↓
Submits POST request to /api/feedback
           ↓
Feedback API validates and stores data
           ↓
Sends Telegram acknowledgment to user
           ↓
Feedback stored in feedback_log.json
```

### 2. Feedback Data Structure

Each feedback entry contains:

```json
{
  "feedback_id": "FB_20251106_143022_DET_001",
  "detection_id": "DET_20251106_143022_001",
  "predicted_label": "Accident",
  "actual_label": "No Accident",
  "is_correct": false,
  "correction_type": "False Positive",
  "submitted_by": "CCTV_Operator_1",
  "image_path": "last_accident_frame.jpg",
  "location": "Pollachi Main Road, Camera #5",
  "comments": "Heavy rain caused false detection",
  "timestamp_original": "2025-11-06T14:30:22",
  "timestamp_feedback": "2025-11-06T14:35:10",
  "status": "pending_review"
}
```

### 3. Retraining Integration

```python
# Export feedback for retraining
GET /api/feedback/export

# Returns training-ready format:
{
  "corrections": [
    {
      "image_path": "path/to/image.jpg",
      "label": "No Accident",  # Corrected label
      "original_prediction": "Accident",
      "correction_type": "False Positive"
    }
  ]
}

# This data can be added to the training dataset
# and used to retrain the model periodically
```

---

## Usage Instructions

### Step 1: Start the Feedback API

```bash
cd Accident-Detection-System-main
python feedback_api.py
```

Expected output:
```
======================================================================
FEEDBACK API - Accident Detection System
======================================================================
Storage directory: D:\SET\Accident-Detection-System-main\feedback_data
Feedback log file: D:\SET\Accident-Detection-System-main\feedback_data\feedback_log.json
Telegram notifications: Enabled

Available endpoints:
  POST   /api/feedback         - Submit new feedback
  GET    /api/feedback         - Retrieve feedback entries
  GET    /api/feedback/export  - Export for retraining
  GET    /api/feedback/stats   - Get feedback statistics
  GET    /api/health           - Health check

Starting server on http://localhost:5000
======================================================================
```

### Step 2: Submit Feedback (Option A - Using Client)

```bash
# In a new terminal
python feedback_client.py
```

Then select from the menu:
- Demo 1: False Positive example
- Demo 2: False Negative example
- Demo 3: True Positive confirmation
- Interactive Mode: Manual entry

### Step 2: Submit Feedback (Option B - Using cURL)

```bash
# False Positive Example
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "detection_id": "DET_20251106_143022_001",
    "predicted_label": "Accident",
    "actual_label": "No Accident",
    "is_correct": false,
    "submitted_by": "CCTV_Operator_1",
    "image_path": "last_accident_frame.jpg",
    "location": "Pollachi Main Road",
    "comments": "False alarm due to heavy rain"
  }'

# False Negative Example
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "detection_id": "DET_20251106_150815_002",
    "predicted_label": "No Accident",
    "actual_label": "Accident",
    "is_correct": false,
    "submitted_by": "Police_Officer_Dept_A",
    "comments": "Minor collision, model confidence was too low"
  }'
```

### Step 3: View Statistics

```bash
curl http://localhost:5000/api/feedback/stats
```

Response:
```json
{
  "status": "success",
  "statistics": {
    "total_feedback": 15,
    "correct_predictions": 12,
    "false_positives": 2,
    "false_negatives": 1,
    "user_reported_accuracy": 80.0,
    "needs_retraining": false
  }
}
```

### Step 4: Export for Retraining

```bash
curl http://localhost:5000/api/feedback/export
```

This returns all corrections in a format ready to be added to the training dataset.

---

## API Reference

### POST /api/feedback
Submit new feedback about a detection.

**Request Body:**
```json
{
  "detection_id": "string (required)",
  "predicted_label": "string (optional)",
  "actual_label": "Accident | No Accident (required)",
  "is_correct": "boolean (required)",
  "submitted_by": "string (optional)",
  "image_path": "string (optional)",
  "location": "string (optional)",
  "comments": "string (optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Feedback submitted successfully",
  "feedback_id": "FB_20251106_143022_DET_001",
  "correction_type": "False Positive"
}
```

### GET /api/feedback
Retrieve all feedback entries.

**Query Parameters:**
- `correction_type`: Filter by type (False Positive, False Negative)
- `status`: Filter by status
- `limit`: Maximum entries to return

### GET /api/feedback/export
Export feedback for retraining.

Returns all corrections in training-ready format.

### GET /api/feedback/stats
Get statistics about feedback submissions.

Returns accuracy metrics and retraining recommendations.

---

## Integration with Training Pipeline

While this module is standalone, here's how it would integrate with the training pipeline:

```python
# In future training script
import json

# Load feedback corrections
with open('feedback_data/feedback_log.json', 'r') as f:
    feedback = json.load(f)

# Filter false positives/negatives
corrections = [f for f in feedback if not f['is_correct']]

# Add to training dataset
for correction in corrections:
    if correction['image_path']:
        # Copy image to appropriate folder
        label_folder = correction['actual_label'].replace(' ', '_')
        target_path = f"data/train/{label_folder}/{correction['feedback_id']}.jpg"
        shutil.copy(correction['image_path'], target_path)

# Retrain model with augmented dataset
# ... training code ...
```

---

## Benefits

1. **Continuous Improvement**: Model improves over time with real-world corrections
2. **User Engagement**: Users can directly contribute to system accuracy
3. **Transparency**: Clear audit trail of all corrections
4. **Analytics**: Track false positive/negative rates
5. **Non-intrusive**: Operates independently without affecting main system

---

## Files Created

1. `feedback_api.py` - REST API server for feedback collection
2. `feedback_client.py` - Client demonstration tool
3. `FEEDBACK_MECHANISM.md` - This documentation
4. `feedback_data/` - Directory for storing feedback (created at runtime)
5. `feedback_data/feedback_log.json` - Feedback storage file (created at runtime)

---

## Requirements

To run the feedback system, install Flask:

```bash
pip install flask
```

Or add to requirements.txt:
```
flask>=2.3.0
```

---

## Demonstration for Reviewers

To show this system to reviewers:

1. Start the API: `python feedback_api.py`
2. Run demos: `python feedback_client.py`
3. Show the statistics endpoint
4. Show the export endpoint
5. Explain the architecture diagram
6. Show the feedback_log.json file

This demonstrates a complete feedback loop without touching the existing codebase.

---

## Future Enhancements

- Web-based feedback submission interface
- Automated retraining triggers
- Integration with main detection pipeline
- Multi-user authentication
- Feedback review and approval workflow
- Real-time dashboard for feedback monitoring

---

## Contact

For questions about the feedback mechanism, refer to this documentation or examine the code in `feedback_api.py` and `feedback_client.py`.




