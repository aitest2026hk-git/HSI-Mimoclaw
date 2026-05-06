#!/usr/bin/env python3
"""
Fetch 2 years of historical OHLCV data for Tencent (0700.HK) from Yahoo Finance
Output: /root/.openclaw/workspace/caisen_data/0700_HK_2y.csv
"""

import csv
import urllib.request
import json
from datetime import datetime, timedelta
import time
import ssl

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def fetch_historical_yahoo(symbol, years=2):
    """
    Fetch historical daily OHLCV data from Yahoo Finance
    Returns list of dicts with Date, Open, High, Low, Close, Volume
    """
    try:
        # Yahoo Finance uses Unix timestamps
        # period1: start date, period2: end date
        # interval: 1d for daily
        
        now = datetime.now()
        start_date = now - timedelta(days=years*365)
        
        period1 = int(start_date.timestamp())
        period2 = int(now.timestamp())
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        url += f"?interval=1d&period1={period1}&period2={period2}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            data = json.loads(response.read().decode())
            
            if 'chart' not in data or 'result' not in data['chart']:
                print(f"❌ No data in response for {symbol}")
                return None
            
            result = data['chart']['result'][0]
            
            # Get timestamps and quote data
            timestamps = result.get('timestamp', [])
            quote = result.get('indicators', {}).get('quote', [{}])[0]
            
            if not timestamps:
                print(f"❌ No timestamps for {symbol}")
                return None
            
            # Extract OHLCV
            opens = quote.get('open', [])
            highs = quote.get('high', [])
            lows = quote.get('low', [])
            closes = quote.get('close', [])
            volumes = quote.get('volume', [])
            
            # Build data list
            historical_data = []
            for i, ts in enumerate(timestamps):
                # Skip if any data is missing
                if i >= len(opens) or i >= len(highs) or i >= len(lows) or i >= len(closes):
                    continue
                
                open_price = opens[i]
                high_price = highs[i]
                low_price = lows[i]
                close_price = closes[i]
                volume = volumes[i] if i < len(volumes) else 0
                
                # Skip if price data is None
                if any(v is None for v in [open_price, high_price, low_price, close_price]):
                    continue
                
                # Convert timestamp to date string
                date_str = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                
                historical_data.append({
                    'Date': date_str,
                    'Open': round(open_price, 2),
                    'High': round(high_price, 2),
                    'Low': round(low_price, 2),
                    'Close': round(close_price, 2),
                    'Volume': int(volume) if volume else 0
                })
            
            return historical_data
            
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

def main():
    symbol = '0700.HK'
    output_file = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    
    print(f"📈 Fetching 2 years of historical data for {symbol}...")
    print(f"   Source: Yahoo Finance")
    print(f"   Output: {output_file}")
    print()
    
    # Fetch data (explicitly request 2 years)
    data = fetch_historical_yahoo(symbol, years=2)
    
    if not data:
        print("❌ Failed to fetch data")
        return
    
    print(f"✅ Fetched {len(data)} trading days")
    
    # Sort by date (oldest first)
    data.sort(key=lambda x: x['Date'])
    
    # Save to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"✅ Saved to {output_file}")
    print()
    
    # Print summary
    if data:
        first_date = data[0]['Date']
        last_date = data[-1]['Date']
        first_close = data[0]['Close']
        last_close = data[-1]['Close']
        price_change = ((last_close - first_close) / first_close) * 100
        
        print(f"📊 Data Summary:")
        print(f"   Date Range: {first_date} to {last_date}")
        print(f"   First Close: HKD {first_close:.2f}")
        print(f"   Last Close: HKD {last_close:.2f}")
        print(f"   Price Change: {price_change:+.1f}%")
        print(f"   Total Records: {len(data)}")

if __name__ == '__main__':
    main()
