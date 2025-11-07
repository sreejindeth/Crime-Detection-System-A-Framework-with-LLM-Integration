import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests

from config import LLM_SETTINGS
from prompts import (
    scene_analysis_prompt,
    structured_summary_prompt,
    safety_recommendations_prompt,
    insurance_report_prompt,
    police_report_prompt,
    safety_report_prompt,
)

LOGGER = logging.getLogger(__name__)


class LLMAnalyzerError(RuntimeError):
    """Raised when the LLM analysis fails."""


@dataclass
class LLMAnalysisResult:
    scene_description: str = ""
    structured_info: Dict[str, Any] = field(default_factory=dict)
    safety_recommendations: str = ""
    insurance_report: str = ""
    police_report: str = ""
    safety_report: str = ""
    raw_responses: Dict[str, Any] = field(default_factory=dict)


def is_llm_available(settings=LLM_SETTINGS, timeout: int = 3) -> bool:
    """Check if LLM provider is available and configured.
    
    For Gemini: checks if API key is set
    For Ollama: checks if server is running
    """
    if not settings.enabled:
        return False
    
    if settings.provider == "gemini":
        return bool(settings.gemini_api_key)
    else:
        # Ollama check
        url = settings.host.rstrip("/") + "/api/version"
        try:
            response = requests.get(url, timeout=timeout)
            return response.ok
        except requests.RequestException:
            return False


# Keep for backward compatibility
def is_ollama_available(settings=LLM_SETTINGS, timeout: int = 3) -> bool:
    """Legacy function - redirects to is_llm_available."""
    return is_llm_available(settings, timeout)


class LLMAnalyzer:
    def __init__(self, settings=LLM_SETTINGS, session: Optional[requests.Session] = None) -> None:
        self.settings = settings
        self._session = session or requests.Session()
        
        # Set up endpoint based on provider
        if self.settings.provider == "gemini":
            if not self.settings.gemini_api_key:
                raise LLMAnalyzerError("GEMINI_API_KEY not set. Please set it as an environment variable.")
            self._endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
        else:
            # Ollama
            self._endpoint = self.settings.host.rstrip("/") + "/api/generate"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def analyze_accident_scene(self, image_path: str, metadata: Dict[str, Any]) -> str:
        prompt = scene_analysis_prompt(metadata)
        return self._generate(prompt, image_path=image_path)

    def extract_structured_info(self, image_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        prompt = structured_summary_prompt(metadata)
        response = self._generate(prompt, image_path=image_path, expect_json=True)
        if isinstance(response, dict):
            return response
        LOGGER.warning("Structured info response was not dict: %s", response)
        return {}

    def generate_safety_recommendations(
        self,
        scene_description: str,
        structured_info: Dict[str, Any],
    ) -> str:
        prompt = safety_recommendations_prompt(scene_description, structured_info)
        return self._generate(prompt)

    def generate_insurance_report(
        self,
        metadata: Dict[str, Any],
        scene_description: str,
        structured_info: Dict[str, Any],
    ) -> str:
        prompt = insurance_report_prompt(metadata, scene_description, structured_info)
        return self._generate(prompt)

    def generate_police_report(
        self,
        metadata: Dict[str, Any],
        scene_description: str,
        structured_info: Dict[str, Any],
    ) -> str:
        prompt = police_report_prompt(metadata, scene_description, structured_info)
        return self._generate(prompt)

    def generate_safety_report(
        self,
        metadata: Dict[str, Any],
        safety_recommendations: str,
    ) -> str:
        prompt = safety_report_prompt(metadata, safety_recommendations)
        return self._generate(prompt)

    def run_full_analysis(self, image_path: str, metadata: Dict[str, Any]) -> LLMAnalysisResult:
        if not self.settings.enabled:
            raise LLMAnalyzerError("LLM analysis has been disabled via configuration")

        result = LLMAnalysisResult()

        try:
            if self.settings.enable_scene_description:
                result.scene_description = self.analyze_accident_scene(image_path, metadata)
                result.raw_responses["scene_description"] = result.scene_description

            if self.settings.enable_structured_summary:
                result.structured_info = self.extract_structured_info(image_path, metadata)
                result.raw_responses["structured_info"] = result.structured_info

            if self.settings.enable_recommendations:
                result.safety_recommendations = self.generate_safety_recommendations(
                    result.scene_description,
                    result.structured_info,
                )
                result.raw_responses["safety_recommendations"] = result.safety_recommendations

            if self.settings.enable_reports:
                result.insurance_report = self.generate_insurance_report(
                    metadata,
                    result.scene_description,
                    result.structured_info,
                )
                result.police_report = self.generate_police_report(
                    metadata,
                    result.scene_description,
                    result.structured_info,
                )
                result.safety_report = self.generate_safety_report(
                    metadata,
                    result.safety_recommendations,
                )
                result.raw_responses["insurance_report"] = result.insurance_report
                result.raw_responses["police_report"] = result.police_report
                result.raw_responses["safety_report"] = result.safety_report

        except LLMAnalyzerError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            raise LLMAnalyzerError(f"LLM analysis failed: {exc}") from exc

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        expect_json: bool = False,
    ) -> Any:
        """Generate response from LLM (Gemini or Ollama)."""
        if self.settings.provider == "gemini":
            return self._generate_gemini(prompt, image_path, expect_json)
        else:
            return self._generate_ollama(prompt, image_path, expect_json)
    
    def _generate_gemini(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        expect_json: bool = False,
    ) -> Any:
        """Generate response using Google Gemini API."""
        # Build contents array
        contents = []
        parts = []
        
        # Add image if provided
        if image_path:
            image_data = self._encode_image(image_path)
            # Detect MIME type
            mime_type = "image/jpeg"
            if image_path.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_path.lower().endswith(".gif"):
                mime_type = "image/gif"
            
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_data
                }
            })
        
        # Add text prompt
        parts.append({"text": prompt})
        contents.append({"parts": parts})
        
        # Build payload
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.settings.temperature,
            }
        }
        
        # For JSON responses, add schema or instruction
        if expect_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        
        attempts = max(self.settings.max_retries, 0) + 1
        last_exc: Optional[Exception] = None
        
        for attempt in range(attempts):
            try:
                # Add API key to URL
                url = f"{self._endpoint}?key={self.settings.gemini_api_key}"
                
                LOGGER.debug("Sending request to Gemini API (attempt %s/%s)", attempt + 1, attempts)
                
                response = self._session.post(
                    url,
                    json=payload,
                    timeout=self.settings.timeout,
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_parts = [part.get("text", "") for part in candidate["content"]["parts"] if "text" in part]
                        text = "".join(text_parts).strip()
                    else:
                        raise LLMAnalyzerError(f"Unexpected Gemini response structure: {data}")
                else:
                    raise LLMAnalyzerError(f"No candidates in Gemini response: {data}")
                
                if expect_json:
                    return self._parse_json_response(text)
                
                return text
                
            except requests.exceptions.HTTPError as exc:
                last_exc = exc
                error_text = ""
                try:
                    error_data = exc.response.json()
                    error_text = str(error_data)
                except:
                    error_text = exc.response.text[:500] if exc.response.text else str(exc)
                
                LOGGER.warning("Gemini API request failed (attempt %s/%s): %s", attempt + 1, attempts, error_text)
                if attempt < attempts - 1:
                    time.sleep(2.0)
                    
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                LOGGER.warning("Gemini API request timed out (attempt %s/%s): %s", attempt + 1, attempts, exc)
                if attempt < attempts - 1:
                    time.sleep(2.0)
                    
            except requests.RequestException as exc:
                last_exc = exc
                LOGGER.warning("Gemini API request failed (attempt %s/%s): %s", attempt + 1, attempts, exc)
                if attempt < attempts - 1:
                    time.sleep(1.5)
                    
            except json.JSONDecodeError as exc:
                last_exc = exc
                LOGGER.warning("Failed to decode Gemini JSON response: %s", exc)
                if attempt < attempts - 1:
                    time.sleep(1.0)
                    
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                LOGGER.error("Unexpected error during Gemini generation: %s", exc)
                if attempt < attempts - 1:
                    time.sleep(1.0)
        
        raise LLMAnalyzerError(f"Failed to obtain response from Gemini API after {attempts} attempts: {last_exc}")
    
    def _generate_ollama(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        expect_json: bool = False,
    ) -> Any:
        """Generate response using Ollama API (original implementation)."""
        payload: Dict[str, Any] = {
            "model": self.settings.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.settings.temperature},
        }

        if image_path:
            payload["images"] = [self._encode_image(image_path)]

        if expect_json:
            payload["format"] = "json"

        attempts = max(self.settings.max_retries, 0) + 1
        last_exc: Optional[Exception] = None

        for attempt in range(attempts):
            try:
                LOGGER.debug("Sending request to Ollama (attempt %s/%s)", attempt + 1, attempts)
                
                response = self._session.post(
                    self._endpoint,
                    json=payload,
                    timeout=self.settings.timeout,
                )
                
                # Check for 500 errors specifically
                if response.status_code == 500:
                    error_text = response.text[:500] if response.text else "No error details"
                    
                    # Check for memory-related errors
                    if "memory" in error_text.lower() or "system memory" in error_text.lower():
                        LOGGER.error(
                            "Ollama memory error: Model requires more RAM than available. "
                            "Error: %s", error_text
                        )
                        raise LLMAnalyzerError(
                            f"Ollama memory error: Model requires more system memory than available. "
                            f"Original error: {error_text}"
                        )
                    else:
                        LOGGER.warning(
                            "Ollama returned 500 error (attempt %s/%s). "
                            "This may indicate model not loaded, memory issues, or image encoding problems. "
                            "Error: %s", attempt + 1, attempts, error_text
                        )
                        if attempt < attempts - 1:
                            time.sleep(3.0)
                        continue
                
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "")

                if expect_json:
                    return self._parse_json_response(text)

                return text.strip()
                
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                LOGGER.warning(
                    "Ollama request timed out (attempt %s/%s). "
                    "Model may be processing or server is overloaded. %s", 
                    attempt + 1, attempts, exc
                )
                if attempt < attempts - 1:
                    time.sleep(2.0)
            except requests.RequestException as exc:
                last_exc = exc
                LOGGER.warning("Ollama request failed (attempt %s/%s): %s", attempt + 1, attempts, exc)
                if attempt < attempts - 1:
                    time.sleep(1.5)
            except json.JSONDecodeError as exc:
                last_exc = exc
                LOGGER.warning("Failed to decode JSON response: %s", exc)
                if attempt < attempts - 1:
                    time.sleep(1.0)
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                LOGGER.error("Unexpected error during LLM generation: %s", exc)
                if attempt < attempts - 1:
                    time.sleep(1.0)

        raise LLMAnalyzerError(f"Failed to obtain response from Ollama after {attempts} attempts: {last_exc}")

    @staticmethod
    def _encode_image(image_path: str) -> str:
        """Encode image to base64 for API (works for both Gemini and Ollama)."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        file_size = os.path.getsize(image_path)
        # Warn if image is very large (APIs have limits)
        if file_size > 10 * 1024 * 1024:  # 10MB
            LOGGER.warning(f"Image file is large ({file_size / 1024 / 1024:.1f}MB), may cause issues")
        
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded

    @staticmethod
    def _parse_json_response(response_text: str) -> Any:
        """Parse the JSON response, attempting to fix common formatting issues."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Attempt to extract JSON substring if the model wrapped it with text
            start = response_text.find("{")
            end = response_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = response_text[start : end + 1]
                return json.loads(snippet)
            raise

