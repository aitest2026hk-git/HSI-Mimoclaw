#!/usr/bin/env python3
"""
Fetch Latest Stock Prices - urllib version (no requests needed)
For: 3690.HK, 916.HK, 728.HK, HSI
"""

import json
import urllib.request
import ssl
from datetime import datetime

def fetch_stock_data(symbol):
    """Fetch stock data from Yahoo Finance using urllib"""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=10d'
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode())
        
        result = data['chart']['result'][0]
        quotes = result['quotes']
        meta = result['meta']
        
        if quotes:
            latest = quotes[-1]
            prev = quotes[-2] if len(quotes) > 1 else quotes[-1]
            
            close = latest.get('close', 0) or 0
            prev_close = prev.get('close', close) or close
            open_p = latest.get('open', close) or close
            high = latest.get('high', close) or close
            low = latest.get('low', close) or close
            volume = latest.get('volume', 0) or 0
            
            change = close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            # Get trading date
            timestamp = latest.get('datetime', meta.get('currentTradingPeriod', {}).get('regular', {}).get('end', 0))
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d') if timestamp else 'N/A'
            
            return {
                'symbol': symbol,
                'date': date_str,
                'close': close,
                'open': open_p,
                'high': high,
                'low': low,
                'volume': volume,
                'change': change,
                'change_pct': change_pct,
                'status': 'OK'
            }
    except urllib.error.HTTPError as e:
        return {'symbol': symbol, 'status': 'ERROR', 'error': f'HTTP {e.code}'}
    except Exception as e:
        return {'symbol': symbol, 'status': 'ERROR', 'error': str(e)}

# Stocks to fetch
stocks = [
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

for symbol, name in stocks:
    print(f'\nFetching {symbol}...')
    data = fetch_stock_data(symbol)
    
    if data['status'] == 'OK':
        results.append(data)
        print(f"  ✅ {name} ({symbol})")
        print(f"     Date: {data['date']}")
        print(f"     Close: HK${data['close']:.2f}")
        print(f"     Change: {data['change']:+.2f} ({data['change_pct']:+.2f}%)")
        print(f"     Open: HK${data['open']:.2f} | High: HK${data['high']:.2f} | Low: HK${data['low']:.2f}")
        print(f"     Volume: {data['volume']:,}")
    else:
        print(f"  ⚠️ {name} ({symbol}): {data.get('error', 'Failed')}")
        results.append(data)

print('\n' + '=' * 80)

# Save results
output_file = '/root/.openclaw/workspace/latest_prices_2026-03-18.json'
with open(output_file, 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'data': results
    }, f, indent=2, ensure_ascii=False)

print(f'💾 Saved to: {output_file}')
print('=' * 80)
