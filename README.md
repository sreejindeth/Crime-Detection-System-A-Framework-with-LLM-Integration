# Accident Detection System

Last updated: 7 Nov 2025

## Overview
Deep learning-based accident detection from CCTV/video with optional LLM-powered post-incident analysis and Telegram notifications. Generates:
- Scene description and structured findings
- Safety recommendations
- Insurance and police-style reports

## Features
- CNN-based accident classifier (`model.json`, `model_weights.keras`)
- Video processing and alerting via Telegram
- Optional LLM analysis via Google Gemini or local Ollama
- Evaluation scripts and metrics export

## Repository structure
- `camera.py` — video loop, detection, Telegram, LLM coordination
- `detection.py` — model loading and inference
- `config.py` — reads configuration from environment
- `llm_analyzer.py` — Gemini/Ollama client and orchestration
- `prompts.py` — prompt templates
- `feedback_api.py` — optional standalone Feedback REST API
- `evaluate_model.py` — metrics and plots
- `data/` — dataset (train/val/test)
- `accident/` — notebooks and model artifacts
- `performance_results/` — evaluation outputs (created at runtime)

## Requirements
- Python 3.10+
- Windows/macOS/Linux
- Optional: Telegram bot (for notifications)
- Optional: Google Gemini API key or Ollama (for local LLM)

## Quick start
1) Create and activate a virtual environment
```
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) Prepare model files
- Ensure `model.json` and `model_weights.keras` are present in repository root.
- If missing, train using `accident/accident-classification(model).ipynb` or `accident-classification.ipynb`.

4) Configure environment
- Copy `.env.example` to `.env` and fill values:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID_ALERT=...
TELEGRAM_CHAT_ID_REPORT=...

LLM_PROVIDER=gemini            # or "ollama"
GEMINI_API_KEY=...             # required if provider==gemini
GEMINI_MODEL=gemini-2.5-flash

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llava:7b-v1.5-q4_0

LLM_ENABLED=true
```
Notes:
- `.env` is ignored by Git. Do NOT commit real credentials.
- To find a Telegram chat ID, message your bot, then run the helper in `tele.py`.

5) Run
```
python main.py
```
Windows (batch):
```
run_accident_detection.bat
```

Video source
- `camera.py` currently opens a sample video path. Update `video_path` or use a camera index with OpenCV if needed.

## LLM analysis (optional)
- Provider is selected via `LLM_PROVIDER` (`gemini` or `ollama`).
- For Gemini, set `GEMINI_API_KEY` in `.env`.
- For Ollama, install Ollama and pull a vision model (e.g. `ollama pull llava:7b`), then set host/model.
- Enable/disable features via environment flags (see `config.py`):
  - `LLM_ENABLE_SCENE`, `LLM_ENABLE_STRUCTURED`, `LLM_ENABLE_RECOMMENDATIONS`, `LLM_ENABLE_REPORTS`, `LLM_NOTIFY_PROGRESS`.

## Evaluation and metrics
Generate quantitative metrics and plots:
```
python evaluate_model.py --split test
```
Artifacts are saved to `performance_results/`:
- `metrics_<split>_<timestamp>.json`, `classification_report_<split>_<timestamp>.txt`
- `images/confusion_matrix_*.png`, `images/roc_curve_*.png`, etc.

## Feedback API (optional)
Run a standalone REST API for collecting false positive/negative feedback:
```
python feedback_api.py
```
Main endpoints:
- `POST /api/feedback` — submit feedback
- `GET  /api/feedback` — list feedback
- `GET  /api/feedback/export` — training-ready corrections
- `GET  /api/feedback/stats` — basic stats

## Security & secrets
- Do not commit `.env` or real credentials.
- `.gitignore` excludes `.env`, virtualenvs, logs, temp files, and large model artifacts.
- `config.py` reads everything from environment variables.

## Troubleshooting
- TensorFlow GPU/CPU conflicts: the app disables GPU by default in `main.py`.
- LLM errors:
  - Gemini: ensure `GEMINI_API_KEY` is set and network is reachable.
  - Ollama: ensure server is running and the model is pulled.
- Telegram: ensure bot token and chat IDs are correct, and the bot has been started with `/start`.

## License
Add a license file (e.g., MIT) if you intend to share publicly.

## Contributing
Issues and PRs are welcome. Please avoid including sensitive data in commits.
