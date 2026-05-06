#!/usr/bin/env python3
"""
Gann Enhanced Module - 小龍 Methodology Implementation
Based on 江恩理論及周期研究 (Gann Theory and Cycle Research)

This module provides enhanced Gann analysis features:
1. Square Root Time Cycles
2. Anniversary Date Analysis
3. Square of Nine Time Projections
4. Enhanced Confluence Scoring
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# Historical pivot dates for major indices (to be expanded)
DEFAULT_PIVOTS = {
    "HSI": [
        datetime(2020, 3, 23),   # COVID low
        datetime(2021, 2, 17),   # Post-COVID high
        datetime(2022, 10, 31),  # Major low
        datetime(2024, 4, 20),   # 小龍 predicted bottom
        datetime(2024, 5, 21),   # 小龍 predicted top
        datetime(2024, 10, 8),   # Recent high
    ],
    "3690.HK": [
        datetime(2021, 2, 17),   # All-time high ~480
        datetime(2022, 10, 24),  # Major low ~50
        datetime(2024, 9, 24),   # Recent surge start
    ],
    "0916.HK": [
        datetime(2020, 1, 2),    # Pre-COVID high
        datetime(2020, 3, 18),   # COVID low
        datetime(2021, 9, 1),    # Peak
        datetime(2024, 2, 5),    # Recent low
    ]
}

# Gann Angle Multipliers for Square of Nine
GANN_ANGLE_MULTIPLIERS = {
    45: 1.125,
    90: 1.25,
    135: 1.375,
    180: 1.5,
    225: 1.625,
    270: 1.75,
    315: 1.875,
    360: 2.0
}

# Solar Terms with Gann Angle Alignment (小龍's 8 Critical Terms)
CRITICAL_SOLAR_TERMS = {
    "春分 Spring Equinox": {"date": "2026-03-21", "tier": 1, "gann_angle": 90, "score": 30},
    "清明 Qingming": {"date": "2026-04-05", "tier": 2, "gann_angle": None, "score": 15},
    "穀雨 Grain Rain": {"date": "2026-04-20", "tier": 2, "gann_angle": None, "score": 15},
    "立夏 Start of Summer": {"date": "2026-05-05", "tier": 2, "gann_angle": 135, "score": 20},
    "小滿 Grain Full": {"date": "2026-05-21", "tier": 3, "gann_angle": None, "score": 10},
    "芒種 Grain in Ear": {"date": "2026-06-05", "tier": 3, "gann_angle": None, "score": 10},
    "夏至 Summer Solstice": {"date": "2026-06-21", "tier": 1, "gann_angle": 180, "score": 30},
    "小暑 Minor Heat": {"date": "2026-07-07", "tier": 3, "gann_angle": None, "score": 10},
    "大暑 Major Heat": {"date": "2026-07-23", "tier": 3, "gann_angle": None, "score": 10},
    "立秋 Start of Autumn": {"date": "2026-08-08", "tier": 2, "gann_angle": 225, "score": 20},
    "處暑 End of Heat": {"date": "2026-08-23", "tier": 3, "gann_angle": None, "score": 10},
    "白露 White Dew": {"date": "2026-09-07", "tier": 3, "gann_angle": None, "score": 10},
    "秋分 Autumn Equinox": {"date": "2026-09-23", "tier": 1, "gann_angle": 270, "score": 30},
    "寒露 Cold Dew": {"date": "2026-10-08", "tier": 1, "gann_angle": None, "score": 25},
    "霜降 Frost's Descent": {"date": "2026-10-23", "tier": 3, "gann_angle": None, "score": 10},
    "立冬 Start of Winter": {"date": "2026-11-07", "tier": 2, "gann_angle": 315, "score": 20},
    "小雪 Minor Snow": {"date": "2026-11-22", "tier": 3, "gann_angle": None, "score": 10},
    "大雪 Major Snow": {"date": "2026-12-07", "tier": 3, "gann_angle": None, "score": 10},
    "冬至 Winter Solstice": {"date": "2026-12-22", "tier": 1, "gann_angle": 360, "score": 30},
}

# ============================================================================
# SQUARE ROOT TIME CYCLE
# ============================================================================

def calculate_square_root_cycles(pivot_date: datetime, current_date: datetime, 
                                  num_cycles: int = 5) -> List[Dict]:
    """
    Calculate Square Root Time Cycles from a pivot date.
    
    Based on 小龍's methodology:
    - days_elapsed = (current_date - pivot_date).days
    - cycle_number = sqrt(days_elapsed)
    - Future turns at: cycle_number², (cycle_number+1)², (cycle_number+2)²...
    
    Returns list of projected turn dates with cycle info.
    """
    days_elapsed = (current_date - pivot_date).days
    if days_elapsed <= 0:
        return []
    
    base_cycle = int(math.sqrt(days_elapsed))
    cycles = []
    
    for i in range(num_cycles):
        cycle_num = base_cycle + i
        projected_days = cycle_num ** 2
        days_until = projected_days - days_elapsed
        turn_date = pivot_date + timedelta(days=projected_days)
        
        # Only include future dates
        if turn_date >= current_date:
            cycles.append({
                "cycle_number": cycle_num,
                "days_from_pivot": projected_days,
                "days_until": days_until,
                "turn_date": turn_date,
                "turn_date_str": turn_date.strftime('%Y-%m-%d'),
                "strength": "Strong" if i == 0 else "Moderate" if i == 1 else "Weak"
            })
    
    return cycles

# ============================================================================
# ANNIVERSARY DATE ANALYSIS
# ============================================================================

def calculate_anniversary_dates(pivot_date: datetime, years_ahead: int = 3) -> List[Dict]:
    """
    Calculate anniversary dates from a pivot.
    
    Based on 小龍's methodology:
    - Check same date in following years (+1y, +2y, +3y)
    - Also check quarterly offsets (+3m, +6m, +9m)
    
    Returns list of anniversary dates with type info.
    """
    anniversaries = []
    
    # Full year anniversaries
    for y in range(1, years_ahead + 1):
        try:
            ann_date = pivot_date.replace(year=pivot_date.year + y)
            anniversaries.append({
                "date": ann_date,
                "date_str": ann_date.strftime('%Y-%m-%d'),
                "type": "Anniversary",
                "offset": f"+{y} year(s)",
                "score": 15
            })
        except ValueError:
            # Handle Feb 29
            continue
    
    # Quarterly offsets from original pivot
    for months in [3, 6, 9]:
        try:
            quarter_date = pivot_date + timedelta(days=months * 30)
            anniversaries.append({
                "date": quarter_date,
                "date_str": quarter_date.strftime('%Y-%m-%d'),
                "type": "Quarterly Offset",
                "offset": f"+{months} months",
                "score": 10
            })
        except:
            continue
    
    return anniversaries

# ============================================================================
# SQUARE OF NINE TIME PROJECTIONS
# ============================================================================

def calculate_square_of_nine(pivot_date: datetime, current_date: datetime) -> List[Dict]:
    """
    Calculate Square of Nine time projections.
    
    Based on 小龍's methodology:
    - base_days = days from major pivot
    - projected_days = base_days * angle_multiplier
    - Key angles: 45°, 90°, 135°, 180°, 225°, 270°, 315°, 360°
    
    Returns list of projected turn dates.
    """
    base_days = (current_date - pivot_date).days
    if base_days <= 0:
        return []
    
    projections = []
    
    for angle, multiplier in GANN_ANGLE_MULTIPLIERS.items():
        projected_days = int(base_days * multiplier)
        turn_date = pivot_date + timedelta(days=projected_days)
        days_until = (turn_date - current_date).days
        
        # Only include future dates
        if turn_date >= current_date:
            projections.append({
                "angle": angle,
                "multiplier": multiplier,
                "days_from_pivot": projected_days,
                "days_until": days_until,
                "turn_date": turn_date,
                "turn_date_str": turn_date.strftime('%Y-%m-%d'),
                "score": 10 if angle in [90, 180, 270, 360] else 5
            })
    
    # Sort by days_until
    projections.sort(key=lambda x: x['days_until'])
    
    return projections

# ============================================================================
# ENHANCED CONFLUENCE SCORING
# ============================================================================

def calculate_confluence_score(date: datetime, pivot_dates: List[datetime],
                                tolerance_days: int = 4) -> Dict:
    """
    Calculate enhanced confluence score for a given date.
    
    Based on 小龍's scoring system:
    | Factor | Points |
    |--------|--------|
    | Solar Term Tier 1 | 30 |
    | Solar Term Tier 2 | 20 |
    | Gann Angle (90°, 180°, 270°, 360°) | 25 |
    | Anniversary Date | 15 |
    | Square Root Cycle | 10 |
    | Square of Nine | 10 |
    
    Returns score breakdown and confidence level.
    """
    score_breakdown = []
    total_score = 0
    
    # Check solar terms
    for term_name, term_info in CRITICAL_SOLAR_TERMS.items():
        term_date = datetime.strptime(term_info["date"], '%Y-%m-%d')
        days_diff = abs((date - term_date).days)
        
        if days_diff <= tolerance_days:
            score = term_info["score"]
            if term_info["gann_angle"] in [90, 180, 270, 360]:
                score += 25  # Bonus for Gann angle alignment
                score_breakdown.append(f"Solar Term + Gann Angle: {term_name} ({term_info['gann_angle']}°)")
            else:
                score_breakdown.append(f"Solar Term: {term_name} (Tier {term_info['tier']})")
            total_score += score
    
    # Check square root cycles from pivots
    for pivot in pivot_dates:
        cycles = calculate_square_root_cycles(pivot, date, num_cycles=2)
        for cycle in cycles:
            if abs(cycle['days_until']) <= tolerance_days:
                score_breakdown.append(f"Square Root Cycle: {cycle['cycle_number']}² from {pivot.strftime('%Y-%m-%d')}")
                total_score += 10
                break
    
    # Check anniversary dates
    for pivot in pivot_dates:
        anniversaries = calculate_anniversary_dates(pivot, years_ahead=3)
        for ann in anniversaries:
            ann_date = ann["date"]
            days_diff = abs((date - ann_date).days)
            if days_diff <= tolerance_days:
                score_breakdown.append(f"Anniversary: {ann['type']} {ann['offset']}")
                total_score += ann["score"]
                break
    
    # Check Square of Nine projections
    for pivot in pivot_dates:
        projections = calculate_square_of_nine(pivot, date)
        for proj in projections:
            if abs(proj['days_until']) <= tolerance_days:
                score_breakdown.append(f"Square of Nine: {proj['angle']}° angle")
                total_score += proj["score"]
                break
    
    # Determine confidence level
    if total_score >= 70:
        confidence = "VERY HIGH"
    elif total_score >= 50:
        confidence = "HIGH"
    elif total_score >= 30:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "total_score": total_score,
        "confidence": confidence,
        "factors": score_breakdown,
        "factor_count": len(score_breakdown)
    }

# ============================================================================
# TURN WINDOW ANALYSIS
# ============================================================================

def analyze_turn_windows(pivot_dates: List[datetime], 
                          year: int,
                          tolerance_days: int = 4) -> List[Dict]:
    """
    Analyze all potential turn windows for a given year.
    
    Combines all methods:
    - Solar terms
    - Square root cycles
    - Anniversary dates
    - Square of nine projections
    
    Returns sorted list of turn windows by score.
    """
    turn_windows = {}
    
    # Generate candidate dates from all methods
    candidate_dates = set()
    
    # Add solar terms
    for term_name, term_info in CRITICAL_SOLAR_TERMS.items():
        term_date = datetime.strptime(term_info["date"], '%Y-%m-%d')
        if term_date.year == year:
            candidate_dates.add(term_date)
    
    # Add square root cycle projections
    for pivot in pivot_dates:
        cycles = calculate_square_root_cycles(pivot, datetime(year, 1, 1), num_cycles=10)
        for cycle in cycles:
            if cycle['turn_date'].year == year or cycle['turn_date'].year == year + 1:
                candidate_dates.add(cycle['turn_date'])
    
    # Add anniversary dates
    for pivot in pivot_dates:
        anniversaries = calculate_anniversary_dates(pivot, years_ahead=5)
        for ann in anniversaries:
            if ann['date'].year == year or ann['date'].year == year + 1:
                candidate_dates.add(ann['date'])
    
    # Add Square of Nine projections
    current = datetime(year, 1, 1)
    for pivot in pivot_dates:
        projections = calculate_square_of_nine(pivot, current)
        for proj in projections:
            if proj['turn_date'].year == year or proj['turn_date'].year == year + 1:
                candidate_dates.add(proj['turn_date'])
    
    # Calculate confluence score for each candidate
    for date in candidate_dates:
        # Create window center date
        window_date = date
        
        # Calculate score
        score_info = calculate_confluence_score(window_date, pivot_dates, tolerance_days)
        
        if score_info['total_score'] > 0:
            window_key = window_date.strftime('%Y-%m-%d')
            turn_windows[window_key] = {
                "date": window_date,
                "date_str": window_key,
                "score": score_info['total_score'],
                "confidence": score_info['confidence'],
                "factors": score_info['factors'],
                "factor_count": score_info['factor_count'],
                "window_start": (window_date - timedelta(days=tolerance_days)).strftime('%Y-%m-%d'),
                "window_end": (window_date + timedelta(days=tolerance_days)).strftime('%Y-%m-%d')
            }
    
    # Sort by score descending
    sorted_windows = sorted(turn_windows.values(), key=lambda x: x['score'], reverse=True)
    
    return sorted_windows

# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def gann_enhanced_analysis(symbol: str, current_date: datetime = None) -> Dict:
    """
    Perform comprehensive Gann-enhanced analysis for a symbol.
    
    Returns:
    - Current turn windows for 2026
    - Key support/resistance dates
    - Confluence scores
    - Trading recommendations
    """
    if current_date is None:
        current_date = datetime.now()
    
    # Get pivot dates for symbol (or use defaults)
    pivot_dates = DEFAULT_PIVOTS.get(symbol, DEFAULT_PIVOTS["HSI"])
    
    # Analyze turn windows for current year
    turn_windows = analyze_turn_windows(pivot_dates, current_date.year)
    
    # Get upcoming windows (next 90 days)
    upcoming = [w for w in turn_windows if datetime.strptime(w['date_str'], '%Y-%m-%d') >= current_date]
    upcoming = upcoming[:10]  # Top 10 upcoming
    
    # Calculate current confluence (today's score)
    current_score = calculate_confluence_score(current_date, pivot_dates)
    
    # Generate square root cycles from most recent pivot
    recent_pivot = max([p for p in pivot_dates if p < current_date], default=pivot_dates[0])
    sqrt_cycles = calculate_square_root_cycles(recent_pivot, current_date)
    
    return {
        "symbol": symbol,
        "analysis_date": current_date.strftime('%Y-%m-%d'),
        "pivot_dates_used": [p.strftime('%Y-%m-%d') for p in pivot_dates],
        "current_confluence": current_score,
        "upcoming_turn_windows": upcoming,
        "square_root_cycles": sqrt_cycles[:5],
        "top_critical_dates": turn_windows[:5],
        "recommendation": generate_recommendation(current_score, upcoming[:3])
    }

def generate_recommendation(current_score: Dict, upcoming_windows: List[Dict]) -> str:
    """Generate trading recommendation based on analysis."""
    if current_score['total_score'] >= 50:
        return "⚠️ HIGH ALERT - Major turn window active. Expect significant volatility. Consider reducing position size."
    elif current_score['total_score'] >= 30:
        return "⚡ MODULATE ALERT - Turn window approaching. Monitor closely for entry/exit signals."
    
    if upcoming_windows:
        next_window = upcoming_windows[0]
        days_until = (datetime.strptime(next_window['date_str'], '%Y-%m-%d') - datetime.now()).days
        if days_until <= 7:
            return f"⏰ TURN INCOMING - High confidence window in {days_until} days ({next_window['date_str']}). Prepare for volatility."
    
    return "📊 NORMAL - No major turn windows active. Follow trend and standard technical analysis."

# ============================================================================
# CLI / TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("小龍 Gann Enhanced Analysis Module")
    print("=" * 70)
    
    # Test with HSI
    result = gann_enhanced_analysis("HSI")
    
    print(f"\n📊 Symbol: {result['symbol']}")
    print(f"📅 Analysis Date: {result['analysis_date']}")
    print(f"\n🎯 Current Confluence Score: {result['current_confluence']['total_score']} points")
    print(f"   Confidence: {result['current_confluence']['confidence']}")
    print(f"   Factors: {', '.join(result['current_confluence']['factors'][:3]) or 'None'}")
    
    print(f"\n📈 Recommendation: {result['recommendation']}")
    
    print(f"\n🔮 Top 5 Upcoming Turn Windows:")
    for i, window in enumerate(result['upcoming_turn_windows'][:5], 1):
        print(f"   {i}. {window['date_str']} (Score: {window['score']}, {window['confidence']})")
        print(f"      Window: {window['window_start']} to {window['window_end']}")
        if window['factors']:
            print(f"      Factors: {', '.join(window['factors'][:2])}")
    
    print(f"\n📐 Square Root Cycles from {result['pivot_dates_used'][-1]}:")
    for cycle in result['square_root_cycles'][:3]:
        print(f"   • {cycle['turn_date_str']}: {cycle['cycle_number']}² = {cycle['days_from_pivot']} days ({cycle['strength']})")
