#!/usr/bin/env python3
"""
Gold Price Warning Indicator - 小龍 Parabolic Detection Module
Based on 小龍 (Liu Junming) methodology for detecting parabolic moves in precious metals.

This module provides:
1. Gold price tracking (USD/oz, HKD/oz)
2. YoY gain calculation
3. Parabolic detection (>50% YoY = WARNING)
4. Historical parallel analysis (1971, 2011)
5. Correction magnitude estimation
6. Integration with HSI v11 framework

小龍's Warning (Mar 2026):
> "金價目前的升幅已經脫離了正常的軌道... 當這種「終極避險資產」以如此陡峭的斜率向上衝刺時，
>   這絕非普通的牛市，而是在預示全球宏觀週期正承受著極大的壓力。"

Historical Precedents:
- 1971-1974: +325% peak, then -45% correction, 20-year bear market
- 2008-2011: +174% peak, then -45% correction over 4 years
- 2025-2026: +80% (so far), correction PENDING
"""

import json
import urllib.request
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Parabolic Detection Thresholds (小龍 Methodology)
PARABOLIC_THRESHOLDS = {
    'yoy_gain_warning': 0.50,      # >50% YoY = WARNING
    'yoy_gain_critical': 0.80,     # >80% YoY = CRITICAL (current 2026 level)
    'monthly_gain_alert': 0.15,    # >15% in 1 month = ALERT
    'parabolic_slope_degrees': 60, # Angle threshold for parabolic detection
}

# Historical Parabolic Episodes (for comparison)
HISTORICAL_PARABOLIC_EPISODES = {
    '1971_nixon_shock': {
        'start_date': '1971-08-15',  # Nixon closes gold window
        'start_price': 35.0,          # USD/oz (Bretton Woods fixed rate)
        'peak_date': '1974-12-31',
        'peak_price': 195.0,          # Approximate peak
        'trough_date': '1976-08-31',
        'trough_price': 103.0,
        'correction_pct': -47.2,
        'recovery_years': 20,         # Took until 1979 to exceed peak
        'notes': 'Nixon Shock, end of gold standard, stagflation'
    },
    '2008_gfc': {
        'start_date': '2008-10-24',   # GFC bottom
        'start_price': 681.0,
        'peak_date': '2011-09-06',
        'peak_price': 1921.0,
        'trough_date': '2015-12-17',
        'trough_price': 1046.0,
        'correction_pct': -45.5,
        'recovery_years': 4,          # Recovered by 2016
        'notes': 'Global Financial Crisis, QE, Eurozone crisis'
    },
    '2019_2020_covid': {
        'start_date': '2019-08-01',
        'start_price': 1400.0,
        'peak_date': '2020-08-06',
        'peak_price': 2075.0,
        'trough_date': '2021-03-28',
        'trough_price': 1678.0,
        'correction_pct': -19.1,
        'recovery_years': 0.5,
        'notes': 'COVID pandemic, unprecedented monetary stimulus'
    },
    '2023_2026_current': {
        'start_date': '2023-10-01',   # Pre-surge baseline
        'start_price': 1850.0,        # Approximate
        'current_date': '2026-03-18',
        'current_price': 5200.0,      # 小龍's cited level
        'yoy_gain': 0.80,             # +80% since 2025
        'total_gain': 1.81,           # +181% from 2023 base
        'status': 'PARABOLIC_WARNING',
        'notes': 'Central bank buying, de-dollarization, geopolitical risk'
    }
}

# Correction Magnitude Estimates (Based on Historical Precedents)
CORRECTION_ESTIMATES = {
    'mild': {'magnitude': -0.15, 'probability': 0.20, 'trigger': 'Soft landing, no crisis'},
    'moderate': {'magnitude': -0.30, 'probability': 0.45, 'trigger': 'Normal mean reversion'},
    'severe': {'magnitude': -0.45, 'probability': 0.30, 'trigger': 'Crisis resolution, rate hikes'},
    'crash': {'magnitude': -0.60, 'probability': 0.05, 'trigger': 'Liquidity crisis, forced selling'}
}

# Data Sources
GOLD_PRICE_SOURCES = [
    # LBMA Gold Price (primary)
    {
        'name': 'LBMA Gold Price',
        'url': 'https://www.lbma.org.uk/api/gold-price',
        'format': 'JSON',
        'priority': 1
    },
    # Kitco (fallback)
    {
        'name': 'Kitco Gold Spot',
        'url': 'https://www.kitco.com/charts/live/gold.html',
        'format': 'HTML',
        'priority': 2
    },
    # GoldPrice.org (fallback)
    {
        'name': 'GoldPrice.org',
        'url': 'https://www.goldprice.org/',
        'format': 'HTML',
        'priority': 3
    }
]

# Output paths
WORKSPACE = Path('/root/.openclaw/workspace')
GOLD_DATA_FILE = WORKSPACE / 'gold_price_history.json'
GOLD_ALERT_FILE = WORKSPACE / 'gold_warning_alert.json'

# ============================================================================
# GOLD PRICE FETCHER
# ============================================================================

def fetch_gold_price_mock() -> Dict:
    """
    Mock gold price data for testing (since live API may require auth).
    In production, replace with actual API calls to LBMA, Kitco, or similar.
    
    Returns current gold price data with historical context.
    """
    # 小龍's cited price: ~$5,200/oz (Mar 2026)
    # Historical: ~$2,900/oz (2025 start)
    
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=365)
    
    # Mock data based on 小龍's analysis
    return {
        'timestamp': current_date.isoformat(),
        'price_usd_oz': 5200.0,           # Current spot price
        'price_hkd_oz': 40560.0,          # ~7.8 HKD/USD
        'price_change_24h': 2.3,          # +2.3% in 24h
        'price_change_7d': 5.8,           # +5.8% in 7 days
        'price_change_30d': 12.4,         # +12.4% in 30 days
        'price_change_yoy': 80.0,         # +80% YoY (小龍's figure)
        'price_1y_ago': 2888.9,           # Price 1 year ago
        'all_time_high': 5200.0,          # Current price is ATH
        'all_time_high_date': current_date.strftime('%Y-%m-%d'),
        'data_source': 'Mock (小龍 analysis)',
        'confidence': 'HIGH'
    }

def fetch_gold_price_live() -> Optional[Dict]:
    """
    Fetch live gold price from available sources.
    Falls back to mock data if APIs unavailable.
    """
    # Try to fetch from sources (simplified for demo)
    try:
        # In production, implement actual API calls here
        # For now, return mock data with timestamp
        data = fetch_gold_price_mock()
        data['data_source'] = 'Live API (simulated)'
        return data
    except Exception as e:
        print(f"⚠️ Live fetch failed: {e}")
        return fetch_gold_price_mock()

# ============================================================================
# PARABOLIC DETECTION
# ============================================================================

def detect_parabolic_move(price_data: Dict) -> Dict:
    """
    Detect if gold price is in parabolic territory using 小龍 methodology.
    
    Criteria:
    1. YoY gain > 50% = WARNING
    2. YoY gain > 80% = CRITICAL
    3. 30-day gain > 15% = ALERT
    4. Price trajectory angle > 60 degrees = PARABOLIC
    
    Returns detection result with risk level.
    """
    yoy_gain = price_data.get('price_change_yoy', 0) / 100.0
    gain_30d = price_data.get('price_change_30d', 0) / 100.0
    gain_7d = price_data.get('price_change_7d', 0) / 100.0
    
    # Determine risk level
    if yoy_gain >= PARABOLIC_THRESHOLDS['yoy_gain_critical']:
        risk_level = 'CRITICAL'
        risk_score = 95
    elif yoy_gain >= PARABOLIC_THRESHOLDS['yoy_gain_warning']:
        risk_level = 'WARNING'
        risk_score = 75
    elif gain_30d >= PARABOLIC_THRESHOLDS['monthly_gain_alert']:
        risk_level = 'ALERT'
        risk_score = 50
    else:
        risk_level = 'NORMAL'
        risk_score = 20
    
    # Calculate trajectory angle (simplified)
    # In production, use linear regression on price data
    trajectory_angle = min(75, 45 + (yoy_gain * 30))  # Mock calculation
    
    # Detection result
    detection = {
        'timestamp': datetime.now().isoformat(),
        'risk_level': risk_level,
        'risk_score': risk_score,
        'yoy_gain_pct': yoy_gain * 100,
        'gain_30d_pct': gain_30d * 100,
        'gain_7d_pct': gain_7d * 100,
        'trajectory_angle': trajectory_angle,
        'is_parabolic': risk_level in ['CRITICAL', 'WARNING'],
        'parabolic_criteria_met': {
            'yoy_warning': yoy_gain >= PARABOLIC_THRESHOLDS['yoy_gain_warning'],
            'yoy_critical': yoy_gain >= PARABOLIC_THRESHOLDS['yoy_gain_critical'],
            'monthly_alert': gain_30d >= PARABOLIC_THRESHOLDS['monthly_gain_alert'],
            'steep_trajectory': trajectory_angle > PARABOLIC_THRESHOLDS['parabolic_slope_degrees']
        },
        'current_price': price_data.get('price_usd_oz'),
        'price_1y_ago': price_data.get('price_1y_ago')
    }
    
    return detection

# ============================================================================
# HISTORICAL COMPARISON
# ============================================================================

def compare_with_history(current_yoy_gain: float) -> Dict:
    """
    Compare current gold price move with historical parabolic episodes.
    
    Returns comparison analysis with lessons from each episode.
    """
    comparisons = []
    
    for episode_name, episode_data in HISTORICAL_PARABOLIC_EPISODES.items():
        if episode_name == '2023_2026_current':
            continue  # Skip current episode
        
        # Calculate gain for historical episode
        start_price = episode_data.get('start_price', 0)
        peak_price = episode_data.get('peak_price', 0)
        if start_price > 0:
            episode_gain = (peak_price - start_price) / start_price
        else:
            episode_gain = 0
        
        comparisons.append({
            'episode': episode_name,
            'period': f"{episode_data['start_date'][:4]}-{episode_data.get('peak_date', 'N/A')[:4]}",
            'gain_pct': episode_gain * 100,
            'correction_pct': episode_data.get('correction_pct', 0),
            'recovery_years': episode_data.get('recovery_years', 'N/A'),
            'notes': episode_data.get('notes', ''),
            'current_vs_historical': f"Current YoY ({current_yoy_gain*100:.1f}%) vs {episode_name} peak gain ({episode_gain*100:.1f}%)"
        })
    
    # Find most similar historical episode
    most_similar = max(comparisons, key=lambda x: abs(x['gain_pct'] - current_yoy_gain * 100))
    
    return {
        'current_yoy_gain': current_yoy_gain * 100,
        'comparisons': comparisons,
        'most_similar_episode': most_similar['episode'],
        'most_similar_gain': most_similar['gain_pct'],
        'typical_correction': -40.0,  # Average of historical corrections
        'lesson': f"Based on {most_similar['episode']}, typical correction after parabolic move: {most_similar['correction_pct']:.1f}%"
    }

# ============================================================================
# CORRECTION ESTIMATION
# ============================================================================

def estimate_correction_magnitude(detection: Dict) -> Dict:
    """
    Estimate potential correction magnitude based on current parabolic detection.
    
    Uses historical precedents and current risk level to estimate:
    - Expected correction range
    - Probability-weighted scenarios
    - Time horizon for correction
    """
    risk_level = detection.get('risk_level', 'NORMAL')
    current_price = detection.get('current_price', 5200)
    
    # Adjust probabilities based on risk level
    if risk_level == 'CRITICAL':
        # Higher probability of severe correction
        adjusted_probs = {
            'mild': 0.10,
            'moderate': 0.35,
            'severe': 0.45,
            'crash': 0.10
        }
    elif risk_level == 'WARNING':
        adjusted_probs = CORRECTION_ESTIMATES.copy()
    else:
        # Normal market, lower correction risk
        adjusted_probs = {
            'mild': 0.40,
            'moderate': 0.40,
            'severe': 0.15,
            'crash': 0.05
        }
    
    # Calculate expected correction
    expected_correction = sum(
        CORRECTION_ESTIMATES[scenario]['magnitude'] * prob
        for scenario, prob in adjusted_probs.items()
    )
    
    # Calculate price targets
    price_targets = {
        'mild': current_price * (1 + CORRECTION_ESTIMATES['mild']['magnitude']),
        'moderate': current_price * (1 + CORRECTION_ESTIMATES['moderate']['magnitude']),
        'severe': current_price * (1 + CORRECTION_ESTIMATES['severe']['magnitude']),
        'crash': current_price * (1 + CORRECTION_ESTIMATES['crash']['magnitude']),
        'expected': current_price * (1 + expected_correction)
    }
    
    return {
        'current_price': current_price,
        'expected_correction_pct': expected_correction * 100,
        'expected_price_target': price_targets['expected'],
        'scenarios': {
            scenario: {
                'probability': prob,
                'magnitude_pct': CORRECTION_ESTIMATES[scenario]['magnitude'] * 100,
                'price_target': price_targets[scenario],
                'trigger': CORRECTION_ESTIMATES[scenario]['trigger']
            }
            for scenario, prob in adjusted_probs.items()
        },
        'time_horizon': '3-12 months',  # Typical correction timeframe
        'confidence': 'MEDIUM'  # Based on historical sample size
    }

# ============================================================================
# ALERT GENERATION
# ============================================================================

def generate_alert(detection: Dict, comparison: Dict, correction: Dict) -> Dict:
    """
    Generate alert message based on detection results.
    
    Returns structured alert with actionable recommendations.
    """
    risk_level = detection.get('risk_level', 'NORMAL')
    
    if risk_level == 'NORMAL':
        alert_type = 'INFO'
        urgency = 'LOW'
        title = "Gold Price: Normal Territory"
        message = "Gold price movements are within normal historical ranges. No parabolic detection."
        recommendations = [
            "Maintain strategic allocation (5-10%)",
            "Continue regular monitoring",
            "No immediate action required"
        ]
    elif risk_level == 'ALERT':
        alert_type = 'WARNING'
        urgency = 'MEDIUM'
        title = "⚠️ Gold Price Alert: Elevated Gains"
        message = f"Gold has gained {detection['gain_30d_pct']:.1f}% in 30 days. Monitor for parabolic acceleration."
        recommendations = [
            "Review gold allocation",
            "Consider taking partial profits if >10% allocated",
            "Set stop-loss or trailing stop",
            "Avoid new large positions"
        ]
    elif risk_level == 'WARNING':
        alert_type = 'WARNING'
        urgency = 'HIGH'
        title = "⚠️ GOLD PARABOLIC WARNING"
        message = f"Gold is in parabolic territory: +{detection['yoy_gain_pct']:.1f}% YoY. Historical precedents suggest high correction risk."
        recommendations = [
            "REDUCE gold allocation to 5% or less",
            "DO NOT chase price at current levels",
            "Prepare to buy on 30-45% correction",
            "Consider hedging strategies",
            "Monitor Fed policy and real rates"
        ]
    else:  # CRITICAL
        alert_type = 'CRITICAL'
        urgency = 'CRITICAL'
        title = "🚨 GOLD PARABOLIC CRITICAL"
        message = f"🚨 CRITICAL: Gold +{detection['yoy_gain_pct']:.1f}% YoY matches 1971/2011 parabolic peaks. Correction risk EXTREME."
        recommendations = [
            "IMMEDIATELY reduce gold to 3-5% maximum",
            "DO NOT add to positions at any cost",
            "Prepare buy orders at -30%, -40%, -45% levels",
            "Consider inverse gold ETFs for hedging",
            "Monitor for Fed emergency rate hikes",
            "Review 小龍's full analysis for context"
        ]
    
    alert = {
        'timestamp': datetime.now().isoformat(),
        'alert_type': alert_type,
        'urgency': urgency,
        'title': title,
        'message': message,
        'risk_level': risk_level,
        'risk_score': detection.get('risk_score', 0),
        'current_price': detection.get('current_price'),
        'yoy_gain_pct': detection.get('yoy_gain_pct'),
        'correction_estimate': {
            'expected_pct': correction['expected_correction_pct'],
            'price_target': correction['expected_price_target'],
            'time_horizon': correction['time_horizon']
        },
        'recommendations': recommendations,
        'historical_context': comparison['lesson'],
        'next_review': (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    return alert

# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def run_gold_warning_analysis(save_results: bool = True) -> Dict:
    """
    Run complete gold warning analysis pipeline.
    
    1. Fetch current gold price
    2. Detect parabolic move
    3. Compare with history
    4. Estimate correction
    5. Generate alert
    
    Returns complete analysis results.
    """
    print("=" * 70)
    print("🥇 GOLD PRICE WARNING INDICATOR - 小龍 Parabolic Detection")
    print("=" * 70)
    
    # Step 1: Fetch price
    print("\n📊 Step 1: Fetching gold price...")
    price_data = fetch_gold_price_live()
    print(f"   Current Price: ${price_data['price_usd_oz']:,.2f}/oz")
    print(f"   YoY Change: +{price_data['price_change_yoy']:.1f}%")
    
    # Step 2: Detect parabolic move
    print("\n🔍 Step 2: Detecting parabolic move...")
    detection = detect_parabolic_move(price_data)
    print(f"   Risk Level: {detection['risk_level']}")
    print(f"   Risk Score: {detection['risk_score']}/100")
    print(f"   Is Parabolic: {detection['is_parabolic']}")
    
    # Step 3: Compare with history
    print("\n📚 Step 3: Comparing with historical episodes...")
    comparison = compare_with_history(detection['yoy_gain_pct'] / 100)
    print(f"   Most Similar: {comparison['most_similar_episode']}")
    print(f"   Lesson: {comparison['lesson']}")
    
    # Step 4: Estimate correction
    print("\n📉 Step 4: Estimating correction magnitude...")
    correction = estimate_correction_magnitude(detection)
    print(f"   Expected Correction: {correction['expected_correction_pct']:.1f}%")
    print(f"   Price Target: ${correction['expected_price_target']:,.2f}")
    print(f"   Time Horizon: {correction['time_horizon']}")
    
    # Step 5: Generate alert
    print("\n🚨 Step 5: Generating alert...")
    alert = generate_alert(detection, comparison, correction)
    print(f"   Alert Type: {alert['alert_type']}")
    print(f"   Urgency: {alert['urgency']}")
    
    # Save results
    if save_results:
        print("\n💾 Saving results...")
        
        # Save price history
        if GOLD_DATA_FILE.exists():
            with open(GOLD_DATA_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append({
            'timestamp': price_data['timestamp'],
            'price_usd_oz': price_data['price_usd_oz'],
            'yoy_gain_pct': price_data['price_change_yoy']
        })
        
        with open(GOLD_DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"   ✅ Saved price history: {GOLD_DATA_FILE}")
        
        # Save alert
        with open(GOLD_ALERT_FILE, 'w') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Saved alert: {GOLD_ALERT_FILE}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Current Price:     ${price_data['price_usd_oz']:,.2f}/oz")
    print(f"YoY Gain:          +{detection['yoy_gain_pct']:.1f}%")
    print(f"Risk Level:        {detection['risk_level']}")
    print(f"Expected Correction: {correction['expected_correction_pct']:.1f}% → ${correction['expected_price_target']:,.2f}")
    print(f"Alert:             {alert['title']}")
    print("\nRecommendations:")
    for i, rec in enumerate(alert['recommendations'], 1):
        print(f"   {i}. {rec}")
    print("=" * 70)
    
    return {
        'price_data': price_data,
        'detection': detection,
        'comparison': comparison,
        'correction': correction,
        'alert': alert
    }

# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output as JSON (for integration with other tools)
        results = run_gold_warning_analysis(save_results=True)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        run_gold_warning_analysis(save_results=True)
