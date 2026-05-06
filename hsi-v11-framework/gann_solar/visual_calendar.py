#!/usr/bin/env python3
"""
Visual Calendar Generator for Gann + Solar Term Turn Windows
Creates markdown calendars with confidence scores and signal overlays.
"""

from datetime import datetime, timedelta
from typing import List, Dict
import sys

sys.path.append('/root/.openclaw/workspace/gann_solar')
from solar_term_calculator import (
    get_solar_terms_for_year,
    analyze_turn_windows,
    SOLAR_TERMS,
    TIER_1_TERMS,
    TIER_2_TERMS
)


def get_confidence_emoji(score: int) -> str:
    """Convert confidence score to emoji."""
    if score >= 70:
        return "🔴"  # Very High - Strong reversal
    elif score >= 50:
        return "🟠"  # High - Reversal likely
    elif score >= 30:
        return "🟡"  # Medium - Watch volatility
    elif score >= 15:
        return "🟢"  # Low - Normal
    else:
        return "⚪"  # No signals


def get_tier_marker(tier: int) -> str:
    """Get marker for solar term tier."""
    if tier == 1:
        return "★★★"
    elif tier == 2:
        return "★★"
    else:
        return "★"


def generate_monthly_calendar(
    year: int,
    month: int,
    turn_windows: List[Dict],
    solar_terms: List[Dict]
) -> str:
    """Generate a markdown calendar for a single month."""
    
    # Create lookup for turn windows by date
    window_lookup = {}
    for w in turn_windows:
        date_key = w['date'].strftime('%Y-%m-%d')
        window_lookup[date_key] = w
    
    # Create lookup for solar terms
    term_lookup = {}
    for t in solar_terms:
        if t['date'].year == year and t['date'].month == month:
            date_key = t['date'].strftime('%Y-%m-%d')
            term_lookup[date_key] = t
    
    # Month names
    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    lines = []
    lines.append(f"### {month_names[month]} {year}")
    lines.append("")
    lines.append("| Mon | Tue | Wed | Thu | Fri | Sat | Sun |")
    lines.append("|-----|-----|-----|-----|-----|-----|-----|")
    
    # Find first day of month and number of days
    first_day = datetime(year, month, 1)
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    # Adjust for Monday start (Python: Monday=0)
    start_weekday = first_day.weekday()
    days_in_month = (next_month - first_day).days
    
    # Empty cells before first day
    row = "| "
    for _ in range(start_weekday):
        row += "     |"
    
    # Fill in days
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day)
        date_key = date.strftime('%Y-%m-%d')
        
        cell = f"{day:2d}"
        
        # Add solar term marker
        if date_key in term_lookup:
            term = term_lookup[date_key]
            tier = term['tier']
            if tier == 1:
                cell = f"🌟{day:2d}"  # Tier 1 - Critical
            elif tier == 2:
                cell = f"⭐{day:2d}"  # Tier 2 - Important
        
        # Add confidence indicator
        if date_key in window_lookup:
            window = window_lookup[date_key]
            score = window['score']
            emoji = get_confidence_emoji(score)
            cell = f"{emoji}{cell[1:]}" if len(cell) > 2 else f"{emoji}{day:2d}"
        
        row += f" {cell} |"
        
        # New row on Sunday (weekday 6)
        if date.weekday() == 6 or day == days_in_month:
            lines.append(row)
            row = "| "
    
    # Pad last row if needed
    if row != "| ":
        while len(row.split('|')) < 9:
            row += "     |"
        lines.append(row)
    
    lines.append("")
    return "\n".join(lines)


def generate_yearly_calendar(year: int, pivot_dates: List[datetime] = None) -> str:
    """Generate complete yearly calendar with all turn windows."""
    
    if pivot_dates is None:
        # Default pivots from 小龍's methodology
        pivot_dates = [
            datetime(2020, 3, 23),   # COVID low
            datetime(2021, 2, 18),   # Post-COVID high
            datetime(2022, 10, 24),  # 2022 low
            datetime(2024, 4, 20),   # Guyu 2024 bottom
            datetime(2024, 5, 21),   # Xiaoman 2024 top
            datetime(2024, 10, 8),   # Oct 2024 high
        ]
    
    # Get solar terms and turn windows
    solar_terms = get_solar_terms_for_year(year)
    turn_windows = analyze_turn_windows(pivot_dates, year)
    
    # Build report
    report = []
    report.append("#" * 80)
    report.append(f"# GANN + SOLAR TERM TURN WINDOW CALENDAR {year}")
    report.append(f"# Based on 江恩小龍's Methodology")
    report.append("#" * 80)
    report.append("")
    report.append("## Legend")
    report.append("")
    report.append("**Solar Term Tiers:**")
    report.append("- 🌟 = Tier 1 (Critical: Equinox/Solstice) - Gann angles 90°, 180°, 270°, 360°")
    report.append("- ⭐ = Tier 2 (Important: Season Start) - Gann angles 45°, 135°, 225°, 315°")
    report.append("- ★ = Tier 3 (Minor)")
    report.append("")
    report.append("**Confidence Indicators:**")
    report.append("- 🔴 = VERY HIGH (70+ pts) - Strong reversal expected")
    report.append("- 🟠 = HIGH (50-69 pts) - Reversal likely")
    report.append("- 🟡 = MEDIUM (30-49 pts) - Watch for volatility")
    report.append("- 🟢 = LOW (15-29 pts) - Normal trading")
    report.append("- ⚪ = No significant signals")
    report.append("")
    report.append("**Alert Windows:** ±4 days from solar terms (80% probability zone per 小龍)")
    report.append("")
    report.append("---")
    report.append("")
    
    # Generate monthly calendars
    for month in range(1, 13):
        report.append(generate_monthly_calendar(year, month, turn_windows, solar_terms))
    
    # Top turn windows summary
    report.append("")
    report.append("---")
    report.append("")
    report.append("## TOP 20 TURN WINDOWS FOR " + str(year))
    report.append("")
    report.append("| Rank | Date | Day | Score | Confidence | Key Signals |")
    report.append("|------|------|-----|-------|------------|-------------|")
    
    for i, window in enumerate(turn_windows[:20], 1):
        date = window['date']
        date_str = date.strftime('%Y-%m-%d')
        day_str = date.strftime('%a')
        score = window['score']
        conf = window['confidence']
        
        # Get top 2 signals
        signals = window.get('matching_signals', [])[:2]
        signal_str = ", ".join([s['type'].replace('SolarTerm_Tier', 'ST-T') for s in signals])
        
        # Emoji
        emoji = get_confidence_emoji(score)
        
        report.append(f"| {i:2d} | {date_str} | {day_str} | {score:3d} | {conf:12s} | {signal_str} |")
    
    report.append("")
    
    # Solar term dates summary
    report.append("")
    report.append("## COMPLETE SOLAR TERM DATES FOR " + str(year))
    report.append("")
    report.append("| # | Name CN | Name EN | Date | Time | Tier | Gann Angle | Alert Window |")
    report.append("|---|---------|---------|------|------|------|------------|--------------|")
    
    for term in solar_terms:
        marker = get_tier_marker(term['tier'])
        angle = f"{term['gann_angle']}°" if term['gann_angle'] else "-"
        date_str = term['date'].strftime('%Y-%m-%d')
        time_str = term['date'].strftime('%H:%M')
        window_start = term['alert_window_start'].strftime('%m-%d')
        window_end = term['alert_window_end'].strftime('%m-%d')
        
        report.append(f"| {term['order']:2d} | {term['name_cn']} | {term['name_en'][:25]} | {date_str} | {time_str} | {marker} | {angle:4s} | {window_start} to {window_end} |")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("*Generated using Gann + Solar Term Confluence Analysis*")
    report.append("*Methodology: 江恩小龍 (Eric Gann Research)*")
    
    return "\n".join(report)


def generate_critical_dates_only(year: int, pivot_dates: List[datetime] = None) -> str:
    """Generate a simplified list of only high-confidence dates."""
    
    if pivot_dates is None:
        pivot_dates = [
            datetime(2020, 3, 23),
            datetime(2021, 2, 18),
            datetime(2022, 10, 24),
            datetime(2024, 4, 20),
            datetime(2024, 5, 21),
            datetime(2024, 10, 8),
        ]
    
    turn_windows = analyze_turn_windows(pivot_dates, year)
    solar_terms = get_solar_terms_for_year(year)
    
    # Filter for high confidence only
    high_conf = [w for w in turn_windows if w['score'] >= 50]
    
    report = []
    report.append("# CRITICAL TURN DATES " + str(year))
    report.append("")
    report.append("Dates with HIGH or VERY HIGH confidence scores (50+ points)")
    report.append("")
    report.append("## By Month")
    report.append("")
    
    current_month = None
    for window in high_conf:
        month = window['date'].month
        if month != current_month:
            month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            report.append(f"### {month_names[month]}")
            report.append("")
            current_month = month
        
        date_str = window['date'].strftime('%Y-%m-%d (%a)')
        emoji = get_confidence_emoji(window['score'])
        
        # Get solar term info if applicable
        st_info = ""
        for term in solar_terms:
            if abs((window['date'] - term['date']).days) <= 4:
                st_info = f" [{term['name_cn']} {get_tier_marker(term['tier'])}]"
                break
        
        signals = [s['type'] for s in window.get('matching_signals', [])[:3]]
        signal_str = " + ".join(signals)
        
        report.append(f"- **{date_str}** {emoji} Score: {window['score']} - {window['action']}{st_info}")
        report.append(f"  - Signals: {signal_str}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    # Generate full 2026 calendar
    calendar_2026 = generate_yearly_calendar(2026)
    
    # Save to file
    with open('/root/.openclaw/workspace/gann_solar/calendar_2026.md', 'w') as f:
        f.write(calendar_2026)
    
    print("Calendar saved to gann_solar/calendar_2026.md")
    print("\n" + "=" * 80)
    print("PREVIEW (First 100 lines):")
    print("=" * 80)
    print("\n".join(calendar_2026.split("\n")[:100]))
