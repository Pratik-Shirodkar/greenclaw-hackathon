# 🌍🦞 GreenClaw — Multi-Agent Climate Action Intelligence

> **An autonomous multi-agent AI system for real-time climate action, built on [OpenClaw](https://openclaw.ai)**
> 
> _UK AI Agent Hackathon EP4 × OpenClaw — Special Edition_

[![OpenClaw](https://img.shields.io/badge/Built%20on-OpenClaw-orange)](https://openclaw.ai)
[![Z.AI](https://img.shields.io/badge/Powered%20by-Z.AI%20GLM--4.5-blue)](https://z.ai)
[![FLock](https://img.shields.io/badge/Inference-FLock.io-green)](https://flock.io)
[![Ethereum](https://img.shields.io/badge/NFTs-Ethereum%20Sepolia-purple)](https://sepolia.etherscan.io)
[![SDG 13](https://img.shields.io/badge/UN%20SDG-13%20Climate%20Action-brightgreen)](https://sdgs.un.org/goals/goal13)

---

## 🎯 What is GreenClaw?

GreenClaw is a **fully autonomous climate operations center** — 6 specialized AI agents that **monitor, analyze, and protect your city 24/7 without any human input**. It combines real-time multi-vector climate telemetry, Z.AI-powered risk analysis, FLock-powered algorithmic directives, on-chain Ethereum credentials, decentralized network ops tracking, carbon footprint calculation, historical trend analysis, and UK government flood alerts — all accessed through a premium Web3 operator console and Telegram bot.

### Architecture

```
User (Web Dashboard / Telegram Bot / CLI)
         │
         ▼
┌──────────────────────────────┐
│    OpenClaw Gateway          │
│    (Autonomous Orchestrator) │
└──────────┬───────────────────┘
           │
    ┌──────┼──────┬──────────┬──────────┬──────────┐
    ▼      ▼      ▼          ▼          ▼          ▼
 🌡️ Climate ⚠️ Risk   💚 Action   📊 Community  🎮 Edu   🧮 Carbon
  Monitor   Analyzer  Advisor    Tracker      Mode   Calculator
    │         │          │           │          │        │
    ▼         ▼          ▼           ▼          ▼        ▼
OpenWeather  Z.AI GLM  FLock API  Local JSON  Built-in FLock API
WAQI API    (Reasoning) (Open-src) (Impact)   Knowledge (Reduction)
NASA EONET           ↓
UK Env Agency   Ethereum Sepolia
                Blockchain (NFTs)
```

### 6 Agent Skills

| Agent | Purpose | Technology |
|---|---|---|
| 🌡️ **Climate Monitor** | Real-time weather, AQI, disaster alerts, **historical trends** | OpenWeatherMap, WAQI, NASA EONET, UK Environment Agency |
| ⚠️ **Risk Analyzer** | AI-powered climate risk assessment with thinking chain | Z.AI GLM-4.5 (thinking mode) |
| 💚 **Action Advisor** | Personalized sustainability recommendations | FLock API (qwen3-30b open-source) |
| 📊 **Community Tracker** | Log eco-actions, track collective impact, **leaderboard** | Local JSON + anti-abuse detection |
| 🎮 **Edu Mode** | Kid-friendly climate education & quizzes | Built-in knowledge base |
| 🧮 **Carbon Calculator** | **Annual carbon footprint estimation + AI reduction strategies** | FLock API + emission factors |

---

## 🌟 Killer Features

### Core Intelligence
1. **True Autonomous Agent Pipeline** — 5 named agents (Sentinel → Analyst → Advisor → Dispatcher → Orchestrator) communicate and hand off work every cycle with zero human input
2. **Z.AI GLM-4.5 Risk Reasoning** — Deep risk analysis with visual thinking chain showing the model's reasoning process live in the dashboard
3. **Vision AI Operations Verification (Z.AI GLM-4V)** — Send a photo to Telegram → Z.AI Vision verifies the field operation → awards Network Credits
4. **Interactive 3D Globe Threat Map** — `globe.gl` visualization of live NASA disasters and city AQI status

### Gamification & Web3
5. **On-Chain Credentials** — Milestone clearance levels minted as ERC-721 NFTs on Ethereum Sepolia Testnet
6. **Network Credits ($GREEN)** — Earn credits for broadcasting field operations with uptime streak multipliers (1.5×/2×/3× for 3/7/14-day uptime)
7. **Active Bounties System** — XP-based protocol directives with clearance level progression (Node Novice → Omni-Clearance)
8. **Anti-Abuse System** — Harmful or invalid operations are caught by Z.AI Vision and rejected by the network.

### New Features (4 Medium-Effort)
9. **🧮 Carbon Footprint Calculator** — Input transport/diet/energy/flights → get annual CO₂ estimate, comparison vs UK & global averages, and FLock AI-powered reduction strategies
10. **📈 Historical Climate Trends** — Chart.js dual-axis line chart tracking AQI and temperature over time for any city
11. **📤 Shareable Impact Cards** — Beautiful HTML card showing your rank, CO₂ saved, badges, and equivalents — downloadable as PNG
12. **🏛️ Localized Policy Alerts** — Real UK Environment Agency flood warnings with severity-coded display (no API key needed)

---

## 🚀 Quick Start

### Prerequisites

- [Python](https://python.org/) ≥ 3.9
- [Node.js](https://nodejs.org/) ≥ 22 (for OpenClaw CLI)
- [OpenClaw](https://openclaw.ai) installed (`npm install -g openclaw@latest`)

### 1. Clone & Install

```bash
git clone https://github.com/Pratik-Shirodkar/greenclaw-hackathon.git
cd greenclaw-hackathon
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
# - TELEGRAM_BOT_TOKEN (from @BotFather)
# - MINTER_PRIVATE_KEY (for Ethereum Sepolia NFT minting)
```

### 3. Run

```bash
# Start the server (Dashboard + API + Autonomous Pipeline)
python server.py

# In a separate terminal, start the Telegram bot
python telegram_bot.py
```

Then open:
- **Dashboard**: http://localhost:8000/dashboard
- **Landing Page**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🏆 Hackathon Bounty Alignment

| Track | Sponsor | How GreenClaw Qualifies |
|---|---|---|
| **AI Agents for Good** | FLock.io ($5,000) | ✅ OpenClaw + FLock API + open-source models + SDG 13 + multi-channel |
| **General Bounty** | Z.AI ($4,000) | ✅ GLM-4.5 as core reasoning engine for risk analysis + GLM-4V for vision proof |
| **Best Multi-Agent System** | Animoca ($500) | ✅ 6-agent coordinated system with named pipeline communication |
| **Claw for Human** | Imperial ($500) | ✅ Showcases OpenClaw's multi-agent orchestration capabilities |
| **Human for Claw** | Imperial ($500) | ✅ Kid-friendly edu-mode for children to interact with |

---

## 🏅 Z.AI Bounty Track Evidence

**"Production-Ready AI Agents Powered by Z.AI"** ($4,000 track)

GreenClaw integrates Z.AI deeply into its core architecture:
- **Deep Reasoning (Risk Analyzer):** Z.AI GLM-4.5's advanced reasoning analyzes complex, multi-variable climate data (Weather, AQI, Disasters). Live "Thinking Mode" visualization in the dashboard shows the model's reasoning chain
- **Multimodal Vision (Telegram Bot):** Z.AI GLM-4V verifies field operation photos for proof-of-impact, bridging AI verification with blockchain rewards (Ethereum Sepolia NFT credentials)
- **Autonomous 24/7 Operation:** Z.AI GLM powers the automated pipeline cycle — no human prompting required

---

## 🏅 FLock Bounty Track Evidence

**"FLock Track"** ($2,000 Gold prize)

GreenClaw strictly follows all FLock track requirements:
1. **Autonomous Agents on OpenClaw:** The system runs as an autonomous multi-agent mesh using the OpenClaw framework
2. **SDG-Aligned with Real-world Impact:** Directly targets **SDG 13 (Climate Action)** and **SDG 11 (Sustainable Cities)**. The Community Tracker measures real-world impact (CO₂ savings in kg)
3. **FLock API & Open-source Models Only:** The Action Advisor, Carbon Footprint Calculator, and orchestrator routing are powered by FLock's open-source models (`qwen3-30b-a3b-instruct-2507`)
4. **Multi-channel Deployment:** Web Dashboard + Telegram Bot with autonomous alert broadcasting

---

## 📁 Project Structure

```
greenclaw/
├── AGENTS.md                          # Orchestrator agent prompt (6 skills)
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # API key template
├── server.py                          # FastAPI backend (all endpoints + pipeline)
├── landing.html                       # Premium landing page
├── telegram_bot.py                    # Telegram bot with vision AI
├── nft_minter.py                      # ERC-721 NFT minting (Ethereum Sepolia)
├── config/
│   └── openclaw.example.json          # Example OpenClaw config
├── dashboard/
│   ├── index.html                     # Dashboard UI
│   ├── dashboard.js                   # Frontend logic (1300+ lines)
│   └── dashboard.css                  # Premium dark theme (3300+ lines)
├── data/                              # Local persistence (auto-created)
│   ├── actions.json                   # Eco-action log
│   ├── wallets.json                   # Carbon credit wallets
│   ├── badges.json                    # NFT badge records
│   ├── quests.json                    # Quest completion state
│   └── climate_history.json           # Historical trend data
└── skills/
    ├── climate-monitor/
    │   ├── SKILL.md
    │   └── scripts/fetch_climate.py
    ├── risk-analyzer/
    │   ├── SKILL.md
    │   └── scripts/analyze_risk.py
    ├── action-advisor/
    │   ├── SKILL.md
    │   └── scripts/advise_action.py
    ├── community-tracker/
    │   ├── SKILL.md
    │   └── scripts/tracker.py
    ├── edu-mode/
    │   └── SKILL.md
    └── carbon-calculator/             # NEW
        ├── SKILL.md
        └── scripts/calculate_footprint.py
```

---

## 🌱 UN SDG Alignment

| SDG | Goal | GreenClaw Contribution |
|---|---|---|
| 🌍 **SDG 13** | Climate Action | Real-time monitoring, risk assessment, actionable recommendations, carbon footprint awareness |
| 🏙️ **SDG 11** | Sustainable Cities | Air quality monitoring, urban environmental tracking, flood warnings |
| 📚 **SDG 4** | Quality Education | Human-in-the-loop agent verification (gamified climate quizzes) and data anomalies |
| 🤝 **SDG 17** | Partnerships | Multi-channel deployment enabling decentralized node coordination |

---

## 🛠️ Technologies Used

| Technology | Role |
|---|---|
| [OpenClaw](https://openclaw.ai) | Agent framework & orchestration |
| [Z.AI GLM-4.5](https://z.ai) | Risk reasoning (thinking mode) |
| [Z.AI GLM-4V](https://z.ai) | Vision AI for eco-action verification |
| [FLock.io](https://flock.io) | Open-source model inference (qwen3-30b) |
| [Ethereum Sepolia](https://sepolia.etherscan.io) | ERC-721 NFT badge minting (Testnet) |
| [FastAPI](https://fastapi.tiangolo.com) | Backend API server |
| [Chart.js](https://chartjs.org) | Historical trend visualization |
| [globe.gl](https://globe.gl) | 3D interactive threat map |
| [OpenWeatherMap](https://openweathermap.org) | Weather data |
| [WAQI](https://waqi.info) | Air quality index |
| [NASA EONET](https://eonet.gsfc.nasa.gov) | Natural disaster events |
| [UK Environment Agency](https://environment.data.gov.uk) | Flood monitoring & policy alerts |

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

_Built with 🦞 for the UK AI Agent Hackathon EP4 × OpenClaw_
