import pandas as pd

df = pd.read_parquet('data/07_portfolios_metadata/complete_metadata_hcm.parquet')
records = []
for portfolio in ['decil_1', 'decil_10']:
    port_df = df[df['portfolio'] == portfolio]
    years = sorted(port_df['year'].unique())
    prev_tickers = set()
    for i, year in enumerate(years):
        current_tickers = set(port_df[port_df['year'] == year]['Ticker'])
        if i == 0:
            turnover_rate = 0.0
        else:
            additions = len(current_tickers - prev_tickers)
            deletions = len(prev_tickers - current_tickers)
            avg_size = (len(current_tickers) + len(prev_tickers)) / 2
            turnover_rate = ((additions + deletions) / 2) / avg_size
        records.append({'portfolio': portfolio, 'year': year, 'turnover_rate': turnover_rate})
        prev_tickers = current_tickers

turnover_df = pd.DataFrame(records)
print(turnover_df)
