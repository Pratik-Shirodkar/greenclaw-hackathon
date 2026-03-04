#!/usr/bin/env python3
"""
GreenClaw Community Tracker — Log eco-actions, track carbon offsets, generate impact reports.
Uses local JSON storage for privacy.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Carbon offset estimates (kg CO₂ per unit)
CARBON_OFFSETS = {
    "recycle": {"per_unit": 0.5, "unit": "item", "emoji": "♻️", "category": "Waste"},
    "recycled": {"per_unit": 0.5, "unit": "item", "emoji": "♻️", "category": "Waste"},
    "recycling": {"per_unit": 0.5, "unit": "item", "emoji": "♻️", "category": "Waste"},
    "cycle": {"per_unit": 2.3, "unit": "trip", "emoji": "🚲", "category": "Transport"},
    "bike": {"per_unit": 2.3, "unit": "trip", "emoji": "🚲", "category": "Transport"},
    "cycling": {"per_unit": 2.3, "unit": "trip", "emoji": "🚲", "category": "Transport"},
    "plant-based": {"per_unit": 2.5, "unit": "meal", "emoji": "🥗", "category": "Food"},
    "vegan": {"per_unit": 2.5, "unit": "meal", "emoji": "🥗", "category": "Food"},
    "vegetarian": {"per_unit": 1.5, "unit": "meal", "emoji": "🥗", "category": "Food"},
    "energy": {"per_unit": 0.8, "unit": "action", "emoji": "💡", "category": "Energy"},
    "led": {"per_unit": 0.3, "unit": "bulb", "emoji": "💡", "category": "Energy"},
    "unplug": {"per_unit": 0.4, "unit": "device", "emoji": "🔌", "category": "Energy"},
    "public transport": {"per_unit": 1.2, "unit": "trip", "emoji": "🚌", "category": "Transport"},
    "bus": {"per_unit": 1.2, "unit": "trip", "emoji": "🚌", "category": "Transport"},
    "train": {"per_unit": 1.5, "unit": "trip", "emoji": "🚆", "category": "Transport"},
    "plant": {"per_unit": 5.0, "unit": "plant", "emoji": "🌱", "category": "Nature"},
    "tree": {"per_unit": 22.0, "unit": "tree", "emoji": "🌳", "category": "Nature"},
    "compost": {"per_unit": 0.3, "unit": "kg", "emoji": "🪱", "category": "Waste"},
    "reusable": {"per_unit": 0.2, "unit": "use", "emoji": "🛍️", "category": "Waste"},
    "water saving": {"per_unit": 0.1, "unit": "action", "emoji": "💧", "category": "Water"},
    "cold wash": {"per_unit": 0.6, "unit": "load", "emoji": "🧺", "category": "Energy"},
}

# Milestone thresholds
MILESTONES = [
    (10, "🌱 Seedling — 10 kg CO₂ saved!"),
    (50, "🌿 Sprout — 50 kg CO₂ saved!"),
    (100, "🌳 Tree — 100 kg CO₂ saved! That's like planting 5 trees!"),
    (250, "🏅 Eco Warrior — 250 kg CO₂ saved!"),
    (500, "⭐ Climate Champion — 500 kg CO₂ saved!"),
    (1000, "🌟 Planet Hero — 1,000 kg CO₂ saved! Incredible!"),
]


def get_data_path() -> Path:
    """Get the path to the actions data file."""
    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "actions.json"


def load_data() -> dict:
    """Load actions data from JSON file."""
    data_path = get_data_path()
    if data_path.exists():
        with open(data_path, "r") as f:
            return json.load(f)
    return {"users": {}, "total_co2_saved": 0, "total_actions": 0}


def save_data(data: dict):
    """Save actions data to JSON file."""
    data_path = get_data_path()
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def estimate_carbon(action_text: str, quantity: int) -> tuple:
    """Estimate carbon savings based on action description."""
    action_lower = action_text.lower()
    
    for keyword, info in CARBON_OFFSETS.items():
        if keyword in action_lower:
            return (
                round(info["per_unit"] * quantity, 2),
                info["emoji"],
                info["category"],
                f'{info["per_unit"]} kg CO₂ per {info["unit"]}'
            )
    
    # Default for unrecognized actions
    return (0.5 * quantity, "🌍", "General", "0.5 kg CO₂ per action (estimated)")


def log_action(user: str, action: str, quantity: int) -> dict:
    """Log an eco-action and return the result."""
    data = load_data()
    
    co2_saved, emoji, category, rate = estimate_carbon(action, quantity)
    
    if user not in data["users"]:
        data["users"][user] = {"actions": [], "total_co2": 0, "total_actions": 0}
    
    entry = {
        "action": action,
        "quantity": quantity,
        "co2_saved_kg": co2_saved,
        "category": category,
        "emoji": emoji,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    data["users"][user]["actions"].append(entry)
    data["users"][user]["total_co2"] = round(data["users"][user]["total_co2"] + co2_saved, 2)
    data["users"][user]["total_actions"] += 1
    data["total_co2_saved"] = round(data["total_co2_saved"] + co2_saved, 2)
    data["total_actions"] += 1
    
    save_data(data)
    
    # Check milestones
    user_total = data["users"][user]["total_co2"]
    milestone_reached = None
    for threshold, message in MILESTONES:
        if user_total >= threshold and (user_total - co2_saved) < threshold:
            milestone_reached = message
    
    return {
        "type": "action_logged",
        "success": True,
        "action": action,
        "quantity": quantity,
        "co2_saved_kg": co2_saved,
        "rate": rate,
        "emoji": emoji,
        "category": category,
        "user_total_co2_kg": data["users"][user]["total_co2"],
        "user_total_actions": data["users"][user]["total_actions"],
        "community_total_co2_kg": data["total_co2_saved"],
        "milestone": milestone_reached,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_stats(user: str) -> dict:
    """Get personal statistics for a user."""
    data = load_data()
    
    if user not in data["users"]:
        return {
            "type": "user_stats",
            "user": user,
            "message": "No actions logged yet! Start by logging your first eco-action. 🌱",
            "total_co2_kg": 0,
            "total_actions": 0,
        }
    
    user_data = data["users"][user]
    actions = user_data["actions"]
    
    # Category breakdown
    categories = {}
    for a in actions:
        cat = a.get("category", "General")
        if cat not in categories:
            categories[cat] = {"count": 0, "co2_kg": 0}
        categories[cat]["count"] += 1
        categories[cat]["co2_kg"] = round(categories[cat]["co2_kg"] + a["co2_saved_kg"], 2)
    
    # Recent actions (last 7)
    recent = actions[-7:] if len(actions) > 7 else actions
    
    # Current milestone
    current_milestone = "🌱 Getting Started"
    next_milestone = MILESTONES[0][1]
    next_threshold = MILESTONES[0][0]
    for i, (threshold, message) in enumerate(MILESTONES):
        if user_data["total_co2"] >= threshold:
            current_milestone = message
            if i + 1 < len(MILESTONES):
                next_milestone = MILESTONES[i + 1][1]
                next_threshold = MILESTONES[i + 1][0]
            else:
                next_milestone = None
                next_threshold = None
    
    return {
        "type": "user_stats",
        "user": user,
        "total_co2_kg": user_data["total_co2"],
        "total_actions": user_data["total_actions"],
        "categories": categories,
        "current_milestone": current_milestone,
        "next_milestone": next_milestone,
        "next_milestone_threshold_kg": next_threshold,
        "co2_to_next_milestone": round(next_threshold - user_data["total_co2"], 2) if next_threshold else 0,
        "recent_actions": recent,
        "equivalents": {
            "trees_equivalent": round(user_data["total_co2"] / 22, 1),
            "car_km_equivalent": round(user_data["total_co2"] / 0.21, 0),
            "flights_london_paris": round(user_data["total_co2"] / 250, 2),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_leaderboard() -> dict:
    """Get community leaderboard."""
    data = load_data()
    
    users_sorted = sorted(
        [(name, info["total_co2"], info["total_actions"]) for name, info in data["users"].items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    medals = ["🥇", "🥈", "🥉"]
    leaderboard = []
    for i, (name, co2, actions) in enumerate(users_sorted[:10]):
        medal = medals[i] if i < 3 else f"#{i+1}"
        leaderboard.append({
            "rank": i + 1,
            "medal": medal,
            "user": name,
            "co2_saved_kg": co2,
            "actions_count": actions,
        })
    
    return {
        "type": "leaderboard",
        "entries": leaderboard,
        "community_total_co2_kg": data["total_co2_saved"],
        "community_total_actions": data["total_actions"],
        "total_users": len(data["users"]),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_report() -> dict:
    """Generate a weekly impact report."""
    data = load_data()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    
    weekly_co2 = 0
    weekly_actions = 0
    weekly_categories = {}
    
    for user_name, user_data in data["users"].items():
        for action in user_data["actions"]:
            if action["timestamp"] >= week_ago:
                weekly_co2 += action["co2_saved_kg"]
                weekly_actions += 1
                cat = action.get("category", "General")
                weekly_categories[cat] = weekly_categories.get(cat, 0) + action["co2_saved_kg"]
    
    return {
        "type": "weekly_report",
        "period": f'{(datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")} to {datetime.utcnow().strftime("%Y-%m-%d")}',
        "weekly_co2_saved_kg": round(weekly_co2, 2),
        "weekly_actions": weekly_actions,
        "weekly_categories": {k: round(v, 2) for k, v in weekly_categories.items()},
        "total_co2_saved_kg": data["total_co2_saved"],
        "total_actions": data["total_actions"],
        "total_users": len(data["users"]),
        "sdg13_impact": f"This week's actions saved {round(weekly_co2, 1)} kg CO₂, equivalent to planting {round(weekly_co2/22, 1)} trees!",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def main():
    parser = argparse.ArgumentParser(description="GreenClaw Community Tracker")
    parser.add_argument("--action", type=str, help="Eco-action to log")
    parser.add_argument("--user", type=str, default="default", help="User name")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity/count")
    parser.add_argument("--stats", action="store_true", help="Show personal stats")
    parser.add_argument("--leaderboard", action="store_true", help="Show community leaderboard")
    parser.add_argument("--report", action="store_true", help="Generate weekly report")
    parser.add_argument("--dry-run", action="store_true", help="Return mock data")
    args = parser.parse_args()

    if args.dry_run:
        mock = {
            "type": "action_logged",
            "success": True,
            "action": args.action or "test recycling",
            "co2_saved_kg": 2.5,
            "emoji": "♻️",
            "user_total_co2_kg": 47.5,
            "user_total_actions": 23,
            "milestone": None,
            "status": "dry_run",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        print(json.dumps(mock, indent=2))
        return

    if args.stats:
        print(json.dumps(get_stats(args.user), indent=2))
    elif args.leaderboard:
        print(json.dumps(get_leaderboard(), indent=2))
    elif args.report:
        print(json.dumps(get_report(), indent=2))
    elif args.action:
        print(json.dumps(log_action(args.user, args.action, args.quantity), indent=2))
    else:
        print(json.dumps({"error": "Specify --action, --stats, --leaderboard, or --report"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
