#!/usr/bin/env python3
"""
Tencent (0700.HK) Technical Analysis Chart with Support/Resistance Lines
Creates an interactive HTML chart with:
- Price action (candlestick)
- Moving averages (20, 50, 200 day)
- Support/Resistance levels
- Trend lines
- Volume
"""

import csv
import json
from datetime import datetime
from collections import defaultdict

def load_data(filepath):
    """Load OHLCV data from CSV"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'Date': row['Date'],
                'Open': float(row['Open']),
                'High': float(row['High']),
                'Low': float(row['Low']),
                'Close': float(row['Close']),
                'Volume': int(row['Volume'])
            })
    return data

def calculate_ma(data, period):
    """Calculate moving average"""
    ma = []
    for i in range(len(data)):
        if i < period - 1:
            ma.append(None)
        else:
            avg = sum(data[j]['Close'] for j in range(i - period + 1, i + 1)) / period
            ma.append(round(avg, 2))
    return ma

def find_support_resistance(data, window=30):
    """Find key support and resistance levels based on price clusters"""
    recent = data[-window:] if len(data) > window else data
    
    # Find local highs and lows
    highs = [d['High'] for d in recent]
    lows = [d['Low'] for d in recent]
    
    # Cluster similar prices
    def cluster_prices(prices, tolerance=5.0):
        clusters = []
        for p in sorted(prices):
            found = False
            for c in clusters:
                if abs(p - c['center']) < tolerance:
                    c['count'] += 1
                    c['sum'] += p
                    c['center'] = c['sum'] / c['count']
                    found = True
                    break
            if not found:
                clusters.append({'center': p, 'count': 1, 'sum': p})
        # Return clusters with multiple touches
        return [c['center'] for c in clusters if c['count'] >= 2]
    
    all_highs = [d['High'] for d in data[-90:]]
    all_lows = [d['Low'] for d in data[-90:]]
    
    resistance_levels = cluster_prices(all_highs, tolerance=8.0)
    support_levels = cluster_prices(all_lows, tolerance=8.0)
    
    # Add recent high/low
    recent_high = max(all_highs)
    recent_low = min(all_lows)
    
    if recent_high not in resistance_levels:
        resistance_levels.append(recent_high)
    if recent_low not in support_levels:
        support_levels.append(recent_low)
    
    return sorted(support_levels), sorted(resistance_levels)

def find_trend_line(data, period=60):
    """Calculate linear regression trend line"""
    recent = data[-period:] if len(data) > period else data
    
    n = len(recent)
    if n < 2:
        return None, None
    
    # Simple linear regression
    x_mean = n / 2
    y_mean = sum(d['Close'] for d in recent) / n
    
    numerator = sum((i - x_mean) * (recent[i]['Close'] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return None, None
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate start and end points
    start_idx = len(data) - period
    start_price = intercept + slope * 0
    end_price = intercept + slope * (n - 1)
    
    return {
        'start_idx': start_idx,
        'start_price': round(start_price, 2),
        'end_idx': len(data) - 1,
        'end_price': round(end_price, 2),
        'slope': slope
    }, intercept

def generate_chart_html(data, ma20, ma50, ma200, support_levels, resistance_levels, trend_info):
    """Generate interactive HTML chart"""
    
    # Prepare data for Chart.js
    labels = [d['Date'] for d in data]
    close_prices = [d['Close'] for d in data]
    volumes = [d['Volume'] for d in data]
    
    # Get recent 90 days for display
    display_start = max(0, len(data) - 90)
    display_labels = labels[display_start:]
    display_close = close_prices[display_start:]
    display_ma20 = ma20[display_start:]
    display_ma50 = ma50[display_start:]
    display_volume = volumes[display_start:]
    
    # Current price
    current_price = data[-1]['Close']
    current_date = data[-1]['Date']
    
    # Price change
    prev_close = data[-2]['Close'] if len(data) > 1 else current_price
    price_change = ((current_price - prev_close) / prev_close) * 100
    
    # Build support/resistance annotations
    annotations = []
    colors = {'support': 'rgba(0, 255, 0, 0.3)', 'resistance': 'rgba(255, 0, 0, 0.3)'}
    
    for i, level in enumerate(support_levels[-3:]):  # Top 3 support
        annotations.append({
            'type': 'line',
            'yMin': level,
            'yMax': level,
            'borderColor': 'rgba(0, 255, 0, 0.8)',
            'borderWidth': 2,
            'borderDash': [5, 5],
            'label': {
                'display': True,
                'content': f'Support: {level:.0f}',
                'position': 'start',
                'backgroundColor': 'rgba(0, 100, 0, 0.8)',
                'color': 'white',
                'font': {'size': 11}
            }
        })
    
    for i, level in enumerate(resistance_levels[-3:]):  # Top 3 resistance
        annotations.append({
            'type': 'line',
            'yMin': level,
            'yMax': level,
            'borderColor': 'rgba(255, 0, 0, 0.8)',
            'borderWidth': 2,
            'borderDash': [5, 5],
            'label': {
                'display': True,
                'content': f'Resistance: {level:.0f}',
                'position': 'start',
                'backgroundColor': 'rgba(100, 0, 0, 0.8)',
                'color': 'white',
                'font': {'size': 11}
            }
        })
    
    # Add MA lines as datasets
    ma20_dataset = []
    ma50_dataset = []
    for i in range(len(display_labels)):
        ma20_dataset.append(display_ma20[i] if display_ma20[i] else None)
        ma50_dataset.append(display_ma50[i] if display_ma50[i] else None)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Tencent (0700.HK) - Technical Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #eee; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #00d4ff; text-align: center; margin-bottom: 10px; }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 20px; }}
        .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .card {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }}
        .card-label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }}
        .card-value {{ font-size: 24px; font-weight: bold; }}
        .positive {{ color: #00ff88; }}
        .negative {{ color: #ff4466; }}
        .chart-container {{ position: relative; height: 500px; margin: 20px 0; background: rgba(0,0,0,0.2); border-radius: 12px; padding: 20px; }}
        .volume-container {{ position: relative; height: 150px; margin: 10px 0 20px; background: rgba(0,0,0,0.2); border-radius: 12px; padding: 20px; }}
        .analysis {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .panel {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; }}
        .panel h3 {{ color: #00d4ff; margin-top: 0; }}
        .level {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        .level.support {{ color: #00ff88; }}
        .level.resistance {{ color: #ff6b6b; }}
        .legend {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 15px 0; justify-content: center; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .legend-color {{ width: 20px; height: 3px; }}
        .trend-up {{ color: #00ff88; }}
        .trend-down {{ color: #ff4466; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Tencent Holdings (0700.HK)</h1>
        <p class="subtitle">Technical Analysis with Support/Resistance Levels & Moving Averages</p>
        
        <div class="dashboard">
            <div class="card">
                <div class="card-label">Current Price</div>
                <div class="card-value">HKD {current_price:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Daily Change</div>
                <div class="card-value {'positive' if price_change >= 0 else 'negative'}">{price_change:+.2f}%</div>
            </div>
            <div class="card">
                <div class="card-label">90-Day High</div>
                <div class="card-value">HKD {max(display_close):.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">90-Day Low</div>
                <div class="card-value">HKD {min(display_close):.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">MA20</div>
                <div class="card-value">HKD {display_ma20[-1] if display_ma20[-1] else 'N/A'}</div>
            </div>
            <div class="card">
                <div class="card-label">MA50</div>
                <div class="card-value">HKD {display_ma50[-1] if display_ma50[-1] else 'N/A'}</div>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #00d4ff;"></div>
                <span>Close Price</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffa500;"></div>
                <span>MA20</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff6b6b;"></div>
                <span>MA50</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(0, 255, 0, 0.8);"></div>
                <span>Support Levels</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(255, 0, 0, 0.8);"></div>
                <span>Resistance Levels</span>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>
        
        <div class="volume-container">
            <canvas id="volumeChart"></canvas>
        </div>
        
        <div class="analysis">
            <div class="panel">
                <h3>📊 Support Levels</h3>
                {''.join(f'<div class="level support"><span>Support {i+1}</span><span>HKD {level:.2f}</span></div>' for i, level in enumerate(reversed(support_levels[-5:])))}
            </div>
            <div class="panel">
                <h3>📈 Resistance Levels</h3>
                {''.join(f'<div class="level resistance"><span>Resistance {i+1}</span><span>HKD {level:.2f}</span></div>' for i, level in enumerate(reversed(resistance_levels[-5:])))}
            </div>
        </div>
        
        <div class="analysis">
            <div class="panel">
                <h3>📉 Trend Analysis</h3>
                <p><strong>Short-term (20-day):</strong> {'<span class="trend-up">Bullish</span>' if current_price > display_ma20[-1] else '<span class="trend-down">Bearish</span>' if display_ma20[-1] else 'N/A'} </p>
                <p><strong>Medium-term (50-day):</strong> {'<span class="trend-up">Bullish</span>' if current_price > display_ma50[-1] else '<span class="trend-down">Bearish</span>' if display_ma50[-1] else 'N/A'}</p>
                <p><strong>MA20 vs MA50:</strong> {'<span class="trend-up">Golden Cross (Bullish)</span>' if display_ma20[-1] and display_ma50[-1] and display_ma20[-1] > display_ma50[-1] else '<span class="trend-down">Death Cross (Bearish)</span>' if display_ma20[-1] and display_ma50[-1] else 'N/A'}</p>
            </div>
            <div class="panel">
                <h3>🎯 Key Levels to Watch</h3>
                <p><strong>Next Resistance:</strong> HKD {resistance_levels[-1]:.2f} if broken → bullish continuation</p>
                <p><strong>Key Support:</strong> HKD {support_levels[-1]:.2f} if broken → bearish reversal</p>
                <p><strong>Current Position:</strong> Price is {'above' if current_price > display_ma20[-1] else 'below'} MA20, suggesting {'strength' if current_price > display_ma20[-1] else 'weakness'}</p>
            </div>
        </div>
    </div>
    
    <script>
        const labels = {json.dumps(display_labels)};
        const closeData = {json.dumps(display_close)};
        const volumeData = {json.dumps(display_volume)};
        const ma20Data = {json.dumps(ma20_dataset)};
        const ma50Data = {json.dumps(ma50_dataset)};
        
        const annotations = {json.dumps(annotations)};
        
        // Price Chart
        const priceCtx = document.getElementById('priceChart').getContext('2d');
        new Chart(priceCtx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Close Price',
                        data: closeData,
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 6
                    }},
                    {{
                        label: 'MA20',
                        data: ma20Data,
                        borderColor: '#ffa500',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0
                    }},
                    {{
                        label: 'MA50',
                        data: ma50Data,
                        borderColor: '#ff6b6b',
                        borderWidth: 2,
                        borderDash: [10, 5],
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    legend: {{
                        labels: {{ color: '#eee', font: {{ size: 12 }} }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.9)',
                        titleColor: '#00d4ff',
                        bodyColor: '#eee',
                        borderColor: '#333',
                        borderWidth: 1,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': HKD ' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }},
                    annotation: {{
                        annotations: annotations
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888', maxTicksLimit: 10 }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888', callback: (v) => 'HKD ' + v }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }}
                }}
            }}
        }});
        
        // Volume Chart
        const volumeCtx = document.getElementById('volumeChart').getContext('2d');
        new Chart(volumeCtx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Volume',
                    data: volumeData,
                    backgroundColor: closeData.map((v, i) => {{
                        if (i === 0) return 'rgba(0, 212, 255, 0.5)';
                        return v >= closeData[i-1] ? 'rgba(0, 255, 136, 0.5)' : 'rgba(255, 68, 102, 0.5)';
                    }}),
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.9)',
                        callbacks: {{
                            label: function(context) {{
                                return 'Volume: ' + context.parsed.y.toLocaleString();
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ display: false }},
                        grid: {{ display: false }}
                    }},
                    y: {{
                        ticks: {{ color: '#888', callback: (v) => (v/1000000).toFixed(1) + 'M' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''
    return html

def main():
    data_path = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    output_path = '/root/.openclaw/workspace/caisen_data/tencent_technical_chart.html'
    
    print("📊 Loading Tencent historical data...")
    data = load_data(data_path)
    print(f"   Loaded {len(data)} trading days")
    
    print("\n📈 Calculating technical indicators...")
    ma20 = calculate_ma(data, 20)
    ma50 = calculate_ma(data, 50)
    ma200 = calculate_ma(data, 200)
    print("   ✓ MA20, MA50, MA200 calculated")
    
    print("\n🎯 Finding support/resistance levels...")
    support_levels, resistance_levels = find_support_resistance(data)
    print(f"   ✓ Found {len(support_levels)} support levels")
    print(f"   ✓ Found {len(resistance_levels)} resistance levels")
    
    print("\n📉 Calculating trend lines...")
    trend_info, intercept = find_trend_line(data)
    if trend_info:
        print(f"   ✓ Trend slope: {trend_info['slope']:.4f} ({'uptrend' if trend_info['slope'] > 0 else 'downtrend'})")
    
    print("\n🎨 Generating interactive chart...")
    html = generate_chart_html(data, ma20, ma50, ma200, support_levels, resistance_levels, trend_info)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Chart saved to: {output_path}")
    
    # Print summary
    current = data[-1]['Close']
    print(f"\n{'='*60}")
    print(f"📊 TENCENT (0700.HK) TECHNICAL SUMMARY")
    print(f"{'='*60}")
    print(f"Current Price:     HKD {current:.2f}")
    print(f"MA20:              HKD {ma20[-1]:.2f} {'↑' if current > ma20[-1] else '↓'}")
    print(f"MA50:              HKD {ma50[-1]:.2f} {'↑' if current > ma50[-1] else '↓'}")
    print(f"MA200:             HKD {ma200[-1]:.2f} {'↑' if current > ma200[-1] else '↓'}")
    print(f"\nKey Support Levels:")
    for i, level in enumerate(reversed(support_levels[-3:]), 1):
        print(f"   S{i}: HKD {level:.2f}")
    print(f"\nKey Resistance Levels:")
    for i, level in enumerate(reversed(resistance_levels[-3:]), 1):
        print(f"   R{i}: HKD {level:.2f}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
