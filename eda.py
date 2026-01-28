# TECH SALES - VISUALIZZAZIONI PYTHON
# Questo script prende i dati gia aggregati da SQL e genera i grafici
# Nessuna logica di business qui - tutto il calcolo e fatto nelle query SQL

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector
import os
import warnings
warnings.filterwarnings('ignore')

# Setup grafico - uso gli stessi colori di Tableau per coerenza
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

COLORS = {
    'primary': '#4E79A7',
    'secondary': '#76B7B2',
    'accent': '#F28E2B',
    'red': '#E15759',
    'green': '#59A14F',
    'gray': '#BAB0AC'
}

print("TECH SALES - GENERAZIONE GRAFICI")
print("=" * 50)
print()


# CONNESSIONE AL DATABASE
# La password la prendo da variabile d'ambiente per sicurezza
# Se non c'e, lascio vuoto (utile per test locali)

print("[1/4] Connessione a MySQL...")

conn = mysql.connector.connect(
    host='localhost',
    database='sales',
    user='root',
    password=os.environ.get('MYSQL_PASSWORD', '')
)


# QUERY SQL - TUTTE LE AGGREGAZIONI SONO QUI
# Python riceve dati gia pronti, non deve calcolare nulla
# Questo evita di duplicare la logica che ho gia scritto in analysis.sql

print("[2/4] Esecuzione query SQL...")
print()

# Overview generale - mi serve per il report iniziale
query_overview = """
SELECT
    COUNT(*) as total_transactions,
    SUM(CASE WHEN currency = 'USD' THEN sales_amount * 74 ELSE sales_amount END) as total_revenue,
    SUM(sales_qty) as total_quantity,
    COUNT(DISTINCT customer_code) as unique_customers,
    COUNT(DISTINCT market_code) as unique_markets,
    MIN(order_date) as start_date,
    MAX(order_date) as end_date
FROM transactions
"""

# Fatturato annuale - per il grafico a barre e calcolo YoY
query_yearly = """
SELECT
    d.year,
    SUM(CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END) as revenue,
    SUM(t.sales_qty) as quantity,
    COUNT(*) as transactions
FROM transactions t
INNER JOIN date d ON t.order_date = d.date
GROUP BY d.year
ORDER BY d.year
"""

# Trend mensile - per il grafico a linea
query_monthly = """
SELECT
    d.year,
    d.month_name as month,
    MONTH(d.date) as month_num,
    SUM(CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END) as revenue
FROM transactions t
INNER JOIN date d ON t.order_date = d.date
GROUP BY d.year, d.month_name, MONTH(d.date)
ORDER BY d.year, MONTH(d.date)
"""

# Top mercati - per il grafico orizzontale
query_markets = """
SELECT
    m.markets_name as market,
    m.zone,
    SUM(CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END) as revenue,
    SUM(t.sales_qty) as quantity,
    COUNT(*) as transactions
FROM transactions t
INNER JOIN markets m ON t.market_code = m.markets_code
GROUP BY m.markets_name, m.zone
ORDER BY revenue DESC
"""

# Top clienti - stesso discorso
query_customers = """
SELECT
    c.custmer_name as customer,
    c.customer_type,
    SUM(CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END) as revenue,
    SUM(t.sales_qty) as quantity,
    COUNT(*) as transactions
FROM transactions t
INNER JOIN customers c ON t.customer_code = c.customer_code
GROUP BY c.custmer_name, c.customer_type
ORDER BY revenue DESC
"""

# Zone geografiche - per il pie chart
query_zones = """
SELECT
    m.zone,
    COUNT(DISTINCT m.markets_code) as n_markets,
    SUM(CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END) as revenue,
    SUM(t.sales_qty) as quantity
FROM transactions t
INNER JOIN markets m ON t.market_code = m.markets_code
GROUP BY m.zone
ORDER BY revenue DESC
"""

# Dati per la heatmap anno x mese
query_heatmap = """
SELECT
    d.year,
    MONTH(d.date) as month_num,
    SUM(CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END) as revenue
FROM transactions t
INNER JOIN date d ON t.order_date = d.date
GROUP BY d.year, MONTH(d.date)
ORDER BY d.year, MONTH(d.date)
"""

# Per il boxplot mi servono i dati grezzi (ma normalizzati)
# Questa e l'unica query che non e aggregata
query_boxplot = """
SELECT
    m.zone,
    CASE WHEN t.currency = 'USD' THEN t.sales_amount * 74 ELSE t.sales_amount END as amount
FROM transactions t
INNER JOIN markets m ON t.market_code = m.markets_code
"""

# Eseguo tutte le query e carico i dataframe
df_overview = pd.read_sql(query_overview, conn)
df_yearly = pd.read_sql(query_yearly, conn)
df_monthly = pd.read_sql(query_monthly, conn)
df_markets = pd.read_sql(query_markets, conn)
df_customers = pd.read_sql(query_customers, conn)
df_zones = pd.read_sql(query_zones, conn)
df_heatmap = pd.read_sql(query_heatmap, conn)
df_boxplot = pd.read_sql(query_boxplot, conn)

conn.close()
print("   Query completate.")
print()


# REPORT METRICHE
# Stampo i numeri principali - i dati arrivano gia calcolati da SQL

print("[3/4] Report metriche...")
print()

overview = df_overview.iloc[0]
print("METRICHE GENERALI:")
print(f"   Transazioni totali:    {overview['total_transactions']:,}")
print(f"   Fatturato totale:      Rs.{overview['total_revenue']/1e6:.1f}M")
print(f"   Quantita venduta:      {overview['total_quantity']:,} unita")
print(f"   Clienti unici:         {overview['unique_customers']}")
print(f"   Mercati:               {overview['unique_markets']}")
print(f"   Periodo:               {overview['start_date']} - {overview['end_date']}")
print()

# Fatturato per anno
print("FATTURATO PER ANNO:")
for _, row in df_yearly.iterrows():
    print(f"   {int(row['year'])}: Rs.{row['revenue']/1e6:.1f}M ({int(row['transactions']):,} transazioni)")
print()

# Calcolo la crescita YoY qui perche e un calcolo semplice sul dataframe
# Non vale la pena farlo in SQL con LAG() per cosi pochi dati
df_yearly['yoy_growth'] = df_yearly['revenue'].pct_change() * 100

print("CRESCITA YoY:")
for _, row in df_yearly.iterrows():
    if pd.notna(row['yoy_growth']):
        symbol = "+" if row['yoy_growth'] > 0 else ""
        print(f"   {int(row['year'])}: {symbol}{row['yoy_growth']:.1f}%")
print()

# Top mercati con percentuali
df_markets['pct'] = df_markets['revenue'] / df_markets['revenue'].sum() * 100
print("TOP 5 MERCATI:")
for i, (_, row) in enumerate(df_markets.head(5).iterrows(), 1):
    print(f"   {i}. {row['market']}: Rs.{row['revenue']/1e6:.1f}M ({row['pct']:.1f}%)")
print()

# Top clienti
df_customers['pct'] = df_customers['revenue'] / df_customers['revenue'].sum() * 100
print("TOP 5 CLIENTI:")
for i, (_, row) in enumerate(df_customers.head(5).iterrows(), 1):
    print(f"   {i}. {row['customer']}: Rs.{row['revenue']/1e6:.1f}M ({row['pct']:.1f}%)")
print()

# Zone
df_zones['pct'] = df_zones['revenue'] / df_zones['revenue'].sum() * 100
print("FATTURATO PER ZONA:")
for _, row in df_zones.iterrows():
    print(f"   {row['zone']}: Rs.{row['revenue']/1e6:.1f}M ({row['pct']:.1f}%) - {int(row['n_markets'])} mercati")
print()

# Insights sulla concentrazione
top3_market_pct = df_markets.head(3)['pct'].sum()
top5_customer_pct = df_customers.head(5)['pct'].sum()
print("CONCENTRAZIONE (rischi):")
print(f"   Top 3 mercati: {top3_market_pct:.1f}% del fatturato")
print(f"   Top 5 clienti: {top5_customer_pct:.1f}% del fatturato")
print()


# CREAZIONE GRAFICI
# Qui Python fa quello che sa fare bene: visualizzare
# I dati sono gia pronti, devo solo plottarli

print("[4/4] Creazione grafici...")
print()

output_dir = os.path.dirname(os.path.abspath(__file__))
charts_dir = os.path.join(output_dir, 'charts')
os.makedirs(charts_dir, exist_ok=True)

# Grafico 1: Fatturato per anno (bar chart)
fig, ax = plt.subplots(figsize=(10, 6))
years = df_yearly['year'].astype(int).astype(str)
revenue = df_yearly['revenue'] / 1e6
bars = ax.bar(years, revenue, color=COLORS['primary'], edgecolor='white')
ax.set_xlabel('Anno', fontsize=12)
ax.set_ylabel('Fatturato (Milioni Rs.)', fontsize=12)
ax.set_title('Fatturato Totale per Anno', fontsize=14, fontweight='bold')
for bar, val in zip(bars, revenue):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{val:.1f}M', ha='center', va='bottom', fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '01_fatturato_per_anno.png'), dpi=150)
plt.close()
print("   01_fatturato_per_anno.png")

# Grafico 2: Trend mensile (line chart)
fig, ax = plt.subplots(figsize=(14, 6))
df_monthly['date'] = pd.to_datetime(
    df_monthly['year'].astype(int).astype(str) + '-' +
    df_monthly['month_num'].astype(int).astype(str) + '-01'
)
ax.plot(df_monthly['date'], df_monthly['revenue']/1e6,
        color=COLORS['accent'], linewidth=2, marker='o', markersize=3)
ax.fill_between(df_monthly['date'], df_monthly['revenue']/1e6,
                alpha=0.3, color=COLORS['accent'])
ax.set_xlabel('Data', fontsize=12)
ax.set_ylabel('Fatturato (Milioni Rs.)', fontsize=12)
ax.set_title('Trend Fatturato Mensile (2017-2020)', fontsize=14, fontweight='bold')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '02_trend_mensile.png'), dpi=150)
plt.close()
print("   02_trend_mensile.png")

# Grafico 3: Top 7 mercati (horizontal bar)
fig, ax = plt.subplots(figsize=(10, 8))
top7 = df_markets.head(7)
colors = [COLORS['accent']] + [COLORS['primary']] * 6  # evidenzio il primo
bars = ax.barh(top7['market'][::-1], top7['revenue'][::-1]/1e6, color=colors[::-1])
ax.set_xlabel('Fatturato (Milioni Rs.)', fontsize=12)
ax.set_title('Top 7 Mercati per Fatturato', fontsize=14, fontweight='bold')
for bar, val in zip(bars, top7['revenue'][::-1]/1e6):
    ax.text(val + 1, bar.get_y() + bar.get_height()/2, f'{val:.1f}M',
            va='center', fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '03_top7_mercati.png'), dpi=150)
plt.close()
print("   03_top7_mercati.png")

# Grafico 4: Top 5 clienti (horizontal bar)
fig, ax = plt.subplots(figsize=(10, 6))
top5 = df_customers.head(5)
bars = ax.barh(top5['customer'][::-1], top5['revenue'][::-1]/1e6, color=COLORS['secondary'])
ax.set_xlabel('Fatturato (Milioni Rs.)', fontsize=12)
ax.set_title('Top 5 Clienti per Fatturato', fontsize=14, fontweight='bold')
for bar, val in zip(bars, top5['revenue'][::-1]/1e6):
    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, f'{val:.1f}M',
            va='center', fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '04_top5_clienti.png'), dpi=150)
plt.close()
print("   04_top5_clienti.png")

# Grafico 5: Distribuzione per zona (pie chart)
fig, ax = plt.subplots(figsize=(8, 8))
zone_colors = [COLORS['primary'], COLORS['secondary'], COLORS['accent'], COLORS['green']]
ax.pie(
    df_zones['revenue'],
    labels=df_zones['zone'].tolist(),
    autopct='%1.1f%%',
    colors=zone_colors[:len(df_zones)],
    explode=[0.05 if i == 0 else 0 for i in range(len(df_zones))],
    startangle=90
)
ax.set_title('Distribuzione Fatturato per Zona', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '05_distribuzione_zone.png'), dpi=150)
plt.close()
print("   05_distribuzione_zone.png")

# Grafico 6: Heatmap mensile
fig, ax = plt.subplots(figsize=(12, 6))
pivot = df_heatmap.pivot(index='year', columns='month_num', values='revenue') / 1e6
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
            cbar_kws={'label': 'Milioni Rs.'})
ax.set_xlabel('Mese', fontsize=12)
ax.set_ylabel('Anno', fontsize=12)
ax.set_title('Heatmap Fatturato Mensile', fontsize=14, fontweight='bold')
ax.set_xticklabels(['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu',
                    'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'])
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '06_heatmap_mensile.png'), dpi=150)
plt.close()
print("   06_heatmap_mensile.png")

# Grafico 7: Box plot per zona
fig, ax = plt.subplots(figsize=(10, 6))
# Tolgo il 99 percentile per non comprimere il grafico
q99 = df_boxplot['amount'].quantile(0.99)
df_box_clean = df_boxplot[df_boxplot['amount'] < q99]
zone_order = df_zones['zone'].tolist()
sns.boxplot(data=df_box_clean, x='zone', y='amount', order=zone_order,
            palette='Set2', ax=ax)
ax.set_xlabel('Zona', fontsize=12)
ax.set_ylabel('Importo Transazione (Rs.)', fontsize=12)
ax.set_title('Distribuzione Importi per Zona', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '07_boxplot_zone.png'), dpi=150)
plt.close()
print("   07_boxplot_zone.png")

# Grafico 8: Crescita YoY
fig, ax = plt.subplots(figsize=(10, 6))
years = df_yearly['year'].astype(int).astype(str).tolist()
growth_rates = [0] + df_yearly['yoy_growth'].dropna().tolist()
colors = [COLORS['green'] if g >= 0 else COLORS['red'] for g in growth_rates]
bars = ax.bar(years, growth_rates, color=colors, edgecolor='white')
ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
ax.set_xlabel('Anno', fontsize=12)
ax.set_ylabel('Crescita YoY (%)', fontsize=12)
ax.set_title('Crescita Anno su Anno', fontsize=14, fontweight='bold')
for bar, val in zip(bars, growth_rates):
    if val != 0:
        offset = 1 if val > 0 else -3
        va = 'bottom' if val > 0 else 'top'
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset,
                f'{val:+.1f}%', ha='center', va=va, fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(charts_dir, '08_crescita_yoy.png'), dpi=150)
plt.close()
print("   08_crescita_yoy.png")

print()
print(f"Grafici salvati in: {charts_dir}")
print()


# EXPORT CSV
# Salvo i dati aggregati per chi vuole usarli in Excel o altri tool

df_markets.to_csv(os.path.join(output_dir, 'market_analysis.csv'), index=False)
df_customers.to_csv(os.path.join(output_dir, 'customer_analysis.csv'), index=False)
df_yearly.to_csv(os.path.join(output_dir, 'yearly_analysis.csv'), index=False)

print("CSV esportati:")
print("   - market_analysis.csv")
print("   - customer_analysis.csv")
print("   - yearly_analysis.csv")
print()

print("=" * 50)
print("FATTO")
print()
print("Nota: questo script usa SQL per le aggregazioni e Python solo per i grafici.")
print("La logica di business e tutta in analysis.sql, qui si fa solo visualizzazione.")
