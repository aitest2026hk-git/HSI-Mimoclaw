#!/usr/bin/env python3
"""
Generate Tencent stock chart as SVG (scalable vector graphics)
SVG can be opened in any browser and converted to other formats
"""

# Tencent price data (last 60 trading days)
data = [
    ("2026-01-02", 623.0), ("2026-01-05", 624.5), ("2026-01-06", 632.5),
    ("2026-01-07", 624.5), ("2026-01-08", 616.0), ("2026-01-09", 611.0),
    ("2026-01-12", 623.0), ("2026-01-13", 627.5), ("2026-01-14", 633.0),
    ("2026-01-15", 622.0), ("2026-01-16", 617.5), ("2026-01-19", 610.0),
    ("2026-01-20", 601.0), ("2026-01-21", 602.5), ("2026-01-22", 597.5),
    ("2026-01-23", 595.0), ("2026-01-26", 599.5), ("2026-01-27", 607.0),
    ("2026-01-28", 621.0), ("2026-01-29", 622.0), ("2026-01-30", 606.0),
    ("2026-02-02", 598.5), ("2026-02-03", 581.0), ("2026-02-04", 558.0),
    ("2026-02-05", 558.5), ("2026-02-06", 547.5), ("2026-02-09", 560.0),
    ("2026-02-10", 551.0), ("2026-02-11", 548.0), ("2026-02-12", 535.5),
    ("2026-02-13", 532.0), ("2026-02-16", 534.5), ("2026-02-20", 522.0),
    ("2026-02-23", 538.0), ("2026-02-24", 520.0), ("2026-02-25", 522.5),
    ("2026-02-26", 512.0), ("2026-02-27", 518.0)
]

# Chart dimensions
WIDTH = 1200
HEIGHT = 600
MARGIN_LEFT = 80
MARGIN_RIGHT = 40
MARGIN_TOP = 60
MARGIN_BOTTOM = 80
CHART_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
CHART_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

# Price range
prices = [p for _, p in data]
min_price = min(prices)
max_price = max(prices)
price_range = max_price - min_price

# Add padding to price range
min_price = int(min_price / 10) * 10 - 10
max_price = int(max_price / 10) * 10 + 10
price_range = max_price - min_price

def x_coord(i):
    return MARGIN_LEFT + (i / (len(data) - 1)) * CHART_WIDTH

def y_coord(price):
    return MARGIN_TOP + (1 - (price - min_price) / price_range) * CHART_HEIGHT

# Calculate MA20
def calc_ma(prices, period):
    ma = []
    for i in range(len(prices)):
        if i < period - 1:
            ma.append(None)
        else:
            ma.append(sum(prices[i-period+1:i+1]) / period)
    return ma

ma20 = calc_ma(prices, 20)

# Support and resistance levels
SUPPORT = 510.5
RESISTANCE = 538.0

# Generate SVG
svg_lines = []
svg_lines.append(f'<?xml version="1.0" encoding="UTF-8"?>')
svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')

# Background
svg_lines.append(f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="#0f0f23"/>')

# Title
svg_lines.append(f'  <text x="{WIDTH/2}" y="35" text-anchor="middle" font-family="Arial" font-size="20" fill="#00ff88" font-weight="bold">騰訊控股 (0700.HK) - 蔡森技術分析</text>')
svg_lines.append(f'  <text x="{WIDTH/2}" y="52" text-anchor="middle" font-family="Arial" font-size="12" fill="#888">2026-02-27 | Current: HKD 518.00</text>')

# Grid lines (horizontal)
for price in range(min_price, max_price + 1, 20):
    y = y_coord(price)
    svg_lines.append(f'  <line x1="{MARGIN_LEFT}" y1="{y}" x2="{WIDTH-MARGIN_RIGHT}" y2="{y}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>')
    svg_lines.append(f'  <text x="{MARGIN_LEFT-5}" y="{y+4}" text-anchor="end" font-family="Arial" font-size="10" fill="#888">{price}</text>')

# Support line
y_support = y_coord(SUPPORT)
svg_lines.append(f'  <line x1="{MARGIN_LEFT}" y1="{y_support}" x2="{WIDTH-MARGIN_RIGHT}" y2="{y_support}" stroke="rgba(0,255,136,0.6)" stroke-width="2" stroke-dasharray="5,5"/>')
svg_lines.append(f'  <text x="{WIDTH-MARGIN_RIGHT+5}" y="{y_support-5}" font-family="Arial" font-size="11" fill="#00ff88">Support: {SUPPORT}</text>')

# Resistance line
y_resist = y_coord(RESISTANCE)
svg_lines.append(f'  <line x1="{MARGIN_LEFT}" y1="{y_resist}" x2="{WIDTH-MARGIN_RIGHT}" y2="{y_resist}" stroke="rgba(255,68,102,0.6)" stroke-width="2" stroke-dasharray="5,5"/>')
svg_lines.append(f'  <text x="{WIDTH-MARGIN_RIGHT+5}" y="{y_resist-5}" font-family="Arial" font-size="11" fill="#ff4466">Resistance: {RESISTANCE}</text>')

# MA20 line
ma20_points = []
for i, ma in enumerate(ma20):
    if ma is not None:
        ma20_points.append(f'{x_coord(i)},{y_coord(ma)}')
if ma20_points:
    svg_lines.append(f'  <polyline points="{" ".join(ma20_points)}" fill="none" stroke="#ffa500" stroke-width="2" stroke-dasharray="5,5"/>')
    svg_lines.append(f'  <text x="{x_coord(len(data)-1)+5}" y="{y_coord(ma20[-1])+4}" font-family="Arial" font-size="11" fill="#ffa500">MA20: {ma20[-1]:.1f}</text>')

# Price line with gradient fill
price_points = []
for i, (date, price) in enumerate(data):
    price_points.append(f'{x_coord(i)},{y_coord(price)}')

# Fill area under price line
fill_points = f'{MARGIN_LEFT},{HEIGHT-MARGIN_BOTTOM} ' + ' '.join(price_points) + f' {WIDTH-MARGIN_RIGHT},{HEIGHT-MARGIN_BOTTOM}'
svg_lines.append(f'  <polygon points="{fill_points}" fill="rgba(0,212,255,0.1)"/>')

# Price line
svg_lines.append(f'  <polyline points="{" ".join(price_points)}" fill="none" stroke="#00d4ff" stroke-width="2.5"/>')

# Data points (circles)
for i, (date, price) in enumerate(data):
    x = x_coord(i)
    y = y_coord(price)
    svg_lines.append(f'  <circle cx="{x}" cy="{y}" r="3" fill="#00d4ff" opacity="0.7"/>')

# X-axis labels (every 5th date)
for i, (date, _) in enumerate(data):
    if i % 5 == 0:
        x = x_coord(i)
        svg_lines.append(f'  <text x="{x}" y="{HEIGHT-MARGIN_BOTTOM+20}" text-anchor="middle" font-family="Arial" font-size="9" fill="#888">{date[5:]}</text>')

# X-axis line
svg_lines.append(f'  <line x1="{MARGIN_LEFT}" y1="{HEIGHT-MARGIN_BOTTOM}" x2="{WIDTH-MARGIN_RIGHT}" y2="{HEIGHT-MARGIN_BOTTOM}" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>')

# Legend
legend_y = HEIGHT - 25
legend_items = [
    ("#00d4ff", "Price"),
    ("#ffa500", "MA20"),
    ("#ff6b6b", "MA50"),
    ("rgba(0,255,136,0.6)", f"Support {SUPPORT}"),
    ("rgba(255,68,102,0.6)", f"Resistance {RESISTANCE}")
]
legend_x = MARGIN_LEFT
for color, label in legend_items:
    svg_lines.append(f'  <rect x="{legend_x}" y="{legend_y-8}" width="15" height="3" fill="{color}"/>')
    svg_lines.append(f'  <text x="{legend_x+20}" y="{legend_y}" font-family="Arial" font-size="11" fill="#ccc">{label}</text>')
    legend_x += 100

# Current price indicator
current_price = prices[-1]
y_current = y_coord(current_price)
svg_lines.append(f'  <circle cx="{x_coord(len(data)-1)}" cy="{y_current}" r="6" fill="#00ff88" opacity="0.8"/>')
svg_lines.append(f'  <text x="{x_coord(len(data)-1)}" y="{y_current-12}" text-anchor="middle" font-family="Arial" font-size="12" fill="#00ff88" font-weight="bold">518.00</text>')

# Signal box
svg_lines.append(f'  <rect x="{MARGIN_LEFT}" y="{MARGIN_TOP-35}" width="150" height="25" fill="rgba(255,68,102,0.2)" stroke="#ff4466" stroke-width="1" rx="5"/>')
svg_lines.append(f'  <text x="{MARGIN_LEFT+75}" y="{MARGIN_TOP-18}" text-anchor="middle" font-family="Arial" font-size="12" fill="#ff4466" font-weight="bold">BEARISH</text>')

svg_lines.append('</svg>')

# Write SVG
with open('/root/.openclaw/workspace/caisen_data/tencent_chart.svg', 'w') as f:
    f.write('\n'.join(svg_lines))

print("✅ SVG chart created: /root/.openclaw/workspace/caisen_data/tencent_chart.svg")
print(f"   Size: {WIDTH}x{HEIGHT} pixels")
print(f"   Data points: {len(data)}")
print(f"   Price range: {min_price} - {max_price}")
print(f"   Current price: {current_price}")
