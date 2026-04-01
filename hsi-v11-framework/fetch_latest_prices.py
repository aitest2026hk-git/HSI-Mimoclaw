#!/usr/bin/env python3
"""
Fetch Latest Stock Prices & Volume Data
For: 3690.HK (Meituan), 916.HK (Longyuan), 728.HK (China Telecom), HSI
"""

import json
import urllib.request
import ssl
from datetime import datetime, timedelta

def fetch_yahoo_data(symbol, days=30):
    """Fetch recent data from Yahoo Finance"""
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={int(start.timestamp())}&period2={int(end.timestamp())}&interval=1d'
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode())
        
        quotes = data['chart']['result'][0]['quotes']
        if quotes:
            latest = quotes[-1]
            prev = quotes[-2] if len(quotes) > 1 else quotes[-1]
            return {
                'symbol': symbol,
                'date': datetime.fromtimestamp(latest['datetime']).strftime('%Y-%m-%d'),
                'close': round(latest.get('close', 0), 2),
                'open': round(latest.get('open', 0), 2),
                'high': round(latest.get('high', 0), 2),
                'low': round(latest.get('low', 0), 2),
                'volume': latest.get('volume', 0),
                'change': round(latest.get('close', 0) - prev.get('close', 0), 2),
                'change_pct': round((latest.get('close', 0) - prev.get('close', 0)) / prev.get('close', 1) * 100, 2)
            }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}
    return None

def fetch_stooq_data(symbol, days=30):
    """Fallback: Fetch from Stooq"""
    try:
        stooq_symbol = symbol.replace('.HK', '')
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&d1={(datetime.now()-timedelta(days=days)).strftime('%Y%m%d')}&d2={datetime.now().strftime('%Y%m%d')}&i=d"
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            lines = response.read().decode().strip().split('\n')
        
        if len(lines) > 1:
            parts = lines[-1].split(',')
            prev_parts = lines[-2].split(',') if len(lines) > 2 else parts
            return {
                'symbol': symbol,
                'date': parts[0],
                'close': float(parts[4]),
                'open': float(parts[1]),
                'high': float(parts[2]),
                'low': float(parts[3]),
                'volume': int(parts[5]) if len(parts) > 5 and parts[5].strip() else 0,
                'change': round(float(parts[4]) - float(prev_parts[4]), 2),
                'change_pct': round((float(parts[4]) - float(prev_parts[4])) / float(prev_parts[4]) * 100, 2)
            }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}
    return None

# Main execution
symbols = [
    ('3690.HK', 'Meituan (美团)'),
    ('916.HK', 'Longyuan Power (龙源电力)'),
    ('728.HK', 'China Telecom (中国电信)'),
    ('^HSI', 'Hang Seng Index (恒生指数)')
]

print('=' * 80)
print('📊 LATEST STOCK PRICES & VOLUME DATA')
print('=' * 80)
print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}')
print('=' * 80)

results = []

for symbol, name in symbols:
    # Try Yahoo first, then Stooq
    data = fetch_yahoo_data(symbol)
    if not data or 'error' in data:
        data = fetch_stooq_data(symbol)
    
    if data and 'error' not in data:
        results.append(data)
        print(f"\n{name} ({symbol})")
        print(f"  Date: {data['date']}")
        print(f"  Close: HK${data['close']:.2f}")
        print(f"  Change: {data['change']:+.2f} ({data['change_pct']:+.2f}%)")
        print(f"  Open: HK${data['open']:.2f} | High: HK${data['high']:.2f} | Low: HK${data['low']:.2f}")
        print(f"  Volume: {data['volume']:,}")
    else:
        print(f"\n⚠️ {name} ({symbol}): Failed to fetch data")
        if data:
            print(f"  Error: {data.get('error', 'Unknown')}")

print('\n' + '=' * 80)

# Save to JSON
output_file = '/root/.openclaw/workspace/latest_prices_2026-03-18.json'
with open(output_file, 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'data': results
    }, f, indent=2)

print(f"💾 Saved to: {output_file}")
print('=' * 80)
