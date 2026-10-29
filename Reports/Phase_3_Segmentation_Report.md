# Phase 3 Technical & Business Report — Customer Segmentation (RFM Analysis)

## 1. Objectives

Phase 3 applies the **RFM (Recency, Frequency, Monetary)** framework to classify the OTA's 989 active customers into behavioural segments. The goals are:

- Quantify customer value objectively using three dimensions: **how recently** they booked, **how often** they book, and **how much revenue** they generate.
- Assign each customer a 1–5 score per dimension and map them to one of **11 named business segments**.
- Identify top-value customers (Champions), customers in decline (At Risk, Hibernating), and recently acquired customers with growth potential (Promising, Recent Customers).
- Export a clean `rfm_segments.csv` for use in Phases 6–9 (dashboards, forecasting, cohort retention).
- Generate prioritised marketing and retention recommendations grounded in data.

---

## 2. Methodology

```mermaid
graph TD
    A[ota_master_dataset.csv] --> B[Filter: Confirmed Bookings Only]
    B --> C[Group by Customer_ID]
    C --> D[Recency: Days since last booking]
    C --> E[Frequency: Count of bookings]
    C --> F[Monetary: Sum of Net_Revenue]
    D & E & F --> G[Quintile Scoring: 1-5 per metric]
    G --> H[RFM_Score String: e.g. 545]
    H --> I[Segment Mapping Table + Fallback Rules]
    I --> J[rfm_segments.csv: 989 customers, 25 columns]
    J --> K[12 Visualisations saved to Images/]
```

**Script:** [customer_segmentation.py](file:///c:/Users/balam/OneDrive/Desktop/OAT/Python/customer_segmentation.py)

**Reference Date for Recency:** `2026-07-01` (day after the last confirmed booking date)

**RFM Scoring Logic:**

| Metric | Direction | Score 5 = |
|--------|-----------|-----------|
| Recency | Inverted (lower days = higher score) | Booked within past few weeks |
| Frequency | Direct (higher count = higher score) | Booked most often |
| Monetary | Direct (higher revenue = higher score) | Generated highest net revenue |

All three dimensions are scored 1–5 using **quintile binning** (`pd.qcut` with `rank(method='first')` to handle ties). This ensures exactly 20% of customers per quintile band per metric.

---

## 3. RFM Output — Key Metrics

| Metric | Value |
|--------|-------|
| Confirmed Bookings Used | 4,898 |
| Unique Customers Segmented | 989 |
| Reference Date | 2026-07-01 |
| Total Confirmed Net Revenue | $2,663,985.85 |
| **Avg Customer Lifetime Value (CLV)** | **$2,693.62** |
| Median Booking Frequency | 3 bookings |

---

## 4. Segment Results

| Segment | Customers | % of Base | Total Revenue | Revenue Share | Avg CLV | Avg Recency (Days) |
|---------|-----------|-----------|---------------|---------------|---------|-------------------|
| **Champions** | 232 | 23.5% | $1,412,151 | **53.0%** | $6,087 | 41 |
| **Loyal Customers** | 141 | 14.3% | $539,063 | 20.2% | $3,823 | 154 |
| At Risk | 68 | 6.9% | $220,550 | 8.3% | $3,243 | 391 |
| Hibernating | 118 | 11.9% | $120,612 | 4.5% | $1,022 | 449 |
| Potential Loyalists | 81 | 8.2% | $96,959 | 3.6% | $1,197 | 89 |
| Can't Lose Them | 55 | 5.6% | $79,178 | 3.0% | $1,440 | 665 |
| Need Attention | 29 | 2.9% | $64,055 | 2.4% | $2,209 | 70 |
| Promising | 56 | 5.7% | $55,668 | 2.1% | $994 | 130 |
| About to Sleep | 70 | 7.1% | $29,765 | 1.1% | $425 | 364 |
| Recent Customers | 54 | 5.5% | $23,975 | 0.9% | $444 | 88 |
| Lost | 85 | 8.6% | $22,009 | 0.8% | $259 | 678 |

> **Key Finding — Pareto Principle Confirmed:** The top two segments (**Champions** + **Loyal Customers**, 37.8% of customers) account for **73.2% of all confirmed net revenue** ($1.95M out of $2.66M). This validates the classic 80/20 rule and means retention of these two groups is the single highest-ROI marketing investment.

---

## 5. Visualisations

### Chart 15 — Segment Overview (Customer vs Revenue Share + Bubble Chart)
**File:** [15_rfm_segment_overview.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/15_rfm_segment_overview.png)

A dual-panel view showing:
- **Left panel (bar chart)**: Every segment's customer % share (lighter shade) vs. revenue % share (solid). The gap between the two bars reveals revenue concentration — Champions take 23.5% of customers but 53.0% of revenue.
- **Right panel (bubble chart)**: Positions each segment on Customer Count × Avg Monetary axes. Bubble size represents total segment revenue. Champions sit at the highest position on both axes.

---

### Chart 16 — RFM Score Heatmap (R × F, coloured by Avg Monetary)
**File:** [16_rfm_heatmap.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/16_rfm_heatmap.png)

A 5×5 matrix where rows are **Recency Scores** (R1–R5) and columns are **Frequency Scores** (F1–F5). Each cell is shaded by average Monetary value. The top-right cell (R=5, F=5) shows the highest average CLV, confirming that customers who book frequently and recently are also the biggest spenders.

---

### Chart 17 — RFM Metric Distributions
**File:** [17_rfm_distributions.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/17_rfm_distributions.png)

Histograms + KDE curves for raw Recency, Frequency, and Monetary values:
- **Recency**: Bimodal distribution — many customers booked very recently (active) and a second cluster at ~400–700 days (lapsed/at-risk).
- **Frequency**: Heavily right-skewed. Majority of customers book only 1–4 times; a tail of high-frequency Champions books 10–20 times.
- **Monetary**: Power-law distribution. A small group of Champions generates $10K–$30K+ lifetime revenue while the majority generate $200–$1,000.

---

### Chart 18 — Score Distributions (R, F, M separately)
**File:** [18_rfm_score_distributions.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/18_rfm_score_distributions.png)

Confirms that quintile scoring produces approximately equal-sized bins (~198 customers per score band), validating the fairness of the scoring mechanism.

---

### Chart 19 — Revenue by Customer Segment (Ranked Bar)
**File:** [19_segment_revenue.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/19_segment_revenue.png)

Champions' $1.41M total revenue dwarfs all other segments. The next-best segment (Loyal Customers at $539K) is 2.6× lower, highlighting the disproportionate contribution of the top tier.

---

### Chart 20 — Radar Profile Comparison
**File:** [20_radar_profiles.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/20_radar_profiles.png)

Five radar charts (Champions, Loyal Customers, At Risk, Hibernating, Lost) plotted on normalised R/F/M + Review Score + Total Nights axes:
- **Champions**: Large, balanced polygon across all 5 metrics.
- **At Risk**: Strong on F/M/Review but small Recency wing — they were valuable but have stopped booking.
- **Lost**: Tiny polygons across all metrics — low engagement across every dimension.

---

### Chart 21 — Segment × Loyalty Status Heatmap
**File:** [21_loyalty_segment.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/21_loyalty_segment.png)

A clear pattern emerges: **Platinum customers are overwhelmingly Champions or Loyal Customers**, confirming the loyalty programme is working effectively. However, a subset of Platinum customers appears in "At Risk" and "Can't Lose Them" — these are the highest-priority targets for re-engagement.

---

### Chart 22 — Average R, F, M by Segment (Horizontal Bars)
**File:** [22_segment_rfm_bars.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/22_segment_rfm_bars.png)

Three panels showing how each segment ranks on each metric individually. "Can't Lose Them" customers have the highest average Recency (664 days) — proving they were once high-value but have been entirely inactive. "Champions" lead in Frequency (~11 bookings) and Monetary (~$6,087).

---

### Chart 23 — Top 20 Champion Customers
**File:** [23_top_champions.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/23_top_champions.png)

Named leaderboard of the top 20 customers by lifetime net revenue. These are the individuals to target with VIP programmes, exclusive previews, and personal account management.

---

### Chart 24 — RFM Total Score Histogram
**File:** [24_rfm_total_histogram.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/24_rfm_total_histogram.png)

Shows the distribution of RFM Total Scores (3–15) with each bar coloured by the dominant segment at that score level. Score 15 bars are dark green (Champions). Score 3 bars are near-black (Lost).

---

### Chart 25 — Country × Segment Stacked Bar
**File:** [25_country_segment.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/25_country_segment.png)

Reveals which countries have the most Champions (high green) vs. Lost/Hibernating customers (dark tones). The USA, India, and UK have the highest absolute Champion counts. India also has a significant "Lost" segment — suggesting lower retention effectiveness in that market.

---

### Chart 26 — Executive KPI Scorecard
**File:** [26_rfm_kpi_scorecard.png](file:///c:/Users/balam/OneDrive/Desktop/OAT/Images/26_rfm_kpi_scorecard.png)

10-panel executive scorecard displaying: Total Customers, Champions, Loyal Customers, At Risk, Lost, Champion Revenue Share (53%), Avg CLV ($2,693), Median Frequency (3 bookings), Avg Recency (262 days), and Total Portfolio Revenue ($2.66M).

---

## 6. Integration with Future Phases

| Future Phase | RFM Integration |
|--------------|----------------|
| **Phase 4 (Performance)** | Break down OTA revenue by customer segment |
| **Phase 5 (Fraud)** | Flag anomalous customers vs. expected RFM behaviour |
| **Phase 6–7 (Dashboards)** | RFM segment slicer in KPI and Interactive Dashboards |
| **Phase 8 (Forecasting)** | Segment-weighted revenue projections (Champions drive predictions) |
| **Phase 9 (Cohort)** | Align cohort months with RFM first-booking dates to trace segment evolution |

The file `Dataset/rfm_segments.csv` (989 rows, 25 columns) is the primary integration asset.

---

## 7. Challenges

1. **Skewed Frequency Distribution**: Most customers book only 1–3 times, so frequency quintile bins are narrow in the low range. `rank(method='first')` was used to break ties before `qcut`, ensuring equal-sized quintiles even with many ties at Frequency=1.
2. **Only 47 Customers Lacked RFM Mapping**: The explicit `SEGMENT_MAP` dictionary covers ~300 RFM string combinations. An 8-rule fallback function (`fallback_segment`) correctly assigned remaining combinations using `RFM_Total` and `R_Score` thresholds.
3. **Confirmed Bookings Only**: Cancellations and no-shows were intentionally excluded. Including them would inflate frequency counts while distorting monetary values (cancelled bookings produce zero revenue).

---

## 8. Business Recommendations

| Priority | Segment | Action | Expected Outcome |
|----------|---------|--------|-----------------|
| 🔴 **Critical** | At Risk (68) | Send personalised win-back offer (e.g., 15% off next stay + priority check-in) | Recover 30–40% with targeted outreach → ~$66K revenue at risk |
| 🔴 **Critical** | Can't Lose Them (55) | Dedicated account manager outreach; survey to understand churn reason | Avg CLV $1,440 × 55 = $79K revenue risk; some recoverable with high-touch service |
| 🟡 **High** | Champions (232) | VIP programme, early access to new hotels, dedicated concierge line | Increase frequency further; Champions already drive 53% of revenue |
| 🟡 **High** | Potential Loyalists (81) | Nurture with loyalty upgrade path (Standard → Silver offers) | Convert to Loyal Customers segment (3× higher avg CLV) |
| 🟡 **High** | Lost (85) | Low-cost re-engagement campaign (email + targeted social ads) | Even 10% reactivation = 8–9 customers, saving ~$2,200 revenue |
| 🟢 **Medium** | Promising (56) | Send second-booking incentive within 30 days of first booking | Increase frequency from 1.6 to 3+ → move to Potential Loyalists |
| 🟢 **Medium** | Hibernating (118) | Segment-specific seasonal offer (Summer/Winter flash deals) | Avg Recency 449 days — reactivation before they join "Lost" segment |
| 🟢 **Low** | Recent Customers (54) | Welcome sequence + personalised property recommendations | Build habit early; these are new customers who haven't yet formed loyalty |

---

## 9. Conclusion

Phase 3 has produced a granular, data-driven customer segmentation using the gold-standard RFM framework. The 989 customers are now classified into 11 actionable segments stored in `rfm_segments.csv`. The Pareto concentration — 37.8% of customers driving 73.2% of revenue — clearly defines where marketing budget should be concentrated: **retaining Champions and Loyal Customers first, re-engaging At Risk and Can't Lose Them second**.

All segmentation outputs (CSV + 12 visualisations + SQL queries) are production-ready and directly feed into Phases 4 through 9.
