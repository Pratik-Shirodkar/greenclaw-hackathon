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
        "🌡️ /climate London — Real-time weather & AQI\n"
        "⚠️ /risk Delhi — Z.AI risk analysis\n"
        "💚 /tips — Eco-sustainability tips\n"
        "🎮 /quiz — Climate quiz\n"
        "📊 /log planted a tree — Log eco-action\n"
        "📈 /stats — Community impact\n"
        "🔔 /alerts — Current autonomous alerts\n\n"
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

    # Photo handler
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Free-text handler (catch-all)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
