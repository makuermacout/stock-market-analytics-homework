# Stock Market Analytics Zoomcamp 2026: Module 2 Homework

Solutions for the DataTalks.Club Stock Market Analytics Zoomcamp, Module 2 (IPO analysis and an RSI trading strategy).

## Files

| File | Question | What it does |
|---|---|---|
| `q1_withdrawn_ipos.py` | Q1 | Scrapes withdrawn IPOs from iposcoop.com, classifies company type, and finds the class with the highest withdrawn value |
| `q2_q3_ipo_stocks.py` | Q2, Q3 | Downloads 2025 IPO prices with yfinance, computes Sharpe ratios (Q2) and fixed-holding-period growth (Q3) |
| `q4_rsi_strategy.py` | Q4 | Net income from investing $1,000 at every RSI < 30 signal, 2000-2025 |

## Running

The scripts were run in Google Colab.

```
pip install -r requirements.txt
python q1_withdrawn_ipos.py
```

Notes:
- Q1 to Q3 pull live data, so exact counts can differ slightly from the homework text.
- Q1 only counts withdrawals filed before 2026-09-11.
- Q4 downloads a parquet file from Google Drive with `gdown`.

## Results

| Question | Result |
|---|---|
| Q1 | Acquisition Corp, about $500M |
| Q2 | Median Sharpe 0.048 |
| Q3 | Best holding period is 1 month (median growth 0.93) |
| Q4 | Net income about $65.8k (5,206 trades, 55.13% win rate) |
