import pandas as pd


url = "https://data.humdata.org/dataset/a8b2f1dc-6428-4e86-b147-55a12d9de481/resource/80b39481-c161-4655-b2e4-677c1b259fab/download/hdx_hapi_idps_syr.csv"


df = pd.read_csv(url)

df.to_excel('results.xlsx',index=False)
