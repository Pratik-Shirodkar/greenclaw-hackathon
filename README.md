# 🌍🦞 GreenClaw — Multi-Agent Climate Action System

> **A multi-agent AI system for climate action, built on [OpenClaw](https://openclaw.ai)**
> 
> _UK AI Agent Hackathon EP4 × OpenClaw — Special Edition_

[![OpenClaw](https://img.shields.io/badge/Built%20on-OpenClaw-orange)](https://openclaw.ai)
[![Z.AI](https://img.shields.io/badge/Powered%20by-Z.AI%20GLM-blue)](https://z.ai)
[![FLock](https://img.shields.io/badge/Inference-FLock.io-green)](https://flock.io)
[![SDG 13](https://img.shields.io/badge/UN%20SDG-13%20Climate%20Action-brightgreen)](https://sdgs.un.org/goals/goal13)

---

## 🎯 What is GreenClaw?

GreenClaw is a **multi-agent climate action AI assistant** that helps communities monitor, understand, and act on environmental data. It combines real-time climate monitoring, AI-powered risk analysis, personalized sustainability advice, community impact tracking, and kid-friendly climate education — all through your favorite messaging platforms.

### Architecture

```
User (Telegram / WhatsApp / CLI)
         │
         ▼
┌──────────────────────────┐
│    OpenClaw Gateway      │
│    (Orchestrator)        │
└──────────┬───────────────┘
           │
    ┌──────┼──────┬──────────┬──────────┐
    ▼      ▼      ▼          ▼          ▼
🌡️ Climate  ⚠️ Risk    💚 Action    📊 Community  🎮 Edu
  Monitor   Analyzer   Advisor     Tracker      Mode
    │         │          │           │            │
    ▼         ▼          ▼           ▼            ▼
OpenWeather  Z.AI GLM   FLock API   Local JSON   Built-in
WAQI API     (Reasoning) (Open-src) (Impact DB)  Knowledge
NASA EONET
```

### Agent Skills

| Agent | Purpose | Technology |
|---|---|---|
| 🌡️ **Climate Monitor** | Real-time weather, AQI, disaster alerts | OpenWeatherMap, WAQI, NASA EONET APIs |
| ⚠️ **Risk Analyzer** | AI-powered climate risk assessment | Z.AI GLM-4.5 (thinking mode) |
| 💚 **Action Advisor** | Personalized sustainability recommendations | FLock API (open-source models) |
| 📊 **Community Tracker** | Log eco-actions, track collective impact | Local JSON storage |
| 🎮 **Edu Mode** | Kid-friendly climate education & quizzes | Built-in knowledge base |

---

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) ≥ 22
- [Python](https://python.org/) ≥ 3.9
- [OpenClaw](https://openclaw.ai) installed (`npm install -g openclaw@latest`)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/greenclaw.git
cd greenclaw
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENWEATHER_API_KEY (free: https://openweathermap.org/api)
# - WAQI_API_KEY (free: https://aqicn.org/data-platform/token/)
# - ZAI_API_KEY (https://open.bigmodel.cn/)
# - FLOCK_API_KEY (https://flock.io/)
```

### 3. Install Skills into OpenClaw

```bash
# Copy skills to your OpenClaw workspace
cp -r skills/* ~/.openclaw/workspace/skills/

# Copy the orchestrator
cp AGENTS.md ~/.openclaw/workspace/AGENTS.md
```

### 4. Run & Multi-Channel Deployment (Telegram)

GreenClaw supports Multi-Channel deployment as required by the FLock track.

```bash
# 1. Local Interactive CLI
openclaw agent --message "What's the air quality in London?"

# 2. Live Dashboard Web UI
python -m http.server 8080 --directory dashboard

# 3. Telegram Bot (Multi-Channel)
# Ensure you have your Telegram Bot Token in .env
openclaw gateway --port 18789 --channel telegram --token "<YOUR_TELEGRAM_BOT_TOKEN>"
```

---

## 🏆 Hackathon Bounty Alignment

| Track | Sponsor | How GreenClaw Qualifies |
|---|---|---|
| **AI Agents for Good** | FLock.io ($5,000) | ✅ OpenClaw + FLock API + open-source models + SDG 13 + multi-channel |
| **General Bounty** | Z.AI ($4,000) | ✅ GLM-4.5 as core reasoning engine for risk analysis |
| **Best Multi-Agent System** | Animoca ($500) | ✅ 5-agent coordinated system with identity & memory |
| **Claw for Human** | Imperial ($500) | ✅ Showcases OpenClaw's multi-agent capabilities |
| **Human for Claw** | Imperial ($500) | ✅ Kid-friendly edu-mode for children to interact with |

---

## 🏅 Z.AI Bounty Track Evidence

This project is submitted for the **"Production-Ready AI Agents Powered by Z.AI"** bounty ($4,000 track). 

GreenClaw integrates Z.AI deeply into its core architecture:
- **Deep Reasoning (Skill Level):** The **Risk Analyzer** skill uses Z.AI GLM-4.5's advanced reasoning capabilities to analyze complex, multi-variable climate data (Weather, AQI, Disaster feeds). It leverages a custom "Thinking Mode" simulation in the Live Dashboard to visually demonstrate the model's complex reasoning chain.

---

## 🏅 FLock Bounty Track Evidence

This project is also submitted for the **"FLock Track"** ($2,000 Gold prize).

GreenClaw strictly follows all FLock track requirements:
1. **Autonomous Agents on OpenClaw:** The system runs as an autonomous multi-agent mesh using the OpenClaw framework.
2. **SDG-Aligned with Real-world Impact:** Directly targets **SDG 13 (Climate Action)** and **SDG 11 (Sustainable Cities)**. The Community Tracker skill measures real-world impact (CO₂ savings in kg).
3. **FLock API & Open-source Models Only:** The **Action Advisor** and **Community Tracker** operations, as well as the main orchestrator routing, are powered exclusively by FLock's open-source models (e.g., `flock/qwen3-235b-a22b-thinking-2507`). We strictly avoid closed-source models for these core interactive components.
4. **Multi-channel Deployment:** Fully configured for both Web UI (Dashboard) and **Telegram** (via OpenClaw Gateway) to reach communities where they are.

---

## 🌟 Killer Features (Built for Hackathon)

1. **Vision AI Eco-Action Proof (Z.AI GLM-4V)**: Send a picture of your eco-friendly action to the Telegram bot. The bot uses Z.AI's multimodal vision model to verify the action, assign an environmental score, and award CO₂ offset points. FLock.io then generates a personalized congratulatory tip.
2. **True Autonomous Broadcasting**: GreenClaw continuously monitors NASA EONET and the World Air Quality Index in the background. If critical thresholds are breached (e.g. AQI > 150), the Dispatcher Agent autonomously pushes alerts via Telegram to all registered users without requiring any prompt.
3. **Interactive 3D Threat Map Globe**: A bespoke `globe.gl` container on the dashboard visualizes the live active NASA disasters (red rings) and your current city's AQI status (orange/green rings) on an interactive 3D Earth.
4. **Kids Mode (Imperial Bounty)**: A specialized Educator Agent (accessible via dashboard toggle) simplifies complex climate science into fun, interactive analogies and quizzes suitable for children, fulfilling the "Human for Claw" bounty requirements.

---

## 📁 Project Structure

```
greenclaw/
├── AGENTS.md                          # Orchestrator agent prompt
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # API key template
├── config/
│   └── openclaw.example.json          # Example OpenClaw config
└── skills/
    ├── climate-monitor/
    │   ├── SKILL.md                   # Skill definition
    │   └── scripts/
    │       └── fetch_climate.py       # Weather/AQI/disaster APIs
    ├── risk-analyzer/
    │   ├── SKILL.md                   # Skill definition
    │   └── scripts/
    │       └── analyze_risk.py        # Z.AI GLM risk analysis
    ├── action-advisor/
    │   ├── SKILL.md                   # Skill definition
    │   └── scripts/
    │       └── advise_action.py       # FLock sustainability advice
    ├── community-tracker/
    │   ├── SKILL.md                   # Skill definition
    │   └── scripts/
    │       └── tracker.py             # Impact tracking & logging
    └── edu-mode/
        └── SKILL.md                   # Kid-friendly climate education
```

---

## 🌱 UN SDG Alignment

GreenClaw directly contributes to:

- **SDG 13 — Climate Action**: Real-time climate monitoring, risk assessment, and actionable recommendations
- **SDG 11 — Sustainable Cities**: Air quality monitoring, urban environmental tracking
- **SDG 4 — Quality Education**: Kid-friendly climate education through edu-mode
- **SDG 17 — Partnerships**: Multi-channel deployment enabling community coordination

---

## 🛠️ Technologies Used

- **[OpenClaw](https://openclaw.ai)** — Agent framework & orchestration
- **[Z.AI GLM-4.5](https://z.ai)** — AI reasoning & risk analysis (thinking mode)
- **[FLock.io](https://flock.io)** — Open-source model inference for recommendations
- **[OpenWeatherMap](https://openweathermap.org)** — Weather data
- **[WAQI](https://waqi.info)** — Air quality data
- **[NASA EONET](https://eonet.gsfc.nasa.gov)** — Natural disaster events

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

_Built with 🦞 for the UK AI Agent Hackathon EP4 × OpenClaw_
