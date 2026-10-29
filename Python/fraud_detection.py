"""
Phase 5: Fraud Detection
OTA Performance & Channel Management Project
============================================================
Inputs  : Dataset/ota_master_dataset.csv
Outputs : Dataset/fraud_report.csv
          Images/42_*.png – 47_*.png
          Reports/Phase_5_Fraud_Report.md
============================================================
Detection methods:
  Rule-Based:
    1. DUPLICATE_BOOKING      – same Customer+Hotel+Checkin within same booking day
    2. ABNORMAL_AMOUNT        – Net_Revenue outside µ ± 3σ per Room_Type
    3. HIGH_COMMISSION        – Commission_Rate > 0.30
    4. EXCESSIVE_CANCELLATION – customer cancel rate > 80% (min 5 bookings)
    5. SUSPECT_FREQUENCY      – ≥10 bookings by same customer in any 30-day window

  Statistical:
    6. IQR_OUTLIER            – Net_Revenue or Commission_Amount below Q1-3×IQR
                                or above Q3+3×IQR
    7. ZSCORE_OUTLIER         – |Z-score| > 3 on Net_Revenue or Commission_Amount
"""
import os
import logging
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# STYLE — identical dark theme
# ─────────────────────────────────────────────
PAL = {
    "bg": "#0F1117", "card": "#1A1D2E",
    "accent1": "#6C63FF", "accent2": "#FF6584",
    "accent3": "#43E97B", "accent4": "#F7971E",
    "accent5": "#00C9FF", "text": "#E8EAF6",
    "sub": "#9FA8DA", "grid": "#2C2F4A",
}
MC = [
    "#6C63FF","#FF6584","#43E97B","#F7971E","#00C9FF",
    "#FF8C69","#A29BFE","#55EFC4","#FD79A8","#FDCB6E",
]

def apply_style():
    plt.rcParams.update({
        "figure.facecolor": PAL["bg"], "axes.facecolor": PAL["card"],
        "axes.edgecolor": PAL["grid"], "axes.labelcolor": PAL["text"],
        "axes.titlecolor": PAL["text"], "axes.titlesize": 13,
        "axes.labelsize": 10, "xtick.color": PAL["sub"],
        "ytick.color": PAL["sub"], "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5, "grid.color": PAL["grid"],
        "grid.linestyle": "--", "grid.alpha": 0.45,
        "legend.facecolor": PAL["card"], "legend.edgecolor": PAL["grid"],
        "legend.labelcolor": PAL["text"], "text.color": PAL["text"],
        "font.family": "DejaVu Sans", "figure.dpi": 150,
    })
apply_style()
def savefig(fig, name):
    os.makedirs("Images", exist_ok=True)
    p = os.path.join("Images", name)
    fig.savefig(p, bbox_inches="tight", facecolor=PAL["bg"])
    plt.close(fig)
    log.info(f"  Saved -> {p}")

def titlebar(fig, title, sub=""):
    fig.text(0.5, 0.987, title, ha="center", va="top",
             fontsize=17, fontweight="bold", color=PAL["text"])
    if sub:
        fig.text(0.5, 0.963, sub, ha="center", va="top",
                 fontsize=10, color=PAL["sub"])

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
def load_data():
    path = os.path.join("Dataset", "ota_master_dataset.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Master dataset not found: {path}")
    df = pd.read_csv(path, parse_dates=["Booking_Date", "Checkin_Date", "Checkout_Date"])
    log.info(f"Dataset loaded: {df.shape}")
    # Ensure numeric columns are properly typed
    for col in ["Net_Revenue", "Gross_Revenue", "Commission_Amount", "Commission_Rate", "Lead_Time"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
# ─────────────────────────────────────────────
# 2. RULE-BASED DETECTION
# ─────────────────────────────────────────────
def detect_duplicate_bookings(df):
    """Flag bookings where the same customer booked the same hotel+checkin on the same day."""
    dups = df.duplicated(
        subset=["Customer_ID", "Hotel_ID", "Checkin_Date", "Booking_Date"],
        keep="first"
    )
    flagged = df[dups].copy()
    flagged["Flag_Type"] = "DUPLICATE_BOOKING"
    flagged["Severity"] = "HIGH"
    flagged["Flag_Notes"] = "Same Customer+Hotel+Checkin on the same Booking_Date"
    log.info(f"  DUPLICATE_BOOKING: {len(flagged)} flags")
    return flagged


def detect_abnormal_amounts(df):
    """Flag Net_Revenue more than 3 std devs from the room-type mean."""
    flagged_list = []
    for rt, grp in df.groupby("Room_Type"):
        mean_r = grp["Net_Revenue"].mean()
        std_r = grp["Net_Revenue"].std()
        if std_r == 0 or pd.isna(std_r):
            continue
        outliers = grp[
            (grp["Net_Revenue"] < mean_r - 3 * std_r) |
            (grp["Net_Revenue"] > mean_r + 3 * std_r)
        ].copy()
        outliers["Flag_Type"] = "ABNORMAL_AMOUNT"
        outliers["Severity"] = "MEDIUM"
        outliers["Flag_Notes"] = (
            f"Net_Revenue outside 3σ for {rt}: "
            f"mean={mean_r:.0f}, std={std_r:.0f}"
        )
        flagged_list.append(outliers)
    if flagged_list:
        flagged = pd.concat(flagged_list, ignore_index=True)
    else:
        flagged = pd.DataFrame(columns=df.columns.tolist() + ["Flag_Type","Severity","Flag_Notes"])
    log.info(f"  ABNORMAL_AMOUNT: {len(flagged)} flags")
    return flagged


def detect_high_commission(df, threshold=0.30):
    """Flag bookings where the commission rate exceeds the threshold."""
    flagged = df[df["Commission_Rate"] > threshold].copy()
    flagged["Flag_Type"] = "HIGH_COMMISSION"
    flagged["Severity"] = "MEDIUM"
    flagged["Flag_Notes"] = f"Commission_Rate > {threshold*100:.0f}%"
    log.info(f"  HIGH_COMMISSION: {len(flagged)} flags")
    return flagged

def detect_excessive_cancellations(df, min_bookings=5, cancel_threshold=0.80):
    """Flag customers who cancel more than cancel_threshold fraction of their bookings."""
    cust_stats = df.groupby("Customer_ID").agg(
        Total=("Booking_ID", "count"),
        Cancelled=("Booking_Status", lambda x: (x == "Cancelled").sum())
    ).reset_index()
    cust_stats["Cancel_Rate"] = cust_stats["Cancelled"] / cust_stats["Total"]
    suspect = cust_stats[
        (cust_stats["Total"] >= min_bookings) &
        (cust_stats["Cancel_Rate"] > cancel_threshold)
    ]["Customer_ID"].tolist()

    flagged = df[df["Customer_ID"].isin(suspect)].copy()
    flagged["Flag_Type"] = "EXCESSIVE_CANCELLATION"
    flagged["Severity"] = "HIGH"
    rate_map = cust_stats.set_index("Customer_ID")["Cancel_Rate"].to_dict()
    flagged["Flag_Notes"] = flagged["Customer_ID"].map(
        lambda c: f"Customer cancel rate = {rate_map.get(c,0)*100:.1f}%"
    )
    log.info(f"  EXCESSIVE_CANCELLATION: {len(flagged)} flags across {len(suspect)} customers")
    return flagged

def detect_suspect_frequency(df, window_days=30, min_bookings=10):
    """Flag customers who make ≥ min_bookings within any rolling window_days-day period."""
    df_sorted = df.sort_values(["Customer_ID", "Booking_Date"]).copy()
    suspect_ids = set()
    for cid, grp in df_sorted.groupby("Customer_ID"):
        dates = grp["Booking_Date"].dropna().sort_values().tolist()
        for i, d in enumerate(dates):
            window_end = d + pd.Timedelta(days=window_days)
            count = sum(1 for dd in dates[i:] if dd <= window_end)
            if count >= min_bookings:
                suspect_ids.add(cid)
                break

    flagged = df[df["Customer_ID"].isin(suspect_ids)].copy()
    flagged["Flag_Type"] = "SUSPECT_FREQUENCY"
    flagged["Severity"] = "HIGH"
    flagged["Flag_Notes"] = f">={min_bookings} bookings in any {window_days}-day window"
    log.info(f"  SUSPECT_FREQUENCY: {len(flagged)} flags across {len(suspect_ids)} customers")
    return flagged


# ─────────────────────────────────────────────
# 3. STATISTICAL ANOMALY DETECTION
# ─────────────────────────────────────────────
def detect_iqr_outliers(df, cols=None, iqr_multiplier=3.0):
    """Flag rows where specified columns fall outside Q1 - k*IQR or Q3 + k*IQR."""
    if cols is None:
        cols = ["Net_Revenue", "Commission_Amount"]
    flagged_list = []
    for col in cols:
        if col not in df.columns:
            continue
        data = df[col].dropna()
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - iqr_multiplier * IQR
        upper = Q3 + iqr_multiplier * IQR
        out = df[(df[col] < lower) | (df[col] > upper)].copy()
        out["Flag_Type"] = f"IQR_OUTLIER_{col.upper()}"
        out["Severity"] = "LOW"
        out["Flag_Notes"] = (
            f"{col} outside [{lower:.2f}, {upper:.2f}] "
            f"(IQR={IQR:.2f}, k={iqr_multiplier})"
        )
        flagged_list.append(out)
        log.info(f"  IQR_OUTLIER_{col.upper()}: {len(out)} flags")
    if flagged_list:
        return pd.concat(flagged_list, ignore_index=True)
    return pd.DataFrame(columns=df.columns.tolist() + ["Flag_Type","Severity","Flag_Notes"])


def detect_zscore_outliers(df, cols=None, z_threshold=3.0):
    """Flag rows where |Z-score| > z_threshold for specified numeric columns."""
    if cols is None:
        cols = ["Net_Revenue", "Commission_Amount"]
    flagged_list = []
    for col in cols:
        if col not in df.columns:
            continue
        mean_c = df[col].mean()
        std_c = df[col].std()
        if std_c == 0 or pd.isna(std_c):
            continue
        z = (df[col] - mean_c) / std_c
        out = df[z.abs() > z_threshold].copy()
        out["Flag_Type"] = f"ZSCORE_OUTLIER_{col.upper()}"
        out["Severity"] = "MEDIUM"
        out["Flag_Notes"] = (
            f"|Z-score| > {z_threshold} for {col}: "
            f"mean={mean_c:.2f}, std={std_c:.2f}"
        )
        flagged_list.append(out)
        log.info(f"  ZSCORE_OUTLIER_{col.upper()}: {len(out)} flags")
    if flagged_list:
        return pd.concat(flagged_list, ignore_index=True)
    return pd.DataFrame(columns=df.columns.tolist() + ["Flag_Type","Severity","Flag_Notes"])

# ─────────────────────────────────────────────
# 4. COMBINE ALL FLAGS
# ─────────────────────────────────────────────
def build_fraud_report(df):
    """Run all detectors and combine into a single fraud report DataFrame."""
    log.info("Running rule-based detectors...")
    parts = [
        detect_duplicate_bookings(df),
        detect_abnormal_amounts(df),
        detect_high_commission(df),
        detect_excessive_cancellations(df),
        detect_suspect_frequency(df),
    ]
    log.info("Running statistical anomaly detectors...")
    parts += [
        detect_iqr_outliers(df),
        detect_zscore_outliers(df),
    ]

    # Combine, keep only rows that were actually flagged
    parts_nonempty = [p for p in parts if len(p) > 0 and "Flag_Type" in p.columns]
    if not parts_nonempty:
        log.warning("No fraud flags detected!")
        return pd.DataFrame()

    report = pd.concat(parts_nonempty, ignore_index=True)

    # Select relevant output columns
    base_cols = [
        "Booking_ID", "Booking_Date", "Customer_ID", "Hotel_ID",
        "Hotel_Name", "OTA_Name", "Booking_Status", "Room_Type",
        "Net_Revenue", "Gross_Revenue", "Commission_Rate",
        "Commission_Amount", "Lead_Time", "Nights",
        "Flag_Type", "Severity", "Flag_Notes",
    ]
    out_cols = [c for c in base_cols if c in report.columns]
    report = report[out_cols].copy()

    # Format date
    for dc in ["Booking_Date"]:
        if dc in report.columns:
            report[dc] = report[dc].astype(str)

    log.info(f"\nTotal fraud flags: {len(report)} across {report['Booking_ID'].nunique()} unique bookings")
    return report


# ─────────────────────────────────────────────
# 5. EXPORT CSV
# ─────────────────────────────────────────────
def export_fraud_report(report):
    os.makedirs("Dataset", exist_ok=True)
    path = os.path.join("Dataset", "fraud_report.csv")
    report.to_csv(path, index=False)
    log.info(f"Exported fraud report -> {path} ({len(report)} rows)")
    return path

# ─────────────────────────────────────────────
# 6. VISUALISATIONS (6 charts: 42–47)
# ─────────────────────────────────────────────
def generate_fraud_visuals(df, report):
    """Generate 6 professional fraud-detection charts."""
    log.info("\nGenerating visualisations...")
    if report.empty:
        log.warning("No flagged data — skipping charts.")
        return
    # ── CHART 42: Flag Type Distribution ─────────────────────────
    flag_counts = report["Flag_Type"].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(16, 7))
    colors42 = [MC[i % len(MC)] for i in range(len(flag_counts))]
    bars = ax.barh(flag_counts.index, flag_counts.values, color=colors42, edgecolor=PAL["bg"])
    ax.set_xlabel("Number of Flagged Records")
    ax.set_title("Fraud Flag Distribution by Type", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    for b in bars:
        w = b.get_width()
        ax.text(w + 2, b.get_y() + b.get_height() / 2,
                f"{int(w):,}", va="center", fontsize=9, color=PAL["text"])
    titlebar(fig, "Phase 5 — Fraud Flag Distribution",
             "Number of records triggering each fraud detection rule")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "42_fraud_flag_distribution.png")

    # ── CHART 43: Severity Breakdown (Pie) ───────────────────────
    sev_counts = report["Severity"].value_counts()
    sev_colors = {"HIGH": PAL["accent2"], "MEDIUM": PAL["accent4"], "LOW": PAL["accent3"]}
    colors43 = [sev_colors.get(s, PAL["accent1"]) for s in sev_counts.index]

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    # Pie
    wedges, texts, autotexts = axes[0].pie(
        sev_counts.values, labels=sev_counts.index,
        colors=colors43, autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": PAL["bg"], "linewidth": 2}
    )
    for t in texts: t.set(color=PAL["text"], fontsize=11)
    for at in autotexts: at.set(color="white", fontsize=9)
    axes[0].set_title("Severity Distribution (All Flags)", fontweight="bold")

    # Stacked bar by Flag_Type
    pivot_sev = report.groupby(["Flag_Type", "Severity"]).size().unstack(fill_value=0)
    bot = np.zeros(len(pivot_sev))
    for sev, clr in sev_colors.items():
        if sev in pivot_sev.columns:
            axes[1].barh(pivot_sev.index, pivot_sev[sev], left=bot,
                         label=sev, color=clr, edgecolor=PAL["bg"], alpha=0.85)
            bot += pivot_sev[sev].values
    axes[1].set_xlabel("Flag Count")
    axes[1].set_title("Severity × Flag Type Breakdown", fontweight="bold")
    axes[1].legend(fontsize=9)
    axes[1].grid(axis="x", alpha=0.3)

    titlebar(fig, "Fraud Severity Analysis",
             "LEFT: overall severity mix | RIGHT: severity per flag type")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "43_fraud_severity.png")

    # ── CHART 44: Flagged Revenue at Risk ────────────────────────
    rev_at_risk = report.groupby("Flag_Type")["Net_Revenue"].sum().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(16, 7))
    colors44 = [PAL["accent2"] if "HIGH" in
                report[report["Flag_Type"] == ft]["Severity"].values[0]
                else PAL["accent4"] for ft in rev_at_risk.index]
    bars = ax.barh(rev_at_risk.index, rev_at_risk.values / 1e3,
                   color=colors44, edgecolor=PAL["bg"])
    ax.set_xlabel("Net Revenue at Risk (USD Thousands)")
    ax.set_title("Revenue at Risk by Fraud Flag Type", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}K"))
    ax.grid(axis="x", alpha=0.3)
    for b in bars:
        w = b.get_width()
        ax.text(w + 0.3, b.get_y() + b.get_height() / 2,
                f"${w:,.0f}K", va="center", fontsize=8.5, color=PAL["text"])
    titlebar(fig, "Revenue at Risk — Flagged Bookings",
             "Total Net Revenue associated with each fraud flag category")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "44_fraud_revenue_risk.png")

    # ── CHART 45: Flagged Bookings by OTA ────────────────────────
    if "OTA_Name" in report.columns:
        ota_flags = report.groupby("OTA_Name")["Booking_ID"].count().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(16, 8))
        colors45 = [MC[i % len(MC)] for i in range(len(ota_flags))]
        bars = ax.barh(ota_flags.index, ota_flags.values, color=colors45, edgecolor=PAL["bg"])
        ax.set_xlabel("Number of Flagged Records")
        ax.set_title("Fraud Flags by OTA Platform", fontweight="bold")
        ax.grid(axis="x", alpha=0.3)
        for b in bars:
            w = b.get_width()
            ax.text(w + 0.3, b.get_y() + b.get_height() / 2,
                    f"{int(w):,}", va="center", fontsize=8.5, color=PAL["text"])
        titlebar(fig, "Fraud Flags by OTA Platform",
                 "Which OTA channels generate the most anomalous bookings")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "45_fraud_by_ota.png")

    # ── CHART 46: Commission Rate Distribution with thresholds ───
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.hist(df["Commission_Rate"].dropna() * 100, bins=30,
            color=PAL["accent1"], edgecolor=PAL["bg"], alpha=0.8, density=True)
    ax.axvline(30, color=PAL["accent2"], lw=2.5, linestyle="--",
               label="Fraud threshold (30%)")
    avg_comm = df["Commission_Rate"].mean() * 100
    ax.axvline(avg_comm, color=PAL["accent3"], lw=2, linestyle=":",
               label=f"Portfolio avg: {avg_comm:.1f}%")
    ax.set_xlabel("Commission Rate (%)")
    ax.set_ylabel("Density")
    ax.set_title("Commission Rate Distribution with Fraud Threshold", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    titlebar(fig, "Commission Rate Distribution",
             "Red dashed line = 30% fraud threshold; bookings above it are HIGH COMMISSION flags")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "46_commission_distribution.png")

    # ── CHART 47: Monthly Fraud Flag Trend ───────────────────────
    if "Booking_Date" in report.columns:
        report["Booking_Date"] = pd.to_datetime(report["Booking_Date"], errors="coerce")
        report["Month"] = report["Booking_Date"].dt.to_period("M")
        monthly_flags = report.groupby(["Month", "Flag_Type"]).size().unstack(fill_value=0)
        monthly_flags.index = monthly_flags.index.astype(str)

        # Total monthly across all types
        monthly_total = monthly_flags.sum(axis=1)
        fig, ax = plt.subplots(figsize=(22, 7))
        x = range(len(monthly_total))
        ax.fill_between(x, monthly_total.values, alpha=0.2, color=PAL["accent2"])
        ax.plot(x, monthly_total.values, color=PAL["accent2"], lw=2.5,
                marker="o", ms=5, label="Total Fraud Flags")
        ax.set_xticks(list(x)[::2])
        ax.set_xticklabels(monthly_total.index.tolist()[::2], rotation=40, ha="right", fontsize=8)
        ax.set_ylabel("Number of Flagged Records")
        ax.set_title("Monthly Fraud Flag Trend", fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        titlebar(fig, "Monthly Fraud Flag Trend",
                 "Tracks anomaly patterns over time — spikes may signal data quality events")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "47_fraud_monthly_trend.png")

    log.info("  Total charts generated: 6 (Images/42 through 47)")


# ─────────────────────────────────────────────
# 7. GENERATE MARKDOWN REPORT
# ─────────────────────────────────────────────
def generate_report(df, report):
    """Write a professional Phase 5 technical report."""
    os.makedirs("Reports", exist_ok=True)

    total_bookings = len(df)
    total_flags = len(report)
    unique_flagged = report["Booking_ID"].nunique() if not report.empty else 0
    flag_pct = unique_flagged / total_bookings * 100 if total_bookings > 0 else 0

    if not report.empty:
        rev_at_risk = report["Net_Revenue"].sum()
        sev_high = (report["Severity"] == "HIGH").sum()
        sev_med = (report["Severity"] == "MEDIUM").sum()
        sev_low = (report["Severity"] == "LOW").sum()
        flag_type_summary = report["Flag_Type"].value_counts().to_dict()
    else:
        rev_at_risk = 0
        sev_high = sev_med = sev_low = 0
        flag_type_summary = {}

    lines = [
        "# Phase 5 — Fraud Detection Technical Report",
        "",
        "**Project**: OTA Performance & Channel Management",
        "**Phase**: 5 — Fraud Detection",
        "**Script**: `Python/fraud_detection.py`",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Bookings Analysed | {total_bookings:,} |",
        f"| Total Fraud Flags Raised | {total_flags:,} |",
        f"| Unique Bookings Flagged | {unique_flagged:,} |",
        f"| Flag Rate (% of bookings) | {flag_pct:.2f}% |",
        f"| Revenue Associated with Flags | ${rev_at_risk:,.2f} |",
        f"| HIGH Severity Flags | {sev_high:,} |",
        f"| MEDIUM Severity Flags | {sev_med:,} |",
        f"| LOW Severity Flags | {sev_low:,} |",
        "",
        "---",
        "",
        "## Detection Methods",
        "",
        "### Rule-Based Detectors",
        "",
        "| Flag Type | Description | Severity |",
        "|-----------|-------------|----------|",
        "| `DUPLICATE_BOOKING` | Same Customer+Hotel+Checkin on same Booking_Date | HIGH |",
        "| `ABNORMAL_AMOUNT` | Net_Revenue deviates > 3σ from Room_Type mean | MEDIUM |",
        "| `HIGH_COMMISSION` | Commission_Rate > 30% | MEDIUM |",
        "| `EXCESSIVE_CANCELLATION` | Customer cancel rate > 80% (min 5 bookings) | HIGH |",
        "| `SUSPECT_FREQUENCY` | ≥10 bookings by same customer in any 30-day window | HIGH |",
        "",
        "### Statistical Anomaly Detectors",
        "",
        "| Flag Type | Description | Severity |",
        "|-----------|-------------|----------|",
        "| `IQR_OUTLIER_*` | Value outside Q1 − 3×IQR or Q3 + 3×IQR | LOW |",
        "| `ZSCORE_OUTLIER_*` | \|Z-score\| > 3.0 | MEDIUM |",
        "",
        "---",
        "",
        "## Flag Summary by Type",
        "",
        "| Flag Type | Count |",
        "|-----------|-------|",
    ]

    for ftype, cnt in flag_type_summary.items():
        lines.append(f"| `{ftype}` | {cnt:,} |")

    lines += [
        "",
        "---",
        "",
        "## Output Files",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `Dataset/fraud_report.csv` | All flagged booking records with flag type, severity, notes |",
        "| `Images/42_fraud_flag_distribution.png` | Bar chart of flag type counts |",
        "| `Images/43_fraud_severity.png` | Severity pie and stacked bar |",
        "| `Images/44_fraud_revenue_risk.png` | Revenue at risk by flag type |",
        "| `Images/45_fraud_by_ota.png` | Fraud flags per OTA platform |",
        "| `Images/46_commission_distribution.png` | Commission distribution with threshold |",
        "| `Images/47_fraud_monthly_trend.png` | Monthly fraud flag trend |",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Duplicate Bookings**: Implement a real-time deduplication check at the booking "
        "API level to prevent same-day duplicate reservations.",
        "2. **High Commission OTAs**: Renegotiate contracts with platforms that systematically "
        "exceed 30% commission rates.",
        "3. **Excessive Cancellations**: Enforce non-refundable policies or deposit requirements "
        "for customers with cancel rates above 80%.",
        "4. **Suspect Frequency**: Flag accounts making ≥10 bookings in 30 days for manual "
        "review to detect bot-driven or bulk reseller activity.",
        "5. **Statistical Outliers**: Audit IQR/Z-score flagged transactions for pricing "
        "system errors or manual override abuse.",
    ]

    path = os.path.join("Reports", "Phase_5_Fraud_Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"Report saved -> {path}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  PHASE 5: FRAUD DETECTION")
    print("=" * 65)

    try:
        df = load_data()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    log.info("\nBuilding fraud report...")
    report = build_fraud_report(df)

    if not report.empty:
        export_fraud_report(report)
        generate_fraud_visuals(df, report)
        generate_report(df, report)

        print("\n" + "=" * 65)
        print(f"  PHASE 5 COMPLETE")
        print(f"  Flags:   {len(report):,} total ({report['Booking_ID'].nunique():,} unique bookings)")
        print(f"  Dataset: Dataset/fraud_report.csv")
        print(f"  Charts:  Images/42 through 47")
        print(f"  Report:  Reports/Phase_5_Fraud_Report.md")
        print("=" * 65)
    else:
        log.warning("No fraud flags to export — report empty.")


if __name__ == "__main__":
    main()
