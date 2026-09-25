import pandas as pd

df = pd.read_parquet("../../data/07_portfolios_metadata/complete_metadata_hcm.parquet")
df = df.reset_index()

outlier = df[(df['year'] == '2019') & (df['mcap_2019'] > 1e14)][['index', 'Sector', 'Industry', 'mcap_2019']]
print("--- 2019 Outlier ---")
print(outlier)

outlier_nodes = outlier['index'].tolist()
print("\n--- History of Outlier Nodes ---")
history = df[df['index'].isin(outlier_nodes)][['index', 'year', 'mcap_2018', 'mcap_2019', 'mcap_2020', 'mcap_2021', 'mcap_2022', 'mcap_2023', 'mcap_2024']]
print(history)
