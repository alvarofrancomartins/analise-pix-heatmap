"""Baixa os dados do heatmap a partir da API oficial do BCB (SPI).

Fonte: BCB "Estatísticas do SPI" (Olinda OData) — recurso PixLiquidadosAtual
(Pix liquidados no SPI, diário). É um "entity set" simples: uma única requisição.

Salva em data/pix_liquidados_atual.csv

Requer: requests, pandas
Usage: python download_data.py
"""
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DATA.mkdir(parents=True, exist_ok=True)

URL = ("https://olinda.bcb.gov.br/olinda/servico/SPI/versao/v1/odata/"
       "PixLiquidadosAtual?$format=json&$top=200000")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "Chrome/120 Safari/537.36",
    "Accept": "application/json",
}

r = requests.get(URL, headers=HEADERS, timeout=300)
r.raise_for_status()
rows = r.json().get("value", [])
df = pd.DataFrame(rows)

out = DATA / "pix_liquidados_atual.csv"
df.to_csv(out, index=False)
print(f"salvo {out}  ({len(df)} linhas; colunas: {', '.join(df.columns)})")
