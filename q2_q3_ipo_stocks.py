# In Colab, first run:  !pip install yfinance lxml
import io
import re

import numpy as np
import pandas as pd
import requests
import yfinance as yf

URL = "https://www.iposcoop.com/2025-pricings/"

# ---------------------------------------------------------------- Q2 step 1
resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
resp.raise_for_status()
tables = pd.read_html(io.StringIO(resp.text))
ipos = next(
    t for t in tables
    if any("symbol" in str(c).lower() for c in t.columns)
    and any("offer" in str(c).lower() for c in t.columns)
)
print("Columns found:", list(ipos.columns))
print("IPOs loaded:", len(ipos))  # expect ~231


def find_col(df, *keywords):
    for c in df.columns:
        name = str(c).lower()
        if all(k in name for k in keywords):
            return c
    raise KeyError(f"No column with {keywords} in {list(df.columns)}")


def to_num(x):
    if pd.isna(x):
        return np.nan
    s = re.sub(r"[^0-9.\-]", "", str(x))
    try:
        return float(s)
    except ValueError:
        return np.nan


c_symbol = find_col(ipos, "symbol")
c_date = find_col(ipos, "offer", "date")
c_return = find_col(ipos, "return")

# ---------------------------------------------------------------- Q2 step 2
ipos["Offer Date"] = pd.to_datetime(ipos[c_date], errors="coerce")
ipos["ret_num"] = ipos[c_return].apply(to_num)

filtered = ipos[(ipos["Offer Date"] < "2025-09-01") & (ipos["ret_num"] != 0)]
tickers = (
    filtered[c_symbol].dropna().astype(str).str.strip().str.upper().unique().tolist()
)
print("Filtered IPOs:", len(tickers))  # expect ~148

# ---------------------------------------------------------------- Q2 step 3
frames, missing = [], []
for t in tickers:
    try:
        d = yf.download(
            t, start="2025-01-01", end="2026-09-29", progress=False, auto_adjust=True
        )
    except Exception:
        d = pd.DataFrame()
    if d is None or d.empty:
        missing.append(t)
        continue
    d.columns = d.columns.get_level_values(0)  # flatten yfinance MultiIndex
    d = d.reset_index()
    d["Ticker"] = t
    frames.append(d[["Date", "Ticker", "Close"]])

stocks_df = pd.concat(frames, ignore_index=True)
stocks_df = stocks_df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
print("Stocks downloaded:", stocks_df["Ticker"].nunique())  # expect ~134
print("Missing (likely delisted):", len(missing))

# ---------------------------------------------------------------- Q2 step 4
g = stocks_df.groupby("Ticker")["Close"]
stocks_df["growth_252d"] = stocks_df["Close"] / g.shift(252)
stocks_df["volatility"] = (
    g.rolling(30).std().reset_index(level=0, drop=True) * np.sqrt(252)
)

# ---------------------------------------------------------------- Q2 step 5
stocks_df["Sharpe"] = (stocks_df["growth_252d"] - 0.05) / stocks_df["volatility"]

# ---------------------------------------------------------------- Q2 step 6
day = stocks_df[stocks_df["Date"] == "2026-09-11"]
print("\n=== Q2: describe() on 2026-09-11 ===")
print(day[["growth_252d", "volatility", "Sharpe"]].describe())
print(f"\nQ2 answer: median Sharpe = {day['Sharpe'].median():.4f}")

# ---------------------------------------------------------------- Q3
g = stocks_df.groupby("Ticker")["Close"]
for m in range(1, 13):
    stocks_df[f"future_growth_{m}_m"] = g.shift(-21 * m) / stocks_df["Close"]

# entry point = first available trading day per ticker
min_dates = (
    stocks_df.groupby("Ticker")["Date"].min().reset_index().rename(columns={"Date": "min_date"})
)
entry = stocks_df.merge(
    min_dates, left_on=["Ticker", "Date"], right_on=["Ticker", "min_date"], how="inner"
)

growth_cols = [f"future_growth_{m}_m" for m in range(1, 13)]
stats = entry[growth_cols].describe()
print("\n=== Q3: describe() at IPO entry ===")
print(stats.T[["count", "mean", "50%"]])

medians = stats.loc["50%"]
best = medians.idxmax()
print(f"\nQ3 answer: best holding period = {best} (median = {medians.max():.4f})")
