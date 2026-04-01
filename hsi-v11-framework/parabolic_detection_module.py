#!/usr/bin/env python3
"""
Parabolic Detection Module - Multi-Asset Class
Extension of 小龍 methodology for detecting parabolic moves across asset classes.

Integrates with:
- gold_warning_indicator.py (Gold/Silver)
- stock_cycling_analyzer_enhanced.py (HSI, individual stocks)
- commodity_cycle_tracker.py (Industrial metals - TODO)

Features:
1. Universal parabolic detection (>50% YoY = WARNING)
2. Cross-asset comparison
3. Portfolio risk scoring
4. Automated alerts for MEMORY.md updates
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Import gold warning module
from gold_warning_indicator import (
    detect_parabolic_move,
    compare_with_history,
    estimate_correction_magnitude,
    generate_alert,
    fetch_gold_price_live,
    PARABOLIC_THRESHOLDS
)

# ============================================================================
# CONFIGURATION
# ============================================================================

WORKSPACE = Path('/root/.openclaw/workspace')
MEMORY_FILE = WORKSPACE / 'MEMORY.md'
PARABOLIC_ALERTS_FILE = WORKSPACE / 'parabolic_alerts_history.json'

# Asset classes to monitor
ASSET_CLASSES = {
    'gold': {
        'name': 'Gold (XAU/USD)',
        'threshold_yoy': 0.50,
        'threshold_30d': 0.15,
        'current_allocation': 0.05,  # 5% (reduced from 10%)
        'max_allocation': 0.10,
        'status': 'CRITICAL'  # Updated 2026-03-18
    },
    'silver': {
        'name': 'Silver (XAG/USD)',
        'threshold_yoy': 0.60,  # Silver more volatile
        'threshold_30d': 0.20,
        'current_allocation': 0.00,  # Not currently held
        'max_allocation': 0.05,
        'status': 'MONITOR'
    },
    'copper': {
        'name': 'Copper (Industrial)',
        'threshold_yoy': 0.40,
        'threshold_30d': 0.15,
        'current_allocation': 0.00,  # Via industrial metals ETF
        'max_allocation': 0.10,
        'status': 'NORMAL'
    },
    'hsi': {
        'name': 'Hang Seng Index',
        'threshold_yoy': 0.50,
        'threshold_30d': 0.15,
        'current_allocation': 0.35,  # Via stocks + ETFs
        'max_allocation': 0.50,
        'status': 'NORMAL'
    },
    'bitcoin': {
        'name': 'Bitcoin (BTC)',
        'threshold_yoy': 1.00,  # Crypto more volatile
        'threshold_30d': 0.30,
        'current_allocation': 0.00,  # Not held
        'max_allocation': 0.03,
        'status': 'MONITOR'
    }
}

# ============================================================================
# MOCK PRICE DATA (Replace with live APIs in production)
# ============================================================================

def get_mock_asset_prices() -> Dict:
    """
    Get mock price data for all monitored assets.
    In production, replace with actual API calls.
    """
    return {
        'gold': {
            'price': 5200.0,
            'price_1y_ago': 2888.9,
            'yoy_gain': 0.80,
            'gain_30d': 0.124,
            'gain_7d': 0.058
        },
        'silver': {
            'price': 62.0,
            'price_1y_ago': 38.0,
            'yoy_gain': 0.63,
            'gain_30d': 0.18,
            'gain_7d': 0.08
        },
        'copper': {
            'price': 4.85,  # USD/lb
            'price_1y_ago': 3.90,
            'yoy_gain': 0.24,
            'gain_30d': 0.08,
            'gain_7d': 0.03
        },
        'hsi': {
            'price': 25700,
            'price_1y_ago': 18500,
            'yoy_gain': 0.39,
            'gain_30d': 0.05,
            'gain_7d': 0.02
        },
        'bitcoin': {
            'price': 95000,
            'price_1y_ago': 52000,
            'yoy_gain': 0.83,
            'gain_30d': 0.25,
            'gain_7d': 0.10
        }
    }

# ============================================================================
# PORTFOLIO RISK SCORING
# ============================================================================

def calculate_portfolio_parabolic_risk(asset_prices: Dict) -> Dict:
    """
    Calculate overall portfolio risk based on parabolic detections.
    
    Returns:
    - Overall risk score (0-100)
    - Risk breakdown by asset
    - Recommended actions
    """
    risk_scores = {}
    total_risk = 0
    total_weight = 0
    
    for asset, config in ASSET_CLASSES.items():
        if asset not in asset_prices:
            continue
        
        price_data = asset_prices[asset]
        yoy_gain = price_data['yoy_gain']
        
        # Calculate risk score for this asset
        if yoy_gain >= PARABOLIC_THRESHOLDS['yoy_gain_critical']:
            asset_risk = 95
        elif yoy_gain >= config['threshold_yoy']:
            asset_risk = 75
        elif price_data['gain_30d'] >= config['threshold_30d']:
            asset_risk = 50
        else:
            asset_risk = 20
        
        # Weight by allocation
        allocation = config['current_allocation']
        weighted_risk = asset_risk * allocation
        
        risk_scores[asset] = {
            'risk_score': asset_risk,
            'yoy_gain': yoy_gain * 100,
            'allocation': allocation * 100,
            'weighted_risk': weighted_risk,
            'status': 'CRITICAL' if asset_risk >= 95 else 'WARNING' if asset_risk >= 75 else 'ALERT' if asset_risk >= 50 else 'NORMAL'
        }
        
        total_risk += weighted_risk
        total_weight += allocation
    
    # Calculate portfolio-level risk
    portfolio_risk = total_risk / max(total_weight, 0.01)  # Avoid division by zero
    
    return {
        'portfolio_risk_score': portfolio_risk,
        'portfolio_risk_level': 'CRITICAL' if portfolio_risk >= 80 else 'WARNING' if portfolio_risk >= 60 else 'ALERT' if portfolio_risk >= 40 else 'NORMAL',
        'asset_breakdown': risk_scores,
        'total_risk_contribution': total_risk,
        'timestamp': datetime.now().isoformat()
    }

# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

def generate_portfolio_recommendations(portfolio_risk: Dict, asset_prices: Dict) -> List[Dict]:
    """
    Generate actionable recommendations based on portfolio risk analysis.
    """
    recommendations = []
    
    # Check each asset
    for asset, risk_data in portfolio_risk['asset_breakdown'].items():
        config = ASSET_CLASSES[asset]
        
        if risk_data['status'] == 'CRITICAL':
            recommendations.append({
                'priority': 'CRITICAL',
                'asset': asset,
                'action': 'REDUCE',
                'current_allocation': f"{risk_data['allocation']:.1f}%",
                'target_allocation': f"{config['max_allocation'] * 0.5:.1f}%",
                'rationale': f"{asset} is in parabolic territory (+{risk_data['yoy_gain']:.1f}% YoY). Historical precedents suggest high correction risk.",
                'urgency': 'IMMEDIATE'
            })
        elif risk_data['status'] == 'WARNING':
            recommendations.append({
                'priority': 'HIGH',
                'asset': asset,
                'action': 'REVIEW',
                'current_allocation': f"{risk_data['allocation']:.1f}%",
                'target_allocation': f"{config['max_allocation'] * 0.7:.1f}%",
                'rationale': f"{asset} showing elevated gains (+{risk_data['yoy_gain']:.1f}% YoY). Consider reducing exposure.",
                'urgency': 'THIS WEEK'
            })
        elif risk_data['status'] == 'ALERT':
            recommendations.append({
                'priority': 'MEDIUM',
                'asset': asset,
                'action': 'MONITOR',
                'current_allocation': f"{risk_data['allocation']:.1f}%",
                'target_allocation': f"{config['max_allocation']:.1f}%",
                'rationale': f"{asset} accelerating (+{risk_data['yoy_gain']:.1f}% YoY, +{asset_prices[asset]['gain_30d']*100:.1f}% in 30d). Watch for parabolic acceleration.",
                'urgency': 'WEEKLY'
            })
    
    # Portfolio-level recommendations
    if portfolio_risk['portfolio_risk_level'] == 'CRITICAL':
        recommendations.append({
            'priority': 'CRITICAL',
            'asset': 'PORTFOLIO',
            'action': 'INCREASE_CASH',
            'current_allocation': 'N/A',
            'target_allocation': '15-20% cash',
            'rationale': f"Portfolio risk score {portfolio_risk['portfolio_risk_score']:.1f}/100 is CRITICAL. Increase dry powder for correction buying.",
            'urgency': 'IMMEDIATE'
        })
    elif portfolio_risk['portfolio_risk_level'] == 'WARNING':
        recommendations.append({
            'priority': 'HIGH',
            'asset': 'PORTFOLIO',
            'action': 'REBALANCE',
            'current_allocation': 'N/A',
            'target_allocation': '10-15% cash',
            'rationale': f"Portfolio risk score {portfolio_risk['portfolio_risk_score']:.1f}/100 is ELEVATED. Consider rebalancing.",
            'urgency': 'THIS WEEK'
        })
    
    return recommendations

# ============================================================================
# MEMORY.MD INTEGRATION
# ============================================================================

def update_memory_with_alert(recommendations: List[Dict]) -> bool:
    """
    Update MEMORY.md with critical parabolic alerts.
    Returns True if update was successful.
    """
    # Find critical recommendations
    critical_recs = [r for r in recommendations if r['priority'] == 'CRITICAL']
    
    if not critical_recs:
        print("ℹ️ No critical alerts to update in MEMORY.md")
        return False
    
    # In production, this would edit MEMORY.md
    # For now, just log what would be updated
    print("\n📝 MEMORY.md updates recommended:")
    for rec in critical_recs:
        print(f"   - {rec['asset']}: {rec['action']} ({rec['current_allocation']} → {rec['target_allocation']})")
    
    return True

# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def run_parabolic_detection_analysis(save_results: bool = True) -> Dict:
    """
    Run complete parabolic detection analysis across all asset classes.
    
    Integrates gold warning indicator with portfolio-level risk scoring.
    """
    print("=" * 70)
    print("🔥 PARABOLIC DETECTION MODULE - 小龍 Multi-Asset Analysis")
    print("=" * 70)
    
    # Step 1: Get asset prices
    print("\n📊 Step 1: Fetching asset prices...")
    asset_prices = get_mock_asset_prices()
    for asset, data in asset_prices.items():
        print(f"   {asset.upper()}: ${data['price']:,.2f} (+{data['yoy_gain']*100:.1f}% YoY)")
    
    # Step 2: Calculate portfolio risk
    print("\n⚠️ Step 2: Calculating portfolio risk...")
    portfolio_risk = calculate_portfolio_parabolic_risk(asset_prices)
    print(f"   Portfolio Risk Score: {portfolio_risk['portfolio_risk_score']:.1f}/100")
    print(f"   Risk Level: {portfolio_risk['portfolio_risk_level']}")
    
    # Step 3: Generate recommendations
    print("\n💡 Step 3: Generating recommendations...")
    recommendations = generate_portfolio_recommendations(portfolio_risk, asset_prices)
    print(f"   Total Recommendations: {len(recommendations)}")
    
    critical_count = len([r for r in recommendations if r['priority'] == 'CRITICAL'])
    high_count = len([r for r in recommendations if r['priority'] == 'HIGH'])
    print(f"   - CRITICAL: {critical_count}")
    print(f"   - HIGH: {high_count}")
    print(f"   - MEDIUM: {len(recommendations) - critical_count - high_count}")
    
    # Step 4: Update MEMORY.md
    print("\n📝 Step 4: Updating MEMORY.md...")
    update_memory_with_alert(recommendations)
    
    # Step 5: Save results
    if save_results:
        print("\n💾 Step 5: Saving results...")
        results = {
            'timestamp': datetime.now().isoformat(),
            'asset_prices': asset_prices,
            'portfolio_risk': portfolio_risk,
            'recommendations': recommendations
        }
        
        with open(PARABOLIC_ALERTS_FILE, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"   ✅ Saved: {PARABOLIC_ALERTS_FILE}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Portfolio Risk:    {portfolio_risk['portfolio_risk_score']:.1f}/100 ({portfolio_risk['portfolio_risk_level']})")
    print(f"Critical Alerts:   {critical_count}")
    print(f"High Priority:     {high_count}")
    
    if recommendations:
        print("\nTop Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. [{rec['priority']}] {rec['asset']}: {rec['action']} → {rec['target_allocation']}")
    
    print("=" * 70)
    
    return {
        'asset_prices': asset_prices,
        'portfolio_risk': portfolio_risk,
        'recommendations': recommendations
    }

# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output as JSON
        results = run_parabolic_detection_analysis(save_results=True)
        print(json.dumps(results, indent=2))
    else:
        # Human-readable output
        run_parabolic_detection_analysis(save_results=True)
