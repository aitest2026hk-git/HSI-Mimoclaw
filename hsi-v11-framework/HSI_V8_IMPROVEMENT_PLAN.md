# HSI Model v8 - Improvement Plan

**Based on Research:** 2026-02-22  
**Target Accuracy:** 55-60% (realistic), 65% (stretch)

---

## 📊 Research Findings Summary

### Gann Theory Best Practices:
- **Time cycles work better than price levels** for prediction timing
- **Anniversary dates** (1, 2, 3, 5, 7 years) show statistical significance
- **Square of 9** most effective for support/resistance identification
- **Gann angles** (1x1, 2x1, 1x2) useful for trend identification
- **Key insight:** Gann signals should be BINARY (on/off near dates), not continuous

### Kondratiev Wave Limitations:
- **Too slow for 90-day predictions** - K-Wave operates on 10-15 year cycles
- **Better as long-term bias filter** than directional signal
- **Current phase (Spring 2020-2035)** = generally bullish but doesn't predict short-term moves
- **Recommendation:** Reduce K-Wave weight or use only as tiebreaker

### Walk-Forward Optimization (WFO):
- **Rolling window approach** prevents overfitting
- **Standard pattern:** 5-year in-sample, 1-year out-of-sample, roll forward annually
- **Multiple OOS tests** = more realistic performance estimate
- **Key benefit:** Adapts to changing market conditions

### Market Regime Detection:
- **Three main regimes:** Trending (up/down), Ranging, Volatile
- **Simple detection:** ADX > 25 = trending, ADX < 20 = ranging
- **Alternative:** Volatility ratio (recent vs historical) + moving average slope
- **Regime-specific rules:** Different signal weights per regime

### On-Balance Volume (OBV):
- **Volume confirms price** - OBV trending with price = strong signal
- **Divergence is key** - Price up + OBV down = warning sign
- **Best as filter** not primary signal
- **Combine with moving average** on OBV for cleaner signals

---

## 🔧 v8 Improvements (Priority Order)

### 1. Walk-Forward Backtest Framework ⭐⭐⭐
**Problem:** Static backtest doesn't reflect real-world performance  
**Solution:** Implement rolling 5-year train / 1-year test cycles

```python
# WFO Cycles for our data (2020-2026):
# Cycle 1: Train 2015-2019, Test 2020
# Cycle 2: Train 2016-2020, Test 2021
# Cycle 3: Train 2017-2021, Test 2022
# Cycle 4: Train 2018-2022, Test 2023
# Cycle 5: Train 2019-2023, Test 2024
# Cycle 6: Train 2020-2024, Test 2025
# Cycle 7: Train 2021-2025, Test 2026 (partial)
```

**Expected Impact:** More realistic accuracy estimate, may show lower but more trustworthy numbers

### 2. Regime-Adaptive Signal Weights ⭐⭐⭐
**Problem:** Same weights used in all market conditions  
**Solution:** Adjust weights based on detected regime

| Regime | Detection | Gann Weight | Technical Weight | Trend Weight |
|--------|-----------|-------------|------------------|--------------|
| Strong Uptrend | ADX>25, SMA50>SMA200 | 0.6 | 0.2 | 0.8 |
| Strong Downtrend | ADX>25, SMA50<SMA200 | 0.6 | 0.2 | 0.8 |
| Ranging | ADX<20, flat MAs | 0.9 | 0.3 | 0.2 |
| Volatile | ATR > 2x normal | 0.5 | 0.4 | 0.3 |

**Expected Impact:** +5-10% accuracy by matching strategy to market state

### 3. OBV Volume Confirmation ⭐⭐
**Problem:** No volume analysis in current model  
**Solution:** Add OBV trend as confirmation filter

```python
# OBV Rules:
- OBV rising + Price rising = Bullish confirmation (+0.2 weight)
- OBV falling + Price falling = Bearish confirmation (+0.2 weight)
- OBV rising + Price falling = Divergence (bullish reversal signal)
- OBV falling + Price rising = Divergence (bearish reversal signal)
- OBV flat = No signal
```

**Expected Impact:** +3-5% accuracy, better false positive filtering

### 4. Simplified K-Wave Usage ⭐
**Problem:** K-Wave too slow for 90-day predictions, diluting signal  
**Solution:** Use only as long-term bias tiebreaker

```python
# New K-Wave logic:
- If all other signals neutral → Use K-Wave phase as tiebreaker
- If strong Gann signals present → Ignore K-Wave (too slow)
- Weight: 0.3 max (down from 0.8)
```

**Expected Impact:** Cleaner signals, less noise from slow cycle

### 5. Improved Gann Time Cycles ⭐⭐⭐
**Problem:** Current implementation too many overlapping signals  
**Solution:** Focus on high-probability windows only

```python
# Refined anniversary windows:
- Major cycles (5, 7 year): ±15 days window, weight 1.0
- Medium cycles (2, 3 year): ±10 days window, weight 0.7
- Minor cycles (1 year): ±7 days window, weight 0.5
- 90/180 day: Remove (too many false signals)
```

**Expected Impact:** Fewer but higher-quality signals, +5-8% accuracy

### 6. Confidence Calibration ⭐⭐
**Problem:** Confidence scores don't match actual accuracy  
**Solution:** Calibrate confidence bins with historical data

```python
# Target calibration:
- 50-60% confidence → Should be ~55% accurate
- 60-70% confidence → Should be ~65% accurate
- 70-80% confidence → Should be ~75% accurate
- 80%+ confidence → Should be ~80%+ accurate
```

**Expected Impact:** More trustworthy confidence scores

---

## 📈 Expected v8 Performance

| Metric | v7 Actual | v8 Target | Improvement |
|--------|-----------|-----------|-------------|
| Overall Accuracy | 30.7% | 55-60% | +25-30 pts |
| High Conf Accuracy | 35.3% | 70%+ | +35 pts |
| Major Drop Recall | 0% | 50%+ | +50 pts |
| Major Rally Recall | 25% | 50%+ | +25 pts |
| Prediction Rate | 100% | 70% (more selective) | -30 pts* |

*Lower prediction rate = more selective, higher quality signals

---

## 🚀 Implementation Plan

### Phase 1: Core Improvements (24 hours)
1. ✅ Implement walk-forward backtest framework
2. ✅ Add regime detection (ADX + MA slope)
3. ✅ Refine Gann time cycle windows
4. ✅ Reduce K-Wave weight

### Phase 2: Volume & Calibration (24 hours)
5. ✅ Add OBV calculation and signals
6. ✅ Implement regime-adaptive weights
7. ✅ Calibrate confidence scoring
8. ✅ Run full WFO backtest

### Phase 3: Validation (12 hours)
9. ✅ Compare v8 vs v7 on same test periods
10. ✅ Document results
11. ✅ Generate current market analysis
12. ✅ Create deployment recommendations

---

## 📝 Key Research Sources

1. **Gann Theory:** Investopedia, TradingView, Bramesh Technical Analysis
2. **K-Wave:** Corporate Finance Institute, Investopedia, academic papers
3. **Walk-Forward:** QuantInsti blog, Wikipedia, QuantConnect docs
4. **Regime Detection:** Medium (Coding Nexus), QuantStart, Reddit r/algotrading
5. **OBV:** Investopedia, NinjaTrader, StockCharts

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Overfitting to recent data | WFO framework with multiple OOS tests |
| Too many parameters | Keep model simple, document each parameter |
| Look-ahead bias | Strict separation of train/test data |
| Regime detection lag | Use multiple confirmation signals |
| Volume data quality | Verify HSI volume data reliability |

---

**Next Step:** Implement v8 with these improvements and run full backtest.
