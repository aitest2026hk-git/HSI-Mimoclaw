# HSI-Mimoclaw

HSI (Hang Seng Index) v11.3 Prediction Framework — Powered by OpenClaw

## Framework Components

- **Gann Theory** — Angular analysis, square of nine, price-time symmetry
- **24 Solar Terms** — Chinese calendar-based market timing
- **Zhou Jintao Cycles** — Kondratiev, Juglar, Kitchin nested cycle framework
- **Technical Analysis** — MA, RSI, MACD, Bollinger Bands, OBV, ATR
- **Caishen Analysis** — Institutional flow and sector rotation
- **Geopolitical Overlay** — Oil, VIX, treasury yields, Fear & Greed

## Structure

```
├── hsi-v11-framework/       # Core analysis tools and data
│   ├── hsi_analysis_v10.py  # Main analysis engine
│   ├── gann_solar/          # Gann + Solar Term modules
│   ├── backtest_results/    # Historical backtest data
│   ├── tools/               # Analyzer utilities
│   └── memory/              # Development logs and methodology docs
├── memory/                  # Daily logs and analysis history
│   ├── hsi-prediction-v11-framework.md
│   ├── hsi-v11-dashboard.md
│   └── YYYY-MM-DD.md        # Daily notes
└── .gitignore
```

## Key Files

- `hsi-prediction-v11-framework.md` — Complete v11 methodology document
- `hsi_analysis_v10.py` — Trend-following + Solar Term confluence engine
- `gann_solar/` — Solar term calculator + confluence scoring
- `run_v11_analysis.py` — One-click analysis runner
- `hsi_v11_alert_system.py` — Real-time alert monitoring

## Latest Analysis (Apr 1, 2026)

- **HSI:** 25,261 (+1.91%)
- **S&P 500:** 6,529 (+2.91%)
- **VIX:** 24.48 (-3.05%)
- **Brent Oil:** $100.64 (-14.96% — major de-escalation signal)
- **Trend Score:** -7 (strong bearish — counter-trend bounce)
- **Verdict:** CAUTIOUSLY ACCUMULATE — oil crash = risk-on, but technicals lag

## Backtested Performance

| Version | Direction Accuracy | Target |
|---------|-------------------|--------|
| v8 | ~52% | 50-55% |
| v10 | ~55% | 55-60% |
| v11 | ~58% | 58-63% |

## Disclaimer

This framework is for educational and research purposes only. Not financial advice.
