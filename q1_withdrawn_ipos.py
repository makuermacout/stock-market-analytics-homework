import io
import re

import numpy as np
import pandas as pd
import requests

URL = "https://www.iposcoop.com/ipos-recently-filed/"

# 1. Load data -------------------------------------------------------------
resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
resp.raise_for_status()
tables = pd.read_html(io.StringIO(resp.text))

# pick the table that has the withdrawn/expected-to-trade column
df = next(t for t in tables if any("expected" in str(c).lower() for c in t.columns))
print("Columns found:", list(df.columns))  # check names if anything below fails


def find_col(*keywords):
    """Find a column whose lowercase name contains all keywords."""
    for c in df.columns:
        name = str(c).lower()
        if all(k in name for k in keywords):
            return c
    raise KeyError(f"No column with {keywords} in {list(df.columns)}")


col_company = find_col("company")
col_low = find_col("price", "low")
col_high = find_col("price", "high")
col_shares = find_col("shares")
col_vol = find_col("vol")
col_trade = find_col("expected")

withdrawn = df[df[col_trade].astype(str).str.strip().str.lower() == "withdrawn"].copy()
print("Withdrawn entries:", len(withdrawn))

# Only count withdrawals filed before the Sep 11, 2026 cutoff
withdrawn["File Date"] = pd.to_datetime(withdrawn["File Date"])
withdrawn = withdrawn[withdrawn["File Date"] < "2026-09-11"].copy()
print("Withdrawn entries after date filter:", len(withdrawn))  # expect ~32

# 2. Company classification (first match wins, case-sensitive) ---------------
def classify(name):
    name = str(name)
    if "Technologies" in name:
        return "Technologies"
    if any(k in name for k in ("Acquisition Corp", "Acquisition Corporation", "Corp")):
        return "Acquisition Corp"
    if "Inc" in name or "Incorporated" in name:
        return "Inc."
    if "Group" in name:
        return "Group"
    if "Ltd" in name or "Limited" in name:
        return "Limited"
    if "Holdings" in name or "Holding" in name:
        return "Holdings"
    return "Other"


withdrawn["Company Type"] = withdrawn[col_company].apply(classify)


# 3. Price parsing ---------------------------------------------------------
def to_num(x):
    """'$8.00' -> 8.0 ; '-', '', NaN -> NaN"""
    if pd.isna(x):
        return np.nan
    s = re.sub(r"[^0-9.\-]", "", str(x))
    if s in ("", "-", "."):
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


low = withdrawn[col_low].apply(to_num)
high = withdrawn[col_high].apply(to_num)
withdrawn["Avg_price"] = (low + high) / 2  # NaN if either side is missing

# 4. Numeric conversion ----------------------------------------------------
withdrawn["shares_m"] = withdrawn[col_shares].apply(to_num)
withdrawn["est_vol_m"] = withdrawn[col_vol].apply(to_num)

# 5. Value calculation -----------------------------------------------------
computed = withdrawn["shares_m"] * withdrawn["Avg_price"]
withdrawn["Shares_offered_value"] = computed.where(computed.notna(), withdrawn["est_vol_m"])

# 6. Aggregation -----------------------------------------------------------
result = (
    withdrawn.groupby("Company Type")["Shares_offered_value"]
    .sum()
    .sort_values(ascending=False)
)
print(result)
print(f"\nAnswer: {result.index[0]} with ${result.iloc[0]:,.2f} million")
