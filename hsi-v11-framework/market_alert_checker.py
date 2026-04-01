#!/usr/bin/env python3
"""
小龍 Market Alert Checker - SPX/HSI/Oil Key Levels
Usage: python market_alert_checker.py

Checks current market prices against 小龍's key levels (Mar 20, 2026 analysis)
"""

import json
from datetime import datetime

# Alert configuration
ALERT_CONFIG = "/root/.openclaw/workspace/market_alerts_config.json"

def load_config():
    with open(ALERT_CONFIG, 'r') as f:
        return json.load(f)

def get_current_prices():
    """
    Note: This is a placeholder. In production, you would fetch from:
    - Yahoo Finance API
    - Alpha Vantage
    - Your broker's API
    
    For now, returns estimated current prices.
    Updated for v11.2: Added Treasury 10Y yield monitoring
    """
    # Placeholder - replace with actual API calls
    # v11.2 UPDATE: Added Treasury_10Y
    return {
        "SPX": 6477,       # Mar 27 close (broke 6,500)
        "HSI": 25000,      # Weekend estimate
        "Oil_Brent": 116,  # Triple top forming
        "Gold": 5200,      # Parabolic peak
        "Treasury_10Y": 4.05  # Broke 4% threshold
    }

def check_levels(current_prices, config):
    """Check current prices against alert levels"""
    alerts_triggered = []
    
    for asset, current in current_prices.items():
        if asset in config["levels"]:
            for alert in config["levels"][asset]["alerts"]:
                level = alert["level"]
                alert_type = alert["type"]
                
                # Check if price crossed level
                if alert_type in ["BUY", "BUY_SIGNAL", "CAPITULATION_BUY"]:
                    if current <= level:
                        alerts_triggered.append({
                            "asset": asset,
                            "level": level,
                            "current": current,
                            "type": alert_type,
                            "description": alert["description"],
                            "action": alert["action"],
                            "priority": alert["priority"]
                        })
                elif alert_type == "WARNING":
                    if current >= level:
                        alerts_triggered.append({
                            "asset": asset,
                            "level": level,
                            "current": current,
                            "type": alert_type,
                            "description": alert["description"],
                            "action": alert["action"],
                            "priority": alert["priority"]
                        })
                elif alert_type == "WATCH":
                    if abs(current - level) / level < 0.02:  # Within 2%
                        alerts_triggered.append({
                            "asset": asset,
                            "level": level,
                            "current": current,
                            "type": "APPROACHING",
                            "description": alert["description"],
                            "action": alert["action"],
                            "priority": "MEDIUM"
                        })
    
    return alerts_triggered

def print_report(current_prices, alerts, config):
    """Print formatted alert report"""
    print("=" * 60)
    print("小龍 Market Alert Check")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    print()
    
    print("📊 CURRENT PRICES:")
    print(f"  • SPX:   {current_prices.get('SPX', 'N/A')}")
    print(f"  • HSI:   {current_prices.get('HSI', 'N/A')}")
    print(f"  • Oil:   ${current_prices.get('Oil_Brent', 'N/A')}/barrel")
    print(f"  • Gold:  ${current_prices.get('Gold', 'N/A')}/oz")
    print()
    
    print("🎯 KEY TARGET LEVELS (小龍 Mar 20):")
    print("  • SPX 6,400 → HSI 23,200: BUY 10% (high-conviction)")
    print("  • SPX 6,300 → HSI 22,500: BUY 10% (capitulation)")
    print("  • Oil $120+: WARNING (stagflation risk)")
    print("  • Gold $5,200: PARABOLIC PEAK — wait for $3,200 (-38%)")
    print()
    
    if alerts:
        print("🚨 ALERTS TRIGGERED:")
        for alert in sorted(alerts, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x["priority"], 4)):
            print(f"  [{alert['priority']}] {alert['asset']} @ {alert['current']}")
            print(f"      Level: {alert['level']} ({alert['type']})")
            print(f"      Action: {alert['action']}")
            print(f"      Note: {alert['description']}")
            print()
    else:
        print("✅ No alerts triggered - prices within normal range")
        print()
    
    print("📋 POSITION STRATEGY:")
    for pos, details in config["positionStrategy"].items():
        if isinstance(details, dict):
            pct = details.get('percent', details.get('rationale', ''))
            action = details.get('action', '')
            print(f"  • {pos}: {pct} → {action}")
    print()
    
    print("=" * 60)

def main():
    config = load_config()
    current_prices = get_current_prices()
    alerts = check_levels(current_prices, config)
    print_report(current_prices, alerts, config)
    
    return len(alerts)

if __name__ == "__main__":
    exit(main())
