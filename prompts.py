from textwrap import dedent
from typing import Dict, Any


def scene_analysis_prompt(metadata: Dict[str, Any]) -> str:
    """Prompt for generating a natural language description of the accident scene."""
    base = dedent(
        """
        You are an expert traffic incident analyst. Examine the provided accident frame image and produce a clear, factual summary of what appears in the scene.

        Guidelines:
        - Describe the road type, number of vehicles, their apparent positions, directions, and any visible collisions.
        - Mention visible damage, smoke, debris, skid marks, or hazards.
        - Note weather, lighting, traffic density, and potential contributing factors (e.g., speeding, lane changes, obstacles).
        - Highlight any visible injuries or persons requiring assistance if discernible.
        - Keep the tone professional and objective.
        - Format the response using short paragraphs and bullet lists when appropriate.
        """
    ).strip()

    context_info = []
    if metadata.get("location"):
        context_info.append(f"Known location: {metadata['location']}")
    if metadata.get("timestamp"):
        context_info.append(f"Detection timestamp: {metadata['timestamp']}")
    if metadata.get("vehicle_id"):
        context_info.append(f"Vehicle ID associated with system: {metadata['vehicle_id']}")

    if context_info:
        base += "\n\nContext:\n- " + "\n- ".join(context_info)

    base += "\n\nReturn only the analysis text."
    return base


def structured_summary_prompt(metadata: Dict[str, Any]) -> str:
    """Prompt instructing the LLM to output JSON structured information."""
    base = dedent(
        """
        You are a structured data extraction assistant. Analyse the accident frame image and return a JSON object with the following structure:
        {
          "accident_severity": "minor | moderate | severe | unclear",
          "collision_type": "rear-end | side-impact | head-on | rollover | multi-vehicle | unclear",
          "vehicles_involved": [
            {
              "vehicle_type": "car | bike | truck | bus | other | unknown",
              "position": "left | center | right | intersection | roadside | unknown",
              "visible_damage": "none | minor | moderate | severe | unknown"
            }
          ],
          "persons_observed": {
            "count": number,
            "possible_injuries": "none | minor | moderate | severe | unknown"
          },
          "road_conditions": "dry | wet | icy | debris | unclear",
          "weather_conditions": "clear | rain | fog | night | other | unclear",
          "contributing_factors": ["list potential causes or leave empty"],
          "immediate_hazards": ["list hazards such as fire, fuel leak, debris"]
        }

        Requirements:
        - The response MUST be valid JSON without additional commentary.
        - Only include keys listed above.
        - Use null for unknown numerical values.
        - Use an empty list when no items are observed.
        """
    ).strip()

    if metadata.get("location"):
        base += f"\nContext hint: The incident location is {metadata['location']}."

    return base


def safety_recommendations_prompt(scene_description: str, structured: Dict[str, Any]) -> str:
    structured_lines = []
    for key, value in structured.items():
        structured_lines.append(f"- {key}: {value}")
    structured_context = "\n".join(structured_lines) if structured_lines else "- No structured data available"

    return dedent(
        f"""
        You are a road safety advisor. Based on the following scene description and structured findings, produce actionable safety recommendations for emergency responders and city authorities.

        Scene description:
        {scene_description or "No narrative available."}

        Structured findings:
{structured_context}

        Provide:
        1. Immediate responder actions (bullet list).
        2. Short-term mitigation steps (1-2 items).
        3. Long-term prevention suggestions (1-2 items).

        Use clear headings and concise bullet points.
        """
    ).strip()


def insurance_report_prompt(metadata: Dict[str, Any], scene_description: str, structured: Dict[str, Any]) -> str:
    return dedent(
        f"""
        You are an insurance claim specialist. Draft a concise accident report for the insured party using the details below. Keep it factual and suitable for claim submission.

        Incident metadata: {metadata}
        Scene summary: {scene_description or "Not available"}
        Structured findings: {structured}

        Include sections:
        - Incident Overview
        - Observed Damages and Impact
        - Potential Liability Notes
        - Recommended Next Steps for the insured party

        Use professional tone with short paragraphs and bullet lists when helpful.
        """
    ).strip()


def police_report_prompt(metadata: Dict[str, Any], scene_description: str, structured: Dict[str, Any]) -> str:
    return dedent(
        f"""
        You are assisting law enforcement. Prepare a factual accident briefing for responding officers.

        Metadata: {metadata}
        Scene summary: {scene_description or "Not available"}
        Structured findings: {structured}

        Provide sections:
        - Summary of Observations
        - Evidence and Hazards on Scene
        - Suggested Immediate Actions
        - Notable Follow-up Items

        Keep sentences direct and objective. Avoid speculation beyond the evidence in the image.
        """
    ).strip()


def safety_report_prompt(metadata: Dict[str, Any], recommendations_text: str) -> str:
    return dedent(
        f"""
        Produce a safety analysis memo for municipal traffic safety teams summarising the AI-generated recommendations.

        Incident metadata: {metadata}
        Recommendations to summarise:
        {recommendations_text or "No recommendations provided."}

        Include:
        - Key Risks
        - Suggested Infrastructure Improvements
        - Monitoring or policy considerations

        Keep the memo concise (under 200 words) with bullet points where appropriate.
        """
    ).strip()














