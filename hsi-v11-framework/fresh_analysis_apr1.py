#!/usr/bin/env python3
"""
HSI v11.3 Fresh Analysis — April 1, 2026
Using latest live data from Yahoo Finance
"""

import csv
import json
from datetime import datetime, timedelta
from statistics import mean, stdev
import math

# ============================================================================
# LOAD DATA
# ============================================================================

def load_data(filepath):
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'date': row['Date'],
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(float(row['Volume']))
                })
            except:
                continue
    return data

data = load_data('/tmp/hsi_latest.csv')
N = len(data)
print(f"Loaded {N} trading days of HSI data")
print(f"Date range: {data[0]['date']} to {data[-1]['date']}")
print()

# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

def sma(p, end_idx):
    if end_idx < p - 1: return None
    return mean([data[i]['close'] for i in range(end_idx - p + 1, end_idx + 1)])

def ema(p, end_idx):
    if end_idx < p - 1: return None
    k = 2 / (p + 1)
    e = mean([data[i]['close'] for i in range(p)])
    for i in range(p, end_idx + 1):
        e = data[i]['close'] * k + e * (1 - k)
    return e

def rsi(p, end_idx):
    if end_idx < p: return 50
    gains, losses = [], []
    for i in range(end_idx - p + 1, end_idx + 1):
        d = data[i]['close'] - data[i-1]['close']
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag, al = mean(gains), mean(losses)
    if al == 0: return 100
    return 100 - (100 / (1 + ag / al))

def macd(end_idx):
    if end_idx < 26: return 0, 0, 0
    ema12 = ema(12, end_idx)
    ema26 = ema(26, end_idx)
    if not ema12 or not ema26: return 0, 0, 0
    macd_line = ema12 - ema26
    # Signal line = 9-period EMA of MACD
    if end_idx < 35: return macd_line, 0, macd_line
    macd_vals = []
    for i in range(35, end_idx + 1):
        e12 = ema(12, i)
        e26 = ema(26, i)
        if e12 and e26:
            macd_vals.append(e12 - e26)
    if not macd_vals: return macd_line, 0, macd_line
    k = 2/10
    signal = macd_vals[0]
    for v in macd_vals[1:]:
        signal = v * k + signal * (1 - k)
    return macd_line, signal, macd_line - signal

def bollinger(p, end_idx):
    if end_idx < p - 1: return None, None, None
    prices = [data[i]['close'] for i in range(end_idx - p + 1, end_idx + 1)]
    m = mean(prices)
    s = stdev(prices)
    return m + 2*s, m, m - 2*s

def atr(p, end_idx):
    if end_idx < p: return 0
    trs = []
    for i in range(end_idx - p + 1, end_idx + 1):
        h, l = data[i]['high'], data[i]['low']
        pc = data[i-1]['close']
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return mean(trs)

def obv(end_idx):
    val = 0
    for i in range(1, end_idx + 1):
        if data[i]['close'] > data[i-1]['close']:
            val += data[i]['volume']
        elif data[i]['close'] < data[i-1]['close']:
            val -= data[i]['volume']
    return val

# ============================================================================
# CURRENT STATE
# ============================================================================

cur = data[-1]
prev = data[-2]
idx = N - 1

print("=" * 70)
print("  HSI v11.3 FRESH ANALYSIS — April 1, 2026")
print("=" * 70)
print(f"\n📊 CURRENT PRICE ACTION")
print(f"  Close:      {cur['close']:,.2f}")
print(f"  Open:       {cur['open']:,.2f}")
print(f"  High:       {cur['high']:,.2f}")
print(f"  Low:        {cur['low']:,.2f}")
print(f"  Day Change: {cur['close'] - prev['close']:+,.2f} ({(cur['close']-prev['close'])/prev['close']*100:+.2f}%)")
print(f"  Volume:     {cur['volume']:,.0f}")

# Key moving averages
ma5 = sma(5, idx)
ma10 = sma(10, idx)
ma20 = sma(20, idx)
ma50 = sma(50, idx)
ma200 = sma(200, idx) if idx >= 199 else None
ema12_val = ema(12, idx)
ema26_val = ema(26, idx)

print(f"\n📈 MOVING AVERAGES")
print(f"  MA5:    {ma5:,.2f}  {'✅ Above' if cur['close'] > ma5 else '❌ Below'}")
print(f"  MA10:   {ma10:,.2f}  {'✅ Above' if cur['close'] > ma10 else '❌ Below'}")
print(f"  MA20:   {ma20:,.2f}  {'✅ Above' if cur['close'] > ma20 else '❌ Below'}")
print(f"  MA50:   {ma50:,.2f}  {'✅ Above' if cur['close'] > ma50 else '❌ Below'}")
if ma200:
    print(f"  MA200:  {ma200:,.2f}  {'✅ Above' if cur['close'] > ma200 else '❌ Below'}")
else:
    print(f"  MA200:  N/A (insufficient data)")

# RSI
rsi14 = rsi(14, idx)
rsi6 = rsi(6, idx)
print(f"\n📊 MOMENTUM")
print(f"  RSI(14): {rsi14:.1f}  {'🔴 Overbought' if rsi14 > 70 else '🟢 Oversold' if rsi14 < 30 else '⚪ Neutral'}")
print(f"  RSI(6):  {rsi6:.1f}  {'🔴 Overbought' if rsi6 > 70 else '🟢 Oversold' if rsi6 < 30 else '⚪ Neutral'}")

# MACD
macd_line, signal, histogram = macd(idx)
print(f"  MACD Line:    {macd_line:.2f}")
print(f"  Signal Line:  {signal:.2f}")
print(f"  Histogram:    {histogram:.2f}  {'🟢 Bullish' if histogram > 0 else '🔴 Bearish'}")

# Bollinger Bands
bb_upper, bb_mid, bb_lower = bollinger(20, idx)
print(f"\n📊 BOLLINGER BANDS (20,2)")
print(f"  Upper:  {bb_upper:,.2f}")
print(f"  Middle: {bb_mid:,.2f}")
print(f"  Lower:  {bb_lower:,.2f}")
bb_pct = (cur['close'] - bb_lower) / (bb_upper - bb_lower) * 100
print(f"  %B:     {bb_pct:.1f}%  {'🔴 Near upper' if bb_pct > 80 else '🟢 Near lower' if bb_pct < 20 else '⚪ Mid-range'}")

# ATR
atr14 = atr(14, idx)
print(f"\n📊 VOLATILITY")
print(f"  ATR(14): {atr14:,.2f}")
print(f"  ATR%:    {atr14/cur['close']*100:.2f}%")

# OBV trend
obv_now = obv(idx)
obv_20 = obv(max(0, idx - 20))
print(f"\n📊 VOLUME (OBV)")
print(f"  OBV Current:  {obv_now:,.0f}")
print(f"  OBV 20d Ago:  {obv_20:,.0f}")
print(f"  OBV Trend:    {'🟢 Rising (accumulation)' if obv_now > obv_20 else '🔴 Falling (distribution)'}")

# ============================================================================
# MULTI-TIMEFRAME ANALYSIS
# ============================================================================

print(f"\n{'='*70}")
print("  MULTI-TIMEFRAME ANALYSIS")
print("=" * 70)

for period, label in [(5, '5-day'), (10, '10-day'), (20, '20-day'), (60, '60-day')]:
    if idx < period: continue
    start_price = data[idx - period]['close']
    change = (cur['close'] - start_price) / start_price * 100
    period_high = max(data[i]['high'] for i in range(idx - period + 1, idx + 1))
    period_low = min(data[i]['low'] for i in range(idx - period + 1, idx + 1))
    pos_in_range = (cur['close'] - period_low) / (period_high - period_low) * 100 if period_high != period_low else 50
    print(f"\n  {label}: {change:+.2f}%  |  Range: {period_low:,.2f} - {period_high:,.2f}  |  Position: {pos_in_range:.0f}%")

# ============================================================================
# SUPPORT / RESISTANCE LEVELS
# ============================================================================

print(f"\n{'='*70}")
print("  KEY SUPPORT & RESISTANCE LEVELS")
print("=" * 70)

# Find recent pivot points
pivots_high = []
pivots_low = []
for i in range(2, N - 2):
    if data[i]['high'] > data[i-1]['high'] and data[i]['high'] > data[i-2]['high'] and \
       data[i]['high'] > data[i+1]['high'] and data[i]['high'] > data[i+2]['high']:
        pivots_high.append((data[i]['date'], data[i]['high']))
    if data[i]['low'] < data[i-1]['low'] and data[i]['low'] < data[i-2]['low'] and \
       data[i]['low'] < data[i+1]['low'] and data[i]['low'] < data[i+2]['low']:
        pivots_low.append((data[i]['date'], data[i]['low']))

# Cluster nearby levels
def cluster_levels(levels, threshold=200):
    if not levels: return []
    levels.sort(key=lambda x: x[1])
    clusters = [[levels[0]]]
    for l in levels[1:]:
        if l[1] - clusters[-1][-1][1] < threshold:
            clusters[-1].append(l)
        else:
            clusters.append([l])
    return [(mean([x[1] for x in c]), max(x[1] for x in c), min(x[1] for x in c), len(c), c[-1][0]) for c in clusters]

# Resistance levels above current price
resistance_levels = [p for p in pivots_high if p[1] > cur['close']]
res_clusters = cluster_levels(resistance_levels, 150)
print(f"\n  RESISTANCE (above {cur['close']:,.2f}):")
for level, high, low, count, recent_date in sorted(res_clusters, key=lambda x: x[0])[:5]:
    distance = (level - cur['close']) / cur['close'] * 100
    print(f"    {level:,.2f}  (+{distance:.1f}%)  [{count} pivots, last: {recent_date}]")

# Support levels below current price
support_levels = [p for p in pivots_low if p[1] < cur['close']]
sup_clusters = cluster_levels(support_levels, 150)
print(f"\n  SUPPORT (below {cur['close']:,.2f}):")
for level, high, low, count, recent_date in sorted(sup_clusters, key=lambda x: x[0], reverse=True)[:5]:
    distance = (cur['close'] - level) / cur['close'] * 100
    print(f"    {level:,.2f}  (-{distance:.1f}%)  [{count} pivots, last: {recent_date}]")

# Key MA levels as S/R
print(f"\n  KEY MA LEVELS:")
for name, val in [('MA5', ma5), ('MA10', ma10), ('MA20', ma20), ('MA50', ma50)]:
    if val:
        pos = 'R' if val > cur['close'] else 'S'
        print(f"    {name}: {val:,.2f} ({pos}) — {abs(val-cur['close']):,.2f} pts away")

# ============================================================================
# TREND SCORING (v11 methodology)
# ============================================================================

print(f"\n{'='*70}")
print("  v11.3 TREND SCORING")
print("=" * 70)

score = 0
factors = []

# Factor 1: MA alignment (bullish if short > long and price > all)
if ma5 > ma10 > ma20 > ma50:
    score += 2; factors.append(("MA Alignment (5>10>20>50)", +2, "✅ Bullish stack"))
elif ma5 < ma10 < ma20 < ma50:
    score -= 2; factors.append(("MA Alignment (5<10<20<50)", -2, "❌ Bearish stack"))
else:
    if cur['close'] > ma20:
        score += 1; factors.append(("Price > MA20", +1, "🟡 Mild bullish"))
    else:
        score -= 1; factors.append(("Price < MA20", -1, "🟡 Mild bearish"))

# Factor 2: Price vs MA50
if cur['close'] > ma50:
    score += 1; factors.append(("Price > MA50", +1, "✅"))
else:
    score -= 1; factors.append(("Price < MA50", -1, "❌"))

# Factor 3: RSI
if rsi14 > 50:
    score += 1; factors.append(("RSI14 > 50", +1, f"✅ RSI={rsi14:.1f}"))
else:
    score -= 1; factors.append(("RSI14 < 50", -1, f"❌ RSI={rsi14:.1f}"))

# Factor 4: MACD
if histogram > 0:
    score += 1; factors.append(("MACD Histogram > 0", +1, "✅ Bullish momentum"))
else:
    score -= 1; factors.append(("MACD Histogram < 0", -1, "❌ Bearish momentum"))

# Factor 5: OBV trend
if obv_now > obv_20:
    score += 1; factors.append(("OBV Rising", +1, "✅ Accumulation"))
else:
    score -= 1; factors.append(("OBV Falling", -1, "❌ Distribution"))

# Factor 6: Bollinger position
if bb_pct > 50:
    score += 1; factors.append(("BB% > 50%", +1, "✅ Upper half"))
else:
    score -= 1; factors.append(("BB% < 50%", -1, "❌ Lower half"))

# Factor 7: Day momentum (today's close vs open)
if cur['close'] > cur['open']:
    score += 1; factors.append(("Bullish candle today", +1, "✅ Close > Open"))
else:
    score -= 1; factors.append(("Bearish candle today", -1, "❌ Close < Open"))

for name, pts, note in factors:
    direction = "▲" if pts > 0 else "▼"
    print(f"  {direction} {pts:+d}  {name:30s}  {note}")

print(f"\n  TREND SCORE: {score}/7")
if score >= 5:
    signal_str = "🟢 STRONG BULLISH"
elif score >= 3:
    signal_str = "🟡 MILD BULLISH"
elif score >= 1:
    signal_str = "⚪ LEAN BULLISH"
elif score == 0:
    signal_str = "⚪ NEUTRAL"
elif score >= -2:
    signal_str = "⚪ LEAN BEARISH"
elif score >= -4:
    signal_str = "🟡 MILD BEARISH"
else:
    signal_str = "🔴 STRONG BEARISH"
print(f"  SIGNAL:    {signal_str}")

# ============================================================================
# MACRO CONTEXT
# ============================================================================

print(f"\n{'='*70}")
print("  MACRO CONTEXT (as of Apr 1, 2026)")
print("=" * 70)

macro = {
    'S&P 500': ('6,528.52', '+2.91%', '🟢'),
    'VIX': ('24.48', '-3.05%', '🟢 Fear receding'),
    'Gold': ('$4,738.80', '+1.96%', '🟡'),
    'Brent Oil': ('$100.64', '-14.96% CRASH', '🟢 De-escalation signal'),
    'WTI Oil': ('$97.93', '', '🟢'),
    '10Y Yield': ('4.31%', '-0.03%', '⚪ Stable'),
}

for name, (level, change, note) in macro.items():
    print(f"  {name:12s}: {level:15s}  {change:20s}  {note}")

# ============================================================================
# GEOPOLITICAL ASSESSMENT
# ============================================================================

print(f"\n{'='*70}")
print("  ⚠️  GEOPOLITICAL ASSESSMENT")
print("=" * 70)
print("""
  MAJOR SIGNAL: Brent crude crashed from $118.35 to $100.64 (-15%)!
  
  This is a STRONG de-escalation signal:
  • Iran/Hormuz premium unwinding rapidly
  • April 6 deadline approaching — markets pricing in resolution
  • S&P 500 +2.91% confirms risk-on rotation
  • VIX declining (30.61 → 25.25 → 24.48) = fear evaporating
  
  Interpretation:
  • Oil crash + equity rally = geopolitical risk-off event REVERSING
  • This aligns with 小龍's "triple top" oil pattern → de-escalation
  • April 6 deadline may see early resolution or extension
""")

# ============================================================================
# v11.3 FRAMEWORK: FOUR-CYCLE POSITIONING
# ============================================================================

print(f"{'='*70}")
print("  v11.3 CYCLE POSITIONING (Zhou Jintao Framework)")
print("=" * 70)
print("""
  Kondratiev (50-60yr):  Depression → Recovery Transition (2025-2026)
  Real Estate (20yr):    Late Decline → Early Recovery
  Juglar (9yr):          Mid-Recovery (2023-2028 peak)
  Kitchin (18mo):        Expansion phase, Q3-Q4 peak expected
  
  Combined: ALL cycles pointing UP (rare alignment)
  Implication: April dip = BUY opportunity in new cycle
""")

# ============================================================================
# ACTIONABLE TRADING FRAMEWORK
# ============================================================================

print(f"{'='*70}")
print("  📋 ACTIONABLE TRADING FRAMEWORK")
print("=" * 70)

# Calculate key levels
recent_20d_high = max(data[i]['high'] for i in range(idx-19, idx+1))
recent_20d_low = min(data[i]['low'] for i in range(idx-19, idx+1))
recent_60d_high = max(data[i]['high'] for i in range(idx-59, idx+1))
recent_60d_low = min(data[i]['low'] for i in range(idx-59, idx+1))

print(f"""
  CURRENT: HSI {cur['close']:,.2f} (Apr 1, 2026)
  SIGNAL:  {signal_str} (Score: {score}/7)
  
  ┌────────────────────────────────────────────────────┐
  │  RESISTANCE ZONES                                  │
  │  R3: {recent_60d_high:,.2f}  (60-day high)                  │
  │  R2: 25,500-25,700  (Mar 19 high area)             │
  │  R1: 25,430  (today's high / near-term ceiling)    │
  ├────────────────────────────────────────────────────┤
  │  CURRENT: {cur['close']:,.2f}                            │
  ├────────────────────────────────────────────────────┤
  │  SUPPORT ZONES                                     │
  │  S1: 25,000-25,100  (psychological + today's low)  │
  │  S2: {ma20:,.2f}  (MA20)                           │
  │  S3: 24,400-24,600  (Mar 30 low area)              │
  │  S4: 24,382  (Mar 23 low — flash crash low)        │
  │  S5: 23,591  (SD inner band — deploy 3%)           │
  │  S6: 22,253  (SD outer band — MAX deploy)          │
  └────────────────────────────────────────────────────┘
  
  RECOMMENDED ACTIONS:
  
  🟢 SHORT-TERM (1-5 days): BULLISH
     • Oil de-escalation + VIX drop = risk-on environment
     • HSI likely tests 25,400-25,500 resistance
     • If oil continues falling → equity rally extends
  
  🟡 MEDIUM-TERM (1-4 weeks): CAUTIOUSLY BULLISH
     • April 6 Iran deadline still binary risk
     • If resolved → 26,000+ test possible
     • If escalates → 24,400 retest likely
     
  📊 POSITION SIZING:
     • At 25,264: Small position (0-2%) — just broke out
     • Pullback to 24,800-25,000: Add 3%
     • Pullback to 24,400: Add 5%
     • Major dip to 23,591: Deploy 3%
     • Capitulation to 22,253: MAX deployment
     
  ⚠️ RISK FACTORS:
     • April 6 Iran deadline (BINARY — 5 days away)
     • Oil reversal if tensions re-escalate
     • S&P 500 at 6,528 — approaching resistance
     • Gold still elevated at $4,739 = lingering fear
""")

# ============================================================================
# COMPARISON WITH MAR 31 ANALYSIS
# ============================================================================

print(f"{'='*70}")
print("  📊 CHANGE SINCE MAR 31 ANALYSIS")
print("=" * 70)
print(f"""
  | Metric          | Mar 31       | Apr 1        | Change         |
  |-----------------|-------------|-------------|----------------|
  | HSI             | 24,788      | 25,261      | +473 (+1.91%)  |
  | S&P 500         | 6,447       | 6,529       | +82 (+1.27%)   |
  | VIX             | 25.25       | 24.48       | -0.77 (-3.05%) |
  | Brent Oil       | $112.78     | $100.64     | -$12.14 (-11%) |
  | Gold            | $4,571      | $4,739      | +$168 (+3.7%)  |
  | 10Y Yield       | 4.34%       | 4.31%       | -0.03%         |
  
  KEY CHANGE: Oil crashed -15% = MAJOR de-escalation signal
  The market has shifted from "WAIT" to "CAUTIOUSLY ACCUMULATE"
""")

print("=" * 70)
print(f"  Analysis complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
