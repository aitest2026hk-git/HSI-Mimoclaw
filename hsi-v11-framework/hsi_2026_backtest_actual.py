#!/usr/bin/env python3
"""
HSI 2026 Backtest Analysis - Actual Data vs. Predictions
Compare predicted turning points vs. actual HSI performance in 2026 YTD
"""

import csv
from datetime import datetime
from pathlib import Path

# ============================================================================
# LOAD ACTUAL HSI 2026 DATA
# ============================================================================

def load_hsi_2026_data():
    """Load actual HSI data for 2026 from hsi.csv"""
    data = []
    with open('/root/.openclaw/workspace/hsi.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header (Chinese), parse data rows
    for line in lines[1:]:  # Skip header
        parts = line.strip().split(',')
        if len(parts) >= 7 and '2026' in parts[0]:
            try:
                date_str = parts[0]  # Format: M/D/YYYY
                date_parts = date_str.split('/')
                if len(date_parts) == 3:
                    date = datetime(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))
                    
                    # Column mapping (Chinese headers):
                    # 日期，收市，開市，高，低，成交量，升跌（%）
                    # 0    1    2    3    4    5    6
                    close = float(parts[1]) if parts[1] else 0
                    open_p = float(parts[2]) if parts[2] else 0
                    high = float(parts[3]) if parts[3] else 0
                    low = float(parts[4]) if parts[4] else 0
                    volume = parts[5] if len(parts) > 5 else '0'
                    change_pct_str = parts[6].replace('%', '') if len(parts) > 6 and parts[6] else '0'
                    change_pct = float(change_pct_str)
                    
                    data.append({
                        'date': date,
                        'date_str': date_str,
                        'open': open_p,
                        'high': high,
                        'low': low,
                        'close': close,
                        'volume': volume,
                        'change_pct': change_pct
                    })
            except Exception as e:
                continue
    return sorted(data, key=lambda x: x['date'])

# ============================================================================
# PREDICTED TURNING POINTS (from our v2.1 model)
# ============================================================================

PREDICTED_TURNS_2026 = [
    {'date': datetime(2026, 3, 24), 'type': 'HIGH', 'confidence': 105, 'event': '春分+Gann 90°+Square Root', 'window': '±5 days'},
    {'date': datetime(2026, 3, 21), 'type': 'WATCH', 'confidence': 75, 'event': '春分 Spring Equinox', 'window': '±3 days'},
    {'date': datetime(2026, 4, 19), 'type': 'MEDIUM', 'confidence': 50, 'event': '穀雨 Grain Rain', 'window': '±5 days'},
    {'date': datetime(2026, 5, 5), 'type': 'MEDIUM', 'confidence': 55, 'event': '立夏 Start of Summer', 'window': '±3 days'},
    {'date': datetime(2026, 5, 20), 'type': 'MEDIUM', 'confidence': 50, 'event': '小滿 Grain Full', 'window': '±5 days'},
    {'date': datetime(2026, 6, 25), 'type': 'HIGH', 'confidence': 85, 'event': '夏至 Summer Solstice+Gann 180°', 'window': '±5 days'},
    {'date': datetime(2026, 8, 11), 'type': 'HIGH', 'confidence': 75, 'event': '立秋 Start of Autumn', 'window': '±5 days'},
    {'date': datetime(2026, 9, 25), 'type': 'MEDIUM', 'confidence': 65, 'event': '秋分 Autumn Equinox', 'window': '±5 days'},
    {'date': datetime(2026, 10, 7), 'type': 'HIGH', 'confidence': 90, 'event': '寒露 Cold Dew', 'window': '±5 days'},
    {'date': datetime(2026, 12, 23), 'type': 'MEDIUM', 'confidence': 65, 'event': '冬至 Winter Solstice', 'window': '±5 days'},
]

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def find_actual_turns(data, window_days=5, min_change_pct=2.0):
    """Find actual turning points in the data"""
    turns = []
    
    for i in range(window_days, len(data) - window_days):
        center = data[i]
        
        # Look at window before and after
        before = data[i-window_days:i]
        after = data[i:i+window_days+1]
        
        if not before or not after:
            continue
        
        # Check if this is a local high
        before_max = max(d['high'] for d in before)
        after_max = max(d['high'] for d in after)
        center_high = center['high']
        
        if center_high > before_max and center_high > after_max:
            # This is a local high
            peak_change = max(d['change_pct'] for d in after[:3])
            if abs(peak_change) >= min_change_pct:
                turns.append({
                    'date': center['date'],
                    'date_str': center['date_str'],
                    'type': 'HIGH',
                    'price': center_high,
                    'change_pct': peak_change
                })
        
        # Check if this is a local low
        before_min = min(d['low'] for d in before)
        after_min = min(d['low'] for d in after)
        center_low = center['low']
        
        if center_low < before_min and center_low < after_min:
            # This is a local low
            trough_change = min(d['change_pct'] for d in after[:3])
            if abs(trough_change) >= min_change_pct:
                turns.append({
                    'date': center['date'],
                    'date_str': center['date_str'],
                    'type': 'LOW',
                    'price': center_low,
                    'change_pct': trough_change
                })
    
    return turns

def match_predictions_to_actuals(predicted, actual, window_days=7):
    """Match predicted turns to actual turns within a time window"""
    matches = []
    unmatched_predictions = []
    unmatched_actuals = actual.copy()
    
    for pred in predicted:
        matched = False
        for i, act in enumerate(unmatched_actuals):
            days_diff = abs((pred['date'] - act['date']).days)
            if days_diff <= window_days:
                # Match found
                matches.append({
                    'predicted': pred,
                    'actual': act,
                    'days_off': days_diff,
                    'accuracy': 'HIGH' if days_diff <= 3 else 'MEDIUM' if days_diff <= 5 else 'LOW'
                })
                unmatched_actuals.pop(i)
                matched = True
                break
        
        if not matched:
            unmatched_predictions.append(pred)
    
    return matches, unmatched_predictions, unmatched_actuals

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

print("=" * 90)
print("📊 HSI 2026 BACKTEST ANALYSIS - Predictions vs. Actual Performance")
print("=" * 90)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 90)

# Load data
print("\n📈 Loading HSI 2026 data...")
hsi_data = load_hsi_2026_data()
print(f"   ✅ Loaded {len(hsi_data)} trading days (Jan 2 - Feb 25, 2026)")

if hsi_data:
    # Summary statistics
    start_price = hsi_data[0]['close']
    end_price = hsi_data[-1]['close']
    high_price = max(d['high'] for d in hsi_data)
    low_price = min(d['low'] for d in hsi_data)
    high_date = [d for d in hsi_data if d['high'] == high_price][0]['date_str']
    low_date = [d for d in hsi_data if d['low'] == low_price][0]['date_str']
    
    print(f"\n📊 2026 YTD Performance Summary:")
    print(f"   Start (Jan 2):   {start_price:,.2f}")
    print(f"   End (Feb 25):    {end_price:,.2f}")
    print(f"   YTD Change:      {((end_price - start_price) / start_price * 100):+.2f}%")
    print(f"   High:            {high_price:,.2f} ({high_date})")
    print(f"   Low:             {low_price:,.2f} ({low_date})")
    print(f"   Volatility:      {((high_price - low_price) / start_price * 100):.2f}% range")

# Find actual turning points
print("\n🔍 Finding actual turning points...")
actual_turns = find_actual_turns(hsi_data, window_days=3, min_change_pct=1.5)
print(f"   Found {len(actual_turns)} turning points (±3 day window, >1.5% change)")

# Show actual turns
if actual_turns:
    print("\n📍 Actual Turning Points (2026 YTD):")
    print("   " + "-" * 70)
    for turn in actual_turns[:15]:  # Show first 15
        print(f"   {turn['date_str']:12} | {turn['type']:4} | Price: {turn['price']:>10,.2f} | Change: {turn['change_pct']:>+6.2f}%")
    if len(actual_turns) > 15:
        print(f"   ... and {len(actual_turns) - 15} more")

# Match predictions to actuals (only for dates that have passed)
print("\n🎯 Matching Predictions to Actuals...")
today = datetime(2026, 2, 25)  # Last data point
past_predictions = [p for p in PREDICTED_TURNS_2026 if p['date'] <= today]
future_predictions = [p for p in PREDICTED_TURNS_2026 if p['date'] > today]

print(f"   Past predictions (before Feb 25): {len(past_predictions)}")
print(f"   Future predictions: {len(future_predictions)}")

matches, unmatched_pred, unmatched_act = match_predictions_to_actuals(
    past_predictions, actual_turns, window_days=10
)

print(f"\n✅ Matches found: {len(matches)}")
print(f"⚠️  Unmatched predictions: {len(unmatched_pred)}")
print(f"⚠️  Unmatched actual turns: {len(unmatched_act)}")

# Show matches
if matches:
    print("\n📋 Prediction Accuracy:")
    print("   " + "-" * 85)
    print(f"   {'Predicted':15} | {'Actual':12} | {'Type':6} | {'Days Off':10} | {'Confidence':12} | {'Event':25}")
    print("   " + "-" * 85)
    for m in matches:
        pred_date = m['predicted']['date'].strftime('%Y-%m-%d')
        act_date = m['actual']['date'].strftime('%Y-%m-%d')
        conf = f"{m['predicted']['confidence']}pts"
        event = m['predicted']['event'][:25]
        print(f"   {pred_date:15} | {act_date:12} | {m['actual']['type']:6} | {m['days_off']:>8} days | {conf:12} | {event:25}")

# Calculate accuracy metrics
if past_predictions:
    accuracy_rate = len(matches) / len(past_predictions) * 100
    avg_days_off = sum(m['days_off'] for m in matches) / len(matches) if matches else 0
    
    print("\n📊 Accuracy Metrics:")
    print(f"   Hit Rate: {len(matches)}/{len(past_predictions)} = {accuracy_rate:.1f}%")
    print(f"   Average Days Off: {avg_days_off:.1f} days")
    
    # By confidence level
    high_conf = [p for p in past_predictions if p['confidence'] >= 75]
    high_conf_matches = [m for m in matches if m['predicted']['confidence'] >= 75]
    if high_conf:
        high_accuracy = len(high_conf_matches) / len(high_conf) * 100
        print(f"   High Confidence (75+ pts): {len(high_conf_matches)}/{len(high_conf)} = {high_accuracy:.1f}%")

# Future predictions
if future_predictions:
    print("\n🔮 Upcoming Turn Windows (Not Yet Testable):")
    print("   " + "-" * 80)
    for pred in future_predictions[:8]:
        date_str = pred['date'].strftime('%Y-%m-%d')
        print(f"   {date_str:12} | {pred['type']:8} | {pred['confidence']:3}pts | {pred['event'][:35]}")

# Save results
output_file = Path('/root/.openclaw/workspace/hsi_2026_backtest_actual.csv')
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Type', 'Predicted Date', 'Actual Date', 'Days Off', 'Confidence', 'Event', 'Actual Price', 'Actual Change%'])
    for m in matches:
        writer.writerow([
            m['actual']['type'],
            m['predicted']['date'].strftime('%Y-%m-%d'),
            m['actual']['date'].strftime('%Y-%m-%d'),
            m['days_off'],
            m['predicted']['confidence'],
            m['predicted']['event'],
            m['actual']['price'],
            f"{m['actual']['change_pct']:.2f}%"
        ])

print(f"\n💾 Results saved to: {output_file}")
print("=" * 90)
