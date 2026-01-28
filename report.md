# Tech Sales Analysis Report

## Executive Summary

**Goal:** Understand why sales are declining and identify where revenue is concentrated.

**Dataset:** 150,000 sales transactions from 2017 to 2020, covering 15 markets in India and 38 customers.

**Key finding:** The business has a serious concentration problem. One market (Delhi) accounts for 52% of revenue and one customer (Electricalsara) accounts for 42%. On top of that, sales have been declining for two consecutive years: -18.8% in 2019, and 2020 started even worse.

---

## Business Context

This analysis helps understand business health before making strategic decisions. When sales drop, the first step is understanding where and why.

**Questions addressed:**
- Which markets and customers generate the most revenue?
- Is there too much dependency on a few customers or markets?
- What does the trend look like over time?
- Are there underdeveloped geographic areas?

---

## Technical Approach

I split the work between SQL and Python to keep things clean:

**SQL handles all the calculations:**
- Data exploration and quality checks
- Revenue aggregations (by market, customer, zone, time)
- Currency normalization (USD to INR conversion)
- KPI validation before building the dashboard

**Python handles only visualizations:**
- Connects to MySQL and runs the aggregation queries
- Generates 8 charts for the report
- No duplicate business logic - just plotting what SQL calculated

This separation makes the code easier to maintain and avoids the "same calculation in two places" problem.

---

## Data Overview

**Source:** Company MySQL database with 5 related tables.

**Structure:**
- transactions: each row is a sale with date, quantity, amount, currency
- customers: customer info with type (Brick & Mortar vs E-Commerce)
- markets: 15 Indian cities grouped into 3 zones (North, Central, South)
- products: product catalog with category
- date: calendar table for time-based joins

**Period covered:** October 2017 - June 2020

**Issues found:**
- Some transactions in USD instead of INR (needed conversion)
- Transactions with zero or negative amounts (likely returns)
- No cost data available (can't calculate margins)

---

## Data Cleaning

**Main problem:** Mixed currencies. Found US dollar transactions mixed with Indian rupees. Applied a conversion rate of 74 INR per USD to normalize.

```sql
SELECT
    SUM(CASE
        WHEN currency = 'USD' THEN sales_amount * 74
        ELSE sales_amount
    END) AS normalized_revenue
FROM transactions;
```

Also checked for anomalies:
- Found suspicious transactions with zero/negative amounts
- No null values in key fields

---

## Key Findings

### Revenue by Market

| Rank | Market | Revenue | % of Total |
|------|--------|---------|------------|
| 1 | Delhi NCR | 519.5M | 52.7% |
| 2 | Mumbai | 150.1M | 15.2% |
| 3 | Ahmedabad | 132.3M | 13.4% |
| 4 | Bhopal | 58.6M | 5.9% |
| 5 | Nagpur | 55.0M | 5.6% |

**Insight:** Top 3 markets generate 81% of total revenue. This is extremely concentrated.

### Revenue by Zone

| Zone | Revenue | % of Total |
|------|---------|------------|
| North | 676.8M | 68.6% |
| Central | 264.4M | 26.8% |
| South | 45.4M | 4.6% |

**Insight:** South zone is underperforming despite having major tech cities (Bengaluru, Chennai, Kochi).

### Top Customers

| Rank | Customer | Revenue | % of Total |
|------|----------|---------|------------|
| 1 | Electricalsara Stores | 413.9M | 42.0% |
| 2 | Electricalslytical | 49.6M | 5.0% |
| 3 | Excel Stores | 49.1M | 5.0% |
| 4 | Premium Stores | 44.9M | 4.6% |
| 5 | Nixon | 43.8M | 4.4% |

**Insight:** Top 5 customers generate 61% of revenue. But the real concern is that one customer alone does 42%. If Electricalsara left, the business would lose nearly half its revenue.

### Revenue Trend

| Year | Revenue | YoY Change |
|------|---------|------------|
| 2017 | 93.3M | - |
| 2018 | 414.8M | +344.6% |
| 2019 | 336.7M | -18.8% |
| 2020 | 142.2M | (partial year) |

**Insight:** After strong growth in 2018, the business started declining. The 2019 drop of 18.8% is significant, and 2020 (only 6 months of data) shows the trend continuing.

---

## Recommendations

If I were presenting this to management:

**The main problem isn't that we sell too little - it's that we depend too much on too few.**

Delhi and Electricalsara together are basically half the business. If either one had problems, we'd be in serious trouble.

**Suggested actions:**

1. **Diversify customers:** Need sales programs to acquire new customers and reduce dependency on Electricalsara. Even bringing them from 42% to 30% would help.

2. **Expand in South:** Bengaluru, Chennai, and Hyderabad are important tech cities but we do almost nothing there. Worth investigating why.

3. **Understand the decline:** Two years of negative trend isn't normal. Need qualitative analysis (talk to sales team, check competition) to understand causes.

4. **Protect top accounts:** In the meantime, make sure big customers are satisfied and have solid contracts.

---

## Limitations

**What's missing from this analysis:**
- Cost data: without margins, I can't tell if we're selling a lot but making little
- Competition data: the decline could be due to competitors I can't see in the data
- Qualitative data: numbers show what's happening, not why
- 2020 is incomplete (only first 6 months), so YoY comparisons are partial

**What I would improve:**
- Add a historical exchange rate table instead of using a fixed rate
- Do cohort analysis to see customer retention over time
- Segment by product type to understand what's declining vs. what's not
- Integrate external market data for context

---

*Analysis completed using SQL (aggregations), Python (visualizations), and Tableau (interactive dashboard).*
