#!/usr/bin/env python3
"""
GreenClaw Risk Analyzer — AI-powered climate risk analysis using Z.AI GLM.
Uses the OpenAI-compatible API to analyze climate data and generate risk assessments.
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print(json.dumps({"error": "openai library not installed. Run: pip install openai"}))
    sys.exit(1)


RISK_ANALYSIS_PROMPT = """You are a climate risk analyst. Analyze the following climate data and provide a structured risk assessment.

City: {city}
Climate Data: {data}
Current Date: {date}

Provide your analysis as a valid JSON object with this exact structure:
{{
    "overall_risk_score": <1-10 integer>,
    "risk_level": "<Low|Moderate|High|Critical>",
    "confidence": "<High|Medium|Low>",
    "risks": [
        {{
            "category": "<Flood|Heat|Air Quality|Storm|Cold|Drought>",
            "score": <1-10>,
            "description": "<brief description>",
            "timeframe": "<immediate|24h|7days>"
        }}
    ],
    "recommendations": [
        "<actionable recommendation 1>",
        "<actionable recommendation 2>",
        "<actionable recommendation 3>"
    ],
    "sdg13_connection": "<how this relates to UN SDG 13 Climate Action>",
    "summary": "<2-3 sentence executive summary>"
}}

Be specific and data-driven in your analysis. Consider seasonal patterns, historical trends, and current conditions.
Return ONLY the JSON object, no other text."""


def analyze_risk(city: str, data: str, api_key: str) -> dict:
    """Send climate data to Z.AI GLM for risk analysis."""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.z.ai/api/paas/v4"
    )

    try:
        response = client.chat.completions.create(
            model="glm-4.5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert climate risk analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": RISK_ANALYSIS_PROMPT.format(
                        city=city,
                        data=data,
                        date=datetime.utcnow().strftime("%Y-%m-%d")
                    )
                }
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        if content.startswith("```"):
            # Remove markdown code block wrapping
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        
        risk_data = json.loads(content)
        
        # Add metadata
        risk_data["type"] = "risk_analysis"
        risk_data["city"] = city
        risk_data["model"] = "Z.AI GLM-4.5"
        risk_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add risk level emoji
        score = risk_data.get("overall_risk_score", 0)
        if score <= 3:
            risk_data["icon"] = "🟢"
        elif score <= 5:
            risk_data["icon"] = "🟡"
        elif score <= 7:
            risk_data["icon"] = "🟠"
        else:
            risk_data["icon"] = "🔴"

        return risk_data

    except json.JSONDecodeError:
        return {
            "type": "risk_analysis",
            "city": city,
            "error": "Failed to parse AI response as JSON",
            "raw_response": content[:500],
            "model": "Z.AI GLM-4.5",
        }
    except Exception as e:
        return {
            "type": "risk_analysis",
            "city": city,
            "error": f"Z.AI API error: {str(e)}",
            "model": "Z.AI GLM-4.5",
        }


def main():
    parser = argparse.ArgumentParser(description="GreenClaw Risk Analyzer")
    parser.add_argument("--city", type=str, required=True, help="City to analyze")
    parser.add_argument("--data", type=str, default="", help="Climate data JSON string")
    parser.add_argument("--quick", action="store_true", help="Quick assessment without detailed data")
    parser.add_argument("--dry-run", action="store_true", help="Return mock data for testing")
    args = parser.parse_args()

    if args.dry_run:
        mock_result = {
            "type": "risk_analysis",
            "city": args.city,
            "overall_risk_score": 4,
            "risk_level": "Moderate",
            "icon": "🟡",
            "confidence": "Medium",
            "risks": [
                {"category": "Air Quality", "score": 5, "description": "Moderate pollution levels expected", "timeframe": "24h"},
                {"category": "Heat", "score": 3, "description": "Slightly above average temperatures", "timeframe": "7days"},
            ],
            "recommendations": [
                "Monitor air quality levels and limit outdoor exercise during peak hours",
                "Stay hydrated and use sun protection",
                "Consider using public transport to reduce emissions"
            ],
            "sdg13_connection": "Individual actions to reduce emissions and adapt to changing climate patterns directly support SDG 13 targets.",
            "summary": "Moderate climate risk detected for the area. Air quality is the primary concern with slightly elevated pollution levels. No immediate weather-related threats identified.",
            "model": "Z.AI GLM-4.5 (dry-run)",
            "status": "dry_run",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        print(json.dumps(mock_result, indent=2))
        return

    api_key = os.environ.get("ZAI_API_KEY", "")
    if not api_key:
        print(json.dumps({"error": "ZAI_API_KEY not set. Get your key at https://open.bigmodel.cn/"}))
        sys.exit(1)

    if args.quick and not args.data:
        args.data = json.dumps({
            "note": f"No detailed data provided. Analyze general climate risks for {args.city} based on your knowledge.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
        })

    result = analyze_risk(args.city, args.data, api_key)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
