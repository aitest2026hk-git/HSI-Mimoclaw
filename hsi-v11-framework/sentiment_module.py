#!/usr/bin/env python3
"""
Sentiment Scoring Module — 小龍's Contrarian Indicator
Based on: "當所有人都不敢買樓，就是見底的時間"
(When everyone is afraid to buy, that's the bottom)

Combines multiple sentiment sources into a single score:
1. Crypto Fear & Greed Index (alternative.me — free, live)
2. VIX Level & Trend
3. Put/Call Ratio (config-based)
4. CNN Fear & Greed (scraped, when available)
5. AAII Sentiment Survey (weekly)

Integrates with:
- gann_enhanced_module.py (confluence scoring)
- stock_cycling_analyzer_enhanced.py (macro adjustment)
- gann_wheel_of_wheels.py (turn date confirmation)
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class SentimentLevel(Enum):
    EXTREME_FEAR = "EXTREME_FEAR"
    FEAR = "FEAR"
    NEUTRAL = "NEUTRAL"
    GREED = "GREED"
    EXTREME_GREED = "EXTREME_GREED"


@dataclass
class SentimentReading:
    """A single sentiment reading from one source."""
    source: str
    value: float            # 0-100 scale
    label: str              # Human-readable label
    timestamp: datetime
    raw_value: float = 0    # Original value before normalization
    raw_unit: str = ""      # Original unit (%, ratio, index)
    weight: float = 1.0     # Weight in combined score
    
    def to_dict(self):
        return {
            'source': self.source,
            'value': round(self.value, 1),
            'label': self.label,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M'),
            'raw_value': self.raw_value,
            'raw_unit': self.raw_unit,
            'weight': self.weight
        }


@dataclass
class SentimentSignal:
    """A contrarian trading signal derived from sentiment."""
    signal: str             # "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
    score: float            # Combined sentiment score (0-100)
    level: SentimentLevel
    description: str
    contrarian_bias: str    # "bullish", "neutral", "bearish"
    confluence_points: int  # Points to add to Gann confluence
    components: List[SentimentReading] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'signal': self.signal,
            'score': round(self.score, 1),
            'level': self.level.value,
            'description': self.description,
            'contrarian_bias': self.contrarian_bias,
            'confluence_points': self.confluence_points,
            'components': [c.to_dict() for c in self.components]
        }


# ============================================================================
# SENTIMENT THRESHOLDS
# ============================================================================

# Fear & Greed scale (0-100)
FEAR_GREED_THRESHOLDS = {
    (0, 25):   SentimentLevel.EXTREME_FEAR,
    (25, 45):  SentimentLevel.FEAR,
    (45, 55):  SentimentLevel.NEUTRAL,
    (55, 75):  SentimentLevel.GREED,
    (75, 101): SentimentLevel.EXTREME_GREED,
}

# VIX thresholds
VIX_THRESHOLDS = {
    (0, 12):   "COMPLACENT",
    (12, 18):  "LOW",
    (18, 25):  "NORMAL",
    (25, 35):  "ELEVATED",
    (35, 50):  "HIGH_FEAR",
    (50, 999): "EXTREME_PANIC",
}

# Put/Call ratio thresholds (CBOE)
PUT_CALL_THRESHOLDS = {
    (0.0, 0.7):  "EXTREME_GREED",
    (0.7, 0.9):  "GREED",
    (0.9, 1.1):  "NEUTRAL",
    (1.1, 1.3):  "FEAR",
    (1.3, 99.0): "EXTREME_FEAR",
}


# ============================================================================
# DATA FETCHERS
# ============================================================================

def fetch_crypto_fear_greed(limit: int = 30) -> List[SentimentReading]:
    """
    Fetch Crypto Fear & Greed Index from alternative.me (free, no key).
    
    Returns historical readings for trend analysis.
    """
    import urllib.request
    import ssl
    
    url = f"https://api.alternative.me/fng/?limit={limit}&format=json"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        readings = []
        for entry in data.get('data', []):
            value = int(entry['value'])
            ts = datetime.fromtimestamp(int(entry['timestamp']))
            label = entry.get('value_classification', _classify_fear_greed(value))
            
            readings.append(SentimentReading(
                source="crypto_fear_greed",
                value=value,
                label=label,
                timestamp=ts,
                raw_value=value,
                raw_unit="index",
                weight=0.8  # Crypto sentiment = 0.8 weight (correlated but not identical)
            ))
        
        return readings
    
    except Exception as e:
        print(f"  ⚠️ Crypto Fear & Greed fetch failed: {e}")
        return []


def fetch_vix_reading(vix_value: float) -> SentimentReading:
    """
    Create a sentiment reading from VIX value.
    
    VIX interpretation:
    - < 12: Complacent (greed)
    - 12-18: Low fear (mild greed)
    - 18-25: Normal
    - 25-35: Elevated fear
    - 35-50: High fear
    - > 50: Extreme panic
    """
    # Convert VIX to 0-100 fear scale (inverse: high VIX = high fear)
    # VIX 10 → ~10 (low fear), VIX 40 → ~80 (high fear)
    fear_score = min(100, max(0, (vix_value - 10) / 40 * 100))
    
    # Classify
    label = "UNKNOWN"
    for (lo, hi), level in VIX_THRESHOLDS.items():
        if lo <= vix_value < hi:
            label = level
            break
    
    return SentimentReading(
        source="vix",
        value=fear_score,
        label=label,
        timestamp=datetime.now(),
        raw_value=vix_value,
        raw_unit="VIX",
        weight=1.0  # VIX = full weight (most reliable for stocks)
    )


def create_put_call_reading(ratio: float) -> SentimentReading:
    """
    Create sentiment reading from Put/Call ratio.
    
    High P/C = fear (more puts = hedging/bearish)
    Low P/C = greed (more calls = bullish bets)
    """
    # Convert to 0-100 fear scale
    # P/C 0.5 → ~10, P/C 1.5 → ~90
    fear_score = min(100, max(0, (ratio - 0.5) / 1.0 * 100))
    
    label = "UNKNOWN"
    for (lo, hi), level in PUT_CALL_THRESHOLDS.items():
        if lo <= ratio < hi:
            label = level
            break
    
    return SentimentReading(
        source="put_call_ratio",
        value=fear_score,
        label=label,
        timestamp=datetime.now(),
        raw_value=ratio,
        raw_unit="ratio",
        weight=0.9
    )


def create_manual_reading(source: str, value: float, unit: str = "", 
                           weight: float = 1.0) -> SentimentReading:
    """
    Create a reading from manually entered data.
    Used for AAII survey, CNN F&G, or custom inputs.
    """
    label = _classify_fear_greed(value) if unit == "index" else f"{value}{unit}"
    
    return SentimentReading(
        source=source,
        value=value,
        label=label,
        timestamp=datetime.now(),
        raw_value=value,
        raw_unit=unit,
        weight=weight
    )


# ============================================================================
# CORE ANALYSIS
# ============================================================================

def _classify_fear_greed(value: float) -> str:
    """Classify a 0-100 fear/greed value."""
    if value <= 25:
        return "Extreme Fear"
    elif value <= 45:
        return "Fear"
    elif value <= 55:
        return "Neutral"
    elif value <= 75:
        return "Greed"
    else:
        return "Extreme Greed"


def calculate_sentiment_level(score: float) -> SentimentLevel:
    """Map a 0-100 score to a SentimentLevel."""
    for (lo, hi), level in FEAR_GREED_THRESHOLDS.items():
        if lo <= score < hi:
            return level
    return SentimentLevel.NEUTRAL


def analyze_sentiment(readings: List[SentimentReading]) -> SentimentSignal:
    """
    Combine multiple sentiment readings into a single contrarian signal.
    
    小龍's principle: Extreme fear = bottom (buy), Extreme greed = top (sell)
    """
    if not readings:
        return SentimentSignal(
            signal="HOLD",
            score=50,
            level=SentimentLevel.NEUTRAL,
            description="No sentiment data available",
            contrarian_bias="neutral",
            confluence_points=0
        )
    
    # Weighted average
    total_weight = sum(r.weight for r in readings)
    weighted_sum = sum(r.value * r.weight for r in readings)
    combined_score = weighted_sum / total_weight if total_weight > 0 else 50
    
    # Determine level
    level = calculate_sentiment_level(combined_score)
    
    # 小龍's contrarian logic:
    # HIGH fear (low score) = BULLISH signal (bottom fishing)
    # HIGH greed (high score) = BEARISH signal (distribution)
    
    if combined_score <= 15:
        signal = "STRONG_BUY"
        bias = "strongly_bullish"
        desc = "🔥 EXTREME FEAR — 小龍's bottom signal active. When all are afraid = buy."
        points = 25
    elif combined_score <= 30:
        signal = "BUY"
        bias = "bullish"
        desc = "📈 FEAR dominant — Contrarian bullish. Accumulate quality names."
        points = 18
    elif combined_score <= 45:
        signal = "HOLD"
        bias = "mildly_bullish"
        desc = "🟡 Mild fear — Cautious optimism. Selective buying."
        points = 10
    elif combined_score <= 55:
        signal = "HOLD"
        bias = "neutral"
        desc = "⚖️ NEUTRAL — No strong contrarian signal. Follow trend."
        points = 0
    elif combined_score <= 75:
        signal = "HOLD"
        bias = "mildly_bearish"
        desc = "🟡 Mild greed — Caution warranted. Tighten stops."
        points = -5
    elif combined_score <= 90:
        signal = "SELL"
        bias = "bearish"
        desc = "📉 GREED dominant — Distribution zone. Reduce exposure."
        points = -15
    else:
        signal = "STRONG_SELL"
        bias = "strongly_bearish"
        desc = "🔴 EXTREME GREED — Euphoria detected. Major top risk."
        points = -25
    
    return SentimentSignal(
        signal=signal,
        score=combined_score,
        level=level,
        description=desc,
        contrarian_bias=bias,
        confluence_points=points,
        components=readings
    )


def analyze_sentiment_trend(readings: List[SentimentReading], 
                             lookback_days: int = 14) -> Dict:
    """
    Analyze sentiment trend over time.
    
    Key patterns:
    - Prolonged extreme fear (>14 days) = strong bottom signal
    - Rapid sentiment shift = trend change coming
    - Divergence (price up, sentiment down) = warning
    """
    if len(readings) < 2:
        return {"trend": "insufficient_data", "pattern": "none"}
    
    # Sort by date
    sorted_readings = sorted(readings, key=lambda r: r.timestamp)
    
    # Recent readings (last N days)
    cutoff = datetime.now() - timedelta(days=lookback_days)
    recent = [r for r in sorted_readings if r.timestamp >= cutoff]
    
    if len(recent) < 2:
        return {"trend": "insufficient_data", "pattern": "none"}
    
    values = [r.value for r in recent]
    avg = sum(values) / len(values)
    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]
    avg_first = sum(first_half) / len(first_half) if first_half else avg
    avg_second = sum(second_half) / len(second_half) if second_half else avg
    
    # Trend direction
    delta = avg_second - avg_first
    if delta > 5:
        trend = "improving"
    elif delta < -5:
        trend = "deteriorating"
    else:
        trend = "stable"
    
    # Pattern detection
    days_in_extreme_fear = sum(1 for v in values if v <= 20)
    days_in_extreme_greed = sum(1 for v in values if v >= 80)
    
    pattern = "none"
    if days_in_extreme_fear >= 14:
        pattern = "prolonged_extreme_fear"
    elif days_in_extreme_greed >= 14:
        pattern = "prolonged_extreme_greed"
    elif all(v <= 15 for v in values[-5:]):
        pattern = "deepening_fear"
    elif all(v >= 85 for v in values[-5:]):
        pattern = "intensifying_greed"
    
    # Mean reversion probability
    if avg <= 15:
        reversion = "high_probability_bounce"
    elif avg >= 85:
        reversion = "high_probability_reversal"
    else:
        reversion = "normal"
    
    return {
        "trend": trend,
        "trend_delta": round(delta, 1),
        "average": round(avg, 1),
        "current": values[-1],
        "lookback_days": lookback_days,
        "data_points": len(recent),
        "days_in_extreme_fear": days_in_extreme_fear,
        "days_in_extreme_greed": days_in_extreme_greed,
        "pattern": pattern,
        "mean_reversion": reversion,
        "interpretation": _interpret_trend(trend, pattern, avg, days_in_extreme_fear)
    }


def _interpret_trend(trend: str, pattern: str, avg: float, 
                      extreme_fear_days: int) -> str:
    """Generate human-readable trend interpretation."""
    parts = []
    
    if pattern == "prolonged_extreme_fear":
        parts.append(f"🔴 {extreme_fear_days}+ days in Extreme Fear — per 小龍's methodology, this is a STRONG bottom signal. "
                    "When all are afraid for an extended period, the selling climax is near.")
    elif pattern == "deepening_fear":
        parts.append("📉 Fear deepening — sentiment getting worse. Watch for capitulation volume.")
    elif pattern == "prolonged_extreme_greed":
        parts.append("🟢 Extended extreme greed — euphoria phase. Distribution recommended.")
    elif pattern == "intensifying_greed":
        parts.append("📈 Greed intensifying — late-stage rally behavior.")
    
    if trend == "improving" and avg < 30:
        parts.append("📊 Sentiment improving from extreme lows — early recovery signal.")
    elif trend == "deteriorating" and avg > 70:
        parts.append("📊 Sentiment deteriorating from highs — topping process.")
    
    return " | ".join(parts) if parts else "No strong pattern detected."


# ============================================================================
# INTEGRATION WITH GANN CONFLUENCE
# ============================================================================

def sentiment_to_confluence(sentiment: SentimentSignal) -> Dict:
    """
    Convert sentiment signal to confluence scoring format.
    
    小龍's sentiment adds up to ±25 points to the Gann confluence score.
    """
    return {
        "source": "Sentiment (小龍 Contrarian)",
        "points": sentiment.confluence_points,
        "signal": sentiment.signal,
        "level": sentiment.level.value,
        "description": sentiment.description,
        "weight": abs(sentiment.confluence_points) / 25.0  # Normalized 0-1
    }


def enrich_wheel_analysis(wheel_result: Dict, sentiment: SentimentSignal) -> Dict:
    """
    Add sentiment context to Wheel of Wheels analysis.
    
    When wheel shows reversal + sentiment is extreme = highest conviction.
    """
    wheel_score = wheel_result.get('total_score', 0)
    sent_score = sentiment.score
    
    # Conviction matrix
    is_wheel_reversal = wheel_score > 150
    is_extreme_sentiment = sent_score <= 20 or sent_score >= 80
    
    if is_wheel_reversal and is_extreme_sentiment:
        conviction = "VERY HIGH"
        note = "🎯 Wheel reversal + Extreme sentiment = Highest conviction setup"
    elif is_wheel_reversal:
        conviction = "HIGH"
        note = "📐 Wheel reversal active, sentiment moderate"
    elif is_extreme_sentiment:
        conviction = "MODERATE-HIGH"
        note = f"📊 Extreme sentiment ({sentiment.level.value}), wheel not yet signaling"
    else:
        conviction = "MODERATE"
        note = "No strong combined signal"
    
    wheel_result['sentiment_enrichment'] = {
        'sentiment_score': sent_score,
        'sentiment_level': sentiment.level.value,
        'sentiment_signal': sentiment.signal,
        'combined_conviction': conviction,
        'note': note
    }
    
    return wheel_result


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_sentiment_report(signal: SentimentSignal, 
                               trend: Dict = None) -> str:
    """Generate formatted sentiment analysis report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  📊 SENTIMENT ANALYSIS — 小龍's Contrarian Indicator")
    lines.append("  '當所有人都不敢買樓，就是見底的時間'")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Combined Score:  {signal.score:.1f} / 100")
    lines.append(f"  Level:           {signal.level.value}")
    lines.append(f"  Signal:          {signal.signal}")
    lines.append(f"  Contrarian Bias: {signal.contrarian_bias}")
    lines.append(f"  Confluence Pts:  {signal.confluence_points:+d}")
    lines.append("")
    lines.append(f"  {signal.description}")
    lines.append("")
    
    # Components
    if signal.components:
        lines.append("─" * 70)
        lines.append("  COMPONENTS")
        lines.append("─" * 70)
        for comp in signal.components:
            lines.append(f"  {comp.source:<25} {comp.value:>5.1f}/100  {comp.label:<18} "
                        f"(raw: {comp.raw_value}{comp.raw_unit}, weight: {comp.weight})")
        lines.append("")
    
    # Trend
    if trend and trend.get('trend') != 'insufficient_data':
        lines.append("─" * 70)
        lines.append("  TREND ANALYSIS")
        lines.append("─" * 70)
        lines.append(f"  Trend:           {trend['trend']} (Δ{trend['trend_delta']:+.1f})")
        lines.append(f"  Average:         {trend['average']:.1f} (last {trend['lookback_days']}d)")
        lines.append(f"  Current:         {trend['current']:.1f}")
        lines.append(f"  Ext.Fear Days:   {trend['days_in_extreme_fear']}")
        lines.append(f"  Ext.Greed Days:  {trend['days_in_extreme_greed']}")
        lines.append(f"  Pattern:         {trend['pattern']}")
        lines.append(f"  Mean Reversion:  {trend['mean_reversion']}")
        lines.append("")
        lines.append(f"  {trend['interpretation']}")
        lines.append("")
    
    # Fear/Greed scale visualization
    lines.append("─" * 70)
    lines.append("  FEAR ←→ GREED SCALE")
    lines.append("─" * 70)
    bar_pos = int(signal.score / 100 * 50)
    bar = "░" * bar_pos + "█" + "░" * (50 - bar_pos)
    lines.append(f"  0{'─'*20}25{'─'*9}50{'─'*9}75{'─'*10}100")
    lines.append(f"  │{' '*bar_pos}▼{' '*(49-bar_pos)}│")
    lines.append(f"  │{bar}│")
    lines.append(f"  EXTREME  FEAR      NEUTRAL    GREED   EXTREME")
    lines.append(f"  FEAR                              GREED")
    lines.append(f"  {' '*max(0,bar_pos-1)}{signal.score:.0f}")
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def run_sentiment_analysis(vix_value: float = None,
                            put_call_ratio: float = None,
                            custom_readings: List[SentimentReading] = None,
                            fetch_live: bool = True) -> Dict:
    """
    Run complete sentiment analysis.
    
    Args:
        vix_value: Current VIX level (if known)
        put_call_ratio: Current CBOE Put/Call ratio (if known)
        custom_readings: Additional manual readings
        fetch_live: Whether to fetch live crypto Fear & Greed
    
    Returns:
        Complete sentiment analysis dict
    """
    print("\n📊 Running Sentiment Analysis...")
    
    readings = []
    
    # 1. Live crypto Fear & Greed
    if fetch_live:
        print("  Fetching Crypto Fear & Greed...")
        crypto_readings = fetch_crypto_fear_greed(limit=30)
        if crypto_readings:
            readings.extend(crypto_readings)
            print(f"  ✅ Got {len(crypto_readings)} days of crypto F&G data")
            print(f"     Latest: {crypto_readings[0].value} ({crypto_readings[0].label})")
    
    # 2. VIX
    if vix_value is not None:
        vix_reading = fetch_vix_reading(vix_value)
        readings.append(vix_reading)
        print(f"  ✅ VIX: {vix_value} → Fear score {vix_reading.value:.1f} ({vix_reading.label})")
    
    # 3. Put/Call
    if put_call_ratio is not None:
        pc_reading = create_put_call_reading(put_call_ratio)
        readings.append(pc_reading)
        print(f"  ✅ Put/Call: {put_call_ratio} → Fear score {pc_reading.value:.1f} ({pc_reading.label})")
    
    # 4. Custom readings
    if custom_readings:
        readings.extend(custom_readings)
        print(f"  ✅ Added {len(custom_readings)} custom readings")
    
    # Current readings only (for signal)
    current_readings = []
    if fetch_live and crypto_readings:
        current_readings.append(crypto_readings[0])  # Most recent
    if vix_value is not None:
        current_readings.append(vix_reading)
    if put_call_ratio is not None:
        current_readings.append(pc_reading)
    if custom_readings:
        current_readings.extend(custom_readings)
    
    # Generate signal
    print("\n  Calculating contrarian signal...")
    signal = analyze_sentiment(current_readings)
    
    # Trend analysis (use all crypto readings)
    print("  Analyzing trend...")
    trend = None
    if crypto_readings:
        trend = analyze_sentiment_trend(crypto_readings, lookback_days=30)
    
    # Generate report
    report = generate_sentiment_report(signal, trend)
    
    # Confluence integration
    confluence = sentiment_to_confluence(signal)
    
    return {
        'signal': signal.to_dict(),
        'trend': trend,
        'confluence': confluence,
        'readings_count': len(readings),
        'report': report
    }


# ============================================================================
# CLI / TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  📊 SENTIMENT MODULE — Live Test")
    print("=" * 70)
    
    # Run with live data + manual VIX
    result = run_sentiment_analysis(
        vix_value=24.48,           # From Apr 1 daily log
        put_call_ratio=1.33,       # From 小龍's post
        fetch_live=True
    )
    
    print(result['report'])
    
    # Show confluence integration
    print("\n🔗 CONFLUENCE INTEGRATION:")
    conf = result['confluence']
    print(f"   Source: {conf['source']}")
    print(f"   Points: {conf['points']:+d}")
    print(f"   Signal: {conf['signal']}")
    print(f"   → Adds to Gann confluence score")
    
    if result['trend']:
        print(f"\n📈 TREND: {result['trend']['trend']} (pattern: {result['trend']['pattern']})")
        print(f"   {result['trend']['interpretation']}")
    
    print()
