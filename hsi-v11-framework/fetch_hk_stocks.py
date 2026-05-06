#!/usr/bin/env python3
"""
Fetch HK stock data from Yahoo Finance
Stocks: 03690.HK (Meituan), 00916.HK (Longyuan), 00020.HK (Sensetime), 02318.HK (Ping An), 00345.HK (Vitasoy)
"""

import urllib.request
import ssl
import json
import os
from datetime import datetime

# Stock codes for Yahoo Finance
STOCKS = [
    {'code': '03690.HK', 'name': 'Meituan', 'file': '3690_HK.csv'},
    {'code': '00916.HK', 'name': 'Longyuan_Power', 'file': '916_HK.csv'},
    {'code': '00020.HK', 'name': 'Sensetime', 'file': '20_HK.csv'},
    {'code': '02318.HK', 'name': 'Ping_An_Insurance', 'file': '2318_HK.csv'},
    {'code': '00345.HK', 'name': 'Vitasoy', 'file': '345_HK.csv'},
]

OUTPUT_DIR = '/root/.openclaw/workspace/caisen_data'

def fetch_yahoo_data(symbol: str) -> dict:
    """Fetch historical data from Yahoo Finance"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1=1672531200&period2=1741392000&interval=1d"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'indicators' in result and 'quote' in result['indicators']:
                    quote = result['indicators']['quote'][0]
                    timestamps = result.get('timestamp', [])
                    
                    rows = []
                    for i in range(len(timestamps)):
                        date = datetime.utcfromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
                        open_p = quote.get('open', [])[i] if i < len(quote.get('open', [])) else None
                        high_p = quote.get('high', [])[i] if i < len(quote.get('high', [])) else None
                        low_p = quote.get('low', [])[i] if i < len(quote.get('low', [])) else None
                        close_p = quote.get('close', [])[i] if i < len(quote.get('close', [])) else None
                        volume = quote.get('volume', [])[i] if i < len(quote.get('volume', [])) else 0
                        
                        if all([open_p, high_p, low_p, close_p]):
                            rows.append({
                                'Date': date,
                                'Open': open_p,
                                'High': high_p,
                                'Low': low_p,
                                'Close': close_p,
                                'Volume': volume
                            })
                    
                    return {'success': True, 'data': rows, 'count': len(rows)}
            
            return {'success': False, 'error': 'No data in response'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def save_csv(rows: list, filepath: str):
    """Save data to CSV"""
    if not rows:
        return False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('Date,Open,High,Low,Close,Volume\n')
        for row in rows:
            f.write(f"{row['Date']},{row['Open']},{row['High']},{row['Low']},{row['Close']},{row['Volume']}\n")
    
    return True


def main():
    print("=" * 60)
    print("Fetching HK Stock Data from Yahoo Finance")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for stock in STOCKS:
        print(f"\nFetching {stock['name']} ({stock['code']})...")
        result = fetch_yahoo_data(stock['code'])
        
        if result['success']:
            filepath = os.path.join(OUTPUT_DIR, stock['file'])
            if save_csv(result['data'], filepath):
                print(f"  ✅ Saved {result['count']} rows to {stock['file']}")
            else:
                print(f"  ❌ Failed to save CSV")
        else:
            print(f"  ❌ Fetch failed: {result['error']}")
    
    print("\n" + "=" * 60)
    print("Done!")


if __name__ == '__main__':
    main()
