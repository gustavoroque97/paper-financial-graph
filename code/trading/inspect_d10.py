import pandas as pd

df_screen = pd.read_parquet("../../data/01_raw/screener_result.parquet")
mcap_dict = df_screen.dropna(subset=['Market Cap', 'Ticker']).set_index('Ticker')['Market Cap'].to_dict()

for year in [2015, 2020, 2024]:
    print(f"\n=== YEAR {year} ===")
    hrm_d10 = pd.read_parquet(f"../../data/06_portfolios/decil_10_{year}_hrm.parquet").columns.tolist()
    pozzi_d10 = pd.read_parquet(f"../../data/06_portfolios/decil_10_{year}_pozzi.parquet").columns.tolist()
    
    hrm_d1 = pd.read_parquet(f"../../data/06_portfolios/decil_1_{year}_hrm.parquet").columns.tolist()
    pozzi_d1 = pd.read_parquet(f"../../data/06_portfolios/decil_1_{year}_pozzi.parquet").columns.tolist()
    
    hrm_mcaps10 = [(t, mcap_dict.get(t, 0)) for t in hrm_d10 if t in mcap_dict]
    pozzi_mcaps10 = [(t, mcap_dict.get(t, 0)) for t in pozzi_d10 if t in mcap_dict]
    
    hrm_mcaps1 = [(t, mcap_dict.get(t, 0)) for t in hrm_d1 if t in mcap_dict]
    pozzi_mcaps1 = [(t, mcap_dict.get(t, 0)) for t in pozzi_d1 if t in mcap_dict]
    
    hrm_mcaps10.sort(key=lambda x: x[1], reverse=True)
    pozzi_mcaps10.sort(key=lambda x: x[1], reverse=True)
    hrm_mcaps1.sort(key=lambda x: x[1], reverse=True)
    pozzi_mcaps1.sort(key=lambda x: x[1], reverse=True)
    
    print("HRM D10 Top:", [t for t,m in hrm_mcaps10[:5]])
    print("Pozzi D10 Top:", [t for t,m in pozzi_mcaps10[:5]])
    print("HRM D1 Top:", [t for t,m in hrm_mcaps1[:5]])
    print("Pozzi D1 Top:", [t for t,m in pozzi_mcaps1[:5]])
    
    # Calculate sum of MCap
    print(f"Total MCap HRM D10: {sum(m for t,m in hrm_mcaps10)/1e9:.1f}B")
    print(f"Total MCap Pozzi D10: {sum(m for t,m in pozzi_mcaps10)/1e9:.1f}B")

