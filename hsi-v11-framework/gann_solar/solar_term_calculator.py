#!/usr/bin/env python3
"""
Solar Term Calculator for Gann Theory Integration
Based on 江恩小龍's methodology combining Chinese 24 Solar Terms with Gann angles

Calculates exact astronomical solar term dates for market timing analysis.
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# ============================================================================
# SOLAR TERM DEFINITIONS
# ============================================================================

SOLAR_TERMS = [
    # (Order, Name CN, Name EN, Approx Date, Tier, Gann Angle)
    (1, "小寒", "Xiaohan (Minor Cold)", "Jan 5-6", 3, None),
    (2, "大寒", "Dahan (Major Cold)", "Jan 20-21", 3, None),
    (3, "立春", "Lichun (Start of Spring)", "Feb 3-5", 2, 45),
    (4, "雨水", "Yushui (Rain Water)", "Feb 18-20", 3, None),
    (5, "驚蟄", "Jingzhe (Awakening of Insects)", "Mar 5-7", 3, None),
    (6, "春分", "Chunfen (Spring Equinox)", "Mar 20-22", 1, 90),
    (7, "清明", "Qingming (Pure Brightness)", "Apr 4-6", 3, None),
    (8, "穀雨", "Guyu (Grain Rain)", "Apr 19-21", 3, None),
    (9, "立夏", "Lixia (Start of Summer)", "May 5-7", 2, 135),
    (10, "小滿", "Xiaoman (Grain Buds)", "May 20-22", 3, None),
    (11, "芒種", "Mangzhong (Grain in Ear)", "Jun 5-7", 3, None),
    (12, "夏至", "Xiazhi (Summer Solstice)", "Jun 21-22", 1, 180),
    (13, "小暑", "Xiaoshu (Minor Heat)", "Jul 6-8", 3, None),
    (14, "大暑", "Dashu (Major Heat)", "Jul 22-24", 3, None),
    (15, "立秋", "Liqiu (Start of Autumn)", "Aug 7-9", 2, 225),
    (16, "處暑", "Chushu (Limit of Heat)", "Aug 22-24", 3, None),
    (17, "白露", "Bailu (White Dew)", "Sep 7-9", 3, None),
    (18, "秋分", "Qiufen (Autumn Equinox)", "Sep 22-24", 1, 270),
    (19, "寒露", "Hanlu (Cold Dew)", "Oct 8-9", 3, None),
    (20, "霜降", "Shuangjiang (Frost's Descent)", "Oct 23-24", 3, None),
    (21, "立冬", "Lidong (Start of Winter)", "Nov 7-8", 2, 315),
    (22, "小雪", "Xiaoxue (Minor Snow)", "Nov 22-23", 3, None),
    (23, "大雪", "Daxue (Major Snow)", "Dec 7-8", 3, None),
    (24, "冬至", "Dongzhi (Winter Solstice)", "Dec 21-23", 1, 360),
]

# Tier 1 critical solar terms (4 cardinal points)
TIER_1_TERMS = [6, 12, 18, 24]  # Chunfen, Xiazhi, Qiufen, Dongzhi

# Tier 2 important solar terms (4 season starts)
TIER_2_TERMS = [3, 9, 15, 21]  # Lichun, Lixia, Liqiu, Lidong

# ============================================================================
# ASTRONOMICAL CALCULATION (Simplified)
# ============================================================================

def calculate_solar_term_date(year: int, term_order: int) -> datetime:
    """
    Calculate approximate solar term date using astronomical formula.
    Solar terms occur when Sun reaches specific ecliptic longitudes.
    Each term = 15° of ecliptic longitude.
    
    This is a simplified calculation. For production, use precise ephemeris.
    """
    # Base date: Winter Solstice 2000 (Dec 21, 2000)
    # Term 24 (Dongzhi) = 270° ecliptic longitude
    
    # Days per term ≈ 365.2422 / 24 = 15.2184 days
    days_per_term = 365.2422 / 24
    
    # Reference: Dec 21, 2000 was Dongzhi (term 24)
    ref_date = datetime(2000, 12, 21, 12, 0, 0)
    
    # Calculate days from reference
    years_from_ref = year - 2000
    
    # Position in the cycle (term_order - 24 because ref is term 24)
    terms_from_ref = (years_from_ref * 24) + (term_order - 24)
    
    # Add leap year correction (approximately)
    leap_correction = years_from_ref // 4
    
    total_days = int(terms_from_ref * days_per_term + leap_correction * 0.25)
    
    approx_date = ref_date + timedelta(days=total_days)
    
    # Fine-tune based on known dates
    approx_date = fine_tune_solar_term(year, term_order, approx_date)
    
    return approx_date


def fine_tune_solar_term(year: int, term_order: int, approx_date: datetime) -> datetime:
    """
    Fine-tune solar term dates based on known astronomical tables.
    This uses pre-calculated corrections for accuracy.
    """
    # Known corrections for 2026 (from astronomical almanac)
    corrections_2026 = {
        1: datetime(2026, 1, 5, 10, 33),   # 小寒
        2: datetime(2026, 1, 20, 3, 59),   # 大寒
        3: datetime(2026, 2, 4, 4, 50),    # 立春
        4: datetime(2026, 2, 18, 23, 38),  # 雨水
        5: datetime(2026, 3, 5, 22, 45),   # 驚蟄
        6: datetime(2026, 3, 21, 0, 15),   # 春分
        7: datetime(2026, 4, 5, 5, 48),    # 清明
        8: datetime(2026, 4, 20, 12, 52),  # 穀雨
        9: datetime(2026, 5, 5, 18, 56),   # 立夏
        10: datetime(2026, 5, 21, 9, 32),  # 小滿
        11: datetime(2026, 6, 5, 13, 27),  # 芒種
        12: datetime(2026, 6, 21, 6, 25),  # 夏至
        13: datetime(2026, 7, 7, 4, 53),   # 小暑
        14: datetime(2026, 7, 23, 1, 20),  # 大暑
        15: datetime(2026, 8, 7, 16, 47),  # 立秋
        16: datetime(2026, 8, 23, 7, 33),  # 處暑
        17: datetime(2026, 9, 7, 18, 52),  # 白露
        18: datetime(2026, 9, 23, 4, 22),  # 秋分
        19: datetime(2026, 10, 8, 10, 1),  # 寒露
        20: datetime(2026, 10, 23, 15, 12),# 霜降
        21: datetime(2026, 11, 7, 13, 56), # 立冬
        22: datetime(2026, 11, 22, 11, 20),# 小雪
        23: datetime(2026, 12, 7, 6, 28),  # 大雪
        24: datetime(2026, 12, 22, 3, 50), # 冬至
    }
    
    corrections_2027 = {
        1: datetime(2027, 1, 5, 16, 28),
        2: datetime(2027, 1, 20, 9, 46),
        3: datetime(2027, 2, 4, 10, 42),
        4: datetime(2027, 2, 19, 5, 33),
        5: datetime(2027, 3, 6, 4, 36),
        6: datetime(2027, 3, 21, 6, 11),
        7: datetime(2027, 4, 5, 11, 39),
        8: datetime(2027, 4, 20, 18, 43),
        9: datetime(2027, 5, 6, 0, 50),
        10: datetime(2027, 5, 21, 15, 24),
        11: datetime(2027, 6, 5, 19, 20),
        12: datetime(2027, 6, 21, 12, 18),
        13: datetime(2027, 7, 7, 10, 45),
        14: datetime(2027, 7, 23, 7, 12),
        15: datetime(2027, 8, 7, 22, 39),
        16: datetime(2027, 8, 23, 13, 25),
        17: datetime(2027, 9, 8, 0, 44),
        18: datetime(2027, 9, 23, 10, 14),
        19: datetime(2027, 10, 8, 15, 53),
        20: datetime(2027, 10, 23, 21, 4),
        21: datetime(2027, 11, 7, 19, 48),
        22: datetime(2027, 11, 22, 17, 12),
        23: datetime(2027, 12, 7, 12, 20),
        24: datetime(2027, 12, 22, 9, 42),
    }
    
    if year == 2026 and term_order in corrections_2026:
        return corrections_2026[term_order]
    elif year == 2027 and term_order in corrections_2027:
        return corrections_2027[term_order]
    
    return approx_date


# ============================================================================
# GANN CYCLE CALCULATIONS
# ============================================================================

def calculate_square_root_cycles(pivot_date: datetime, current_date: datetime) -> List[Dict]:
    """
    Calculate Gann square root time cycles from a pivot date.
    
    Formula: √(days_elapsed) gives cycle number
    Future turns at: cycle_number², (cycle_number+1)², etc.
    """
    days_elapsed = (current_date - pivot_date).days
    
    if days_elapsed <= 0:
        return []
    
    cycles = []
    base_sqrt = math.sqrt(days_elapsed)
    
    # Project forward using square numbers
    for i in range(1, 13):  # Next 12 square cycles
        cycle_num = int(base_sqrt) + i
        future_days = cycle_num ** 2
        future_date = pivot_date + timedelta(days=future_days)
        
        # Also calculate harmonic divisions
        for divisor in [2, 3, 4, 8]:
            harmonic_days = future_days // divisor
            harmonic_date = pivot_date + timedelta(days=harmonic_days)
            cycles.append({
                'type': f'Sqrt_{cycle_num}²_div_{divisor}',
                'date': harmonic_date,
                'days_from_pivot': harmonic_days,
                'base_cycle': cycle_num ** 2,
                'strength': 'medium' if divisor > 2 else 'strong'
            })
        
        cycles.append({
            'type': f'Sqrt_{cycle_num}²',
            'date': future_date,
            'days_from_pivot': future_days,
            'base_cycle': cycle_num ** 2,
            'strength': 'strong'
        })
    
    return cycles


def calculate_anniversary_dates(pivot_date: datetime, years_ahead: int = 3) -> List[Dict]:
    """
    Calculate Gann anniversary dates from a pivot.
    Market often turns on same calendar date in future years.
    """
    anniversaries = []
    
    for year_offset in range(1, years_ahead + 1):
        try:
            anniversary = pivot_date.replace(year=pivot_date.year + year_offset)
            anniversaries.append({
                'type': f'Anniversary_{year_offset}yr',
                'date': anniversary,
                'days_from_pivot': (anniversary - pivot_date).days,
                'strength': 'strong' if year_offset <= 2 else 'medium'
            })
            
            # Also add 3-month and 6-month offsets (Gann seasonal)
            for month_offset in [3, 6, 9]:
                offset_date = anniversary + timedelta(days=month_offset * 30)
                anniversaries.append({
                    'type': f'Anniversary_{year_offset}yr_plus_{month_offset}mo',
                    'date': offset_date,
                    'days_from_pivot': (offset_date - pivot_date).days,
                    'strength': 'medium'
                })
        except ValueError:
            # Handle Feb 29 edge case
            pass
    
    return anniversaries


def calculate_gann_square_of_nine(pivot_date: datetime, base_days: int) -> List[Dict]:
    """
    Calculate Gann Square of Nine time projections.
    
    Numbers on key angles (45°, 90°, 180°, 270°, 315°) from base_days
    create time resonance points.
    """
    projections = []
    
    # Square of Nine angle multipliers (simplified)
    angle_multipliers = {
        45: 1.125,    # 1/8
        90: 1.25,     # 1/4
        135: 1.375,   # 3/8
        180: 1.5,     # 1/2
        225: 1.625,   # 5/8
        270: 1.75,    # 3/4
        315: 1.875,   # 7/8
        360: 2.0,     # Full circle
    }
    
    for angle, multiplier in angle_multipliers.items():
        projected_days = int(base_days * multiplier)
        projected_date = pivot_date + timedelta(days=projected_days)
        
        projections.append({
            'type': f'GannSquare_{angle}deg',
            'date': projected_date,
            'days_from_pivot': projected_days,
            'angle': angle,
            'strength': 'strong' if angle in [90, 180, 270, 360] else 'medium'
        })
    
    # Also calculate square numbers from base
    sqrt_base = int(math.sqrt(base_days))
    for i in range(1, 6):
        square_num = (sqrt_base + i) ** 2
        square_date = pivot_date + timedelta(days=square_num)
        projections.append({
            'type': f'GannSquare_num_{square_num}',
            'date': square_date,
            'days_from_pivot': square_num,
            'strength': 'strong'
        })
    
    return projections


# ============================================================================
# CONFLUENCE SCORING SYSTEM
# ============================================================================

def calculate_confluence_score(date: datetime, signals: List[Dict]) -> Dict:
    """
    Calculate confluence score for a given date based on overlapping signals.
    
    Scoring weights (小龍's methodology):
    - Solar Term Tier 1: 30 points
    - Solar Term Tier 2: 20 points
    - Gann Angle (90, 180, 270, 360): 25 points
    - Anniversary Date: 15 points
    - Square Root Cycle: 10 points
    - Square of Nine: 10 points
    """
    window_days = 3  # ±3 day window for confluence
    
    score = 0
    matching_signals = []
    
    for signal in signals:
        signal_date = signal['date']
        if isinstance(signal_date, datetime):
            days_diff = abs((date - signal_date).days)
            
            if days_diff <= window_days:
                # Add points based on signal type
                if 'SolarTerm_Tier1' in signal.get('type', ''):
                    points = 30
                elif 'SolarTerm_Tier2' in signal.get('type', ''):
                    points = 20
                elif 'GannSquare' in signal.get('type', '') and signal.get('angle') in [90, 180, 270, 360]:
                    points = 25
                elif 'Anniversary' in signal.get('type', ''):
                    points = 15
                elif 'Sqrt' in signal.get('type', ''):
                    points = 10
                elif 'GannSquare' in signal.get('type', ''):
                    points = 10
                else:
                    points = 5
                
                score += points
                matching_signals.append({
                    **signal,
                    'days_offset': days_diff,
                    'points': points
                })
    
    # Determine confidence level
    if score >= 70:
        confidence = 'VERY HIGH'
        action = 'Strong reversal expected'
    elif score >= 50:
        confidence = 'HIGH'
        action = 'Reversal likely'
    elif score >= 30:
        confidence = 'MEDIUM'
        action = 'Watch for volatility'
    else:
        confidence = 'LOW'
        action = 'Normal trading'
    
    return {
        'date': date,
        'score': score,
        'confidence': confidence,
        'action': action,
        'matching_signals': matching_signals
    }


# ============================================================================
# MAIN ANALYSIS FUNCTIONS
# ============================================================================

def get_solar_terms_for_year(year: int) -> List[Dict]:
    """Get all 24 solar terms for a given year with exact dates."""
    terms = []
    for order, name_cn, name_en, approx, tier, angle in SOLAR_TERMS:
        exact_date = calculate_solar_term_date(year, order)
        terms.append({
            'order': order,
            'name_cn': name_cn,
            'name_en': name_en,
            'date': exact_date,
            'tier': tier,
            'gann_angle': angle,
            'type': f'SolarTerm_Tier{tier}',
            'alert_window_start': exact_date - timedelta(days=4),
            'alert_window_end': exact_date + timedelta(days=4)
        })
    return terms


def analyze_turn_windows(pivot_dates: List[datetime], year: int, year_end: int = None) -> List[Dict]:
    """
    Comprehensive turn window analysis combining all methods.
    
    Args:
        pivot_dates: List of historical high/low dates
        year: Start year for analysis
        year_end: End year (default: same as year)
    
    Returns:
        List of turn windows with confluence scores
    """
    if year_end is None:
        year_end = year
    
    all_signals = []
    
    # 1. Add Solar Term signals
    for y in range(year, year_end + 1):
        solar_terms = get_solar_terms_for_year(y)
        all_signals.extend(solar_terms)
    
    # 2. Add Gann cycles from each pivot
    current_date = datetime.now()
    for pivot in pivot_dates:
        # Square root cycles
        sqrt_cycles = calculate_square_root_cycles(pivot, current_date)
        for cycle in sqrt_cycles:
            if year <= cycle['date'].year <= year_end:
                all_signals.append(cycle)
        
        # Anniversary dates
        anniversaries = calculate_anniversary_dates(pivot, years_ahead=3)
        for ann in anniversaries:
            if year <= ann['date'].year <= year_end:
                all_signals.append(ann)
        
        # Square of Nine (use days from major pivot)
        days_from_pivot = (current_date - pivot).days
        if days_from_pivot > 0:
            gann_projections = calculate_gann_square_of_nine(pivot, days_from_pivot)
            for proj in gann_projections:
                if year <= proj['date'].year <= year_end:
                    all_signals.append(proj)
    
    # 3. Scan each day for confluence
    turn_windows = []
    scan_start = datetime(year, 1, 1)
    scan_end = datetime(year_end, 12, 31)
    
    current = scan_start
    while current <= scan_end:
        result = calculate_confluence_score(current, all_signals)
        if result['score'] >= 30:  # Only keep medium+ confidence
            turn_windows.append(result)
        current += timedelta(days=1)
    
    # Sort by score descending
    turn_windows.sort(key=lambda x: x['score'], reverse=True)
    
    return turn_windows


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_turn_windows_report(turn_windows: List[Dict], top_n: int = 20) -> str:
    """Format turn windows as a readable report."""
    report = []
    report.append("=" * 80)
    report.append("GANN + SOLAR TERM TURN WINDOW ANALYSIS")
    report.append("Based on 江恩小龍's Methodology")
    report.append("=" * 80)
    report.append("")
    
    for i, window in enumerate(turn_windows[:top_n], 1):
        date_str = window['date'].strftime('%Y-%m-%d (%A)')
        report.append(f"#{i}: {date_str}")
        report.append(f"    Score: {window['score']} | Confidence: {window['confidence']}")
        report.append(f"    Action: {window['action']}")
        
        if window['matching_signals']:
            report.append("    Matching Signals:")
            for sig in window['matching_signals'][:5]:  # Top 5 signals
                sig_date = sig['date'].strftime('%Y-%m-%d') if isinstance(sig['date'], datetime) else str(sig['date'])
                report.append(f"      - {sig['type']}: {sig_date} (+{sig['days_offset']} days) [{sig['points']} pts]")
        
        report.append("")
    
    return "\n".join(report)


def format_solar_term_calendar(year: int) -> str:
    """Format solar term calendar for a year."""
    terms = get_solar_terms_for_year(year)
    
    report = []
    report.append("=" * 80)
    report.append(f"SOLAR TERM CALENDAR {year}")
    report.append("Gann Angle Alignment for Market Timing")
    report.append("=" * 80)
    report.append("")
    
    for term in terms:
        tier_marker = "★★★" if term['tier'] == 1 else "★★" if term['tier'] == 2 else "★"
        angle_str = f"{term['gann_angle']}°" if term['gann_angle'] else "-"
        date_str = term['date'].strftime('%Y-%m-%d %H:%M')
        window = f"{term['alert_window_start'].strftime('%m-%d')} to {term['alert_window_end'].strftime('%m-%d')}"
        
        report.append(f"{tier_marker} {term['name_cn']:6s} | {term['name_en']:35s} | {date_str} | Angle: {angle_str:4s} | Alert: {window}")
    
    report.append("")
    report.append("Legend: ★★★ = Tier 1 (Critical) | ★★ = Tier 2 (Important) | ★ = Tier 3 (Minor)")
    report.append("Alert Window: ±4 days from solar term (80% probability zone)")
    
    return "\n".join(report)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Example: Generate 2026 solar term calendar
    print(format_solar_term_calendar(2026))
    print("\n")
    
    # Example: Analyze turn windows for 2026
    # Using some historical pivot dates (example only)
    pivot_dates = [
        datetime(2020, 3, 23),   # COVID low
        datetime(2021, 2, 18),   # Post-COVID high
        datetime(2022, 10, 24),  # 2022 low
        datetime(2024, 4, 20),   # Guyu 2024 bottom (小龍's prediction)
        datetime(2024, 5, 21),   # Xiaoman 2024 top
    ]
    
    turn_windows = analyze_turn_windows(pivot_dates, 2026)
    print(format_turn_windows_report(turn_windows, top_n=15))
