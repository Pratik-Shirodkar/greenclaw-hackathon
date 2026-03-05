#!/usr/bin/env python3
"""
GreenClaw Telegram Bot — Multi-Channel Climate Agent
Uses the same backend API as the dashboard for consistent responses.

Commands:
  /start   — Welcome + help
  /climate — Real-time weather + AQI for any city
  /risk    — Z.AI-powered risk analysis
  /tips    — FLock eco-tips
  /quiz    — Climate quiz
  /log     — Log an eco-action
  /stats   — Community impact stats
  /alerts  — Current autonomous alerts

Usage:
  1. Get bot token from @BotFather on Telegram
  2. Add TELEGRAM_BOT_TOKEN to .env
  3. Run: python telegram_bot.py
"""

import os
import sys
import json
import base64
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

# Import from python-telegram-bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_BASE = os.getenv("GREENCLAW_API", "http://localhost:8000")

http = httpx.Client(timeout=60.0)

# ──────────────────────────────────────────────
# /start command
# ──────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Register user silently for autonomous broadcasts
    try:
        http.post(f"{API_BASE}/api/community/register", json={
            "chat_id": update.effective_chat.id,
            "user": update.effective_user.first_name or "telegram_user"
        }, timeout=5.0)
    except Exception as e:
        print(f"Registration failed: {e}")

    await update.message.reply_text(
        "🌍🦞 *Welcome to GreenClaw!*\n\n"
        "I'm your AI climate action agent, powered by Z.AI + FLock.io.\n\n"
        "*🌡️ Climate*\n"
        "/climate London — Real-time weather & AQI\n"
        "/risk Delhi — Z.AI risk analysis\n"
        "/predict Tokyo — 7-day predictive forecast\n"
        "/debate Mumbai — Multi-agent climate debate\n\n"
        "*🌿 Eco-Actions*\n"
        "/log planted a tree — Log an eco-action\n"
        "/quest — Daily climate missions\n"
        "📸 Send a photo — Vision AI verification\n\n"
        "*💰 Rewards*\n"
        "/wallet — Your carbon credit wallet\n"
        "/badges — Achievement NFT badges\n"
        "/stats — Community impact\n\n"
        "*🎮 More*\n"
        "/tips — Sustainability tips\n"
        "/quiz — Climate quiz\n"
        "/alerts — Autonomous alerts\n\n"
        "Or just type a message and I'll route it to the right agent! 🤖",
        parse_mode="Markdown"
    )

# ──────────────────────────────────────────────
# /climate <city>
# ──────────────────────────────────────────────
async def cmd_climate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else "London"
    await update.message.reply_text(f"📡 Fetching live climate data for *{city}*...", parse_mode="Markdown")

    try:
        r = http.get(f"{API_BASE}/api/climate/{city}")
        data = r.json()
        w = data.get("weather", {})
        a = data.get("aqi", {})

        if "error" in w:
            await update.message.reply_text(f"⚠️ Error: {w['error']}")
            return

        msg = (
            f"🌡️ *{city}* — {w.get('condition', '')} {w.get('icon', '')}\n"
            f"🌡 Temperature: *{w.get('temp', '?')}°C* (feels like {w.get('feels', '?')}°C)\n"
            f"💧 Humidity: {w.get('humidity', '?')}%\n"
            f"💨 Wind: {w.get('wind', '?')} m/s\n"
        )

        if a and "error" not in a:
            msg += (
                f"\n💨 *Air Quality:* {a.get('icon', '')} AQI {a.get('value', '?')} — {a.get('category', '?')}\n"
                f"_{a.get('advice', '')}_"
            )

        # Show disasters if any
        disasters = data.get("disasters", [])
        if disasters and not any("Error" in d.get("title", "") for d in disasters):
            msg += f"\n\n🌪 *Active Disasters:* {len(disasters)}"
            for d in disasters[:3]:
                msg += f"\n  {d.get('icon', '⚠️')} {d.get('title', '')}"

        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error connecting to backend: {e}\nMake sure server.py is running!")

# ──────────────────────────────────────────────
# /risk <city>
# ──────────────────────────────────────────────
async def cmd_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else "London"
    await update.message.reply_text(
        f"🧠 Running Z.AI GLM risk analysis for *{city}*...\nThis may take 10-15 seconds.",
        parse_mode="Markdown"
    )

    try:
        r = http.post(f"{API_BASE}/api/risk/{city}", timeout=60.0)
        data = r.json()

        if "error" in data:
            await update.message.reply_text(f"⚠️ Error: {data['error']}")
            return

        msg = (
            f"⚠️ *Risk Analysis — {city}*\n"
            f"📊 Score: *{data.get('score', '?')}/10* ({data.get('level', '?')})\n"
            f"🎯 Confidence: {data.get('confidence', '?')}\n"
            f"🤖 Model: {data.get('model', 'Z.AI')}\n\n"
        )

        # Risk categories
        for r_item in data.get("risks", [])[:5]:
            bar = "█" * r_item.get("score", 0) + "░" * (10 - r_item.get("score", 0))
            msg += f"  {bar} {r_item.get('category', '')} ({r_item.get('score', '?')}/10)\n"

        # Recommendations
        recs = data.get("recommendations", [])
        if recs:
            msg += "\n📋 *Recommendations:*\n"
            for i, rec in enumerate(recs[:4], 1):
                msg += f"  {i}. {rec}\n"

        # SDG 13
        if data.get("sdg13"):
            msg += f"\n🌍 *SDG 13:* {data['sdg13']}"

        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /tips
# ──────────────────────────────────────────────
async def cmd_tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else "London"
    await update.message.reply_text(f"💚 Getting eco-tips from FLock.io for *{city}*...", parse_mode="Markdown")

    try:
        r = http.post(f"{API_BASE}/api/advice", json={"mode": "tips", "city": city}, timeout=60.0)
        data = r.json()

        if "error" in data:
            await update.message.reply_text(f"⚠️ {data['error']}")
            return

        msg = f"💚 *Eco-Tips for {city}:*\n\n"
        impacts = {"low": "🌱", "medium": "🌿", "high": "🌳"}
        for i, tip in enumerate(data.get("tips", [])[:5], 1):
            icon = impacts.get(tip.get("impact", ""), "🌍")
            msg += f"{i}. {icon} {tip.get('action', '')}\n   _Saves ~{tip.get('carbon_savings_kg', '?')} kg CO₂_\n\n"

        if data.get("motivation"):
            msg += f"💪 _{data['motivation']}_"

        msg += f"\n\n_Powered by FLock.io (open-source AI)_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /quiz
# ──────────────────────────────────────────────
async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = http.post(f"{API_BASE}/api/chat", json={"message": "quiz me", "city": "London"})
        data = r.json()
        await update.message.reply_text(data.get("reply", "No quiz available right now."), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /log <action>
# ──────────────────────────────────────────────
async def cmd_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = " ".join(context.args) if context.args else ""
    if not action:
        await update.message.reply_text("📝 Usage: /log recycled plastic bottles")
        return

    username = update.effective_user.first_name or "telegram_user"
    try:
        r = http.post(f"{API_BASE}/api/community/log", json={"user": username, "action": action})
        data = r.json()
        await update.message.reply_text(
            f"✅ Logged: *{action}*\n"
            f"{data.get('emoji', '🌍')} Estimated CO₂ saved: *{data.get('co2_kg', 0)} kg*\n"
            f"Keep it up, {username}! 💪",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /stats
# ──────────────────────────────────────────────
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = http.get(f"{API_BASE}/api/community/stats")
        data = r.json()
        eq = data.get("equivalents", {})
        msg = (
            f"📊 *Community Impact Dashboard*\n\n"
            f"🌍 Total CO₂ saved: *{data.get('total_co2_kg', 0)} kg*\n"
            f"📋 Total actions: {data.get('total_actions', 0)}\n\n"
            f"🌳 Trees equivalent: {eq.get('trees_equivalent', 0)}\n"
            f"🚗 Car km avoided: {eq.get('car_km_saved', 0)}\n"
            f"✈️ Flights offset: {eq.get('flights_offset', 0)}\n"
        )

        leaderboard = data.get("leaderboard", [])
        if leaderboard:
            msg += "\n🏆 *Leaderboard:*\n"
            medals = ["🥇", "🥈", "🥉"]
            for i, entry in enumerate(leaderboard[:5]):
                medal = medals[i] if i < 3 else f"{i+1}."
                msg += f"  {medal} {entry['user']} — {entry['co2_kg']} kg\n"

        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /alerts
# ──────────────────────────────────────────────
async def cmd_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = http.get(f"{API_BASE}/api/alerts")
        data = r.json()
        alerts = data.get("alerts", [])

        if not alerts:
            await update.message.reply_text("✅ No active climate alerts. All clear! 🌍")
            return

        msg = f"🔔 *{len(alerts)} Active Climate Alerts:*\n\n"
        for alert in alerts:
            severity_icon = "🟡" if alert.get("severity") == "warning" else "🔴"
            msg += f"{severity_icon} {alert.get('message', '')}\n\n"

            # Show analysis if present
            analysis = alert.get("analysis")
            if analysis:
                msg += f"   🧠 Risk: {analysis.get('score', '?')}/10 ({analysis.get('level', '?')})\n"

            # Show tips if present
            tips = alert.get("advice", [])
            if tips:
                msg += f"   💚 Tip: {tips[0]}\n"

            msg += "\n"

        msg += "_Alerts generated autonomously by GreenClaw Agent_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# Free-text — route through chat orchestrator
# ──────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Register user silently for autonomous broadcasts
    try:
        http.post(f"{API_BASE}/api/community/register", json={
            "chat_id": update.effective_chat.id,
            "user": update.effective_user.first_name or "telegram_user"
        }, timeout=5.0)
    except Exception:
        pass

    msg = update.message.text
    try:
        r = http.post(f"{API_BASE}/api/chat", json={"message": msg, "city": "London"}, timeout=60.0)
        data = r.json()
        skill = data.get("skill", "")
        reply = data.get("reply", "Sorry, I couldn't process that.")

        skill_label = ""
        if skill and skill != "orchestrator":
            icons = {"climate-monitor": "🌡️", "risk-analyzer": "⚠️", "action-advisor": "💚",
                     "community-tracker": "📊", "edu-mode": "🎮"}
            skill_label = f"_{icons.get(skill, '🤖')} {skill}_\n\n"

        await update.message.reply_text(skill_label + reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}\nIs server.py running on {API_BASE}?")

# ──────────────────────────────────────────────
# Photo Handler — Vision AI Eco-Action
# ──────────────────────────────────────────────
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "telegram_user"
    await update.message.reply_text(
        "📸 *Analyzing Photo...*\nGreenClaw is using Z.AI GLM-4V to verify your eco-action!",
        parse_mode="Markdown"
    )
    
    try:
        # Get a smaller resolution photo to avoid Z.AI payload limits (index -2 or 0)
        photos = update.message.photo
        chosen_photo = photos[-2] if len(photos) > 1 else photos[0]
        
        photo_file = await chosen_photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        img_b64 = base64.b64encode(photo_bytes).decode("utf-8")
        
        # Send to backend
        r = http.post(
            f"{API_BASE}/api/community/vision",
            json={"user": user, "image_base64": img_b64},
            timeout=120.0
        )
        data = r.json()
        
        if "error" in data:
            await update.message.reply_text(f"⚠️ Vision Error: {data['error']}")
            return
            
        if data.get("success"):
            msg = (
                f"✅ *Eco-Action Verified by Z.AI!* (Score: {data.get('score', '?')}/10)\n\n"
                f"👁️ *Z.AI GLM-4V sees:* _{data.get('description', '')}_\n\n"
                f"🎉 You earned *{data.get('co2_kg', 0)} kg* of CO₂ offset!\n\n"
                f"💚 *FLock.io says:* {data.get('tip', '')}"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("🤔 Hmm, I couldn't process that photo.")
            
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /wallet — Carbon Credit Wallet
# ──────────────────────────────────────────────
async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "telegram_user"
    try:
        r = http.get(f"{API_BASE}/api/wallet/{user}")
        data = r.json()
        
        next_info = ""
        if data.get("next_rank"):
            nr = data["next_rank"]
            next_info = f"\n📈 Next rank: {nr['icon']} {nr['name']} ({nr['remaining']} credits away)"
        
        msg = (
            f"🪙 *{user}'s Carbon Wallet*\n\n"
            f"{data.get('rank_icon', '🌱')} Rank: *{data.get('rank_name', 'Seedling')}*\n"
            f"💰 Credits: *{data.get('credits', 0)} $GREEN*\n"
            f"🌍 Lifetime CO₂ saved: *{data.get('lifetime_co2_kg', 0)} kg*\n"
            f"📋 Total actions: {data.get('actions_count', 0)}\n"
            f"🔥 Streak: {data.get('streak_days', 0)} days"
            f"{next_info}\n\n"
        )
        addr = data.get("wallet_address")
        if addr:
            msg += f"🔗 Wallet: `{addr[:6]}...{addr[-4:]}`\n\n"
            msg += f"_NFTs mint directly to your wallet!_"
        else:
            msg += f"_Link your wallet: /connect 0xYourAddress_"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /connect <address> — Link wallet for NFT minting
# ──────────────────────────────────────────────
async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "telegram_user"
    if not context.args:
        await update.message.reply_text(
            "🔗 *Connect your wallet for NFT badges!*\n\n"
            "Usage: `/connect 0xYourWalletAddress`\n\n"
            "Your achievement badges will be minted as real ERC-721 NFTs on Ethereum Sepolia directly to your wallet!",
            parse_mode="Markdown"
        )
        return
    
    address = context.args[0].strip()
    if not address.startswith("0x") or len(address) != 42:
        await update.message.reply_text("❌ Invalid address. Must be `0x` followed by 40 hex characters.", parse_mode="Markdown")
        return
    
    try:
        r = http.post(f"{API_BASE}/api/wallet/connect?user={user}&address={address}")
        data = r.json()
        if data.get("success"):
            await update.message.reply_text(
                f"✅ *Wallet Connected!*\n\n"
                f"🔗 Address: `{address}`\n"
                f"🏅 All future NFT badges will mint to this wallet!\n\n"
                f"_View on Etherscan: https://sepolia.etherscan.io/address/{address}_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"⚠️ {data.get('error', 'Connection failed')}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /badges — Achievement NFT Badges
# ──────────────────────────────────────────────
async def cmd_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "telegram_user"
    try:
        r = http.get(f"{API_BASE}/api/badges/{user}")
        data = r.json()
        badges = data.get("badges", [])
        
        if not badges:
            msg = (
                f"🏅 *{user}'s Trophy Case*\n\n"
                f"No badges yet! Complete eco-actions to earn your first badge.\n\n"
                f"_Try: /log recycled plastic bottles_"
            )
        else:
            badge_list = "\n".join([f"  {b['name']} — _{b['desc']}_\n  Token: `{b['token_id']}`" for b in badges])
            msg = (
                f"🏅 *{user}'s Trophy Case* ({len(badges)} badges)\n\n"
                f"{badge_list}\n\n"
                f"_{len(data.get('available_milestones', []))} more badges available!_"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# /debate <city> — Multi-Agent Climate Debate
# ──────────────────────────────────────────────
async def cmd_debate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else "London"
    await update.message.reply_text(f"🌍 *Initiating multi-agent debate for {city}...*\n_5 agents will argue about the best climate strategy!_", parse_mode="Markdown")
    
    try:
        r = http.get(f"{API_BASE}/api/debate/{city}", timeout=120.0)
        data = r.json()
        debate = data.get("debate", [])
        
        msg = f"🎤 *Climate Debate: {city}*\n\n"
        for entry in debate:
            msg += f"{entry['icon']} *{entry['agent']}:*\n{entry['message']}\n\n"
        msg += "_Debate powered by Z.AI + FLock.io multi-agent system_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Debate error: {e}")

# ──────────────────────────────────────────────
# /predict <city> — Predictive Climate Forecast
# ──────────────────────────────────────────────
async def cmd_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args) if context.args else "London"
    await update.message.reply_text(f"🔮 *Generating predictive forecast for {city}...*", parse_mode="Markdown")
    
    try:
        r = http.get(f"{API_BASE}/api/predict/{city}", timeout=60.0)
        data = r.json()
        
        if "error" in data:
            await update.message.reply_text(f"⚠️ {data['error']}")
            return
        
        pred = data.get("prediction", {})
        trend_icon = {"improving": "📈", "stable": "➡️", "worsening": "📉"}.get(pred.get("risk_trend", ""), "❓")
        
        msg = f"🔮 *7-Day Predictive Forecast: {city}*\n\n"
        msg += f"Trend: {trend_icon} *{pred.get('risk_trend', 'unknown').title()}*\n\n"
        
        for p in pred.get("predictions", []):
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(p.get("risk", ""), "⚪")
            msg += f"Day {p['day']}: {risk_icon} {p.get('event', '')} (Conf: {int(p.get('confidence', 0)*100)}%)\n"
        
        warnings = pred.get("early_warnings", [])
        if warnings:
            msg += f"\n⚠️ *Early Warnings:*\n"
            for w in warnings:
                msg += f"  • {w}\n"
        
        msg += f"\n_Predictions by Z.AI GLM-4 Thinking Mode_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Prediction error: {e}")

# ──────────────────────────────────────────────
# /quest — Climate Quest System
# ──────────────────────────────────────────────
async def cmd_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "telegram_user"
    args = context.args
    
    # If user wants to complete a quest: /quest done 3
    if args and args[0].lower() == "done" and len(args) > 1:
        try:
            quest_id = int(args[1])
            r = http.post(f"{API_BASE}/api/quest/complete", json={"user": user, "quest_id": quest_id})
            data = r.json()
            
            if "error" in data:
                await update.message.reply_text(f"⚠️ {data['error']}")
                return
            
            quest = data.get("quest", {})
            msg = (
                f"✅ *Quest Complete!*\n\n"
                f"📋 {quest.get('title', '')}\n"
                f"⭐ XP earned: +{data.get('xp_earned', 0)}\n"
                f"🪙 Credits earned: +{data.get('wallet', {}).get('earned_this_action', 0)} $GREEN\n"
                f"🌍 CO₂ saved: {quest.get('co2_kg', 0)} kg\n\n"
                f"📊 Level: {data.get('level_name', '')} (XP: {data.get('total_xp', 0)})\n"
                f"📈 Next level in: {data.get('next_level_xp', '?')} XP"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")
        return
    
    # Show available quests
    try:
        r = http.get(f"{API_BASE}/api/quests")
        data = r.json()
        quests = data.get("quests", [])
        
        # Get profile
        r2 = http.get(f"{API_BASE}/api/quest/profile/{user}")
        profile = r2.json()
        
        msg = (
            f"🎮 *Daily Climate Quests*\n"
            f"📊 {profile.get('level_name', '🥚 Hatchling')} | XP: {profile.get('total_xp', 0)} | Today: {profile.get('quests_completed_today', 0)}/5\n\n"
        )
        
        for q in quests:
            msg += f"*{q['id']}.* {q['title']}\n   ⭐ {q['xp']} XP | 🌍 {q['co2_kg']} kg CO₂\n\n"
        
        msg += f"_Complete a quest: /quest done <number>_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        print("   Get a token from @BotFather on Telegram:")
        print("   1. Open Telegram and search for @BotFather")
        print("   2. Send /newbot and follow the steps")
        print("   3. Add the token to your .env file")
        sys.exit(1)

    print("🌍🦞 GreenClaw Telegram Bot — Starting...")
    print(f"   API Backend: {API_BASE}")
    print("   Send /start to your bot on Telegram!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("climate", cmd_climate))
    app.add_handler(CommandHandler("weather", cmd_climate))
    app.add_handler(CommandHandler("risk", cmd_risk))
    app.add_handler(CommandHandler("tips", cmd_tips))
    app.add_handler(CommandHandler("advice", cmd_tips))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("log", cmd_log))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("alerts", cmd_alerts))
    # Phase 15: Winning Features
    app.add_handler(CommandHandler("wallet", cmd_wallet))
    app.add_handler(CommandHandler("connect", cmd_connect))
    app.add_handler(CommandHandler("badges", cmd_badges))
    app.add_handler(CommandHandler("debate", cmd_debate))
    app.add_handler(CommandHandler("predict", cmd_predict))
    app.add_handler(CommandHandler("quest", cmd_quest))

    # Photo handler
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Free-text handler (catch-all)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

