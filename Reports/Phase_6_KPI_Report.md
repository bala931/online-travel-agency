# Phase 6 — KPI Monitoring Dashboard Report

**Project**: OTA Performance & Channel Management
**Phase**: 6 — KPI Monitoring Dashboard Datasets
**Script**: `Python/kpi_dashboard.py`

---

## Portfolio KPI Summary

| KPI | Value |
|-----|-------|
| Total Bookings | 5,900 |
| Net Revenue | $3,221,903.70 |
| Gross Revenue | $3,672,315.66 |
| Commission Amount | $450,411.96 |
| Avg Commission Rate | 13.77% |
| Cancellation Rate | 14.14% |
| Total Room Nights | 15,486 |
| ADR (Avg Daily Rate) | $208.05 |
| RevPAR | $7.06 |
| Estimated Occupancy Rate | 3.39% |

---

## Top OTAs by Net Revenue

| OTA | Bookings | Net Revenue | Cancel Rate | Avg Commission |
|-----|----------|------------|------------|----------------|
| EaseMyTrip | 393 | $240,960 | 14.0% | 11.0% |
| Trivago | 422 | $237,390 | 13.0% | 10.0% |
| Airbnb | 388 | $236,630 | 15.7% | 10.0% |
| Agoda | 395 | $235,373 | 13.9% | 12.0% |
| Goibibo | 403 | $231,641 | 14.1% | 14.0% |

---

## Top Properties by Net Revenue

| Hotel | Bookings | Net Revenue | Cancel Rate | ADR |
|-------|----------|------------|------------|-----|
| Burj Al Arab | 243 | $279,241 | 15.6% | $432.93 |
| The Plaza Hotel | 258 | $204,413 | 14.3% | $309.72 |
| Mandarin Oriental | 251 | $203,456 | 16.7% | $305.03 |
| Hotel Ritz | 225 | $197,917 | 15.6% | $308.28 |
| Taj Mahal Palace | 254 | $183,187 | 14.6% | $254.78 |

---

## Output Files

| File | Description |
|------|-------------|
| `Dataset/kpi_monthly.csv` | Monthly KPI metrics |
| `Dataset/kpi_by_ota.csv` | OTA-level KPI summary |
| `Dataset/kpi_by_property.csv` | Property-level KPI summary |
| `Dataset/kpi_by_customer_segment.csv` | Customer segment KPIs |
| `Dataset/kpi_summary.csv` | Single-row portfolio snapshot |
| `Images/48_kpi_scorecard.png` | Portfolio KPI tile scorecard |
| `Images/49_monthly_revenue_adr.png` | Monthly Revenue and ADR trends |
| `Images/50_ota_revenue_commission.png` | OTA revenue and commission comparison |
| `Images/51_occupancy_heatmap.png` | Room nights heatmap by month × property |
| `Images/52_cancellation_analysis.png` | Cancellation rate by OTA and monthly |
| `Images/53_customer_segment_kpi.png` | Customer segment revenue and bookings |

---

## Recommendations

1. **RevPAR Improvement**: Focus upselling strategies on low-ADR periods to lift RevPAR.
2. **OTA Commission Renegotiation**: Platforms exceeding 25% commission deserve contract review.
3. **Cancellation Reduction**: OTAs with >20% cancel rate should offer incentive-based retention.
4. **Segment Focus**: Direct investment in top-revenue segments to maximise lifetime value.
5. **Occupancy Efficiency**: Identify low-occupancy months for dynamic pricing campaigns.