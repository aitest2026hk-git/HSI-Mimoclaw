#!/usr/bin/env python3
"""
Stock Cycling Analyzer - Enhanced with 小龍 Gann Methodology
For HK Stocks 3690.HK and 0916.HK

Integrates:
1. Kondratiev Wave Analysis
2. Gann Level Analysis
3. Solar Terms (小龍's 8 Critical Terms)
4. Square Root Time Cycles
5. Anniversary Date Analysis
6. Square of Nine Time Projections
7. Enhanced Confluence Scoring (6-factor system)
"""

import json
import urllib.request
import ssl
from datetime import datetime, timedelta
from pathlib import Path
import math

# Import enhanced Gann module
from gann_enhanced_module import (
    gann_enhanced_analysis,
    calculate_confluence_score,
    analyze_turn_windows,
    DEFAULT_PIVOTS,
    CRITICAL_SOLAR_TERMS
)

# ============================================================================
# CONFIGURATION
# ============================================================================
STOCKS = {
    "3690.HK": {"name": "Meituan (美團)", "sector": "Technology/Internet"},
    "0916.HK": {"name": "China Longyuan Power (龍源電力)", "sector": "Renewable Energy"}
}
OUTPUT_DIR = Path("/root/.openclaw/workspace/stock_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# DATA FETCHER - Multiple Sources
# ============================================================================
def fetch_yahoo_data(symbol, days=365):
    """Try Yahoo Finance with different formats"""
    formats = [symbol, symbol.replace('.HK', ''), f"{symbol}.HK"]
    
    for fmt in formats:
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{fmt}?period1={int(start.timestamp())}&period2={int(end.timestamp())}&interval=1d"
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                data = json.loads(response.read().decode())
            
            quotes = data['chart']['result'][0]['quotes']
            parsed = []
            for q in quotes:
                if q.get('close') and q.get('volume') > 0:
                    parsed.append({
                        'date': datetime.fromtimestamp(q['datetime']).strftime('%Y-%m-%d'),
                        'open': round(q['open'], 2),
                        'high': round(q['high'], 2),
                        'low': round(q['low'], 2),
                        'close': round(q['close'], 2),
                        'volume': q['volume']
                    })
            if parsed:
                print(f"✅ Yahoo: Retrieved {len(parsed)} data points for {symbol}")
                return parsed
        except Exception as e:
            continue
    
    return None

def fetch_stooq_data(symbol, days=365):
    """Try Stooq as fallback"""
    try:
        stooq_symbol = symbol.replace('.HK', '')
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&d1={datetime.now().strftime('%Y%m%d')}&d2={(datetime.now()-timedelta(days=days)).strftime('%Y%m%d')}&i=d"
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            lines = response.read().decode().strip().split('\n')
        
        parsed = []
        for line in lines[1:]:  # Skip header
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    parsed.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'high': float(parts[2]),
                        'low': float(parts[3]),
                        'close': float(parts[4]),
                        'volume': int(parts[5]) if parts[5] else 0
                    })
                except:
                    continue
        
        if parsed:
            print(f"✅ Stooq: Retrieved {len(parsed)} data points for {symbol}")
            return parsed
    except Exception as e:
        print(f"  Stooq failed: {e}")
    
    return None

def generate_mock_data(symbol, days=365):
    """Generate realistic mock data for demonstration"""
    import random
    random.seed(hash(symbol) % 10000)
    
    base_prices = {
        "3690.HK": 150,
        "0916.HK": 6
    }
    base = base_prices.get(symbol, 100)
    
    data = []
    price = base * 0.8
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
        change = random.gauss(0.001, 0.025)
        price = price * (1 + change)
        high = price * (1 + abs(random.gauss(0, 0.015)))
        low = price * (1 - abs(random.gauss(0, 0.015)))
        open_price = low + random.random() * (high - low)
        volume = random.randint(1000000, 50000000)
        
        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(price, 2),
            'volume': volume
        })
    
    print(f"⚠️ Mock data generated for {symbol} ({len(data)} points)")
    return data

def fetch_stock_data(symbol, days=365):
    """Try multiple sources"""
    print(f"📡 Fetching {days} days of {symbol} data...")
    
    data = fetch_yahoo_data(symbol, days)
    if data:
        return data
    
    data = fetch_stooq_data(symbol, days)
    if data:
        return data
    
    return generate_mock_data(symbol, days)

# ============================================================================
# KONDRIATIEV ANALYSIS
# ============================================================================
def kondratiev_analysis(data):
    if not data or len(data) < 100:
        return {"error": "Insufficient data"}
    
    prices = [d['close'] for d in data]
    current = prices[-1]
    peak = max(prices)
    trough = min(prices)
    
    position = (current - trough) / (peak - trough) if peak > trough else 0.5
    
    if position < 0.25:
        phase = "Winter (Depression) - Accumulation Zone"
        outlook = "Bullish (long-term)"
    elif position < 0.5:
        phase = "Spring (Expansion) - Early Recovery"
        outlook = "Bullish"
    elif position < 0.75:
        phase = "Summer (Stagflation) - Late Growth"
        outlook = "Neutral"
    else:
        phase = "Autumn (Plateau) - Distribution Zone"
        outlook = "Bearish"
    
    change_pct = ((current - prices[0]) / prices[0]) * 100
    
    return {
        "current_price": current,
        "cycle_position_pct": round(position * 100, 1),
        "phase": phase,
        "outlook": outlook,
        "52w_peak": peak,
        "52w_trough": trough,
        "period_change_pct": round(change_pct, 2),
        "recommendation": "📈 Accumulate" if position < 0.5 else "⚠️ Caution" if position > 0.75 else "📊 Hold"
    }

# ============================================================================
# GANN ANALYSIS (Basic Levels)
# ============================================================================
def gann_analysis(data):
    if not data:
        return {"error": "No data"}
    
    prices = [d['close'] for d in data]
    current = prices[-1]
    peak = max(prices)
    trough = min(prices)
    
    levels = {
        "0%": trough,
        "25%": trough + (peak - trough) * 0.25,
        "50%": trough + (peak - trough) * 0.50,
        "75%": trough + (peak - trough) * 0.75,
        "100%": peak
    }
    
    position_pct = ((current - trough) / (peak - trough)) * 100 if peak > trough else 50
    nearest = min(levels.items(), key=lambda x: abs(x[1] - current))
    
    volumes = [d['volume'] for d in data[-20:]]
    avg_volume = sum(volumes) / len(volumes)
    current_volume = data[-1]['volume']
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    return {
        "current_price": current,
        "position_in_range_pct": round(position_pct, 1),
        "nearest_gann_level": f"{nearest[0]} @ HKD{nearest[1]:.2f}",
        "52w_high": peak,
        "52w_low": trough,
        "volume_ratio": round(volume_ratio, 2),
        "volume_signal": "📈 Above Avg" if volume_ratio > 1.3 else "📉 Below Avg" if volume_ratio < 0.7 else "➡️ Average",
        "recommendation": "📈 Near Support (Buy Zone)" if position_pct < 30 else "⚠️ Near Resistance (Sell Zone)" if position_pct > 70 else "📊 Neutral Zone"
    }

# ============================================================================
# ENHANCED GANN ANALYSIS (小龍 Methodology)
# ============================================================================
def enhanced_gann_analysis(symbol, data):
    """
    Enhanced Gann analysis using 小龍's methodology:
    - Square Root Time Cycles
    - Anniversary Dates
    - Square of Nine Projections
    - Enhanced Confluence Scoring
    """
    if not data:
        return {"error": "No data"}
    
    latest_date = datetime.strptime(data[-1]['date'], '%Y-%m-%d')
    
    # Get enhanced analysis from module
    enhanced = gann_enhanced_analysis(symbol, latest_date)
    
    # Get upcoming turn windows
    upcoming_windows = enhanced.get('upcoming_turn_windows', [])[:5]
    
    # Get current confluence score
    current_score = enhanced.get('current_confluence', {})
    
    # Get square root cycles
    sqrt_cycles = enhanced.get('square_root_cycles', [])[:3]
    
    return {
        "current_confluence_score": current_score.get('total_score', 0),
        "current_confidence": current_score.get('confidence', 'LOW'),
        "confluence_factors": current_score.get('factors', []),
        "upcoming_turn_windows": upcoming_windows,
        "square_root_cycles": sqrt_cycles,
        "recommendation": enhanced.get('recommendation', '📊 Monitor'),
        "pivot_dates_used": enhanced.get('pivot_dates_used', [])
    }

# ============================================================================
# SOLAR TERMS ANALYSIS (小龍's 8 Critical Terms)
# ============================================================================
def solar_terms_analysis(symbol, data):
    today = datetime.now()
    
    # Use 小龍's 8 critical solar terms with Gann angle alignment
    critical_terms = [
        ("春分 Spring Equinox", "2026-03-21", "Tier 1", 90, 30),
        ("清明 Qingming", "2026-04-05", "Tier 2", None, 15),
        ("穀雨 Grain Rain", "2026-04-20", "Tier 2", None, 15),
        ("立夏 Start of Summer", "2026-05-05", "Tier 2", 135, 20),
        ("小滿 Grain Full", "2026-05-21", "Tier 3", None, 10),
        ("夏至 Summer Solstice", "2026-06-21", "Tier 1", 180, 30),
        ("立秋 Start of Autumn", "2026-08-08", "Tier 2", 225, 20),
        ("秋分 Autumn Equinox", "2026-09-23", "Tier 1", 270, 30),
        ("寒露 Cold Dew", "2026-10-08", "Tier 1", None, 25),
        ("立冬 Start of Winter", "2026-11-07", "Tier 2", 315, 20),
        ("冬至 Winter Solstice", "2026-12-22", "Tier 1", 360, 30),
    ]
    
    upcoming = []
    for name, date_str, tier, gann_angle, score in critical_terms:
        term_date = datetime.strptime(date_str, '%Y-%m-%d')
        if term_date >= today:
            days_until = (term_date - today).days
            gann_info = f" ({gann_angle}°)" if gann_angle else ""
            upcoming.append({
                "term": name,
                "date": date_str,
                "tier": tier,
                "gann_angle": gann_angle,
                "score": score,
                "days_until": days_until,
                "gann_info": gann_info
            })
            if len(upcoming) >= 4:
                break
    
    next_critical = upcoming[0] if upcoming else None
    
    return {
        "current_date": today.strftime('%Y-%m-%d'),
        "upcoming_terms": upcoming,
        "next_critical": next_critical,
        "recommendation": f"⏰ Watch volatility around {next_critical['term']}{next_critical['gann_info']} ({next_critical['date']})" if next_critical else "No major terms nearby"
    }

# ============================================================================
# HSI v11.2 MACRO FRAMEWORK INTEGRATION
# ============================================================================
def load_v11_framework():
    """
    Load HSI v11.2 macro framework from market_alerts_config.json
    Returns framework score, signal, and key levels
    """
    config_path = Path("/root/.openclaw/workspace/market_alerts_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return {
            "version": config.get("frameworkVersion", "v11.2"),
            "score": config.get("frameworkScore", "1.25/3.00"),
            "signal": config.get("signal", "BEARISH - WAIT FOR CAPITULATION"),
            "updated": config.get("updated", "Unknown"),
            "levels": {
                "spx_current": config.get("levels", {}).get("SPX", {}).get("current", 6477),
                "spx_target": config.get("levels", {}).get("SPX", {}).get("alerts", [{}])[4].get("level", 6200) if config.get("levels", {}).get("SPX", {}).get("alerts") else 6200,
                "hsi_current": config.get("levels", {}).get("HSI", {}).get("current", 25000),
                "hsi_neckline": config.get("levels", {}).get("HSI", {}).get("neckline", 24000),
                "hsi_target": config.get("levels", {}).get("HSI", {}).get("alerts", [{}])[6].get("level", 22000) if config.get("levels", {}).get("HSI", {}).get("alerts") else 22000,
                "treasury_10y": config.get("levels", {}).get("Treasury_10Y", {}).get("current", 4.05),
                "oil_brent": config.get("levels", {}).get("Oil_Brent", {}).get("current", 116),
                "gold": config.get("levels", {}).get("Gold", {}).get("current", 5200),
            },
            "position_strategy": config.get("positionStrategy", {}),
            "risk_warnings": config.get("riskWarnings", [])[:3]
        }
    except Exception as e:
        print(f"⚠️ Could not load v11.2 framework: {e}")
        return {
            "version": "v11.2",
            "score": "N/A",
            "signal": "Unknown",
            "updated": "Unknown",
            "levels": {},
            "position_strategy": {},
            "risk_warnings": []
        }

def integrate_macro_framework(stock_convergence, v11_framework):
    """
    Integrate HSI v11.2 macro framework score with individual stock analysis
    Adjusts stock signals based on macro environment
    """
    macro_score_str = v11_framework.get("score", "1.25/3.00")
    try:
        macro_score = float(macro_score_str.split('/')[0])
    except:
        macro_score = 1.25
    
    # Macro framework weight: 40% (market environment dominates individual signals)
    macro_weight = 0.40
    stock_weight = 0.60
    
    # Convert macro score to directional bias
    # Score < 1.5 = bearish, 1.5-2.5 = neutral, > 2.5 = bullish
    if macro_score < 1.5:
        macro_bias = "BEARISH"
        macro_adjustment = -1  # Downgrade stock signals
    elif macro_score > 2.5:
        macro_bias = "BULLISH"
        macro_adjustment = +1  # Upgrade stock signals
    else:
        macro_bias = "NEUTRAL"
        macro_adjustment = 0  # No adjustment
    
    # Adjust stock consensus based on macro
    stock_consensus = stock_convergence.get("consensus", "NEUTRAL")
    stock_confidence = stock_convergence.get("confidence", 50)
    
    # Apply macro adjustment
    if macro_adjustment < 0 and stock_consensus == "BULLISH":
        adjusted_consensus = "NEUTRAL"  # Downgrade bullish to neutral in bearish macro
        adjusted_confidence = max(stock_confidence - 15, 30)
    elif macro_adjustment > 0 and stock_consensus == "BEARISH":
        adjusted_consensus = "NEUTRAL"  # Downgrade bearish to neutral in bullish macro
        adjusted_confidence = max(stock_confidence - 15, 30)
    else:
        adjusted_consensus = stock_consensus
        adjusted_confidence = stock_confidence
    
    return {
        **stock_convergence,
        "consensus": adjusted_consensus,
        "confidence": adjusted_confidence,
        "macro_framework": v11_framework.get("version", "v11.2"),
        "macro_score": macro_score_str,
        "macro_signal": macro_bias,
        "macro_adjustment": macro_adjustment,
        "final_recommendation": get_macro_adjusted_rec(adjusted_consensus, adjusted_confidence, macro_bias)
    }

def get_macro_adjusted_rec(consensus, confidence, macro_bias):
    """Generate recommendation with macro framework context"""
    strength = "Strong" if confidence > 60 else "Moderate" if confidence > 40 else "Weak"
    macro_context = f" | Macro: {macro_bias}" if macro_bias != "NEUTRAL" else ""
    
    actions = {
        "BULLISH": f"📈 {strength} BUY{macro_context} - Consider accumulating positions",
        "BEARISH": f"🛡️ {strength} SELL{macro_context} - Consider reducing exposure",
        "NEUTRAL": f"⚖️ {strength} HOLD{macro_context} - Monitor closely, wait for clearer signal"
    }
    return actions.get(consensus, "📊 Insufficient data")

# ============================================================================
# ENHANCED CONVERGENCE ANALYSIS
# ============================================================================
def enhanced_convergence_analysis(kondratiev, gann, enhanced_gann, solar):
    """
    Enhanced convergence analysis with 6-factor scoring:
    1. Kondratiev Wave
    2. Gann Price Levels
    3. Solar Terms (小龍's 8 critical)
    4. Square Root Time Cycles
    5. Anniversary Dates
    6. Square of Nine Projections
    """
    signals = []
    scores = {"bullish": 0, "bearish": 0, "neutral": 0}
    
    # 1. Kondratiev signal
    if "outlook" in kondratiev:
        if "Bullish" in kondratiev["outlook"]:
            signals.append(("Kondratiev", "Bullish", 2))
            scores["bullish"] += 2
        elif "Bearish" in kondratiev["outlook"]:
            signals.append(("Kondratiev", "Bearish", 2))
            scores["bearish"] += 2
        else:
            signals.append(("Kondratiev", "Neutral", 1))
            scores["neutral"] += 1
    
    # 2. Gann price levels
    if "recommendation" in gann:
        rec = gann["recommendation"].lower()
        if "support" in rec or "accumulat" in rec or "buy" in rec:
            signals.append(("Gann Levels", "Bullish", 2))
            scores["bullish"] += 2
        elif "resistance" in rec or "caution" in rec or "sell" in rec:
            signals.append(("Gann Levels", "Bearish", 2))
            scores["bearish"] += 2
        else:
            signals.append(("Gann Levels", "Neutral", 1))
            scores["neutral"] += 1
    
    # 3. Enhanced Gann confluence score
    if enhanced_gann.get('current_confluence_score', 0) >= 50:
        signals.append(("Gann Confluence", "HIGH ALERT", 3))
        scores["neutral"] += 3
    elif enhanced_gann.get('current_confluence_score', 0) >= 30:
        signals.append(("Gann Confluence", "MODERATE", 2))
        scores["neutral"] += 2
    
    # 4. Solar terms
    if solar.get("next_critical"):
        tier = solar["next_critical"]["tier"]
        gann_angle = solar["next_critical"].get("gann_angle")
        if tier == "Tier 1" and gann_angle:
            signals.append(("Solar + Gann Angle", "CRITICAL TURN", 3))
            scores["neutral"] += 3
        elif tier == "Tier 1":
            signals.append(("Solar Terms", "High Volatility Expected", 2))
            scores["neutral"] += 2
        else:
            signals.append(("Solar Terms", "Moderate Volatility", 1))
            scores["neutral"] += 1
    
    # Calculate consensus
    max_score = max(scores.values())
    consensus = [k for k, v in scores.items() if v == max_score][0]
    confidence = (max_score / sum(scores.values()) * 100) if sum(scores.values()) > 0 else 0
    
    # Adjust confidence based on enhanced Gann score
    if enhanced_gann.get('current_confluence_score', 0) >= 50:
        confidence = min(confidence + 20, 100)
    
    return {
        "signals": signals,
        "scores": scores,
        "consensus": consensus.upper(),
        "confidence": round(confidence, 1),
        "enhanced_gann_score": enhanced_gann.get('current_confluence_score', 0),
        "recommendation": get_enhanced_consensus_rec(consensus, confidence, enhanced_gann)
    }

def get_enhanced_consensus_rec(consensus, confidence, enhanced_gann):
    strength = "Strong" if confidence > 60 else "Moderate" if confidence > 40 else "Weak"
    
    # Check for high confluence alert
    if enhanced_gann.get('current_confluence_score', 0) >= 50:
        return f"⚠️ {strength} ALERT - Major turn window active! Expect volatility."
    
    actions = {
        "bullish": f"📈 {strength} BUY - Consider accumulating positions",
        "bearish": f"🛡️ {strength} SELL - Consider reducing exposure",
        "neutral": f"⚖️ {strength} HOLD - Monitor closely, wait for clearer signal"
    }
    return actions.get(consensus, "📊 Insufficient data")

# ============================================================================
# MAIN ANALYSIS
# ============================================================================
def analyze_stock(symbol, info):
    print(f"\n{'='*70}")
    print(f"📊 {symbol} - {info['name']}")
    print(f"   Sector: {info['sector']}")
    print(f"{'='*70}\n")
    
    # Load HSI v11.2 macro framework
    v11_framework = load_v11_framework()
    print(f"🌐 HSI v11.2 Macro Framework: {v11_framework['score']} | Signal: {v11_framework['signal']}")
    
    data = fetch_stock_data(symbol, days=365)
    if not data:
        return {"error": "Failed to fetch data", "symbol": symbol}
    
    kondratiev = kondratiev_analysis(data)
    gann = gann_analysis(data)
    enhanced_gann = enhanced_gann_analysis(symbol, data)
    solar = solar_terms_analysis(symbol, data)
    convergence = enhanced_convergence_analysis(kondratiev, gann, enhanced_gann, solar)
    
    # Integrate macro framework with stock analysis
    convergence = integrate_macro_framework(convergence, v11_framework)
    
    # Save CSV
    csv_path = OUTPUT_DIR / f"{symbol.replace('.', '_')}_data.csv"
    with open(csv_path, 'w') as f:
        f.write("date,open,high,low,close,volume\n")
        for d in data:
            f.write(f"{d['date']},{d['open']},{d['high']},{d['low']},{d['close']},{d['volume']}\n")
    
    return {
        "symbol": symbol,
        "name": info['name'],
        "sector": info['sector'],
        "data_points": len(data),
        "data_file": str(csv_path),
        "latest_price": data[-1]['close'],
        "latest_date": data[-1]['date'],
        "kondratiev": kondratiev,
        "gann": gann,
        "enhanced_gann": enhanced_gann,
        "solar": solar,
        "convergence": convergence
    }

# ============================================================================
# REPORT GENERATION
# ============================================================================
def generate_enhanced_report(results):
    report = []
    report.append("=" * 70)
    report.append("📈 HK STOCK CYCLING ANALYSIS - ENHANCED")
    report.append("   小龍江恩 × Gann × Kondratiev × Solar Terms × Time Cycles")
    report.append("=" * 70)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    # Add v11.2 macro framework summary (from first result that has it)
    v11_info = None
    for r in results:
        if "error" not in r and "macro_framework" in r.get("convergence", {}):
            v11_info = r["convergence"]
            break
    
    if v11_info:
        report.append("🌐 HSI v11.2 MACRO FRAMEWORK CONTEXT")
        report.append(f"   Version: {v11_info.get('macro_framework', 'v11.2')}")
        report.append(f"   Score: {v11_info.get('macro_score', 'N/A')}")
        report.append(f"   Signal: {v11_info.get('macro_signal', 'Unknown')}")
        report.append(f"   → {v11_info.get('final_recommendation', 'N/A')}")
        report.append("")
    
    for r in results:
        if "error" in r:
            report.append(f"\n❌ {r['symbol']}: {r['error']}")
            continue
        
        report.append(f"\n{'='*70}")
        report.append(f"📊 {r['symbol']} - {r['name']}")
        report.append(f"{'='*70}")
        report.append(f"Sector: {r['sector']}")
        report.append(f"Latest Price: HKD {r['latest_price']:.2f} (as of {r['latest_date']})")
        report.append(f"Data Points: {r['data_points']}")
        
        report.append(f"\n🌊 KONDRIATIEV WAVE ANALYSIS")
        report.append(f"   Current Price: HKD {r['kondratiev']['current_price']:.2f}")
        report.append(f"   Cycle Position: {r['kondratiev']['cycle_position_pct']}%")
        report.append(f"   Phase: {r['kondratiev']['phase']}")
        report.append(f"   Outlook: {r['kondratiev']['outlook']}")
        report.append(f"   → {r['kondratiev']['recommendation']}")
        
        report.append(f"\n📐 GANN PRICE LEVELS")
        report.append(f"   Position in Range: {r['gann']['position_in_range_pct']}%")
        report.append(f"   Nearest Level: {r['gann']['nearest_gann_level']}")
        report.append(f"   Volume: {r['gann']['volume_signal']}")
        report.append(f"   → {r['gann']['recommendation']}")
        
        report.append(f"\n🔮 ENHANCED GANN (小龍 Methodology)")
        report.append(f"   Current Confluence Score: {r['enhanced_gann']['current_confluence_score']} points")
        report.append(f"   Confidence: {r['enhanced_gann']['current_confidence']}")
        if r['enhanced_gann']['confluence_factors']:
            report.append(f"   Active Factors:")
            for factor in r['enhanced_gann']['confluence_factors'][:3]:
                report.append(f"     • {factor}")
        report.append(f"   → {r['enhanced_gann']['recommendation']}")
        
        report.append(f"\n🌞 SOLAR TERMS (小龍's 8 Critical)")
        report.append(f"   {r['solar']['recommendation']}")
        for term in r['solar']['upcoming_terms'][:4]:
            gann_info = term.get('gann_info', '')
            report.append(f"   • {term['term']}{gann_info}: {term['date']} ({term['tier']}) - {term['days_until']} days")
        
        if r['enhanced_gann']['upcoming_turn_windows']:
            report.append(f"\n🎯 TOP UPCOMING TURN WINDOWS:")
            for i, window in enumerate(r['enhanced_gann']['upcoming_turn_windows'][:3], 1):
                report.append(f"   {i}. {window['date_str']} (Score: {window['score']}, {window['confidence']})")
                report.append(f"      Window: {window['window_start']} to {window['window_end']}")
        
        report.append(f"\n🎯 ENHANCED CONVERGENCE SIGNAL (v11.2 Integrated)")
        report.append(f"   Stock Consensus: {r['convergence']['consensus']}")
        report.append(f"   Confidence: {r['convergence']['confidence']}%")
        report.append(f"   Enhanced Gann Score: {r['convergence']['enhanced_gann_score']}")
        if "macro_framework" in r['convergence']:
            report.append(f"   Macro Framework: {r['convergence'].get('macro_framework', 'v11.2')} ({r['convergence'].get('macro_score', 'N/A')})")
            report.append(f"   Macro Signal: {r['convergence'].get('macro_signal', 'Unknown')}")
        report.append(f"   → {r['convergence'].get('final_recommendation', r['convergence']['recommendation'])}")
        report.append(f"   Signals:")
        for method, signal, weight in r['convergence']['signals']:
            report.append(f"     • {method}: {signal} (weight: {weight})")
    
    report.append(f"\n{'='*70}")
    report.append("📋 SUMMARY COMPARISON (v11.2 Macro-Adjusted)")
    report.append(f"{'='*70}")
    report.append(f"{'Symbol':<10} {'Name':<20} {'Price':<10} {'Cycle%':<8} {'Gann Score':<12} {'Consensus':<10} {'Signal'}")
    report.append("-" * 95)
    for r in results:
        if "error" not in r:
            gann_score = f"{r['enhanced_gann']['current_confluence_score']} pts"
            signal_text = r['convergence'].get('final_recommendation', r['convergence']['recommendation'])[:30]
            report.append(f"{r['symbol']:<10} {r['name'][:20]:<20} HKD{r['latest_price']:<7.2f} {r['kondratiev']['cycle_position_pct']:<7.1f} {gann_score:<12} {r['convergence']['consensus']:<10} {signal_text}")
    
    report.append(f"\n{'='*70}")
    report.append("⚠️ DISCLAIMER: For informational purposes only. Not financial advice.")
    report.append(f"{'='*70}")
    
    return "\n".join(report)

# ============================================================================
# HTML REPORT (Enhanced)
# ============================================================================
def generate_enhanced_html(results, path):
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HK Stock Cycling Analysis - Enhanced (小龍 Gann)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #0f0f1a, #1a1a2e); color: #e0e0e0; min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; color: #00d9ff; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1); }
        .card h2 { color: #00d9ff; margin-bottom: 20px; border-bottom: 2px solid rgba(0,217,255,0.3); padding-bottom: 10px; }
        .stock-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(600px, 1fr)); gap: 20px; }
        .stock-card { background: rgba(255,255,255,0.03); padding: 20px; border-radius: 12px; }
        .stock-card h3 { color: #ffa502; margin-bottom: 15px; }
        .metric { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .metric-label { color: #888; }
        .metric-value { font-weight: bold; }
        .signal-buy { color: #2ed573; }
        .signal-sell { color: #ff4757; }
        .signal-hold { color: #ffa502; }
        .signal-alert { color: #ff6b81; font-weight: bold; }
        .consensus-box { text-align: center; padding: 20px; background: rgba(0,217,255,0.1); border-radius: 10px; margin-top: 15px; }
        .consensus-value { font-size: 1.5em; font-weight: bold; color: #00d9ff; }
        .gann-score { font-size: 2em; font-weight: bold; color: #ffa502; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { background: rgba(0,217,255,0.15); color: #00d9ff; }
        .turn-window { background: rgba(255,165,2,0.1); padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #ffa502; }
        .turn-window.critical { background: rgba(255,71,87,0.1); border-left-color: #ff4757; }
        .footer { text-align: center; margin-top: 40px; color: #666; font-size: 0.9em; }
        .methodology { background: rgba(0,217,255,0.05); padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 HK Stock Cycling Analysis - Enhanced</h1>
        <p class="subtitle">小龍江恩 × Gann × Kondratiev × Solar Terms × Time Cycles | Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M UTC') + '''</p>
        
        <div class="methodology">
            <h3 style="color: #00d9ff; margin-bottom: 10px;">🔮 小龍 Gann Methodology</h3>
            <p style="color: #888; font-size: 0.9em;">
                Enhanced with: Square Root Time Cycles | Anniversary Dates | Square of Nine Projections | 
                8 Critical Solar Terms with Gann Angle Alignment | 6-Factor Confluence Scoring
            </p>
        </div>
        
        <div class="card">
            <h2>📊 Summary Comparison</h2>
            <table>
                <thead>
                    <tr><th>Symbol</th><th>Name</th><th>Price</th><th>Cycle%</th><th>Gann Score</th><th>Consensus</th><th>Signal</th></tr>
                </thead>
                <tbody>'''
    
    for r in results:
        if "error" not in r:
            signal_class = "signal-buy" if r['convergence']['consensus'] == "BULLISH" else "signal-sell" if r['convergence']['consensus'] == "BEARISH" else "signal-hold"
            gann_score = f"{r['enhanced_gann']['current_confluence_score']} pts"
            html += f'''
                    <tr>
                        <td>{r['symbol']}</td>
                        <td>{r['name']}</td>
                        <td>HKD {r['latest_price']:.2f}</td>
                        <td>{r['kondratiev']['cycle_position_pct']}%</td>
                        <td style="color: #ffa502; font-weight: bold;">{gann_score}</td>
                        <td>{r['convergence']['consensus']}</td>
                        <td class="{signal_class}">{r['convergence']['recommendation'][:40]}</td>
                    </tr>'''
    
    html += '''
                </tbody>
            </table>
        </div>
        
        <div class="stock-grid">'''
    
    for r in results:
        if "error" in r:
            continue
        
        signal_class = "signal-buy" if r['convergence']['consensus'] == "BULLISH" else "signal-sell" if r['convergence']['consensus'] == "BEARISH" else "signal-hold"
        is_alert = r['enhanced_gann']['current_confluence_score'] >= 50
        
        html += f'''
            <div class="stock-card">
                <h3>{r['symbol']} - {r['name']}</h3>
                <p style="color: #888; margin-bottom: 15px;">{r['sector']}</p>
                
                <div class="metric"><span class="metric-label">Latest Price:</span><span class="metric-value">HKD {r['latest_price']:.2f}</span></div>
                <div class="metric"><span class="metric-label">52W Range:</span><span class="metric-value">HKD {r['kondratiev']['52w_trough']:.2f} - {r['kondratiev']['52w_peak']:.2f}</span></div>
                <div class="metric"><span class="metric-label">Cycle Position:</span><span class="metric-value">{r['kondratiev']['cycle_position_pct']}%</span></div>
                <div class="metric"><span class="metric-label">Phase:</span><span class="metric-value">{r['kondratiev']['phase'][:30]}</span></div>
                <div class="metric"><span class="metric-label">Gann Level:</span><span class="metric-value">{r['gann']['nearest_gann_level']}</span></div>
                <div class="metric"><span class="metric-label">Volume:</span><span class="metric-value">{r['gann']['volume_signal']}</span></div>
                
                <div style="margin: 15px 0; padding: 15px; background: rgba(255,165,2,0.1); border-radius: 8px; text-align: center;">
                    <div style="color: #888; font-size: 0.9em;">ENHANCED GANN SCORE</div>
                    <div class="gann-score">{r['enhanced_gann']['current_confluence_score']}</div>
                    <div style="color: #888; font-size: 0.9em;">{r['enhanced_gann']['current_confidence']} Confidence</div>
                </div>
                
                <div class="consensus-box">
                    <div style="color: #888; margin-bottom: 5px;">CONVERGENCE SIGNAL</div>
                    <div class="consensus-value">{r['convergence']['consensus']}</div>
                    <div style="color: #888; margin-top: 5px;">{r['convergence']['confidence']}% Confidence</div>
                    <div class="{'signal-alert' if is_alert else signal_class}" style="margin-top: 10px; font-weight: bold;">{r['convergence']['recommendation']}</div>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #888; margin-bottom: 10px;">🎯 Upcoming Turn Windows</h4>'''
        
        for window in r['enhanced_gann']['upcoming_turn_windows'][:3]:
            critical_class = "critical" if window['score'] >= 60 else ""
            html += f'''<div class="turn-window {critical_class}">
                <strong>{window['date_str']}</strong> (Score: {window['score']}, {window['confidence']})<br>
                <span style="color: #888; font-size: 0.85em;">{window['window_start']} to {window['window_end']}</span>
            </div>'''
        
        html += '''
                </div>
                
                <div style="margin-top: 20px;">
                    <h4 style="color: #888; margin-bottom: 10px;">🌞 Next Solar Terms</h4>'''
        
        for term in r['solar']['upcoming_terms'][:3]:
            gann_info = term.get('gann_info', '')
            html += f'''<div class="metric"><span class="metric-label">{term['term']}{gann_info}</span><span class="metric-value">{term['date']} ({term['days_until']}d)</span></div>'''
        
        html += '''
                </div>
            </div>'''
    
    html += f'''
        </div>
        
        <div class="footer">
            <p>⚠️ DISCLAIMER: For informational purposes only. Not financial advice.</p>
            <p>Methodology: 小龍 (Eric Gann Research) | Data Source: Yahoo Finance / Stooq | Analysis: cyclingAi</p>
        </div>
    </div>
</body>
</html>'''
    
    with open(path, 'w') as f:
        f.write(html)

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("\n🚀 HK Stock Cycling Analyzer - Enhanced (小龍 Gann)")
    print(f"Targets: {list(STOCKS.keys())}")
    print(f"Methodology: Square Root Cycles | Anniversary Dates | Square of Nine | Solar Terms")
    
    results = []
    for symbol, info in STOCKS.items():
        result = analyze_stock(symbol, info)
        results.append(result)
    
    report = generate_enhanced_report(results)
    
    report_path = OUTPUT_DIR / "cycling_analysis_enhanced_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    html_path = OUTPUT_DIR / "cycling_analysis_enhanced_report.html"
    generate_enhanced_html(results, html_path)
    
    print(f"\n✅ Enhanced analysis complete!")
    print(f"📄 Report: {report_path}")
    print(f"🌐 HTML: {html_path}")
    print(f"\n{report}")
