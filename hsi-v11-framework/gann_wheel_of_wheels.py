#!/usr/bin/env python3
"""
Gann Wheel of Wheels (江恩輪中輪) Module
Based on 小龍's methodology — 江恩理論及周期研究

The Wheel of Wheels is Gann's most powerful timing tool. It maps BOTH price and time
onto a single 360° circular coordinate system. When price and time reach the same
degree on the wheel, they "square" (平衡) — creating high-probability reversal points.

Key Concepts:
1. Price-to-Degree: Map any price level to a 0-360° position
2. Time-to-Degree: Map any calendar day to a 0-360° position  
3. Price-Time Square: When price degree ≈ time degree → REVERSAL
4. Critical Angles: 0°/360°, 90°, 180°, 270° (cardinal) + 45°, 135°, 225°, 315° (fixed)
5. Harmonic Resonance: Angles that are multiples of 30° (zodiac) or 45° (Gann)

小龍 used this to predict:
- 2017 bull market (in 2016)
- 2018 correction (in 2016)
- 2021 property peak
- 2024 HSI 穀雨 bottom / 小滿 top
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONSTANTS
# ============================================================================

# Critical angles on the Wheel (degrees)
CARDINAL_ANGLES = [0, 90, 180, 270]          # Strongest reversals
FIXED_ANGLES = [45, 135, 225, 315]           # Strong reversals
ZODIAC_ANGLES = [i * 30 for i in range(12)]  # 12 zodiac signs (30° each)
GANN_HARMONIC_ANGLES = [i * 45 for i in range(8)]  # 8-fold division

# All critical angles (deduplicated, sorted)
ALL_CRITICAL_ANGLES = sorted(set(CARDINAL_ANGLES + FIXED_ANGLES + ZODIAC_ANGLES))

# Angle significance weights
ANGLE_WEIGHTS = {
    0: 30, 30: 12, 45: 22, 60: 12, 90: 30, 120: 12,
    135: 22, 150: 12, 180: 30, 210: 12, 225: 22, 240: 12,
    270: 30, 300: 12, 315: 22, 330: 12, 360: 30
}

# Annual cycle: 360° = 365.25 days (1° ≈ 1.0146 days)
DEGREES_PER_DAY = 360.0 / 365.25  # ≈ 0.9856°/day

# Default wheel size for price mapping (auto-scaled per instrument)
DEFAULT_WHEEL_SIZE = 100  # Price units per full 360° rotation


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class WheelPosition:
    """A position on the wheel (price or time mapped to degrees)."""
    value: float              # Original value (price or days)
    degrees: float            # Position on 0-360° wheel
    nearest_critical: int     # Nearest critical angle
    distance_to_critical: float  # Degrees away from nearest critical angle
    significance: str         # "cardinal", "fixed", "zodiac", "none"
    weight: int              # Scoring weight
    
    def to_dict(self):
        return {
            'value': self.value,
            'degrees': round(self.degrees, 2),
            'nearest_critical': self.nearest_critical,
            'distance_to_critical': round(self.distance_to_critical, 2),
            'significance': self.significance,
            'weight': self.weight
        }


@dataclass 
class PriceTimeSquare:
    """A price-time square (平衡點) — when price and time align on the wheel."""
    date: datetime
    price: float
    price_degrees: float
    time_degrees: float
    alignment_error: float     # Degrees difference between price & time
    square_type: str           # "exact", "harmonic", "near"
    score: int
    description: str
    
    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'price': self.price,
            'price_degrees': round(self.price_degrees, 2),
            'time_degrees': round(self.time_degrees, 2),
            'alignment_error': round(self.alignment_error, 2),
            'square_type': self.square_type,
            'score': self.score,
            'description': self.description
        }


@dataclass
class WheelProjection:
    """A projected turn date from the Wheel of Wheels."""
    projection_date: datetime
    source_angle: float
    projection_type: str       # "cardinal", "harmonic", "zodiac", "square"
    days_from_now: int
    score: int
    description: str
    
    def to_dict(self):
        return {
            'projection_date': self.projection_date.strftime('%Y-%m-%d'),
            'source_angle': round(self.source_angle, 2),
            'projection_type': self.projection_type,
            'days_from_now': self.days_from_now,
            'score': self.score,
            'description': self.description
        }


# ============================================================================
# CORE WHEEL FUNCTIONS
# ============================================================================

def price_to_degrees(price: float, base_price: float = 0, 
                     wheel_size: float = DEFAULT_WHEEL_SIZE) -> float:
    """
    Map a price level to a position on the 360° wheel.
    
    Formula: degrees = ((price - base_price) % wheel_size) / wheel_size * 360
    
    The wheel_size determines how many price units = one full rotation.
    For HSI (~25,000), use wheel_size=100 or 1000 depending on granularity.
    """
    if wheel_size <= 0:
        return 0
    normalized = (price - base_price) % wheel_size
    return (normalized / wheel_size) * 360


def time_to_degrees(days_from_pivot: int) -> float:
    """
    Map elapsed days from a pivot to a position on the 360° wheel.
    
    Formula: degrees = (days * DEGREES_PER_DAY) % 360
    
    One full year = 360° on the wheel.
    """
    return (days_from_pivot * DEGREES_PER_DAY) % 360


def degrees_to_angle_type(degrees: float) -> str:
    """Classify a degree position by its nearest angle type."""
    degrees = degrees % 360
    
    for angle in CARDINAL_ANGLES:
        if abs(degrees - angle) < 5 or abs(degrees - angle + 360) < 5:
            return "cardinal"
    
    for angle in FIXED_ANGLES:
        if abs(degrees - angle) < 5 or abs(degrees - angle + 360) < 5:
            return "fixed"
    
    for angle in ZODIAC_ANGLES:
        if abs(degrees - angle) < 5 or abs(degrees - angle + 360) < 5:
            return "zodiac"
    
    return "none"


def nearest_critical_angle(degrees: float) -> Tuple[int, float]:
    """Find the nearest critical angle and distance to it."""
    degrees = degrees % 360
    best_angle = 0
    best_distance = 360
    
    for angle in ALL_CRITICAL_ANGLES:
        # Distance on the circle (shortest path)
        dist = min(abs(degrees - angle), 360 - abs(degrees - angle))
        if dist < best_distance:
            best_distance = dist
            best_angle = angle
    
    return best_angle, best_distance


def get_position(degrees: float) -> WheelPosition:
    """Get full wheel position analysis for a given degree value."""
    degrees = degrees % 360
    nearest, distance = nearest_critical_angle(degrees)
    sig_type = degrees_to_angle_type(degrees)
    
    weight = ANGLE_WEIGHTS.get(nearest, 5)
    # Reduce weight by distance penalty (closer = stronger)
    distance_penalty = int(distance / 5)
    weight = max(1, weight - distance_penalty)
    
    return WheelPosition(
        value=degrees,
        degrees=degrees,
        nearest_critical=nearest,
        distance_to_critical=distance,
        significance=sig_type,
        weight=weight
    )


# ============================================================================
# PRICE-TIME SQUARE DETECTION
# ============================================================================

def detect_price_time_squares(
    prices: List[Tuple[datetime, float]],
    pivot_date: datetime,
    wheel_size: float = DEFAULT_WHEEL_SIZE,
    tolerance_degrees: float = 10
) -> List[PriceTimeSquare]:
    """
    Detect price-time squares (平衡點) — the core of Wheel of Wheels.
    
    A price-time square occurs when the price degree ≈ time degree on the wheel.
    
    Args:
        prices: List of (date, price) tuples
        pivot_date: Starting date for time measurement
        wheel_size: Price units per 360° rotation
        tolerance_degrees: How close price and time must be to "square"
    
    Returns:
        List of PriceTimeSquare events sorted by score
    """
    squares = []
    
    for date, price in prices:
        days_elapsed = (date - pivot_date).days
        if days_elapsed <= 0:
            continue
        
        # Map price and time to degrees
        price_deg = price_to_degrees(price, wheel_size=wheel_size)
        time_deg = time_to_degrees(days_elapsed)
        
        # Calculate alignment (shortest angular distance)
        error = min(abs(price_deg - time_deg), 360 - abs(price_deg - time_deg))
        
        if error <= tolerance_degrees:
            # Determine square type
            if error <= 3:
                square_type = "exact"
                score = 35
            elif error <= 7:
                square_type = "harmonic"
                score = 25
            else:
                square_type = "near"
                score = 15
            
            # Bonus if squaring at a critical angle
            price_pos = get_position(price_deg)
            time_pos = get_position(time_deg)
            score += max(price_pos.weight, time_pos.weight)
            
            desc = (f"Price {price:.0f} ({price_deg:.1f}°) squares Time "
                    f"{days_elapsed}d ({time_deg:.1f}°) — error {error:.1f}°")
            
            squares.append(PriceTimeSquare(
                date=date,
                price=price,
                price_degrees=price_deg,
                time_degrees=time_deg,
                alignment_error=error,
                square_type=square_type,
                score=score,
                description=desc
            ))
    
    squares.sort(key=lambda s: s.score, reverse=True)
    return squares


# ============================================================================
# WHEEL PROJECTIONS (TURN DATE FORECASTING)
# ============================================================================

def project_turn_dates(
    pivot_date: datetime,
    current_date: datetime,
    current_price: float,
    wheel_size: float = DEFAULT_WHEEL_SIZE,
    days_ahead: int = 180,
    num_projections: int = 20
) -> List[WheelProjection]:
    """
    Project future turn dates using the Wheel of Wheels.
    
    Three projection methods:
    1. Time reaches critical angle (0°, 90°, 180°, 270°, etc.)
    2. Price would reach critical angle at current rate
    3. Price-time would square
    
    Args:
        pivot_date: Starting date for time measurement
        current_date: Today's date
        current_price: Current price level
        wheel_size: Price units per 360° rotation
        days_ahead: How far to project
        num_projections: Max projections to return
    
    Returns:
        List of WheelProjection sorted by date
    """
    projections = []
    current_days = (current_date - pivot_date).days
    
    # === Method 1: Time reaches critical angles ===
    for angle in ALL_CRITICAL_ANGLES:
        # Current time position
        current_time_deg = time_to_degrees(current_days)
        
        # How many more degrees to reach this angle?
        degrees_needed = (angle - current_time_deg) % 360
        if degrees_needed < 1:
            degrees_needed += 360  # Skip if we're basically there
        
        days_needed = degrees_needed / DEGREES_PER_DAY
        
        if days_needed <= days_ahead:
            proj_date = current_date + timedelta(days=int(days_needed))
            sig_type = degrees_to_angle_type(angle)
            
            weight = ANGLE_WEIGHTS.get(angle, 5)
            
            projections.append(WheelProjection(
                projection_date=proj_date,
                source_angle=angle,
                projection_type=f"time→{sig_type}" if sig_type != "none" else "time→minor",
                days_from_now=int(days_needed),
                score=weight,
                description=f"Time reaches {angle}° ({sig_type}) in {int(days_needed)} days"
            ))
    
    # === Method 2: Price-time square projections ===
    # Estimate daily price change from recent data
    price_deg = price_to_degrees(current_price, wheel_size=wheel_size)
    time_deg = time_to_degrees(current_days)
    
    for target_angle in ALL_CRITICAL_ANGLES:
        # When would time reach this angle?
        degrees_needed = (target_angle - time_deg) % 360
        if degrees_needed < 1:
            degrees_needed += 360
        
        days_at_angle = int(degrees_needed / DEGREES_PER_DAY)
        
        if days_at_angle > days_ahead:
            continue
        
        # What would price need to be to also be at this angle?
        # price_deg_target = target_angle
        # price_target = target_angle / 360 * wheel_size + base
        # But we don't know base, so we check: would price naturally land there?
        
        proj_date = current_date + timedelta(days=days_at_angle)
        
        # Check if this creates a potential square
        future_time_deg = target_angle
        future_price_deg = price_to_degrees(current_price, wheel_size=wheel_size)
        # Price doesn't change in this projection (conservative)
        error = min(abs(future_price_deg - future_time_deg), 
                    360 - abs(future_price_deg - future_time_deg))
        
        if error <= 15:  # Loose tolerance for projection
            weight = ANGLE_WEIGHTS.get(target_angle, 5) + 10  # Square bonus
            projections.append(WheelProjection(
                projection_date=proj_date,
                source_angle=target_angle,
                projection_type="price-time-square",
                days_from_now=days_at_angle,
                score=weight,
                description=(f"Potential price-time square at {target_angle}° "
                           f"(price {future_price_deg:.1f}° ≈ time {future_time_deg:.1f}°)")
            ))
    
    # === Method 3: Full circle completions ===
    current_circle = current_days / 365.25
    next_whole = math.ceil(current_circle)
    for i in range(4):
        target_days = int((next_whole + i) * 365.25)
        days_until = target_days - current_days
        if 0 < days_until <= days_ahead:
            proj_date = current_date + timedelta(days=days_until)
            projections.append(WheelProjection(
                projection_date=proj_date,
                source_angle=0,
                projection_type="full-circle",
                days_from_now=days_until,
                score=20,
                description=f"Full year circle #{next_whole + i} completes"
            ))
    
    # Deduplicate by date (keep highest score)
    seen = {}
    for p in projections:
        key = p.projection_date.strftime('%Y-%m-%d')
        if key not in seen or p.score > seen[key].score:
            seen[key] = p
    
    result = sorted(seen.values(), key=lambda x: x.days_from_now)
    return result[:num_projections]


# ============================================================================
# MULTI-WHEEL ANALYSIS (Different price scales)
# ============================================================================

def multi_wheel_analysis(
    price: float,
    days_elapsed: int,
    wheel_sizes: List[float] = None
) -> Dict:
    """
    Run price-time analysis across multiple wheel sizes.
    
    Different wheel sizes reveal different cycle harmonics:
    - Small (10-50): Short-term cycles
    - Medium (100-500): Medium-term cycles  
    - Large (1000+): Long-term cycles
    
    Returns position on each wheel and combined score.
    """
    if wheel_sizes is None:
        wheel_sizes = [10, 50, 100, 500, 1000]
    
    results = {}
    combined_score = 0
    
    time_deg = time_to_degrees(days_elapsed)
    
    for ws in wheel_sizes:
        price_deg = price_to_degrees(price, wheel_size=ws)
        price_pos = get_position(price_deg)
        time_pos = get_position(time_deg)
        
        # Price-time alignment error
        error = min(abs(price_deg - time_deg), 360 - abs(price_deg - time_deg))
        
        # Score for this wheel size
        ws_score = 0
        ws_score += price_pos.weight
        ws_score += time_pos.weight
        if error <= 10:
            ws_score += 15  # Alignment bonus
        elif error <= 20:
            ws_score += 8
        
        results[f"wheel_{ws}"] = {
            'wheel_size': ws,
            'price_degrees': round(price_deg, 2),
            'time_degrees': round(time_deg, 2),
            'alignment_error': round(error, 2),
            'price_position': price_pos.to_dict(),
            'time_position': time_pos.to_dict(),
            'wheel_score': ws_score
        }
        
        combined_score += ws_score
    
    return {
        'wheels': results,
        'combined_score': combined_score,
        'max_possible': len(wheel_sizes) * 75,  # Approximate max per wheel
        'signal_strength': (
            "VERY STRONG" if combined_score > 200 else
            "STRONG" if combined_score > 150 else
            "MODERATE" if combined_score > 100 else
            "WEAK"
        )
    }


# ============================================================================
# INTEGRATED GANN WHEEL ANALYSIS
# ============================================================================

def wheel_of_wheels_analysis(
    symbol: str,
    current_price: float,
    current_date: datetime = None,
    pivot_dates: List[datetime] = None,
    wheel_size: float = DEFAULT_WHEEL_SIZE
) -> Dict:
    """
    Complete Wheel of Wheels analysis for a symbol.
    
    Combines:
    1. Multi-wheel position analysis
    2. Price-time square detection (historical)
    3. Turn date projections (future)
    4. Confluence with existing Gann/Solar signals
    
    Returns comprehensive analysis dict.
    """
    if current_date is None:
        current_date = datetime.now()
    
    if pivot_dates is None:
        # Use default pivots from gann_enhanced_module
        from gann_enhanced_module import DEFAULT_PIVOTS
        pivot_dates = DEFAULT_PIVOTS.get(symbol, DEFAULT_PIVOTS["HSI"])
    
    # Use most recent pivot
    recent_pivot = max([p for p in pivot_dates if p < current_date], default=pivot_dates[0])
    days_elapsed = (current_date - recent_pivot).days
    
    # 1. Multi-wheel analysis
    multi = multi_wheel_analysis(current_price, days_elapsed)
    
    # 2. Time projections from each pivot
    all_projections = []
    for pivot in pivot_dates:
        projs = project_turn_dates(
            pivot_date=pivot,
            current_date=current_date,
            current_price=current_price,
            wheel_size=wheel_size,
            days_ahead=180
        )
        all_projections.extend(projs)
    
    # Deduplicate projections by date, keep highest score
    seen = {}
    for p in all_projections:
        key = p.projection_date.strftime('%Y-%m-%d')
        if key not in seen or p.score > seen[key].score:
            seen[key] = p
    unique_projections = sorted(seen.values(), key=lambda x: x.days_from_now)
    
    # 3. Current wheel position summary
    time_deg = time_to_degrees(days_elapsed)
    price_deg = price_to_degrees(current_price, wheel_size=wheel_size)
    time_pos = get_position(time_deg)
    price_pos = get_position(price_deg)
    
    # 4. Combined signal
    total_score = multi['combined_score']
    if time_pos.significance == "cardinal":
        total_score += 15
    elif time_pos.significance == "fixed":
        total_score += 10
    if price_pos.significance == "cardinal":
        total_score += 15
    elif price_pos.significance == "fixed":
        total_score += 10
    
    # Generate recommendation
    rec = _generate_wheel_recommendation(
        time_pos, price_pos, total_score, unique_projections[:3]
    )
    
    return {
        'symbol': symbol,
        'analysis_date': current_date.strftime('%Y-%m-%d'),
        'current_price': current_price,
        'pivot_used': recent_pivot.strftime('%Y-%m-%d'),
        'days_from_pivot': days_elapsed,
        'wheel_size': wheel_size,
        'time_degrees': round(time_deg, 2),
        'price_degrees': round(price_deg, 2),
        'time_position': time_pos.to_dict(),
        'price_position': price_pos.to_dict(),
        'multi_wheel': multi,
        'total_score': total_score,
        'signal_strength': (
            "VERY STRONG" if total_score > 150 else
            "STRONG" if total_score > 110 else
            "MODERATE" if total_score > 70 else
            "WEAK"
        ),
        'projections': [p.to_dict() for p in unique_projections[:15]],
        'top_projections': [p.to_dict() for p in unique_projections[:5]],
        'recommendation': rec
    }


def _generate_wheel_recommendation(
    time_pos: WheelPosition,
    price_pos: WheelPosition,
    total_score: int,
    upcoming: List[WheelProjection]
) -> str:
    """Generate trading recommendation from wheel analysis."""
    parts = []
    
    # Time position
    if time_pos.significance == "cardinal":
        parts.append(f"🔴 Time at CARDINAL {time_pos.nearest_critical}° — major cycle inflection point")
    elif time_pos.significance == "fixed":
        parts.append(f"🟡 Time at FIXED {time_pos.nearest_critical}° — secondary cycle point")
    
    # Price position
    if price_pos.significance == "cardinal":
        parts.append(f"🔴 Price at CARDINAL {price_pos.nearest_critical}° — strong support/resistance")
    elif price_pos.significance == "fixed":
        parts.append(f"🟡 Price at FIXED {price_pos.nearest_critical}° — moderate S/R")
    
    # Alignment
    error = abs(time_pos.degrees - price_pos.degrees)
    error = min(error, 360 - error)
    if error <= 5:
        parts.append(f"⚡ PRICE-TIME SQUARE (error {error:.1f}°) — HIGH REVERSAL PROBABILITY")
    elif error <= 15:
        parts.append(f"📐 Price-time approaching square (error {error:.1f}°)")
    
    # Overall
    if total_score > 150:
        parts.append("🎯 VERDICT: STRONG REVERSAL SIGNAL — high conviction setup")
    elif total_score > 110:
        parts.append("📊 VERDICT: Notable cycle point — monitor closely")
    elif total_score > 70:
        parts.append("📈 VERDICT: Moderate signal — normal trading with awareness")
    else:
        parts.append("📋 VERDICT: No major wheel signal — follow trend")
    
    # Next key date
    if upcoming:
        next_proj = upcoming[0]
        parts.append(f"⏰ Next wheel event: {next_proj.description}")
    
    return "\n".join(parts)


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_wheel_report(analysis: Dict) -> str:
    """Generate formatted text report from wheel analysis."""
    lines = []
    lines.append("=" * 70)
    lines.append("  江恩輪中輪 WHEEL OF WHEELS ANALYSIS")
    lines.append("  Based on 小龍's Gann Methodology")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Symbol:      {analysis['symbol']}")
    lines.append(f"  Date:        {analysis['analysis_date']}")
    lines.append(f"  Price:       {analysis['current_price']:,.2f}")
    lines.append(f"  Pivot:       {analysis['pivot_used']} ({analysis['days_from_pivot']} days ago)")
    lines.append(f"  Wheel Size:  {analysis['wheel_size']} price units / 360°")
    lines.append("")
    lines.append("─" * 70)
    lines.append("  WHEEL POSITIONS")
    lines.append("─" * 70)
    lines.append(f"  Time:    {analysis['time_degrees']:>7.2f}°  → nearest {analysis['time_position']['nearest_critical']}° "
                f"({analysis['time_position']['significance']}, {analysis['time_position']['distance_to_critical']:.1f}° away)")
    lines.append(f"  Price:   {analysis['price_degrees']:>7.2f}°  → nearest {analysis['price_position']['nearest_critical']}° "
                f"({analysis['price_position']['significance']}, {analysis['price_position']['distance_to_critical']:.1f}° away)")
    lines.append("")
    
    # Multi-wheel summary
    lines.append("─" * 70)
    lines.append("  MULTI-WHEEL ANALYSIS")
    lines.append("─" * 70)
    mw = analysis['multi_wheel']
    for wheel_key, wheel_data in mw['wheels'].items():
        ws = wheel_data['wheel_size']
        pd = wheel_data['price_degrees']
        td = wheel_data['time_degrees']
        err = wheel_data['alignment_error']
        sc = wheel_data['wheel_score']
        bar = "█" * min(int(sc / 5), 20)
        lines.append(f"  Wheel {ws:>5}: Price {pd:>6.1f}° | Time {td:>6.1f}° | "
                    f"Err {err:>5.1f}° | Score {sc:>3} {bar}")
    lines.append(f"  Combined Score: {mw['combined_score']} ({mw['signal_strength']})")
    lines.append("")
    
    # Signal
    lines.append("─" * 70)
    lines.append("  SIGNAL")
    lines.append("─" * 70)
    lines.append(f"  Total Score:    {analysis['total_score']}")
    lines.append(f"  Strength:       {analysis['signal_strength']}")
    lines.append("")
    
    # Projections
    lines.append("─" * 70)
    lines.append("  UPCOMING WHEEL EVENTS (Next 15)")
    lines.append("─" * 70)
    for i, proj in enumerate(analysis['projections'][:15], 1):
        lines.append(f"  {i:>2}. {proj['projection_date']}  ({proj['days_from_now']:>3}d)  "
                    f"[{proj['projection_type']:<20}]  Score {proj['score']:>2}  "
                    f"{proj['description']}")
    lines.append("")
    
    # Recommendation
    lines.append("─" * 70)
    lines.append("  RECOMMENDATION")
    lines.append("─" * 70)
    for line in analysis['recommendation'].split('\n'):
        lines.append(f"  {line}")
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


# ============================================================================
# CLI / TEST
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  江恩輪中輪 WHEEL OF WHEELS — Test Run")
    print("=" * 70)
    
    # Test with HSI current values
    test_date = datetime(2026, 4, 1)
    test_price = 25261.0
    
    # HSI pivot dates
    pivots = [
        datetime(2020, 3, 23),   # COVID low
        datetime(2021, 2, 17),   # Post-COVID high
        datetime(2022, 10, 31),  # Major low
        datetime(2024, 4, 20),   # 穀雨 bottom
        datetime(2024, 5, 21),   # 小滿 top
        datetime(2024, 10, 8),   # Recent high
    ]
    
    # Run analysis
    result = wheel_of_wheels_analysis(
        symbol="HSI",
        current_price=test_price,
        current_date=test_date,
        pivot_dates=pivots,
        wheel_size=100
    )
    
    # Print report
    report = generate_wheel_report(result)
    print(report)
    
    # Quick summary
    print("\n📊 QUICK SUMMARY:")
    print(f"   Time on wheel: {result['time_degrees']}° (near {result['time_position']['nearest_critical']}°)")
    print(f"   Price on wheel: {result['price_degrees']}° (near {result['price_position']['nearest_critical']}°)")
    print(f"   Signal: {result['signal_strength']} ({result['total_score']} pts)")
    print(f"   Next event: {result['top_projections'][0]['description'] if result['top_projections'] else 'N/A'}")
    print()
