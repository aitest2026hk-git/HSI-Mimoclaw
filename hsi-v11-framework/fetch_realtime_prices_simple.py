#!/usr/bin/env python3
"""
HSI v11 - Real-Time Price Fetcher (urllib version - no external dependencies)
Fetches current prices for HSI constituents and updates the watchlist
"""

import csv
import urllib.request
import json
from datetime import datetime
import time
import ssl

# Create SSL context that doesn't verify certificates (for simplicity)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

HSI_STOCKS = [
    {'code': '0700.HK', 'name': 'Tencent', 'sector': 'Technology'},
    {'code': '9988.HK', 'name': 'Alibaba', 'sector': 'Technology'},
    {'code': '1810.HK', 'name': 'Xiaomi', 'sector': 'Technology'},
    {'code': '0981.HK', 'name': 'SMIC', 'sector': 'Technology'},
    {'code': '0005.HK', 'name': 'HSBC', 'sector': 'Financials'},
    {'code': '1299.HK', 'name': 'AIA', 'sector': 'Financials'},
    {'code': '3988.HK', 'name': 'Bank of China', 'sector': 'Financials'},
    {'code': '0939.HK', 'name': 'CCB', 'sector': 'Financials'},
    {'code': '0016.HK', 'name': 'Sun Hung Kai', 'sector': 'Properties'},
    {'code': '1113.HK', 'name': 'CK Asset', 'sector': 'Properties'},
    {'code': '1109.HK', 'name': 'CR Land', 'sector': 'Properties'},
    {'code': '0002.HK', 'name': 'CLP', 'sector': 'Utilities'},
    {'code': '2638.HK', 'name': 'HK Electric', 'sector': 'Utilities'},
    {'code': '0003.HK', 'name': 'Town Gas', 'sector': 'Utilities'},
    {'code': '2319.HK', 'name': 'Mengniu', 'sector': 'Consumer'},
    {'code': '9633.HK', 'name': 'Nongfu Spring', 'sector': 'Consumer'},
    {'code': '0291.HK', 'name': 'CR Beer', 'sector': 'Consumer'},
    {'code': '1766.HK', 'name': 'CRRC', 'sector': 'Industrials'},
    {'code': '2208.HK', 'name': 'Goldwind', 'sector': 'Industrials'},
    {'code': '0066.HK', 'name': 'MTR', 'sector': 'Industrials'},
    {'code': '0883.HK', 'name': 'CNOOC', 'sector': 'Energy'},
]

def fetch_price_yahoo(symbol):
    """Fetch price from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode())
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return result['meta']['regularMarketPrice']
    except Exception as e:
        pass
    return None

def fetch_price_stooq(symbol):
    """Fetch price from Stooq (fallback)"""
    try:
        stooq_sym = symbol.replace('.HK', '')
        url = f"https://stooq.com/q/l/?s={stooq_sym}&f=sd2t2ohlcv&h&e=csv"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            lines = response.read().decode().strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split(',')
                if len(parts) >= 5 and parts[4] != '0':
                    return float(parts[4])
    except:
        pass
    return None

def calc_values(price, sector):
    """Calculate buy zone, stop loss, target"""
    vol = {'Technology': 0.15, 'Financials': 0.10, 'Properties': 0.12, 
           'Utilities': 0.08, 'Consumer': 0.12, 'Industrials': 0.12, 'Energy': 0.15}.get(sector, 0.12)
    
    growth = {'Technology': 0.50, 'Financials': 0.30, 'Properties': 0.35,
              'Utilities': 0.20, 'Consumer': 0.35, 'Industrials': 0.40, 'Energy': 0.25}.get(sector, 0.30)
    
    stop_pct = vol
    
    buy_low = price * (1 - vol)
    buy_high = price * (1 - vol * 0.5)
    stop = price * (1 - stop_pct)
    target = price * (1 + growth)
    
    return f"{buy_low:.2f}", f"{buy_high:.2f}", f"{stop:.2f}", f"{target:.2f}"

def get_rating(sector):
    ratings = {'Technology': '🚀 Strong Buy', 'Financials': '✅ Hold', 'Properties': '🚀 Buy',
               'Utilities': '⚠️ Hold', 'Consumer': '✅ Hold', 'Industrials': '🚀 Buy', 'Energy': '⚠️ Hold'}
    return ratings.get(sector, '✅ Hold')

def main():
    print("🔄 Fetching prices for HSI constituents...")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    results = []
    success = 0
    
    for i, stock in enumerate(HSI_STOCKS, 1):
        print(f"[{i}/{len(HSI_STOCKS)}] {stock['code']}...", end=" ")
        
        price = fetch_price_yahoo(stock['code'])
        if not price:
            price = fetch_price_stooq(stock['code'])
        
        if price:
            print(f"✅ HKD {price:.2f}")
            success += 1
            buy_l, buy_h, stop, target = calc_values(price, stock['sector'])
            
            results.append({
                'Stock Code': stock['code'], 'Name': stock['name'], 'Sector': stock['sector'],
                'Target Weight': 'TBD', 'Current Price': f"{price:.2f}",
                'Buy Zone Low': buy_l, 'Buy Zone High': buy_h, 'Stop Loss': stop,
                '2030 Target': target, 'Rating': get_rating(stock['sector']),
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
        else:
            print("❌ N/A")
            results.append({
                'Stock Code': stock['code'], 'Name': stock['name'], 'Sector': stock['sector'],
                'Target Weight': 'TBD', 'Current Price': 'N/A',
                'Buy Zone Low': 'TBD', 'Buy Zone High': 'TBD', 'Stop Loss': 'TBD',
                '2030 Target': 'TBD', 'Rating': '⏳ Pending',
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
        
        time.sleep(0.3)  # Rate limiting
    
    # Save to CSV
    output = 'hsi_v11_constituents_watchlist_updated.csv'
    with open(output, 'w', newline='', encoding='utf-8') as f:
        fields = ['Stock Code', 'Name', 'Sector', 'Target Weight', 'Current Price',
                  'Buy Zone Low', 'Buy Zone High', 'Stop Loss', '2030 Target', 'Rating', 'Last Updated']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    
    print()
    print(f"✅ Saved: {output}")
    print(f"   Success: {success}/{len(HSI_STOCKS)} stocks")
    
    # Sector summary
    sectors = {}
    for r in results:
        if r['Current Price'] != 'N/A':
            sec = r['Sector']
            if sec not in sectors:
                sectors[sec] = []
            sectors[sec].append(float(r['Current Price']))
    
    if sectors:
        print()
        print("📊 Sector Summary:")
        for sec, prices in sectors.items():
            print(f"   {sec}: {len(prices)} stocks, Avg: HKD {sum(prices)/len(prices):.2f}")

if __name__ == '__main__':
    main()
