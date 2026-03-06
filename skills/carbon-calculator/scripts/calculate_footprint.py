#!/usr/bin/env python3
"""
GreenClaw Carbon Footprint Calculator
Estimates annual CO₂ emissions from lifestyle inputs.
"""

import argparse
import json
import sys

# Emission factors (kg CO₂ per year)
TRANSPORT = {
    "car_petrol": 4600,
    "car_diesel": 4200,
    "car_electric": 1500,
    "public_transit": 1200,
    "bike_walk": 0,
    "motorcycle": 2100,
}

DIET = {
    "meat_heavy": 3300,
    "mixed": 2500,
    "vegetarian": 1700,
    "vegan": 1500,
}

ENERGY = {
    "gas": 2900,
    "electric": 2100,
    "renewable": 500,
    "mixed": 2500,
}

FLIGHTS = {
    "frequent": 3400,  # 4+ flights/year
    "occasional": 1200,  # 1-3 flights/year
    "rare": 400,  # <1 flight/year
    "none": 0,
}

UK_AVERAGE = 5500
GLOBAL_AVERAGE = 4700


def calculate(transport="mixed", diet="mixed", energy="mixed", flights="occasional", household=1):
    t = TRANSPORT.get(transport, 2500)
    d = DIET.get(diet, 2500)
    e = ENERGY.get(energy, 2500) / max(household, 1)
    f = FLIGHTS.get(flights, 1200)

    total = t + d + e + f
    breakdown = {
        "transport": {"kg": round(t), "pct": round(t / total * 100)},
        "diet": {"kg": round(d), "pct": round(d / total * 100)},
        "energy": {"kg": round(e), "pct": round(e / total * 100)},
        "flights": {"kg": round(f), "pct": round(f / total * 100)},
    }

    return {
        "total_kg": round(total),
        "total_tonnes": round(total / 1000, 1),
        "breakdown": breakdown,
        "vs_uk": round((total / UK_AVERAGE - 1) * 100),
        "vs_global": round((total / GLOBAL_AVERAGE - 1) * 100),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carbon Footprint Calculator")
    parser.add_argument("--transport", default="mixed", choices=list(TRANSPORT.keys()))
    parser.add_argument("--diet", default="mixed", choices=list(DIET.keys()))
    parser.add_argument("--energy", default="mixed", choices=list(ENERGY.keys()))
    parser.add_argument("--flights", default="occasional", choices=list(FLIGHTS.keys()))
    parser.add_argument("--household", type=int, default=1)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    result = calculate(args.transport, args.diet, args.energy, args.flights, args.household)
    print(json.dumps(result, indent=2))
