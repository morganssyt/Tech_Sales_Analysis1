-- ANALISI VENDITE TECH - QUERY SQL
-- Scopo: Esplorazione dati e validazione KPI prima di costruire la dashboard Tableau
-- Database: sales (MySQL)
-- Tabelle: transactions, customers, products, markets, date


-- SEZIONE 1: ESPLORAZIONE INIZIALE DEI DATI
-- Prima di costruire qualsiasi cosa, volevo capire con cosa stavo lavorando

-- Controllare quali tabelle esistono e il conteggio righe
SELECT 'transactions' AS nome_tabella, COUNT(*) AS conteggio_righe FROM sales.transactions
UNION ALL
SELECT 'customers', COUNT(*) FROM sales.customers
UNION ALL
SELECT 'products', COUNT(*) FROM sales.products
UNION ALL
SELECT 'markets', COUNT(*) FROM sales.markets
UNION ALL
SELECT 'date', COUNT(*) FROM sales.date;

-- Vedere il range di date nei dati
SELECT MIN(order_date) AS data_iniziale, MAX(order_date) AS data_finale
FROM sales.transactions;

-- Controllare i tipi di valuta (ho scoperto che era importante dopo)
SELECT DISTINCT currency
FROM sales.transactions;


-- SEZIONE 2: CALCOLI FATTURATO TOTALE
-- Queste query mi hanno aiutato a verificare i numeri KPI prima di metterli in Tableau

-- Fatturato totale per il 2020 (join con tabella date per filtrare per anno)
SELECT SUM(sales.transactions.sales_amount) AS fatturato_totale_2020
FROM sales.transactions
INNER JOIN sales.date ON sales.transactions.order_date = sales.date.date
WHERE sales.date.year = 2020;

-- Fatturato totale su tutti gli anni
SELECT SUM(sales_amount) AS fatturato_totale_sempre
FROM sales.transactions;

-- Fatturato suddiviso per anno
SELECT d.year AS anno, SUM(t.sales_amount) AS fatturato_annuale
FROM sales.transactions t
INNER JOIN sales.date d ON t.order_date = d.date
GROUP BY d.year
ORDER BY d.year;


-- SEZIONE 3: FATTURATO PER MERCATO
-- Questo alimenta direttamente il grafico a barre "Fatturato per Mercato" in Tableau

SELECT
    m.markets_name AS nome_mercato,
    m.zone AS zona,
    SUM(t.sales_amount) AS fatturato_totale,
    COUNT(*) AS conteggio_transazioni
FROM sales.transactions t
INNER JOIN sales.markets m ON t.market_code = m.markets_code
GROUP BY m.markets_name, m.zone
ORDER BY fatturato_totale DESC;

-- Controllo veloce: quale zona performa meglio in generale?
SELECT
    m.zone AS zona,
    SUM(t.sales_amount) AS fatturato_zona
FROM sales.transactions t
INNER JOIN sales.markets m ON t.market_code = m.markets_code
GROUP BY m.zone
ORDER BY fatturato_zona DESC;


-- SEZIONE 4: QUANTITA VENDUTE PER MERCATO
-- Il volume puo raccontare una storia diversa dal fatturato

SELECT
    m.markets_name AS nome_mercato,
    SUM(t.sales_qty) AS quantita_totale,
    SUM(t.sales_amount) AS fatturato_totale,
    ROUND(SUM(t.sales_amount) / SUM(t.sales_qty), 2) AS prezzo_medio_per_unita
FROM sales.transactions t
INNER JOIN sales.markets m ON t.market_code = m.markets_code
GROUP BY m.markets_name
ORDER BY quantita_totale DESC;


-- SEZIONE 5: ANALISI TOP CLIENTI
-- Identificare chi genera piu fatturato

-- Top 5 clienti per fatturato
SELECT
    c.custmer_name AS nome_cliente,
    c.customer_type AS tipo_cliente,
    SUM(t.sales_amount) AS fatturato_totale,
    SUM(t.sales_qty) AS quantita_totale
FROM sales.transactions t
INNER JOIN sales.customers c ON t.customer_code = c.customer_code
GROUP BY c.custmer_name, c.customer_type
ORDER BY fatturato_totale DESC
LIMIT 5;

-- Breakdown per tipo cliente (Brick & Mortar vs E-Commerce)
SELECT
    c.customer_type AS tipo_cliente,
    COUNT(DISTINCT c.customer_code) AS conteggio_clienti,
    SUM(t.sales_amount) AS fatturato_totale
FROM sales.transactions t
INNER JOIN sales.customers c ON t.customer_code = c.customer_code
GROUP BY c.customer_type
ORDER BY fatturato_totale DESC;


-- SEZIONE 6: ANALISI TOP PRODOTTI
-- Quali prodotti performano meglio?

-- Top 5 prodotti per fatturato
SELECT
    p.product_code AS codice_prodotto,
    p.product_type AS tipo_prodotto,
    SUM(t.sales_amount) AS fatturato_totale,
    SUM(t.sales_qty) AS quantita_totale
FROM sales.transactions t
INNER JOIN sales.products p ON t.product_code = p.product_code
GROUP BY p.product_code, p.product_type
ORDER BY fatturato_totale DESC
LIMIT 5;

-- Performance per tipo prodotto
SELECT
    p.product_type AS tipo_prodotto,
    COUNT(DISTINCT p.product_code) AS conteggio_prodotti,
    SUM(t.sales_amount) AS fatturato_totale,
    SUM(t.sales_qty) AS quantita_totale
FROM sales.transactions t
INNER JOIN sales.products p ON t.product_code = p.product_code
GROUP BY p.product_type
ORDER BY fatturato_totale DESC;


-- SEZIONE 7: ANALISI TEMPORALE
-- Capire i trend nel tempo, alimenta il grafico linea/area

-- Trend fatturato mensile
SELECT
    d.year AS anno,
    d.month_name AS nome_mese,
    SUM(t.sales_amount) AS fatturato_mensile
FROM sales.transactions t
INNER JOIN sales.date d ON t.order_date = d.date
GROUP BY d.year, d.month_name
ORDER BY d.year, fatturato_mensile DESC;

-- Confronto anno su anno
SELECT
    d.year AS anno,
    SUM(t.sales_amount) AS fatturato_totale,
    SUM(t.sales_qty) AS quantita_totale,
    COUNT(*) AS conteggio_transazioni
FROM sales.transactions t
INNER JOIN sales.date d ON t.order_date = d.date
GROUP BY d.year
ORDER BY d.year;


-- SEZIONE 8: CONTROLLI QUALITA DATI
-- Trovati alcuni problemi che serviva gestire in Tableau

-- Controllare transazioni in valute diverse
SELECT
    currency AS valuta,
    COUNT(*) AS conteggio_transazioni,
    SUM(sales_amount) AS importo_totale
FROM sales.transactions
GROUP BY currency;

-- Nota: Trovate transazioni USD che servono conversione in INR
-- In Tableau, ho creato un campo calcolato:
-- IF [currency] == 'USD' THEN [sales_amount] * 74 ELSE [sales_amount] END

-- Controllare valori null nei campi chiave
SELECT
    SUM(CASE WHEN customer_code IS NULL THEN 1 ELSE 0 END) AS clienti_null,
    SUM(CASE WHEN product_code IS NULL THEN 1 ELSE 0 END) AS prodotti_null,
    SUM(CASE WHEN sales_amount IS NULL THEN 1 ELSE 0 END) AS importi_null,
    SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) AS date_null
FROM sales.transactions;

-- Controllare importi negativi o zero (potenziali problemi dati)
SELECT COUNT(*) AS transazioni_sospette
FROM sales.transactions
WHERE sales_amount <= 0;


-- SEZIONE 9: QUERY FATTURATO NORMALIZZATO
-- Dopo aver scoperto il problema valute, ecco come calcolo il fatturato "vero" con conversione valuta

-- Fatturato totale normalizzato (convertendo USD in INR)
SELECT
    SUM(CASE
        WHEN currency = 'USD' THEN sales_amount * 74
        ELSE sales_amount
    END) AS fatturato_totale_normalizzato
FROM sales.transactions;

-- Fatturato normalizzato per mercato
SELECT
    m.markets_name AS nome_mercato,
    SUM(CASE
        WHEN t.currency = 'USD' THEN t.sales_amount * 74
        ELSE t.sales_amount
    END) AS fatturato_normalizzato
FROM sales.transactions t
INNER JOIN sales.markets m ON t.market_code = m.markets_code
GROUP BY m.markets_name
ORDER BY fatturato_normalizzato DESC;


-- SEZIONE 10: ANALISI COMBINATA
-- Query piu complesse con join di piu tabelle

-- Dettaglio transazione completo con tutti i dati dimensionali
SELECT
    t.order_date AS data_ordine,
    d.year AS anno,
    d.month_name AS nome_mese,
    m.markets_name AS nome_mercato,
    m.zone AS zona,
    c.custmer_name AS nome_cliente,
    c.customer_type AS tipo_cliente,
    p.product_code AS codice_prodotto,
    p.product_type AS tipo_prodotto,
    t.sales_qty AS quantita,
    t.sales_amount AS importo,
    t.currency AS valuta,
    CASE
        WHEN t.currency = 'USD' THEN t.sales_amount * 74
        ELSE t.sales_amount
    END AS importo_normalizzato
FROM sales.transactions t
INNER JOIN sales.date d ON t.order_date = d.date
INNER JOIN sales.markets m ON t.market_code = m.markets_code
INNER JOIN sales.customers c ON t.customer_code = c.customer_code
INNER JOIN sales.products p ON t.product_code = p.product_code
ORDER BY t.order_date DESC
LIMIT 100;

-- Analisi combinazione Mercato + Cliente
-- Quali clienti sono piu forti in quali mercati?
SELECT
    m.markets_name AS nome_mercato,
    c.custmer_name AS nome_cliente,
    SUM(t.sales_amount) AS fatturato_totale
FROM sales.transactions t
INNER JOIN sales.markets m ON t.market_code = m.markets_code
INNER JOIN sales.customers c ON t.customer_code = c.customer_code
GROUP BY m.markets_name, c.custmer_name
ORDER BY m.markets_name, fatturato_totale DESC;


-- NOTE E LIMITAZIONI
/*
Cose che ho notato durante questa analisi:

1. Problema Valute: Alcune transazioni sono in USD, altre in INR.
   Ho usato un tasso di cambio fisso di 74 INR/USD per la normalizzazione.
   In uno scenario reale, userei una tabella di tassi di cambio con tassi storici o in tempo reale.

2. Completezza Dati:
   Nessun dato sui costi disponibile, quindi non posso calcolare i margini di profitto.
   Nessun dato sulla posizione cliente oltre al livello mercato.

3. Semplificazioni:
   Ho assunto che tutte le transazioni siano valide (nessuna gestione resi/rimborsi).
   Nessun controllo duplicati effettuato.
   Il filtro date assume join puliti sulle date.

4. Cosa farei diversamente in un lavoro reale:
   Costruire prima un report sulla qualita dati appropriato.
   Creare una tabella di staging con dati normalizzati.
   Documentare tutte le assunzioni piu formalmente.
   Aggiungere indici per le performance su dataset grandi.
*/
