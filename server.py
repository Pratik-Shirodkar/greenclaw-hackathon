#!/usr/bin/env python3
"""
GreenClaw v2 — Backend API Server
FastAPI server that connects the dashboard to real APIs and provides
an AI chat interface, automated alerts, and community tracking.
"""

import asyncio
import json
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load environment variables (override=True ensures fresh .env values)
load_dotenv(override=True)

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WAQI_KEY = os.getenv("WAQI_API_KEY", "")
ZAI_KEY = os.getenv("ZAI_API_KEY", "")
FLOCK_KEY = os.getenv("FLOCK_API_KEY", "")

ZAI_BASE = "https://api.z.ai/api/paas/v4"
FLOCK_BASE = "https://api.flock.io/v1"

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
ACTIONS_FILE = DATA_DIR / "actions.json"
USERS_FILE = DATA_DIR / "users.json"

# In-memory alert store
active_alerts: list[dict] = []
alert_cities = ["London", "Delhi", "Tokyo", "Mumbai", "Beijing"]

# ──────────────────────────────────────────────
# Lifespan (background alert monitor)
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(autonomous_pipeline())
    yield
    task.cancel()

app = FastAPI(
    title="GreenClaw API",
    description="Multi-Agent Climate Action Intelligence",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    city: str = "London"
    kids_mode: bool = False

class AdviceRequest(BaseModel):
    mode: str = "tips"
    city: str = "London"
    context: str = "general user"

class ActionLogRequest(BaseModel):
    user: str = "anonymous"
    action: str

class VisionLogRequest(BaseModel):
    user: str = "anonymous"
    image_base64: str

class RegisterRequest(BaseModel):
    chat_id: int
    user: str = "anonymous"

# ──────────────────────────────────────────────
# HTTP Client
# ──────────────────────────────────────────────
http = httpx.AsyncClient(timeout=30.0)

# ──────────────────────────────────────────────
# CLIMATE DATA ENDPOINTS
# ──────────────────────────────────────────────
@app.get("/api/climate/{city}")
async def get_climate(city: str):
    """Fetch live weather + AQI + disasters for a city."""
    weather = await fetch_weather(city)
    aqi = await fetch_aqi(city)
    disasters = await fetch_disasters()
    return {
        "city": city,
        "weather": weather,
        "aqi": aqi,
        "disasters": disasters,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

async def fetch_weather(city: str) -> dict:
    if not OPENWEATHER_KEY:
        return {"error": "OPENWEATHER_API_KEY not set"}
    try:
        # Current weather
        r = await http.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": OPENWEATHER_KEY, "units": "metric"},
        )
        r.raise_for_status()
        d = r.json()
        current = {
            "temp": d["main"]["temp"],
            "feels": d["main"]["feels_like"],
            "humidity": d["main"]["humidity"],
            "pressure": d["main"]["pressure"],
            "wind": d["wind"]["speed"],
            "condition": d["weather"][0]["description"].title(),
            "icon": weather_emoji(d["weather"][0]["main"]),
            "country": d["sys"]["country"],
            "lat": d["coord"]["lat"],
            "lon": d["coord"]["lon"],
        }
        # 5-day forecast
        r2 = await http.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": city, "appid": OPENWEATHER_KEY, "units": "metric"},
        )
        r2.raise_for_status()
        forecast_raw = r2.json()["list"]
        # Group by day, pick noon entries
        days_seen = set()
        forecast = []
        for entry in forecast_raw:
            day = entry["dt_txt"][:10]
            if day not in days_seen and len(forecast) < 5:
                days_seen.add(day)
                forecast.append({
                    "date": day,
                    "high": entry["main"]["temp_max"],
                    "low": entry["main"]["temp_min"],
                    "cond": entry["weather"][0]["description"].title(),
                })
        current["forecast"] = forecast
        return current
    except Exception as e:
        return {"error": str(e)}

async def fetch_aqi(city: str) -> dict:
    if not WAQI_KEY:
        return {"error": "WAQI_API_KEY not set"}
    try:
        r = await http.get(f"https://api.waqi.info/feed/{city}/", params={"token": WAQI_KEY})
        r.raise_for_status()
        d = r.json()
        if d.get("status") != "ok":
            return {"error": d.get("data", "AQI lookup failed")}
        data = d["data"]
        aqi_val = data["aqi"]
        cat, icon = aqi_category(aqi_val)
        pollutants = {}
        for key in ["pm25", "pm10", "o3", "no2", "so2", "co"]:
            if key in data.get("iaqi", {}):
                label = key.upper().replace("PM25", "PM2.5").replace("PM10", "PM10")
                pollutants[label] = data["iaqi"][key]["v"]
        return {
            "value": aqi_val,
            "category": cat,
            "icon": icon,
            "advice": aqi_advice(cat),
            "pollutants": pollutants,
        }
    except Exception as e:
        return {"error": str(e)}

async def fetch_disasters() -> list:
    try:
        r = await http.get("https://eonet.gsfc.nasa.gov/api/v3/events", params={"status": "open", "limit": 10})
        r.raise_for_status()
        events = r.json().get("events", [])
        result = []
        for ev in events[:8]:
            cats = [c["title"] for c in ev.get("categories", [])]
            coords = []
            if ev.get("geometry") and len(ev["geometry"]) > 0:
                coords = ev["geometry"][0].get("coordinates", [])
            result.append({
                "title": ev["title"],
                "icon": disaster_emoji(cats),
                "categories": cats,
                "date": ev.get("geometry", [{}])[0].get("date", "")[:10] if ev.get("geometry") else "",
                "coords": coords, # [lon, lat] from NASA
            })
        return result
    except Exception as e:
        print(f"NASA EONET API Error (Ignored): {e}")
        return []  # Gracefully hide disasters section if API is down

# ──────────────────────────────────────────────
# Z.AI RISK ANALYSIS
# ──────────────────────────────────────────────
@app.post("/api/risk/{city}")
async def analyze_risk(city: str):
    """Run Z.AI GLM risk analysis on live climate data."""
    # First fetch live data
    climate = await get_climate(city)
    
    if not ZAI_KEY:
        return {"error": "ZAI_API_KEY not set", "climate": climate}

    weather = climate.get("weather", {})
    aqi = climate.get("aqi", {})

    prompt = f"""You are an expert climate risk analyst. Analyze the following real-time environmental data and produce a comprehensive risk assessment.

City: {city}
Temperature: {weather.get('temp', 'N/A')}°C (Feels like: {weather.get('feels', 'N/A')}°C)
Humidity: {weather.get('humidity', 'N/A')}%
Wind: {weather.get('wind', 'N/A')} m/s
Condition: {weather.get('condition', 'N/A')}
AQI: {aqi.get('value', 'N/A')} ({aqi.get('category', 'N/A')})
Pollutants: {json.dumps(aqi.get('pollutants', {}))}
Active Disasters Nearby: {len(climate.get('disasters', []))}

Respond with ONLY a valid JSON object:
{{
    "score": <1-10 overall risk score>,
    "level": "<Low|Moderate|High|Critical>",
    "confidence": "<Low|Medium|High>",
    "risks": [
        {{"category": "<risk type>", "score": <1-10>, "desc": "<short explanation>"}}
    ],
    "recommendations": ["<actionable recommendation 1>", "<actionable recommendation 2>"],
    "sdg13": "<how this connects to UN SDG 13 Climate Action>",
    "thinking_steps": [
        {{"label": "<step name>", "text": "<what the model analyzed>"}},
    ]
}}"""

    try:
        r = await http.post(
            f"{ZAI_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {ZAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "glm-4-plus",
                "messages": [
                    {"role": "system", "content": "You are a climate risk analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            },
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        # Clean markdown
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        result = json.loads(content)
        result["model"] = "Z.AI GLM-4-Plus"
        result["climate_data"] = climate
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse Z.AI response", "raw": content[:500], "climate_data": climate}
    except Exception as e:
        return {"error": f"Z.AI API error: {str(e)}", "climate_data": climate}

# ──────────────────────────────────────────────
# FLOCK ACTION ADVISOR
# ──────────────────────────────────────────────
@app.post("/api/advice")
async def get_advice(req: AdviceRequest):
    """Get sustainability advice from FLock open-source models."""
    if not FLOCK_KEY:
        return {"error": "FLOCK_API_KEY not set"}

    prompts = {
        "tips": f"Generate 5 personalized eco-tips for someone in {req.city}. Context: {req.context}. Respond with JSON: {{\"tips\": [{{\"action\": \"...\", \"impact\": \"low|medium|high\", \"carbon_savings_kg\": N, \"category\": \"Transport|Energy|Food|Waste\"}}], \"motivation\": \"...\"}}",
        "carbon": f"Analyze carbon footprint for someone in {req.city}, context: {req.context}. Respond with JSON: {{\"estimate_kg_yearly\": N, \"strategies\": [{{\"action\": \"...\", \"savings_kg\": N}}], \"quick_wins\": [\"...\"]}}",
        "challenge": f"Create a fun 7-day eco-challenge. Respond with JSON: {{\"name\": \"...\", \"description\": \"...\", \"daily_tasks\": [{{\"day\": 1, \"task\": \"...\", \"points\": N}}], \"total_points\": N}}",
    }

    try:
        r = await http.post(
            f"{FLOCK_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {FLOCK_KEY}", "Content-Type": "application/json"},
            json={
                "model": "qwen3-30b-a3b-instruct-2507",
                "messages": [
                    {"role": "system", "content": "You are a sustainability expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompts.get(req.mode, prompts["tips"])},
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
            },
            timeout=60.0,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        # Strip <think> tags if present (thinking model)
        if "<think>" in content:
            import re
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        result = json.loads(content)
        result["model"] = "FLock.io (open-source)"
        result["type"] = req.mode
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse FLock response", "raw": content[:500]}
    except Exception as e:
        return {"error": f"FLock API error: {str(e)}"}

# ──────────────────────────────────────────────
# CHAT (Orchestrator)
# ──────────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Chat with GreenClaw — routes to the appropriate skill."""
    msg = req.message.lower()
    skill_used = "orchestrator"
    result = {}

    # Extract city from message if mentioned (e.g. "weather in Tokyo")
    city = req.city
    for prep in [" in ", " for ", " at ", " of "]:
        if prep in msg:
            potential_city = req.message.split(prep)[-1].strip().rstrip("?!.")
            if len(potential_city) > 1 and len(potential_city) < 50:
                city = potential_city
                break

    # Kids Mode routing (Imperial Bounty)
    if req.kids_mode:
        skill_used = "edu-mode"
        try:
            r = await http.post(
                f"{ZAI_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {ZAI_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "glm-4-plus",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are the GreenClaw Educator Agent 🎮. You are talking to a 7-year-old child who wants to learn about the planet. Answer playfully, use fun emojis, and keep your answer very short (2-3 sentences max). Explain complex climate concepts simply."
                        },
                        {"role": "user", "content": req.message},
                    ],
                    "temperature": 0.8,
                },
                timeout=60.0,
            )
            r.raise_for_status()
            summary = r.json()["choices"][0]["message"]["content"].strip()
            result = {"type": "edu-mode", "response": summary}
        except Exception as e:
            summary = get_edu_response(msg) # Fallback to hardcoded quiz
            result = {"type": "edu-mode", "response": summary, "error": str(e)}

    # Standard routing (only if not kids mode)
    elif any(w in msg for w in ["weather", "temperature", "air quality", "aqi", "pollution", "climate", "forecast"]):
        skill_used = "climate-monitor"
        result = await get_climate(city)
        summary = format_climate_summary(result)
    elif any(w in msg for w in ["risk", "danger", "threat", "hazard", "analyze", "assessment"]):
        skill_used = "risk-analyzer"
        result = await analyze_risk(city)
        summary = format_risk_summary(result)
    elif any(w in msg for w in ["tip", "advice", "eco", "sustainable", "green", "carbon", "reduce", "footprint"]):
        skill_used = "action-advisor"
        result = await get_advice(AdviceRequest(mode="tips", city=city))
        summary = format_advice_summary(result)
    elif any(w in msg for w in ["log", "track", "recycle", "planted", "walked", "biked"]):
        skill_used = "community-tracker"
        result = log_community_action(ActionLogRequest(user="chat_user", action=req.message))
        summary = f"✅ Logged your eco-action! {result.get('emoji', '🌍')} Estimated CO₂ saved: {result.get('co2_kg', 0)} kg"
    elif any(w in msg for w in ["quiz", "question", "learn", "teach", "kid", "edu", "fun fact"]):
        skill_used = "edu-mode"
        summary = get_edu_response(msg)
        result = {"type": "edu-mode", "response": summary}
    elif any(w in msg for w in ["disaster", "earthquake", "flood", "wildfire", "storm", "volcano"]):
        skill_used = "climate-monitor"
        disasters = await fetch_disasters()
        result = {"disasters": disasters}
        summary = format_disaster_summary(disasters)
    elif any(w in msg for w in ["hello", "hi", "hey", "help"]):
        summary = """👋 Hey! I'm **GreenClaw** 🌍🦞 — your AI climate action companion!

Here's what I can do:
🌡️ **"Weather in London"** — Real-time climate data
⚠️ **"Risk analysis for Delhi"** — AI-powered risk assessment (Z.AI GLM)
💚 **"Give me eco-tips"** — Sustainability advice (FLock.io)
📊 **"Log: I recycled today"** — Track your eco-actions
🎮 **"Quiz me!"** — Fun climate quiz

What would you like to know?"""
        result = {"type": "greeting"}
    else:
        summary = f"🤔 I'm not sure what you mean by that. Try asking about **weather**, **risk analysis**, **eco-tips**, or say **help** to see what I can do!"
        result = {"type": "fallback"}

    return {
        "reply": summary,
        "skill": skill_used,
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ──────────────────────────────────────────────
# COMMUNITY TRACKER
# ──────────────────────────────────────────────
CO2_ESTIMATES = {
    "recycle": (0.5, "♻️"), "recycled": (0.5, "♻️"), "compost": (0.3, "🪱"),
    "bike": (2.3, "🚲"), "cycle": (2.3, "🚲"), "walk": (0.8, "🚶"),
    "bus": (1.2, "🚌"), "train": (1.5, "🚆"), "carpool": (1.8, "🚗"),
    "vegan": (2.5, "🥗"), "vegetarian": (1.5, "🥗"), "plant": (5.0, "🌱"),
    "planted": (5.0, "🌱"), "tree": (22.0, "🌳"), "reusable": (0.2, "🛍️"),
    "led": (0.3, "💡"), "unplug": (0.4, "🔌"), "solar": (3.0, "☀️"),
    "shower": (0.5, "🚿"), "laundry": (0.3, "👕"),
}

@app.post("/api/community/log")
def log_community_action(req: ActionLogRequest):
    """Log an eco-action and estimate CO₂ savings."""
    co2 = 0.5
    emoji = "🌍"
    for keyword, (val, icon) in CO2_ESTIMATES.items():
        if keyword in req.action.lower():
            co2 = val
            emoji = icon
            break

    entry = {
        "user": req.user,
        "action": req.action,
        "co2_kg": co2,
        "emoji": emoji,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Persist
    actions = []
    if ACTIONS_FILE.exists():
        try:
            actions = json.loads(ACTIONS_FILE.read_text())
        except Exception:
            actions = []
    actions.append(entry)
    ACTIONS_FILE.write_text(json.dumps(actions, indent=2))
    return entry

@app.post("/api/community/register")
def register_user(req: RegisterRequest):
    """Registers a Telegram user for autonomous broadcasting."""
    users = {}
    if USERS_FILE.exists():
        try:
            users = json.loads(USERS_FILE.read_text())
        except Exception:
            pass
    users[str(req.chat_id)] = req.user
    USERS_FILE.write_text(json.dumps(users, indent=2))
    return {"success": True}

@app.post("/api/community/vision")
async def log_vision_action(req: VisionLogRequest):
    """Z.AI GLM-4V multimodality to verify eco-actions and FLock for reward tips."""
    if not ZAI_KEY:
        return {"error": "ZAI_API_KEY not set"}

    prompt = "You are an AI environmental judge. Look at this image. Describe what the person is doing to help the environment (e.g., recycling, using a reusable cup, taking public transit). Give this action a score from 1 to 10 for environmental impact. Respond ONLY in valid JSON format: {\"description\": \"<short description>\", \"score\": <number>}"
    
    try:
        # 1. Z.AI GLM-4V Vision Analysis
        r_zai = await http.post(
            f"{ZAI_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {ZAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "glm-4v-plus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{req.image_base64}"}}
                        ]
                    }
                ],
                "temperature": 0.5
            },
            timeout=60.0,
        )
        r_zai.raise_for_status()
        
        zai_content = r_zai.json()["choices"][0]["message"]["content"].strip()
        if zai_content.startswith("```json"):
            zai_content = zai_content[7:-3].strip()
        elif zai_content.startswith("```"):
            zai_content = zai_content[3:-3].strip()
            
        zai_data = json.loads(zai_content)
        desc = zai_data.get("description", "Unknown eco action")
        score = zai_data.get("score", 5)
        
        # 2. FLock Personalized Tip Generation
        flock_msg = f"A user just completed this eco-action: {desc}. Write a short, punchy 1-sentence personalized congratulatory message and a tip for them."
        tip = "Great job helping the planet!"
        if FLOCK_KEY:
            try:
                r_flock = await http.post(
                    f"{FLOCK_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {FLOCK_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "qwen/qwen2.5-72b-instruct",
                        "messages": [{"role": "user", "content": flock_msg}],
                        "max_tokens": 100,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                if r_flock.status_code == 200:
                    tip = r_flock.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"FLock tip error: {e}")

        # 3. Log the verified action
        co2_saved = score * 2.5
        entry = {
            "user": req.user,
            "action": f"[Verified Photo] {desc}",
            "co2_kg": round(co2_saved, 2),
            "emoji": "📸",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        actions = []
        if ACTIONS_FILE.exists():
            try:
                actions = json.loads(ACTIONS_FILE.read_text())
            except Exception:
                pass
        actions.append(entry)
        ACTIONS_FILE.write_text(json.dumps(actions, indent=2))
        
        return {
            "success": True,
            "description": desc,
            "score": score,
            "co2_kg": entry["co2_kg"],
            "tip": tip
        }
        
    except Exception as e:
        print(f"Vision API Error: {e}")
        return {"error": str(e)}

@app.get("/api/community/stats")
def community_stats():
    """Get community impact statistics."""
    actions = []
    if ACTIONS_FILE.exists():
        try:
            actions = json.loads(ACTIONS_FILE.read_text())
        except Exception:
            actions = []

    total_co2 = sum(a.get("co2_kg", 0) for a in actions)
    user_stats = {}
    for a in actions:
        u = a.get("user", "anonymous")
        user_stats[u] = user_stats.get(u, 0) + a.get("co2_kg", 0)

    leaderboard = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_actions": len(actions),
        "total_co2_kg": round(total_co2, 2),
        "equivalents": {
            "trees_equivalent": round(total_co2 / 22, 1),
            "car_km_saved": round(total_co2 / 0.21),
            "flights_offset": round(total_co2 / 250, 2),
        },
        "leaderboard": [{"user": u, "co2_kg": round(v, 2)} for u, v in leaderboard],
        "recent": actions[-10:][::-1],
    }

# ──────────────────────────────────────────────
# MULTI-AGENT CONVERSATION SYSTEM
# 4 Named Agents that explicitly communicate:
#   🛰️ Sentinel  — Environmental Monitor (scans data)
#   🧠 Analyst   — Risk Intelligence (Z.AI GLM deep reasoning)
#   💚 Advisor   — Sustainability Coach (FLock open-source advice)
#   📢 Dispatcher — Alert Controller (pushes to channels)
# ──────────────────────────────────────────────

AGENTS = {
    "sentinel":   {"name": "Sentinel",   "icon": "🛰️", "role": "Environmental Monitor",  "color": "#60a5fa"},
    "analyst":    {"name": "Analyst",    "icon": "🧠", "role": "Risk Intelligence",       "color": "#fbbf24"},
    "advisor":    {"name": "Advisor",    "icon": "💚", "role": "Sustainability Coach",    "color": "#4ade80"},
    "dispatcher": {"name": "Dispatcher", "icon": "📢", "role": "Alert Controller",        "color": "#f87171"},
    "orchestrator": {"name": "Orchestrator", "icon": "🤖", "role": "Pipeline Controller", "color": "#a78bfa"},
}

agent_conversation: list[dict] = []
MAX_CONV = 80

@app.get("/api/alerts")
def get_alerts():
    """Get active climate alerts."""
    return {"alerts": active_alerts, "count": len(active_alerts)}

@app.get("/api/pipeline/log")
def get_pipeline_log():
    """Legacy compat — converts agent conversation to event format."""
    events = []
    for msg in agent_conversation[-20:]:
        events.append({
            "type": msg.get("action", "message"),
            "city": msg.get("city", "global"),
            "detail": msg.get("text", ""),
            "data": msg.get("data", {}),
            "timestamp": msg.get("timestamp", ""),
        })
    return {"events": events, "total": len(agent_conversation)}

@app.get("/api/agents/conversation")
def get_agent_conversation():
    """Get the multi-agent conversation — the core differentiator."""
    return {
        "agents": AGENTS,
        "messages": agent_conversation[-30:],
        "total": len(agent_conversation),
    }

def agent_says(agent_id: str, text: str, city: str = "global", action: str = "message",
               to: str = None, data: dict = None):
    """An agent speaks in the shared conversation."""
    agent = AGENTS.get(agent_id, AGENTS["orchestrator"])
    entry = {
        "agent": agent_id, "name": agent["name"], "icon": agent["icon"],
        "role": agent["role"], "color": agent["color"],
        "text": text, "city": city, "action": action,
        "to": to, "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    agent_conversation.append(entry)
    if len(agent_conversation) > MAX_CONV:
        agent_conversation.pop(0)
    to_str = f" → @{to}" if to else ""
    print(f"  {agent['icon']} {agent['name']}{to_str}: {text}")

async def autonomous_pipeline():
    """
    MULTI-AGENT AUTONOMOUS PIPELINE
    Agents communicate and hand off work to each other.
    """
    await asyncio.sleep(5)
    cycle = 0

    while True:
        cycle += 1

        # ── ORCHESTRATOR announces cycle ──
        agent_says("orchestrator",
            f"Starting monitoring cycle #{cycle}. Sentinel, scan all monitored cities.",
            action="cycle_start", to="sentinel")
        await asyncio.sleep(0.5)

        new_alerts = []
        high_risk_cities = []

        # ── SENTINEL scans cities ──
        agent_says("sentinel",
            f"Roger. Scanning {len(alert_cities)} cities...",
            action="scan_start")

        for city in alert_cities:
            try:
                aqi = await fetch_aqi(city)
                val = aqi.get("value", 0)
                weather = await fetch_weather(city)
                temp = weather.get("temp", 20)
                cond = weather.get("condition", "Unknown")

                if isinstance(val, (int, float)) and val > 100:
                    severity = "warning" if val < 150 else "danger"

                    if val > 150:
                        agent_says("sentinel",
                            f"🚨 {city}: AQI {val} ({aqi.get('category', '?')}), "
                            f"exceeds WHO limit by {val - 50}%. Temp {temp}°C. Flagging for deep analysis.",
                            city=city, action="threshold_breach",
                            data={"aqi": val, "temp": temp, "severity": "danger"})
                        high_risk_cities.append({
                            "city": city, "aqi": val, "temp": temp,
                            "weather": weather, "aqi_data": aqi
                        })
                    else:
                        agent_says("sentinel",
                            f"⚠️ {city}: AQI {val} ({aqi.get('category', '?')}), "
                            f"temp {temp}°C. Above moderate threshold.",
                            city=city, action="threshold_breach",
                            data={"aqi": val, "temp": temp, "severity": "warning"})

                    new_alerts.append({
                        "type": "aqi", "city": city, "severity": severity,
                        "message": f"⚠️ {city}: AQI {val} ({aqi.get('category', 'Unknown')}). {aqi.get('advice', '')}",
                        "value": val,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                if isinstance(temp, (int, float)) and temp > 40:
                    agent_says("sentinel",
                        f"🔥 {city}: {temp}°C — extreme heat! Flagging immediately.",
                        city=city, action="heat_alert")
                    new_alerts.append({
                        "type": "heat", "city": city, "severity": "danger",
                        "message": f"🔥 {city}: {temp}°C! Stay hydrated, avoid outdoors.",
                        "value": temp,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    if city not in [c["city"] for c in high_risk_cities]:
                        high_risk_cities.append({
                            "city": city, "aqi": val, "temp": temp,
                            "weather": weather, "aqi_data": aqi
                        })

            except Exception as e:
                agent_says("sentinel", f"Scan error for {city}: {str(e)[:60]}",
                           city=city, action="error")

        # Sentinel hands off
        if high_risk_cities:
            agent_says("sentinel",
                f"Scan done. {len(new_alerts)} alerts. "
                f"@Analyst — need deep analysis on: {', '.join(c['city'] for c in high_risk_cities)}",
                action="handoff", to="analyst")
        elif new_alerts:
            agent_says("sentinel",
                f"Scan done. {len(new_alerts)} moderate alerts, no critical cities.",
                action="scan_complete")
        else:
            agent_says("sentinel",
                f"All {len(alert_cities)} cities safe. ✅", action="all_clear")

        # ── ANALYST runs Z.AI ──
        for risk_city in high_risk_cities[:2]:
            city_name = risk_city["city"]

            agent_says("analyst",
                f"Copy. Running Z.AI GLM-4-Plus on {city_name} "
                f"(AQI {risk_city['aqi']}, {risk_city['temp']}°C)...",
                city=city_name, action="analyzing", to="sentinel")

            try:
                risk_result = await analyze_risk(city_name)
                score = risk_result.get("score", 0)
                level = risk_result.get("level", "Unknown")
                recs = risk_result.get("recommendations", [])

                agent_says("analyst",
                    f"{city_name}: Risk **{score}/10 ({level})**. "
                    f"Key: {recs[0] if recs else 'Monitor closely'}. "
                    f"@Advisor — generate protective recommendations.",
                    city=city_name, action="analysis_complete", to="advisor",
                    data={"score": score, "level": level, "model": "Z.AI GLM-4-Plus"})

                for alert in new_alerts:
                    if alert["city"] == city_name:
                        alert["analysis"] = {"score": score, "level": level, "recommendations": recs[:3]}
                        alert["message"] += f"\n🧠 Z.AI: Risk {score}/10 ({level})"
                        if recs:
                            alert["message"] += f"\n→ {recs[0]}"

            except Exception as e:
                agent_says("analyst",
                    f"Z.AI failed for {city_name}: {str(e)[:60]}. "
                    f"@Advisor — use general safety recs.",
                    city=city_name, action="error", to="advisor")

            # ── ADVISOR generates FLock tips ──
            if FLOCK_KEY:
                agent_says("advisor",
                    f"Querying FLock qwen3-30b for {city_name} "
                    f"(AQI {risk_city['aqi']}, {risk_city['temp']}°C)...",
                    city=city_name, action="advising")

                try:
                    advice_result = await get_advice(AdviceRequest(
                        mode="tips", city=city_name,
                        context=f"AQI is {risk_city['aqi']}, temperature is {risk_city['temp']}°C"
                    ))
                    if "tips" in advice_result:
                        tips = [t.get("action", "") for t in advice_result["tips"][:3]]
                        agent_says("advisor",
                            f"FLock: {len(advice_result.get('tips', []))} tips for {city_name}. "
                            f"Top: \"{tips[0]}\". "
                            f"@Dispatcher — push alerts with analysis + tips.",
                            city=city_name, action="advice_ready", to="dispatcher",
                            data={"tips": tips, "model": "FLock qwen3-30b"})

                        for alert in new_alerts:
                            if alert["city"] == city_name:
                                alert["advice"] = tips
                                if tips:
                                    alert["message"] += f"\n💚 Tip: {tips[0]}"
                    elif "error" in advice_result:
                        agent_says("advisor",
                            f"FLock error: {advice_result['error'][:40]}",
                            city=city_name, action="error")
                except Exception as e:
                    agent_says("advisor", f"FLock error: {str(e)[:40]}",
                               city=city_name, action="error")

            await asyncio.sleep(1)

        # ── DISPATCHER pushes alerts ──
        active_alerts.clear()
        active_alerts.extend(new_alerts)

        if new_alerts:
            enriched = sum(1 for a in new_alerts if a.get("analysis"))
            agent_says("dispatcher",
                f"Published {len(new_alerts)} alerts. "
                f"{enriched} enriched with Z.AI + FLock. "
                f"Channels: Dashboard ✅"
                + (f", Telegram ({len(high_risk_cities)} critical) 📨" if high_risk_cities else ""),
                action="alerts_pushed",
                data={"count": len(new_alerts)})
                
            # TRUE AUTONOMOUS BROADCASTING TO TELEGRAM
            telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if telegram_bot_token and USERS_FILE.exists():
                try:
                    registered_users = json.loads(USERS_FILE.read_text())
                    for alert in new_alerts:
                        if alert.get("severity") == "danger":
                            msg = f"🚨 *URGENT AUTONOMOUS ALERT* 🚨\n\n**{alert['city']}**: {alert['message']}\n\n"
                            if "analysis" in alert:
                                msg += f"🧠 *Z.AI Analysis:* Risk {alert['analysis']['score']}/10 ({alert['analysis']['level']})\n"
                            if "advice" in alert and alert["advice"]:
                                msg += f"💚 *FLock Tip:* {alert['advice'][0]}\n"
                                
                            for chat_id in registered_users.keys():
                                try:
                                    await http.post(
                                        f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                                        json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
                                        timeout=10.0
                                    )
                                except Exception as e:
                                    print(f"Broadcast failed for {chat_id}: {e}")
                except Exception as e:
                    print(f"Error broadcasting to telegram: {e}")

        else:
            agent_says("dispatcher", "No alerts needed. All clear. 🟢", action="all_clear")

        # ── ORCHESTRATOR closes ──
        agent_says("orchestrator",
            f"Cycle #{cycle} done. {len(new_alerts)} alerts, "
            f"{len(high_risk_cities)} deep analyses. Next scan in 5 min.",
            action="cycle_end")

        await asyncio.sleep(300)



# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────
def weather_emoji(condition: str) -> str:
    m = {"Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Drizzle": "🌦️", "Thunderstorm": "⛈️",
         "Snow": "❄️", "Mist": "🌫️", "Fog": "🌫️", "Haze": "🌫️", "Smoke": "💨", "Dust": "🌪️"}
    return m.get(condition, "🌍")

def disaster_emoji(categories: list) -> str:
    m = {"Wildfires": "🔥", "Severe Storms": "🌪️", "Volcanoes": "🌋", "Floods": "🌊",
         "Earthquakes": "🫨", "Drought": "🏜️", "Dust and Haze": "🌫️", "Sea and Lake Ice": "🧊",
         "Snow": "❄️", "Landslides": "⛰️", "Temperature Extremes": "🌡️"}
    for cat in categories:
        if cat in m:
            return m[cat]
    return "⚠️"

def aqi_category(val: int) -> tuple[str, str]:
    if val <= 50: return "Good", "🟢"
    if val <= 100: return "Moderate", "🟡"
    if val <= 150: return "Unhealthy for Sensitive Groups", "🟠"
    if val <= 200: return "Unhealthy", "🔴"
    if val <= 300: return "Very Unhealthy", "🟣"
    return "Hazardous", "⚫"

def aqi_advice(category: str) -> str:
    m = {
        "Good": "Air quality is satisfactory. Enjoy outdoor activities! 🌳",
        "Moderate": "Acceptable. Sensitive individuals should limit prolonged outdoor exertion.",
        "Unhealthy for Sensitive Groups": "Members of sensitive groups may experience health effects. Limit prolonged outdoor exertion.",
        "Unhealthy": "Everyone may experience health effects. Limit outdoor exertion. Wear masks outdoors. 😷",
        "Very Unhealthy": "Health alert! Everyone should avoid outdoor exertion. Stay indoors.",
        "Hazardous": "Emergency conditions! Everyone should avoid all outdoor activity. 🚨",
    }
    return m.get(category, "Check local air quality guidelines.")

def format_climate_summary(data: dict) -> str:
    w = data.get("weather", {})
    a = data.get("aqi", {})
    if "error" in w:
        return f"⚠️ Could not fetch weather data: {w['error']}"
    lines = [
        f"🌡️ **{data['city']}** — {w.get('condition', 'N/A')} {w.get('icon', '')}",
        f"**Temperature:** {w.get('temp', 'N/A')}°C (feels like {w.get('feels', 'N/A')}°C)",
        f"**Humidity:** {w.get('humidity', 'N/A')}% · **Wind:** {w.get('wind', 'N/A')} m/s",
    ]
    if a and "error" not in a:
        lines.append(f"**Air Quality:** {a.get('icon', '')} AQI {a.get('value', 'N/A')} — {a.get('category', 'N/A')}")
        lines.append(f"_{a.get('advice', '')}_")
    return "\n".join(lines)

def format_risk_summary(data: dict) -> str:
    if "error" in data:
        return f"⚠️ Risk analysis error: {data['error']}"
    lines = [
        f"⚠️ **Risk Assessment** — Score: **{data.get('score', '?')}/10** ({data.get('level', '?')})",
        f"_Confidence: {data.get('confidence', '?')} · Model: {data.get('model', 'Z.AI')}_",
        "",
    ]
    for r in data.get("risks", []):
        lines.append(f"• **{r['category']}** ({r['score']}/10): {r['desc']}")
    lines.append("\n**Recommendations:**")
    for rec in data.get("recommendations", []):
        lines.append(f"  → {rec}")
    if data.get("sdg13"):
        lines.append(f"\n🌍 **SDG 13:** {data['sdg13']}")
    return "\n".join(lines)

def format_advice_summary(data: dict) -> str:
    if "error" in data:
        return f"⚠️ Could not get advice: {data['error']}"
    lines = ["💚 **Eco-Tips for You:**\n"]
    for i, tip in enumerate(data.get("tips", []), 1):
        impact = {"low": "🌱", "medium": "🌿", "high": "🌳"}.get(tip.get("impact", ""), "🌍")
        lines.append(f"{i}. {impact} {tip.get('action', '')} — saves ~{tip.get('carbon_savings_kg', '?')} kg CO₂/year")
    if data.get("motivation"):
        lines.append(f"\n_{data['motivation']}_")
    return "\n".join(lines)

def format_disaster_summary(disasters: list) -> str:
    if not disasters:
        return "✅ No active disasters detected globally!"
    lines = [f"🚨 **{len(disasters)} Active Disasters:**\n"]
    for d in disasters[:6]:
        lines.append(f"  {d['icon']} **{d['title']}** ({d.get('date', 'recent')})")
    return "\n".join(lines)

QUIZ_QUESTIONS = [
    {"q": "🌍 What gas do trees absorb from the atmosphere?", "a": "Carbon Dioxide (CO₂)", "fact": "A single tree absorbs about 22 kg of CO₂ per year!"},
    {"q": "☀️ What is the largest source of renewable energy?", "a": "Solar energy", "fact": "The sun produces enough energy in 1 second to power Earth for 500,000 years!"},
    {"q": "🌊 What percentage of Earth's surface is water?", "a": "About 71%", "fact": "The ocean absorbs 30% of the CO₂ we produce!"},
    {"q": "🔋 Which country generates the most wind energy?", "a": "China", "fact": "A single wind turbine can power 1,500 homes!"},
    {"q": "🐋 How is a whale helpful for fighting climate change?", "a": "A whale captures ~33 tonnes of CO₂ in its lifetime!", "fact": "Whales are like swimming carbon sinks!"},
]

FUN_FACTS = [
    "🐋 A single large whale captures about 33 TONS of CO₂ over its lifetime!",
    "🌱 If every family in the UK planted one tree, it would capture 5 million tonnes of CO₂!",
    "🚲 Biking 10 km instead of driving saves about 2.3 kg of CO₂!",
    "🌊 The ocean absorbs about 30% of the CO₂ we produce — it's Earth's giant sponge!",
    "⚡ A wind turbine can power 1,500 homes for a whole year!",
    "🌳 The Amazon rainforest produces 20% of the world's oxygen!",
    "🐝 Bees pollinate 75% of the food we eat — protect the bees, protect our food!",
]

import random
def get_edu_response(msg: str) -> str:
    if "quiz" in msg or "question" in msg:
        q = random.choice(QUIZ_QUESTIONS)
        return f"🎮 **Climate Quiz Time!**\n\n{q['q']}\n\n_Think about it, then ask me for the answer!_\n\n💡 **Fun Fact:** {q['fact']}"
    elif "fact" in msg:
        return f"🌟 **Did You Know?**\n\n{random.choice(FUN_FACTS)}"
    else:
        q = random.choice(QUIZ_QUESTIONS)
        return f"🎮 **Welcome to Edu Mode!** Let's learn about our planet!\n\n{q['q']}\n\n💡 **Fun Fact:** {random.choice(FUN_FACTS)}"

# ──────────────────────────────────────────────
# SERVE LANDING PAGE + DASHBOARD
# ──────────────────────────────────────────────
DASHBOARD_DIR = Path(__file__).parent / "dashboard"
LANDING_FILE = Path(__file__).parent / "landing.html"

@app.get("/")
async def serve_landing():
    return FileResponse(LANDING_FILE)

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")

app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

# Serve CSS/JS directly
@app.get("/dashboard.css")
async def serve_css():
    return FileResponse(DASHBOARD_DIR / "dashboard.css", media_type="text/css")

@app.get("/dashboard.js")
async def serve_js():
    return FileResponse(DASHBOARD_DIR / "dashboard.js", media_type="application/javascript")

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🌍🦞 GreenClaw v2 — Starting server...")
    print("   Dashboard: http://localhost:8000")
    print("   API Docs:  http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
