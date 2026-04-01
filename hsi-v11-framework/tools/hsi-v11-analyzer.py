#!/usr/bin/env python3
"""
HSI v11 Analyzer - Consolidated Single-File Version
Hang Seng Index Analysis with Kondratiev, Gann, Solar Terms & Convergence
"""

import json
import urllib.request
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

# ============================================================================
# CONFIGURATION
# ============================================================================
DATA_DIR = "/root/.openclaw/workspace/tools/hsi-v11-analyzer/data"
OUTPUT_FILE = "/root/.openclaw/workspace/tools/hsi-v11-analyzer/report.txt"

# Yahoo Finance HSI ticker
HSI_TICKER = "^HSI"
YAHOO_URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{HSI_TICKER}"

# ============================================================================
# DATA FETCHER
# ============================================================================
def fetch_hsi_data(days: int = 365) -> List[Dict]:
    """Fetch HSI historical data from Yahoo Finance"""
    print(f"📡 Fetching {days} days of HSI data...")
    
    end = datetime.now()
    start = end - timedelta(days=days)
    
    url = f"{YAHOO_URL}?period1={int(start.timestamp())}&period2={int(end.timestamp())}&interval=1d"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode())
        
        quotes = data['chart']['result'][0]['quotes']
        parsed = []
        for q in quotes:
            if q.get('close') and q.get('volume') > 0:
                parsed.append({
                    'date': datetime.fromtimestamp(q['datetime']),
                    'open': q['open'],
                    'high': q['high'],
                    'low': q['low'],
                    'close': q['close'],
                    'volume': q['volume']
                })
        print(f"✅ Retrieved {len(parsed)} data points")
        return parsed
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

# ============================================================================
# KONDRIATIEV WAVES (Long-term Economic Cycles ~54 years)
# ============================================================================
class KondratievAnalyzer:
    """Kondratiev Wave Analysis for long-term market cycles"""
    
    PHASES = ["Spring (Expansion)", "Summer (Stagnation)", "Autumn (Recession)", "Winter (Depression)"]
    
    # Approximate K-wave timeline (based on historical analysis)
    WAVES = [
        {"start": 1790, "end": 1844, "phase": 0},
        {"start": 1844, "end": 1898, "phase": 1},
        {"start": 1898, "end": 1952, "phase": 2},
        {"start": 1952, "end": 2006, "phase": 3},
        {"start": 2006, "end": 2060, "phase": 0},  # Current wave
    ]
    
    def analyze(self, data: List[Dict]) -> Dict:
        """Analyze current K-wave position"""
        current_year = datetime.now().year
        
        for wave in self.WAVES:
            if wave["start"] <= current_year <= wave["end"]:
                phase_idx = wave["phase"]
                progress = (current_year - wave["start"]) / (wave["end"] - wave["start"]) * 100
                
                return {
                    "current_wave_start": wave["start"],
                    "current_wave_end": wave["end"],
                    "phase": self.PHASES[phase_idx],
                    "phase_index": phase_idx,
                    "progress_percent": round(progress, 1),
                    "years_remaining": wave["end"] - current_year,
                    "outlook": "Bullish" if phase_idx in [0, 1] else "Bearish"
                }
        return {"error": "Unable to determine K-wave position"}

# ============================================================================
# GANN THEORY (Price-Time Geometry)
# ============================================================================
class GannAnalyzer:
    """Gann Theory Analysis - Price-Time Squaring"""
    
    GANN_ANGLES = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 2.0, 4.0, 8.0]
    
    def __init__(self, data: List[Dict]):
        self.data = data
        if data:
            self.high = max(d['high'] for d in data)
            self.low = min(d['low'] for d in data)
            self.current = data[-1]['close']
    
    def calculate_support_resistance(self) -> Dict:
        """Calculate Gann support/resistance levels"""
        price_range = self.high - self.low
        
        levels = {
            "resistance": [],
            "support": [],
            "current_price": self.current
        }
        
        for angle in self.GANN_ANGLES:
            resistance = self.low + (price_range * angle)
            support = self.high - (price_range * angle)
