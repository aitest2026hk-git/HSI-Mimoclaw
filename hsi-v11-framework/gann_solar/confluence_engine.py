#!/usr/bin/env python3
"""
Confluence Engine for Gann + Solar Term Analysis
Prototype implementation of 小龍's scoring methodology

This engine combines multiple timing signals and calculates probability scores
for market turning points.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class SignalType(Enum):
    SOLAR_TERM_T1 = "solar_term_tier1"
    SOLAR_TERM_T2 = "solar_term_tier2"
    SOLAR_TERM_T3 = "solar_term_tier3"
    GANN_ANGLE = "gann_angle"
    ANNIVERSARY = "anniversary"
    SQUARE_ROOT = "square_root"
    SQUARE_OF_NINE = "square_of_nine"
    FIBONACCI_TIME = "fibonacci_time"
    SEASONAL = "seasonal"


class ConfidenceLevel(Enum):
    VERY_HIGH = "VERY HIGH (>70)"
    HIGH = "HIGH (50-70)"
    MEDIUM = "MEDIUM (30-50)"
    LOW = "LOW (<30)"


@dataclass
class TimingSignal:
    """Represents a single timing signal from any method."""
    signal_type: SignalType
    date: datetime
    source_description: str
    strength: str  # 'strong', 'medium', 'weak'
    base_points: int
    metadata: Dict = None
    
    def to_dict(self):
        return {
            'signal_type': self.signal_type.value,
            'date': self.date.isoformat(),
            'source_description': self.source_description,
            'strength': self.strength,
            'base_points': self.base_points,
            'metadata': self.metadata or {}
        }


@dataclass
class ConfluenceZone:
    """Represents a time window where multiple signals converge."""
    center_date: datetime
    window_start: datetime
    window_end: datetime
    total_score: int
    confidence: ConfidenceLevel
    signals: List[TimingSignal]
    recommended_action: str
    notes: str = ""
    
    def to_dict(self):
        return {
            'center_date': self.center_date.isoformat(),
            'window_start': self.window_start.isoformat(),
            'window_end': self.window_end.isoformat(),
            'total_score': self.total_score,
            'confidence': self.confidence.value,
            'signals': [s.to_dict() for s in self.signals],
            'recommended_action': self.recommended_action,
            'notes': self.notes
        }


# ============================================================================
# SCORING WEIGHTS (Based on 小龍's methodology)
# ============================================================================

SCORING_WEIGHTS = {
    # Solar Terms (highest priority - astronomical certainty)
    SignalType.SOLAR_TERM_T1: {'base': 30, 'description': 'Tier 1 Solar Term (Equinox/Solstice)'},
    SignalType.SOLAR_TERM_T2: {'base': 20, 'description': 'Tier 2 Solar Term (Season Start)'},
    SignalType.SOLAR_TERM_T3: {'base': 10, 'description': 'Tier 3 Solar Term (Minor)'},
    
    # Gann Methods
    SignalType.GANN_ANGLE: {'base': 25, 'description': 'Gann Major Angle (90°, 180°, 270°, 360°)'},
    SignalType.SQUARE_ROOT: {'base': 15, 'description': 'Square Root Time Cycle'},
    SignalType.SQUARE_OF_NINE: {'base': 12, 'description': 'Square of Nine Projection'},
    
    # Anniversary & Seasonal
    SignalType.ANNIVERSARY: {'base': 18, 'description': 'Anniversary Date (1yr, 2yr, etc.)'},
    SignalType.SEASONAL: {'base': 10, 'description': 'Gann Seasonal Date'},
    
    # Fibonacci (optional enhancement)
    SignalType.FIBONACCI_TIME: {'base': 12, 'description': 'Fibonacci Time Sequence'},
}

# Strength multipliers
STRENGTH_MULTIPLIERS = {
    'strong': 1.5,
    'medium': 1.0,
    'weak': 0.7
}

# Confluence bonus (extra points when multiple signals align)
CONFLUENCE_BONUS = {
    2: 5,    # 2 signals = +5
    3: 12,   # 3 signals = +12
    4: 22,   # 4 signals = +22
    5: 35,   # 5+ signals = +35
}


# ============================================================================
# CONFLUENCE ENGINE
# ============================================================================

class ConfluenceEngine:
    """
    Main engine for calculating confluence zones from timing signals.
    """
    
    def __init__(self, window_days: int = 3):
        """
        Initialize the engine.
        
        Args:
            window_days: Number of days (±) to consider for signal convergence
        """
        self.window_days = window_days
        self.signals: List[TimingSignal] = []
    
    def add_signal(self, signal: TimingSignal):
        """Add a timing signal to the analysis."""
        self.signals.append(signal)
    
    def add_signals(self, signals: List[TimingSignal]):
        """Add multiple timing signals."""
        self.signals.extend(signals)
    
    def clear_signals(self):
        """Clear all signals."""
        self.signals = []
    
    def find_confluence_zones(self, 
                              start_date: datetime, 
                              end_date: datetime,
                              min_score: int = 25) -> List[ConfluenceZone]:
        """
        Scan a date range and find all confluence zones.
        
        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            min_score: Minimum score to include in results
        
        Returns:
            List of ConfluenceZone objects, sorted by score descending
        """
        zones = []
        current = start_date
        
        while current <= end_date:
            # Check if this date has signals within window
            matching_signals = self._find_matching_signals(current)
            
            if matching_signals:
                # Calculate score
                score, adjusted_signals = self._calculate_score(matching_signals)
                
                if score >= min_score:
                    # Determine confidence and action
                    confidence, action = self._get_confidence_level(score)
                    
                    # Create zone
                    zone = ConfluenceZone(
                        center_date=current,
                        window_start=current - timedelta(days=self.window_days),
                        window_end=current + timedelta(days=self.window_days),
                        total_score=score,
                        confidence=confidence,
                        signals=adjusted_signals,
                        recommended_action=action,
                        notes=self._generate_notes(adjusted_signals)
                    )
                    zones.append(zone)
            
            current += timedelta(days=1)
        
        # Sort by score and remove overlapping zones
        zones.sort(key=lambda z: z.total_score, reverse=True)
        zones = self._remove_overlapping_zones(zones)
        
        return zones
    
    def _find_matching_signals(self, target_date: datetime) -> List[TimingSignal]:
        """Find all signals within the window of target date."""
        matching = []
        for signal in self.signals:
            days_diff = abs((target_date - signal.date).days)
            if days_diff <= self.window_days:
                # Create a copy with offset metadata
                signal_copy = TimingSignal(
                    signal_type=signal.signal_type,
                    date=signal.date,
                    source_description=signal.source_description,
                    strength=signal.strength,
                    base_points=signal.base_points,
                    metadata={**(signal.metadata or {}), 'offset_days': days_diff}
                )
                matching.append(signal_copy)
        return matching
    
    def _calculate_score(self, signals: List[TimingSignal]) -> Tuple[int, List[TimingSignal]]:
        """
        Calculate total score for a set of signals.
        
        Returns:
            Tuple of (total_score, adjusted_signals_with_points)
        """
        total = 0
        adjusted = []
        
        for signal in signals:
            # Get base points from weight table
            weight_info = SCORING_WEIGHTS.get(signal.signal_type, {'base': 5})
            base = weight_info['base']
            
            # Apply strength multiplier
            multiplier = STRENGTH_MULTIPLIERS.get(signal.strength, 1.0)
            points = int(base * multiplier)
            
            # Reduce points for offset (further from exact date = less precise)
            offset = signal.metadata.get('offset_days', 0) if signal.metadata else 0
            offset_penalty = max(0, 3 - offset)  # -0, -1, -2, -3 points
            final_points = max(1, points - offset_penalty)
            
            total += final_points
            
            # Store calculated points in signal
            adjusted_signal = TimingSignal(
                signal_type=signal.signal_type,
                date=signal.date,
                source_description=signal.source_description,
                strength=signal.strength,
                base_points=final_points,
                metadata=signal.metadata
            )
            adjusted.append(adjusted_signal)
        
        # Add confluence bonus
        signal_count = len(adjusted)
        bonus = CONFLUENCE_BONUS.get(min(signal_count, 5), 0)
        total += bonus
        
        return total, adjusted
    
    def _get_confidence_level(self, score: int) -> Tuple[ConfidenceLevel, str]:
        """Map score to confidence level and recommended action."""
        if score >= 70:
            return ConfidenceLevel.VERY_HIGH, "STRONG REVERSAL EXPECTED - High conviction trade setup"
        elif score >= 50:
            return ConfidenceLevel.HIGH, "REVERSAL LIKELY - Consider positioning for turn"
        elif score >= 30:
            return ConfidenceLevel.MEDIUM, "VOLATILITY EXPECTED - Watch for opportunities"
        else:
            return ConfidenceLevel.LOW, "NORMAL TRADING - No special action required"
    
    def _generate_notes(self, signals: List[TimingSignal]) -> str:
        """Generate human-readable notes about the confluence."""
        notes = []
        
        # Count by type
        type_counts = {}
        for s in signals:
            type_name = s.signal_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        if 'solar_term_tier1' in type_counts:
            notes.append(f"Major solar term alignment ({type_counts['solar_term_tier1']})")
        if 'gann_angle' in type_counts:
            notes.append(f"Gann angle convergence ({type_counts['gann_angle']})")
        if 'anniversary' in type_counts:
            notes.append(f"Anniversary date(s) ({type_counts['anniversary']})")
        
        # Check for particularly strong combinations
        has_solar = 'solar_term_tier1' in type_counts or 'solar_term_tier2' in type_counts
        has_gann = 'gann_angle' in type_counts or 'square_of_nine' in type_counts
        
        if has_solar and has_gann:
            notes.append("★ East-West alignment: Solar term + Gann method")
        
        return "; ".join(notes) if notes else "Multiple timing signals converge"
    
    def _remove_overlapping_zones(self, zones: List[ConfluenceZone]) -> List[ConfluenceZone]:
        """Remove zones that overlap, keeping the higher-scored one."""
        if not zones:
            return []
        
        result = [zones[0]]
        for zone in zones[1:]:
            # Check if this zone overlaps with any existing
            overlaps = False
            for existing in result:
                if zone.window_start <= existing.window_end and zone.window_end >= existing.window_start:
                    overlaps = True
                    break
            
            if not overlaps:
                result.append(zone)
        
        return result


# ============================================================================
# SIGNAL GENERATORS
# ============================================================================

def generate_solar_term_signals(years: List[int]) -> List[TimingSignal]:
    """Generate solar term signals for given years."""
    from solar_term_calculator import get_solar_terms_for_year
    
    signals = []
    for year in years:
        terms = get_solar_terms_for_year(year)
        for term in terms:
            if term['tier'] == 1:
                sig_type = SignalType.SOLAR_TERM_T1
            elif term['tier'] == 2:
                sig_type = SignalType.SOLAR_TERM_T2
            else:
                sig_type = SignalType.SOLAR_TERM_T3
            
            signals.append(TimingSignal(
                signal_type=sig_type,
                date=term['date'],
                source_description=f"{term['name_cn']} ({term['name_en']}) - {term['gann_angle']}° Gann angle" if term['gann_angle'] else f"{term['name_cn']} ({term['name_en']})",
                strength='strong' if term['tier'] <= 2 else 'medium',
                base_points=SCORING_WEIGHTS[sig_type]['base'],
                metadata={
                    'solar_term_name': term['name_cn'],
                    'tier': term['tier'],
                    'gann_angle': term['gann_angle']
                }
            ))
    return signals


def generate_anniversary_signals(pivot_dates: List[datetime], 
                                  years_ahead: int = 3) -> List[TimingSignal]:
    """Generate anniversary date signals from pivot points."""
    signals = []
    
    for pivot in pivot_dates:
        for year_offset in range(1, years_ahead + 1):
            try:
                anniversary = pivot.replace(year=pivot.year + year_offset)
                signals.append(TimingSignal(
                    signal_type=SignalType.ANNIVERSARY,
                    date=anniversary,
                    source_description=f"{year_offset}-year anniversary of {pivot.strftime('%Y-%m-%d')}",
                    strength='strong' if year_offset <= 2 else 'medium',
                    base_points=SCORING_WEIGHTS[SignalType.ANNIVERSARY]['base'],
                    metadata={
                        'pivot_date': pivot.isoformat(),
                        'year_offset': year_offset
                    }
                ))
                
                # Add 3-month, 6-month, 9-month offsets (Gann seasonal)
                for month_offset in [3, 6, 9]:
                    offset_date = anniversary + timedelta(days=month_offset * 30)
                    signals.append(TimingSignal(
                        signal_type=SignalType.SEASONAL,
                        date=offset_date,
                        source_description=f"{year_offset}yr + {month_offset}mo from {pivot.strftime('%Y-%m-%d')}",
                        strength='medium',
                        base_points=SCORING_WEIGHTS[SignalType.SEASONAL]['base'],
                        metadata={
                            'pivot_date': pivot.isoformat(),
                            'year_offset': year_offset,
                            'month_offset': month_offset
                        }
                    ))
            except ValueError:
                pass  # Skip Feb 29 edge cases
    
    return signals


def generate_gann_cycle_signals(pivot_dates: List[datetime],
                                 reference_date: datetime = None) -> List[TimingSignal]:
    """Generate Gann square root and square of nine signals."""
    from solar_term_calculator import calculate_square_root_cycles, calculate_gann_square_of_nine
    import math
    
    if reference_date is None:
        reference_date = datetime.now()
    
    signals = []
    
    for pivot in pivot_dates:
        days_elapsed = (reference_date - pivot).days
        if days_elapsed <= 0:
            continue
        
        # Square root cycles
        sqrt_cycles = calculate_square_root_cycles(pivot, reference_date)
        for cycle in sqrt_cycles[:10]:  # Limit to next 10 cycles
            signals.append(TimingSignal(
                signal_type=SignalType.SQUARE_ROOT,
                date=cycle['date'],
                source_description=f"Sqrt cycle {cycle['type']} from {pivot.strftime('%Y-%m-%d')}",
                strength=cycle.get('strength', 'medium'),
                base_points=SCORING_WEIGHTS[SignalType.SQUARE_ROOT]['base'],
                metadata={
                    'pivot_date': pivot.isoformat(),
                    'cycle_type': cycle['type'],
                    'days_from_pivot': cycle['days_from_pivot']
                }
            ))
        
        # Square of Nine
        gann_projs = calculate_gann_square_of_nine(pivot, days_elapsed)
        for proj in gann_projs[:12]:  # Limit projections
            signals.append(TimingSignal(
                signal_type=SignalType.SQUARE_OF_NINE,
                date=proj['date'],
                source_description=f"Gann Square {proj['type']} from {pivot.strftime('%Y-%m-%d')}",
                strength=proj.get('strength', 'medium'),
                base_points=SCORING_WEIGHTS[SignalType.SQUARE_OF_NINE]['base'],
                metadata={
                    'pivot_date': pivot.isoformat(),
                    'projection_type': proj['type'],
                    'angle': proj.get('angle'),
                    'days_from_pivot': proj['days_from_pivot']
                }
            ))
    
    return signals


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_confluence_report(zones: List[ConfluenceZone], 
                                title: str = "Confluence Analysis Report") -> str:
    """Generate a formatted text report of confluence zones."""
    lines = []
    lines.append("=" * 80)
    lines.append(title)
    lines.append("Based on 江恩小龍's Gann + Solar Term Methodology")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Total Zones Found: {len(zones)}")
    lines.append("")
    
    # Summary by confidence
    confidence_counts = {}
    for z in zones:
        conf = z.confidence.value.split()[0]
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    
    lines.append("CONFIDENCE DISTRIBUTION:")
    for conf, count in sorted(confidence_counts.items()):
        lines.append(f"  {conf}: {count} zones")
    lines.append("")
    
    # Detailed zones
    lines.append("-" * 80)
    lines.append("TOP CONFLUENCE ZONES (Sorted by Score)")
    lines.append("-" * 80)
    
    for i, zone in enumerate(zones[:20], 1):
        lines.append("")
        lines.append(f"#{i}: {zone.center_date.strftime('%Y-%m-%d (%A)')}")
        lines.append(f"    Window: {zone.window_start.strftime('%m-%d')} to {zone.window_end.strftime('%m-%d')}")
        lines.append(f"    Score: {zone.total_score} | Confidence: {zone.confidence.value}")
        lines.append(f"    Action: {zone.recommended_action}")
        
        if zone.notes:
            lines.append(f"    Notes: {zone.notes}")
        
        lines.append("    Signals:")
        for sig in zone.signals[:6]:  # Show top 6 signals
            date_str = sig.date.strftime('%m-%d')
            offset = sig.metadata.get('offset_days', 0) if sig.metadata else 0
            offset_str = f" (+{offset}d)" if offset > 0 else ""
            lines.append(f"      • [{sig.base_points}pts] {sig.source_description}{offset_str}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def export_zones_json(zones: List[ConfluenceZone], filepath: str):
    """Export zones to JSON file."""
    data = {
        'generated_at': datetime.now().isoformat(),
        'methodology': 'Gann + Solar Term Confluence (江恩小龍)',
        'total_zones': len(zones),
        'zones': [z.to_dict() for z in zones]
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# ============================================================================
# MAIN EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("Initializing Confluence Engine...")
    
    engine = ConfluenceEngine(window_days=3)
    
    # Generate signals
    print("Generating solar term signals for 2026-2027...")
    solar_signals = generate_solar_term_signals([2026, 2027])
    engine.add_signals(solar_signals)
    
    print("Generating anniversary signals...")
    pivot_dates = [
        datetime(2020, 3, 23),   # COVID low
        datetime(2022, 10, 24),  # 2022 low
        datetime(2024, 4, 20),   # Guyu 2024 bottom
        datetime(2024, 5, 21),   # Xiaoman 2024 top
        datetime(2025, 1, 15),   # Example recent pivot
    ]
    anniversary_signals = generate_anniversary_signals(pivot_dates, years_ahead=3)
    engine.add_signals(anniversary_signals)
    
    print("Generating Gann cycle signals...")
    gann_signals = generate_gann_cycle_signals(pivot_dates)
    engine.add_signals(gann_signals)
    
    print(f"Total signals loaded: {len(engine.signals)}")
    print("")
    
    # Find confluence zones
    print("Scanning for confluence zones in 2026...")
    zones = engine.find_confluence_zones(
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31),
        min_score=25
    )
    
    print(f"Found {len(zones)} confluence zones")
    print("")
    
    # Generate report
    report = generate_confluence_report(zones, "2026 Market Turn Window Analysis")
    print(report)
    
    # Export to JSON
    export_zones_json(zones, '/root/.openclaw/workspace/gann_solar/confluence_zones_2026.json')
    print("\nJSON export saved to: confluence_zones_2026.json")
