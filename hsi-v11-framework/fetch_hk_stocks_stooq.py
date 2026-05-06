#!/usr/bin/env python3
"""
Fetch HK stock data from Stooq.com
Stocks: 03690.HK (Meituan), 00916.HK (Longyuan), 00020.HK (Sensetime), 02318.HK (Ping An), 00345.HK (Vitasoy)
"""

import urllib.request
import ssl
import os
from datetime import datetime

# Stock codes for Stooq (format: CODE.HK)
STOCKS = [
    {'code': '3690.HK', 'name': 'Meituan', 'file': '3690_HK.csv'},
    {'code': '916.HK', 'name': 'Longyuan_Power', 'file': '916_HK.csv'},
    {'code': '20.HK', 'name': 'Sensetime', 'file': '20_HK.csv'},
    {'code': '2318.HK', 'name': 'Ping_An_Insurance', 'file': '2318_HK.csv'},
    {'code': '345.HK', 'name': 'Vitasoy', 'file': '345_HK.csv'},
]

OUTPUT_DIR = '/root/.openclaw/workspace/caisen_data'

def fetch_stooq_data(symbol: str) -> dict:
    """Fetch historical data from Stooq.com"""
    # Stooq URL format: https://stooq.com/q/d/l/?s=SYMBOL&d1=YYYYMMDD&d2=YYYYMMDD
    url = f"https://stooq.com/q/d/l/?s={symbol}&d1=20240101&d2=20260306"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            content = response.read().decode('utf-8')
            lines = content.strip().split('\n')
            
            if len(lines) < 2:
                return {'success': False, 'error': 'No data returned'}
            
            # Parse CSV (Date,Open,High,Low,Close,Volume)
            rows = []
            for line in lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) >= 6:
                    try:
                        rows.append({
                            'Date': parts[0],
                            'Open': float(parts[1]) if parts[1] else 0,
                            'High': float(parts[2]) if parts[2] else 0,
                            'Low': float(parts[3]) if parts[3] else 0,
                            'Close': float(parts[4]) if parts[4] else 0,
                            'Volume': float(parts[5]) if parts[5] else 0
                        })
                    except:
                        continue
            
            if rows:
                return {'success': True, 'data': rows, 'count': len(rows)}
            else:
                return {'success': False, 'error': 'No valid data parsed'}
            
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
    print("Fetching HK Stock Data from Stooq.com")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for stock in STOCKS:
        print(f"\nFetching {stock['name']} ({stock['code']})...")
        result = fetch_stooq_data(stock['code'])
        
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
