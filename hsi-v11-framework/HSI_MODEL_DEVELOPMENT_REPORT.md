# HSI Model Development - Comprehensive Report

**Date:** 2026-02-22  
**Models Tested:** v1 through v9  
**Target Accuracy:** 65% (stretch), 55-60% (realistic)  
**Current Best:** v9 at 38.8% (walk-forward validated)

---

## 📊 Executive Summary

After extensive development and testing of 9 model iterations, **the 65% accuracy target at 90-day prediction horizon is not achievable** with the current approach. The best validated accuracy is **38.8%** (v9, trend-following), which is below the 50% random baseline for 3-class prediction.

**Key Finding:** 90-day directional prediction using technical analysis, Gann theory, and Kondratiev waves shows **no statistical edge** over random guessing in walk-forward testing.

---

## 📈 Model Evolution Summary

| Version | Approach | Accuracy | High Conf Acc | Key Issue |
|---------|----------|----------|---------------|-----------|
| v1 | Basic Gann + K-Wave | 34.7% | N/A | Too simple |
| v2 | Added bullish signals | 50.7%* | N/A | *Overfitted (no WFO) |
| v3 | Ensemble (RSI, MACD, Bollinger) | 52.0%* | N/A | *Overfitted |
| v4 | Confluence filtering | 48.0%* | N/A | Too few signals |
| v5 | Weight learning | 0%* | N/A | No predictions generated |
| v6 | Simplified Gann + K-Wave | 32.0% | N/A | Too many NEUTRAL calls |
| v7 | Calibrated thresholds | 30.7% | 35.3% | Worse than v6 |
| v8 | WFO + Regime + OBV | 31.2% | 28.3% | Inverted confidence |
| **v9** | **Trend-following + Gann confirm** | **38.8%** | **39.1%** | **Best so far, still below target** |

*Static backtest (not walk-forward validated)

---

## 🔍 Key Learnings

### What Didn't Work:

1. **Gann Anniversary Theory**
   - Top/bottom anniversaries show NO predictive power at 90-day horizon
   - Creates bearish bias that fights actual trends
   - Research confirms: Gann better for support/resistance levels than direction

2. **Kondratiev Wave**
   - Cycle too slow (10-15 years) for 90-day predictions
   - Useful as long-term bias only, not directional signal
   - Reduced weight from 0.8 to 0.3 had minimal impact

3. **Complex Signal Weighting**
   - More signals ≠ better accuracy
   - Weight optimization overfits to historical data
   - Simple approaches (v9) outperform complex ones (v8)

4. **Confidence Calibration**
   - High confidence predictions (70%+) performed WORSE than low confidence
   - Indicates model doesn't understand its own uncertainty
   - Fundamental issue with scoring methodology

### What Showed Promise:

1. **Trend-Following (v9)**
   - 38.8% is the best walk-forward validated result
   - Price vs 50/200 MA provides reasonable directional bias
   - Don't fight the trend = sound principle

2. **Volume Confirmation (OBV)**
   - OBV divergence sometimes precedes reversals
   - Works better as filter than primary signal

3. **Walk-Forward Optimization**
   - Provides realistic performance estimates
   - Prevents overfitting to specific time periods
   - Should be standard for all future testing

---

## 📚 Research Findings

### Academic/Industry Research:

1. **HSI-Specific Studies:**
   - MDPI 2024: BiLSTM models show ~55-60% accuracy on HSI (requires deep learning)
   - VAR-LSTM models: Better at volatility prediction than direction
   - Random Forest/Decision Trees: ~50-55% on daily direction, not 90-day

2. **Gann Theory Research:**
   - No peer-reviewed evidence of predictive power
   - Popular in retail trading, not institutional
   - Works better for identifying support/resistance than timing

3. **Trend-Following:**
   - 50/200 MA crossover: ~52-55% accuracy in trending markets
   - Performs poorly in ranging/choppy markets
   - Requires additional filters for regime detection

4. **Machine Learning Approaches:**
   - LSTM/GRU models: 55-65% reported accuracy (but often overfitted)
   - Require significant data preprocessing and tuning
   - Best for short-term (1-10 day) predictions, not 90-day

---

## ⚠️ Why 65% Is Unrealistic

### Market Efficiency:
- HSI is heavily traded by institutions with superior data/models
- Any simple, publicly-known pattern gets arbitraged away
- 90-day horizon includes unpredictable events (policy, geopolitics, earnings)

### Model Limitations:
- Technical analysis is backward-looking
- Gann/K-Wave are theoretical frameworks, not proven systems
- No model can predict black swan events (COVID, geopolitical shocks)

### Statistical Reality:
- Even professional hedge funds target 55-60% directional accuracy
- 65%+ typically requires:
  - Alternative data (satellite, credit card, sentiment)
  - High-frequency trading (not 90-day)
  - Significant capital for diversification

---

## 🎯 Recommendations

### Option 1: Adjust Expectations (Recommended)
**Target:** 50-55% accuracy with good risk management

```
- Accept that 50%+ is still valuable (better than random)
- Focus on risk/reward ratio, not just accuracy
- Use predictions as ONE input among many
- Implement position sizing based on confidence
```

### Option 2: Shorten Prediction Horizon
**Target:** 30-day predictions instead of 90-day

```
- Shorter horizon = less uncertainty
- Technical signals more relevant at 30 days
- Can compound multiple 30-day predictions
- Requires more frequent model updates
```

### Option 3: Add External Data
**Target:** Improve signal quality with new data sources

```
- Macroeconomic indicators (China PMI, US rates, HK policy)
- Sentiment data (news, social media, analyst ratings)
- Flow data (northbound/southbound stock connect)
- Options market data (put/call ratios, implied volatility)
```

### Option 4: Ensemble Approach
**Target:** Combine multiple weak models

```
- Run v9 (trend) + ML model + sentiment model
- Use voting or stacking to combine predictions
- Diversify across uncorrelated signals
- More robust than single model
```

### Option 5: Focus on Risk Management
**Target:** Profitable despite ~50% accuracy

```
- Cut losses quickly (stop-loss at -5%)
- Let winners run (take profit at +10-15%)
- Size positions based on confidence
- Avoid predictions during high uncertainty
```

---

## 📋 Current Model Status (v9)

### Strengths:
✅ Walk-forward validated (realistic performance estimate)  
✅ Simple, interpretable signals  
✅ Trend-following principle is sound  
✅ No look-ahead bias  

### Weaknesses:
❌ 38.8% accuracy below 50% baseline  
❌ Confidence scores not calibrated  
❌ Poor major drop/rally recall  
❌ No edge in 90-day predictions  

### Current Reading (Feb 20, 2026):
- **Prediction:** NEUTRAL
- **Confidence:** 57%
- **Risk Score:** 51/100
- **Expected Move:** 0%
- **Trend Score:** 0.00 (flat)
- **Momentum:** -0.08 (slightly negative)
- **Volume:** 0.00 (neutral)

---

## 🚀 Next Steps (If Continuing Development)

### Immediate (1-2 weeks):
1. **Test 30-day horizon** - Modify v9 for shorter predictions
2. **Add macro data** - China PMI, US Treasury yields, USD/HKD
3. **Calibrate confidence** - Use isotonic regression or Platt scaling
4. **Backtest risk management** - Test stop-loss/take-profit rules

### Medium-term (1 month):
5. **Build ML model** - LSTM or XGBoost with walk-forward
6. **Add sentiment data** - News sentiment, analyst upgrades/downgrades
7. **Ensemble v9 + ML** - Combine predictions
8. **Paper trade** - Real-time testing with virtual capital

### Long-term (3 months):
9. **Production deployment** - If 50%+ accuracy achieved
10. **Continuous monitoring** - Track live performance vs backtest
11. **Model retraining** - Quarterly updates with new data

---

## 📁 Files Generated

### Models:
- `hsi_analysis.py` - v1 (original)
- `hsi_analysis_v2.py` through `hsi_analysis_v9.py` - Iterative improvements

### Backtest Results:
- `hsi_backtest_results.csv` - v1
- `hsi_backtest_v2_results.csv` through `hsi_backtest_v9_results.csv`

### Reports:
- `hsi_model_comparison.md` - v1 vs v2
- `hsi_backtest_report.md` - v1 detailed
- `hsi_current_analysis_v2.md` - v2 current reading
- `hsi_v6_report.md` - v6 current
- `HSI_ANALYSIS_SUMMARY.md` - Project overview
- `HSI_V8_IMPROVEMENT_PLAN.md` - v8 planning
- `HSI_MODEL_DEVELOPMENT_REPORT.md` - This document

### Status Files:
- `hsi_status.json` - Machine-readable current status
- `hsi_v8_wfo_summary.json` - v8 WFO results
- `hsi_v9_wfo_summary.json` - v9 WFO results

### Data:
- `hsi.csv` - Raw data (11,449 points, 1980-2026)
- `hsi_processed.csv` - Cleaned data

---

## 💡 Final Thoughts

**The honest answer:** Predicting stock market direction at 90-day horizon with 65% accuracy using publicly available data and technical analysis is **not achievable**. This is consistent with academic research and industry experience.

**What IS achievable:**
- 50-55% directional accuracy (small but real edge)
- Better risk management than buy-and-hold
- Systematic approach that removes emotion
- Framework for incorporating additional signals

**The path forward:** Either adjust targets to realistic levels, or invest significantly more resources (alternative data, ML infrastructure, research time) to pursue the 65% goal.

---

*Disclaimer: This analysis is for educational/research purposes only. Not financial advice. Past performance does not guarantee future results.*
