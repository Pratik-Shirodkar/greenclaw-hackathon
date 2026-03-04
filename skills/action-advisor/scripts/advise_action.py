#!/usr/bin/env python3
"""
GreenClaw Action Advisor — Personalized sustainability recommendations via FLock.io.
Uses open-source models through FLock's OpenAI-compatible API.
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


TIPS_PROMPT = """You are a sustainability advisor helping people take meaningful climate action. Generate 5 personalized eco-tips.

Location: {city}
User Context: {context}
Date: {date}

Respond with a valid JSON object:
{{
    "tips": [
        {{
            "action": "<specific actionable tip>",
            "impact": "<low|medium|high>",
            "carbon_savings_kg": <estimated annual CO2 savings in kg>,
            "difficulty": "<Easy|Medium|Hard>",
            "category": "<Transport|Energy|Food|Waste|Water|Shopping>"
        }}
    ],
    "motivation": "<encouraging message>",
    "sdg_alignment": ["<SDG number and name>"]
}}

Return ONLY valid JSON."""

CARBON_PROMPT = """You are a carbon footprint analyst. Analyze the user's lifestyle and provide specific reduction strategies.

User Context: {context}
Location: {city}
Date: {date}

Respond with a valid JSON object:
{{
    "current_estimate_kg_yearly": <rough estimate>,
    "target_kg_yearly": <recommended target>,
    "strategies": [
        {{
            "action": "<specific strategy>",
            "savings_kg_yearly": <estimated savings>,
            "difficulty": "<Easy|Medium|Hard>",
            "timeframe": "<immediate|1month|6months|1year>"
        }}
    ],
    "quick_wins": ["<immediate easy action 1>", "<immediate easy action 2>", "<immediate easy action 3>"],
    "motivation": "<encouraging message>"
}}

Return ONLY valid JSON."""

EMERGENCY_PROMPT = """You are a climate emergency preparedness expert. Provide specific preparation guidance.

Risk Type: {risk}
Location: {city}
Date: {date}

Respond with a valid JSON object:
{{
    "risk_type": "{risk}",
    "preparedness_checklist": [
        {{
            "item": "<preparation step>",
            "priority": "<essential|recommended|optional>",
            "timeframe": "<now|24h|week>"
        }}
    ],
    "emergency_contacts": "<reminder to save local emergency numbers>",
    "evacuation_tips": ["<tip 1>", "<tip 2>"],
    "supplies_needed": ["<supply 1>", "<supply 2>", "<supply 3>"]
}}

Return ONLY valid JSON."""

CHALLENGE_PROMPT = """You are a gamification expert for sustainability. Create a fun weekly eco-challenge.

Date: {date}

Respond with a valid JSON object:
{{
    "challenge_name": "<creative challenge name with emoji>",
    "description": "<fun description of the challenge>",
    "duration": "7 days",
    "daily_tasks": [
        {{
            "day": 1,
            "task": "<specific daily task>",
            "points": <points value 10-100>
        }}
    ],
    "total_points": <sum of all points>,
    "reward": "<virtual reward/badge description>",
    "estimated_impact": "<estimated environmental impact>"
}}

Return ONLY valid JSON. Make it fun, achievable, and impactful!"""


def call_flock_api(prompt: str, api_key: str) -> dict:
    """Call FLock API (OpenAI-compatible) with the given prompt."""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.flock.io/v1"
    )

    try:
        response = client.chat.completions.create(
            model="flock-open-model",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert sustainability and climate action advisor. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        
        return json.loads(content)

    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response", "raw": content[:500]}
    except Exception as e:
        return {"error": f"FLock API error: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="GreenClaw Action Advisor")
    parser.add_argument("--mode", choices=["tips", "carbon", "emergency", "challenge"], required=True)
    parser.add_argument("--city", type=str, default="your area")
    parser.add_argument("--context", type=str, default="general user")
    parser.add_argument("--risk", type=str, default="general climate risk")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        mock_results = {
            "tips": {
                "type": "eco_tips",
                "tips": [
                    {"action": "Switch to LED light bulbs", "impact": "medium", "carbon_savings_kg": 45,
                     "difficulty": "Easy", "category": "Energy"},
                    {"action": "Use a reusable water bottle", "impact": "low", "carbon_savings_kg": 8,
                     "difficulty": "Easy", "category": "Waste"},
                    {"action": "Take public transport once a week", "impact": "high", "carbon_savings_kg": 200,
                     "difficulty": "Medium", "category": "Transport"},
                ],
                "motivation": "Every small action adds up! You're making a real difference! 🌱",
                "status": "dry_run",
            },
            "carbon": {
                "type": "carbon_analysis",
                "current_estimate_kg_yearly": 8500,
                "target_kg_yearly": 5000,
                "strategies": [
                    {"action": "Reduce car usage", "savings_kg_yearly": 1200, "difficulty": "Medium", "timeframe": "1month"}
                ],
                "quick_wins": ["Unplug unused electronics", "Eat one plant-based meal today"],
                "status": "dry_run",
            },
            "emergency": {
                "type": "emergency_prep",
                "risk_type": "flood",
                "preparedness_checklist": [
                    {"item": "Prepare emergency kit", "priority": "essential", "timeframe": "now"}
                ],
                "status": "dry_run",
            },
            "challenge": {
                "type": "weekly_challenge",
                "challenge_name": "🌱 Zero Waste Week",
                "description": "Try to produce no single-use plastic waste for 7 days!",
                "daily_tasks": [
                    {"day": 1, "task": "Bring reusable bags to every store", "points": 20}
                ],
                "total_points": 350,
                "status": "dry_run",
            },
        }
        result = mock_results.get(args.mode, {})
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        print(json.dumps(result, indent=2))
        return

    api_key = os.environ.get("FLOCK_API_KEY", "")
    if not api_key:
        print(json.dumps({"error": "FLOCK_API_KEY not set. Get your key at https://flock.io/"}))
        sys.exit(1)

    date = datetime.utcnow().strftime("%Y-%m-%d")
    prompts = {
        "tips": TIPS_PROMPT.format(city=args.city, context=args.context, date=date),
        "carbon": CARBON_PROMPT.format(city=args.city, context=args.context, date=date),
        "emergency": EMERGENCY_PROMPT.format(risk=args.risk, city=args.city, date=date),
        "challenge": CHALLENGE_PROMPT.format(date=date),
    }

    result = call_flock_api(prompts[args.mode], api_key)
    
    type_map = {"tips": "eco_tips", "carbon": "carbon_analysis", "emergency": "emergency_prep", "challenge": "weekly_challenge"}
    result["type"] = type_map.get(args.mode, args.mode)
    result["model"] = "FLock.io (open-source)"
    result["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
