#!/usr/bin/env python3
"""
HSI v11 - Real-Time Price Fetcher
Fetches current prices for all HSI constituents and updates the watchlist
Sources: Yahoo Finance, Stooq, or other free APIs
"""

import csv
import requests
import json
from datetime import datetime, timedelta
import time

# HSI Constituents with Yahoo Finance symbols
HSI_STOCKS = [
    {'code': '0700.HK', 'name': 'Tencent', 'sector': 'Technology', 'yahoo': '0700.HK'},
    {'code': '9988.HK', 'name': 'Alibaba', 'sector': 'Technology', 'yahoo': '9988.HK'},
    {'code': '1810.HK', 'name': 'Xiaomi', 'sector': 'Technology', 'yahoo': '1810.HK'},
    {'code': '0981.HK', 'name': 'SMIC', 'sector': 'Technology', 'yahoo': '0981.HK'},
    {'code': '0005.HK', 'name': 'HSBC', 'sector': 'Financials', 'yahoo': '0005.HK'},
    {'code': '1299.HK', 'name': 'AIA', 'sector': 'Financials', 'yahoo': '1299.HK'},
    {'code': '3988.HK', 'name': 'Bank of China', 'sector': 'Financials', 'yahoo': '3988.HK'},
    {'code': '0939.HK', 'name': 'CCB', 'sector': 'Financials', 'yahoo': '0939.HK'},
    {'code': '0016.HK', 'name': 'Sun Hung Kai', 'sector': 'Properties', 'yahoo': '0016.HK'},
    {'code': '1113.HK', 'name': 'CK Asset', 'sector': 'Properties', 'yahoo': '1113.HK'},
    {'code': '1109.HK', 'name': 'CR Land', 'sector': 'Properties', 'yahoo': '1109.HK'},
    {'code': '0002.HK', 'name': 'CLP', 'sector': 'Utilities', 'yahoo': '0002.HK'},
    {'code': '2638.HK', 'name': 'HK Electric', 'sector': 'Utilities', 'yahoo': '2638.HK'},
    {'code': '0003.HK', 'name': 'Town Gas', 'sector': 'Utilities', 'yahoo': '0003.HK'},
    {'code': '2319.HK', 'name': 'Mengniu', 'sector': 'Consumer', 'yahoo': '2319.HK'},
    {'code': '9633.HK', 'name': 'Nongfu Spring', 'sector': 'Consumer', 'yahoo': '9633.HK'},
    {'code': '0291.HK', 'name': 'CR Beer', 'sector': 'Consumer', 'yahoo': '0291.HK'},
    {'code': '1766.HK', 'name': 'CRRC', 'sector': 'Industrials', 'yahoo': '1766.HK'},
    {'code': '2208.HK', 'name': 'Goldwind', 'sector': 'Industrials', 'yahoo': '2208.HK'},
    {'code': '0066.HK', 'name': 'MTR', 'sector': 'Industrials', 'yahoo': '0066.HK'},
    {'code': '0883.HK', 'name': 'CNOOC', 'sector': 'Energy', 'yahoo': '0883.HK'},
]

def fetch_yahoo_price(symbol):
    """Fetch current price from Yahoo Finance API"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return result['meta']['regularMarketPrice']
        return None
    except Exception as e:
        print(f"  ⚠️ Error fetching {symbol}: {e}")
        return None

def fetch_stooq_price(symbol):
    """Fallback: Fetch from Stooq"""
    try:
        # Convert HK symbol for Stooq
        stooq_symbol = symbol.replace('.HK', '')
        url = f"https://stooq.com/q/l/?s={stooq_symbol}&f=sd2t2ohlcv&h&e=csv"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split(',')
                if len(parts) >= 5 and parts[4] != '0':
                    return float(parts[4])  # Close price
        return None
    except Exception as e:
        print(f"  ⚠️ Stooq error for {symbol}: {e}")
        return None

def calculate_buy_zone(current_price, sector):
    """Calculate buy zone based on current price and sector volatility"""
    if not current_price:
        return "TBD", "TBD"
    
    # Sector-specific volatility adjustments
    volatility = {
        'Technology': 0.15,
        'Financials': 0.10,
        'Properties': 0.12,
        'Utilities': 0.08,
        'Consumer': 0.12,
        'Industrials': 0.12,
        'Energy': 0.15
    }
    
    vol = volatility.get(sector, 0.12)
    buy_low = current_price * (1 - vol)
    buy_high = current_price * (1 - vol * 0.5)
    
    return f"{buy_low:.2f}", f"{buy_high:.2f}"

def calculate_stop_loss(current_price, sector):
    """Calculate stop loss based on sector"""
    if not current_price:
        return "TBD"
    
    stop_loss_pct = {
        'Technology': 0.15,
        'Financials': 0.10,
        'Properties': 0.12,
        'Utilities': 0.08,
        'Consumer': 0.12,
        'Industrials': 0.12,
        'Energy': 0.15
    }
    
    pct = stop_loss_pct.get(sector, 0.12)
    stop = current_price * (1 - pct)
    return f"{stop:.2f}"

def calculate_2030_target(current_price, sector):
    """Calculate 2030 target based on sector growth potential"""
    if not current_price:
        return "TBD"
    
    # Based on HSI target of 25,000 from ~19,000 = ~32% growth by 2030
    # Sector-specific multipliers
    growth = {
        'Technology': 0.50,  # 50% growth potential
        'Financials': 0.30,  # 30% growth
        'Properties': 0.35,  # 35% growth
        'Utilities': 0.20,   # 20% growth (defensive)
        'Consumer': 0.35,    # 35% growth
        'Industrials': 0.40, # 40% growth
        'Energy': 0.25       # 25% growth
    }
    
    g = growth.get(sector, 0.30)
    target = current_price * (1 + g)
    return f"{target:.2f}"

def update_watchlist():
    """Main function to update watchlist with current prices"""
    print("🔄 Fetching real-time prices for HSI constituents...")
    print(f"   Total stocks: {len(HSI_STOCKS)}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    updated_stocks = []
    
    for i, stock in enumerate(HSI_STOCKS, 1):
        print(f"[{i}/{len(HSI_STOCKS)}] Fetching {stock['code']} ({stock['name']})...", end=" ")
        
        # Try Yahoo first, then Stooq
        price = fetch_yahoo_price(stock['yahoo'])
        if not price:
            price = fetch_stooq_price(stock['yahoo'])
        
        if price:
            print(f"✅ HKD {price:.2f}")
            
            # Calculate derived values
            buy_low, buy_high = calculate_buy_zone(price, stock['sector'])
            stop_loss = calculate_stop_loss(price, stock['sector'])
            target_2030 = calculate_2030_target(price, stock['sector'])
            
            # Determine rating based on sector allocation
            sector_weights = {
                'Technology': '🚀 Strong Buy',
                'Financials': '✅ Hold',
                'Properties': '🚀 Buy',
                'Utilities': '⚠️ Hold',
                'Consumer': '✅ Hold',
                'Industrials': '🚀 Buy',
                'Energy': '⚠️ Hold'
            }
            
            updated_stocks.append({
                'code': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'target_weight': stock.get('target_weight', 'TBD'),
                'current_price': f"{price:.2f}",
                'buy_low': buy_low,
                'buy_high': buy_high,
                'stop_loss': stop_loss,
                'target_2030': target_2030,
                'rating': sector_weights.get(stock['sector'], '✅ Hold'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
        else:
            print("❌ Failed")
            updated_stocks.append({
                'code': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'target_weight': 'TBD',
                'current_price': 'N/A',
                'buy_low': 'TBD',
                'buy_high': 'TBD',
                'stop_loss': 'TBD',
                'target_2030': 'TBD',
                'rating': '⏳ Pending',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
        
        # Rate limiting - be nice to APIs
        time.sleep(0.5)
    
    # Write updated watchlist
    output_file = 'hsi_v11_constituents_watchlist_updated.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Stock Code', 'Name', 'Sector', 'Target Weight', 'Current Price', 
                     'Buy Zone Low', 'Buy Zone High', 'Stop Loss', '2030 Target', 
                     'Rating', 'Last Updated']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for stock in updated_stocks:
            writer.writerow({
                'Stock Code': stock['code'],
                'Name': stock['name'],
                'Sector': stock['sector'],
                'Target Weight': stock['target_weight'],
                'Current Price': stock['current_price'],
                'Buy Zone Low': stock['buy_low'],
                'Buy Zone High': stock['buy_high'],
                'Stop Loss': stock['stop_loss'],
                '2030 Target': stock['target_2030'],
                'Rating': stock['rating'],
                'Last Updated': stock['last_updated']
            })
    
    print()
    print(f"✅ Updated watchlist saved: {output_file}")
    print(f"   Successfully fetched: {sum(1 for s in updated_stocks if s['current_price'] != 'N/A')}/{len(updated_stocks)}")
    
    # Generate summary statistics
    sectors = {}
    for stock in updated_stocks:
        if stock['current_price'] != 'N/A':
            sector = stock['sector']
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(float(stock['current_price']))
    
    print()
    print("📊 Sector Summary:")
    for sector, prices in sectors.items():
        avg = sum(prices) / len(prices)
        print(f"   {sector}: {len(prices)} stocks, Avg Price: HKD {avg:.2f}")
    
    return output_file

if __name__ == '__main__':
    update_watchlist()
