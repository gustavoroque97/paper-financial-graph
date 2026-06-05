import pandas as pd
df = pd.read_parquet('data/07_portfolios_metadata/complete_metadata_hcm.parquet')
series = df['mcap_2015'].dropna()
print(series.head())
if series.dtype == 'object' or series.dtype.name == 'string':
    series = series.astype(str).str.replace(',', '.', regex=False)
    series = pd.to_numeric(series, errors='coerce').dropna()
print(series.head())
