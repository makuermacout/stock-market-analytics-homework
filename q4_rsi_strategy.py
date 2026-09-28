# In Colab, first run:  !pip install gdown pyarrow
import gdown
import pandas as pd

file_id = "1grCTCzMZKY5sJRtdbLVCXg8JXA8VPyg-"
gdown.download(f"https://drive.google.com/uc?id={file_id}", "data.parquet", quiet=False)
df = pd.read_parquet("data.parquet", engine="pyarrow")
print("Shape:", df.shape)
print("Columns:", list(df.columns))  # check names if anything below fails


def find_col(*keywords, exact=None):
    if exact and exact in df.columns:
        return exact
    for c in df.columns:
        name = str(c).lower()
        if all(k in name for k in keywords):
            return c
    raise KeyError(f"No column with {keywords} in {list(df.columns)}")


c_rsi = find_col("rsi", exact="rsi")
c_date = find_col("date", exact="Date")
c_growth = "growth_future_30d"

# Date may be the index in some versions of the file
if c_date not in df.columns and df.index.name and "date" in str(df.index.name).lower():
    df = df.reset_index()

df[c_date] = pd.to_datetime(df[c_date])

selected_df = df[
    (df[c_rsi] < 30)
    & (df[c_date] >= "2000-01-01")
    & (df[c_date] <= "2025-06-01")
].dropna(subset=[c_growth])

net_income = 1000 * (selected_df[c_growth] - 1).sum()

print("Trades:", len(selected_df))  # homework says ~5,206
print("Avg 30d return:", f"{(selected_df[c_growth] - 1).mean():.2%}")  # ~1.26%
print("Win rate:", f"{(selected_df[c_growth] > 1).mean():.2%}")  # ~55.13%
print(f"\nQ4 answer: net income = ${net_income:,.0f}  ->  {net_income / 1000:.1f} thousand")
