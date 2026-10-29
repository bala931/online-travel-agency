# Phase 5 — Fraud Detection Technical Report

**Project**: OTA Performance & Channel Management
**Phase**: 5 — Fraud Detection
**Script**: `Python/fraud_detection.py`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Bookings Analysed | 5,900 |
| Total Fraud Flags Raised | 709 |
| Unique Bookings Flagged | 260 |
| Flag Rate (% of bookings) | 4.41% |
| Revenue Associated with Flags | $2,405,540.04 |
| HIGH Severity Flags | 0 |
| MEDIUM Severity Flags | 323 |
| LOW Severity Flags | 386 |

---

## Detection Methods

### Rule-Based Detectors

| Flag Type | Description | Severity |
|-----------|-------------|----------|
| `DUPLICATE_BOOKING` | Same Customer+Hotel+Checkin on same Booking_Date | HIGH |
| `ABNORMAL_AMOUNT` | Net_Revenue deviates > 3σ from Room_Type mean | MEDIUM |
| `HIGH_COMMISSION` | Commission_Rate > 30% | MEDIUM |
| `EXCESSIVE_CANCELLATION` | Customer cancel rate > 80% (min 5 bookings) | HIGH |
| `SUSPECT_FREQUENCY` | ≥10 bookings by same customer in any 30-day window | HIGH |

### Statistical Anomaly Detectors

| Flag Type | Description | Severity |
|-----------|-------------|----------|
| `IQR_OUTLIER_*` | Value outside Q1 − 3×IQR or Q3 + 3×IQR | LOW |
| `ZSCORE_OUTLIER_*` | \|Z-score\| > 3.0 | MEDIUM |

---

## Flag Summary by Type

| Flag Type | Count |
|-----------|-------|
| `IQR_OUTLIER_COMMISSION_AMOUNT` | 194 |
| `IQR_OUTLIER_NET_REVENUE` | 192 |
| `ZSCORE_OUTLIER_NET_REVENUE` | 117 |
| `ABNORMAL_AMOUNT` | 104 |
| `ZSCORE_OUTLIER_COMMISSION_AMOUNT` | 102 |

---

## Output Files

| File | Description |
|------|-------------|
| `Dataset/fraud_report.csv` | All flagged booking records with flag type, severity, notes |
| `Images/42_fraud_flag_distribution.png` | Bar chart of flag type counts |
| `Images/43_fraud_severity.png` | Severity pie and stacked bar |
| `Images/44_fraud_revenue_risk.png` | Revenue at risk by flag type |
| `Images/45_fraud_by_ota.png` | Fraud flags per OTA platform |
| `Images/46_commission_distribution.png` | Commission distribution with threshold |
| `Images/47_fraud_monthly_trend.png` | Monthly fraud flag trend |

---

## Recommendations

1. **Duplicate Bookings**: Implement a real-time deduplication check at the booking API level to prevent same-day duplicate reservations.
2. **High Commission OTAs**: Renegotiate contracts with platforms that systematically exceed 30% commission rates.
3. **Excessive Cancellations**: Enforce non-refundable policies or deposit requirements for customers with cancel rates above 80%.
4. **Suspect Frequency**: Flag accounts making ≥10 bookings in 30 days for manual review to detect bot-driven or bulk reseller activity.
5. **Statistical Outliers**: Audit IQR/Z-score flagged transactions for pricing system errors or manual override abuse.