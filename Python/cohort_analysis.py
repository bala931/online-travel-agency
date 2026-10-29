"""
Phase 9: Cohort & Retention Analysis
OTA Performance & Channel Management Project
============================================================
Inputs  : Dataset/ota_master_dataset.csv
Outputs : Dataset/cohort_retention.csv
          Images/66_*.png – 71_*.png
          Reports/Phase_9_Cohort_Report.md
============================================================
Analysis:
  1. Acquisition cohorts (first booking month)
  2. Monthly retention matrix (% retained in month N)
  3. Cohort revenue contribution
  4. Repeat booking analysis
  5. Customer Lifetime Value (CLV) estimation
  6. Retention KPIs per segment
"""

import os
import logging
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import matplotlib.cm as cm

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# STYLE
# ─────────────────────────────────────────────
PAL = {
    "bg": "#0F1117", "card": "#1A1D2E",
    "accent1": "#6C63FF", "accent2": "#FF6584",
    "accent3": "#43E97B", "accent4": "#F7971E",
    "accent5": "#00C9FF", "text": "#E8EAF6",
    "sub": "#9FA8DA", "grid": "#2C2F4A",
}
MC = ["#6C63FF","#FF6584","#43E97B","#F7971E","#00C9FF",
      "#FF8C69","#A29BFE","#55EFC4","#FD79A8","#FDCB6E"]

def apply_style():
    plt.rcParams.update({
        "figure.facecolor": PAL["bg"], "axes.facecolor": PAL["card"],
        "axes.edgecolor": PAL["grid"], "axes.labelcolor": PAL["text"],
        "axes.titlecolor": PAL["text"], "axes.titlesize": 13,
        "axes.labelsize": 10, "xtick.color": PAL["sub"],
        "ytick.color": PAL["sub"], "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5, "grid.color": PAL["grid"],
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
    df = pd.read_csv(path, parse_dates=["Booking_Date"])
    df["Net_Revenue"] = pd.to_numeric(df["Net_Revenue"], errors="coerce")
    df["Nights"] = pd.to_numeric(df.get("Nights", pd.Series(dtype=float)), errors="coerce").fillna(1)
    log.info(f"Master dataset loaded: {df.shape}")
    return df


# ─────────────────────────────────────────────
# 2. BUILD COHORT TABLES
# ─────────────────────────────────────────────
def build_cohort_data(df):
    """Assign each customer their acquisition cohort (month of first booking)."""
    df = df.copy()
    df["Booking_Month"] = df["Booking_Date"].dt.to_period("M")

    # First booking month per customer
    first_booking = df.groupby("Customer_ID")["Booking_Month"].min().reset_index()
    first_booking.columns = ["Customer_ID", "Cohort_Month"]
    df = df.merge(first_booking, on="Customer_ID", how="left")

    # Month offset (0 = acquisition month)
    df["Month_Offset"] = (df["Booking_Month"] - df["Cohort_Month"]).apply(lambda x: x.n)
    return df


def build_retention_matrix(df_cohort):
    """Build customer-count retention matrix: rows = cohort, cols = month offset."""
    cohort_data = df_cohort.groupby(["Cohort_Month","Month_Offset"])["Customer_ID"].nunique().reset_index()
    cohort_data.columns = ["Cohort_Month","Month_Offset","Customers"]

    # Pivot
    matrix = cohort_data.pivot_table(index="Cohort_Month", columns="Month_Offset",
                                     values="Customers", fill_value=0)
    matrix.index = matrix.index.astype(str)

    # Compute retention % relative to cohort size (month 0)
    cohort_size = matrix[0] if 0 in matrix.columns else matrix.iloc[:, 0]
    retention_pct = matrix.divide(cohort_size, axis=0) * 100

    # Limit to offsets 0–11 (first year)
    max_offset = min(11, max(matrix.columns))
    offset_cols = [c for c in range(0, max_offset + 1) if c in matrix.columns]
    return matrix[offset_cols], retention_pct[offset_cols], cohort_size


def build_cohort_revenue(df_cohort):
    """Revenue by cohort × month offset."""
    rev = df_cohort.groupby(["Cohort_Month","Month_Offset"])["Net_Revenue"].sum().reset_index()
    rev_matrix = rev.pivot_table(index="Cohort_Month", columns="Month_Offset",
                                  values="Net_Revenue", fill_value=0)
    rev_matrix.index = rev_matrix.index.astype(str)
    max_offset = min(11, max(rev_matrix.columns))
    offset_cols = [c for c in range(0, max_offset + 1) if c in rev_matrix.columns]
    return rev_matrix[offset_cols]


def build_customer_clv(df_cohort):
    """Simple CLV: total revenue per customer, seg by repeat behaviour."""
    clv = df_cohort.groupby("Customer_ID").agg(
        Cohort_Month=("Cohort_Month", "first"),
        Total_Bookings=("Booking_ID", "count"),
        Total_Revenue=("Net_Revenue", "sum"),
        Avg_Revenue_per_Booking=("Net_Revenue", "mean"),
        Booking_Span_Days=("Booking_Date", lambda x: (x.max()-x.min()).days),
    ).reset_index()
    clv["Cohort_Month"] = clv["Cohort_Month"].astype(str)
    clv["Is_Repeat"] = clv["Total_Bookings"] > 1
    clv["Frequency_Segment"] = pd.cut(clv["Total_Bookings"],
                                       bins=[0,1,2,4,9999],
                                       labels=["One-Time","Occasional","Regular","VIP"])
    return clv.sort_values("Total_Revenue", ascending=False).round(2)


def repeat_booking_stats(df_cohort):
    """Summary stats on repeat bookings."""
    customer_totals = df_cohort.groupby("Customer_ID")["Booking_ID"].count().reset_index()
    customer_totals.columns = ["Customer_ID","Booking_Count"]
    total_customers = len(customer_totals)
    repeat_customers = (customer_totals["Booking_Count"] > 1).sum()
    one_time = total_customers - repeat_customers
    avg_bookings = customer_totals["Booking_Count"].mean()
    repeat_rate = repeat_customers / total_customers * 100 if total_customers > 0 else 0
    return {
        "Total_Customers": total_customers,
        "One_Time_Customers": int(one_time),
        "Repeat_Customers": int(repeat_customers),
        "Repeat_Rate_Pct": round(repeat_rate, 2),
        "Avg_Bookings_per_Customer": round(avg_bookings, 2),
        "Max_Bookings_by_One_Customer": int(customer_totals["Booking_Count"].max()),
    }


# ─────────────────────────────────────────────
# 3. EXPORT CSV
# ─────────────────────────────────────────────
def export_cohort(retention_pct, clv):
    os.makedirs("Dataset", exist_ok=True)
    # Retention matrix
    ret_path = os.path.join("Dataset", "cohort_retention.csv")
    retention_pct.to_csv(ret_path)
    log.info(f"  Exported -> {ret_path} ({len(retention_pct)} cohorts)")

    # CLV table
    clv_path = os.path.join("Dataset", "cohort_clv.csv")
    clv.to_csv(clv_path, index=False)
    log.info(f"  Exported -> {clv_path} ({len(clv)} customers)")


# ─────────────────────────────────────────────
# 4. VISUALISATIONS (Charts 66–71)
# ─────────────────────────────────────────────
def generate_cohort_charts(retention_matrix, retention_pct, rev_matrix, clv, cohort_size, repeat_stats, df_cohort):
    log.info("\nGenerating cohort & retention charts...")

    # ── CHART 66: Cohort Retention Heatmap (%) ───────────────────
    fig, ax = plt.subplots(figsize=(22, max(7, len(retention_pct) * 0.55 + 3)))
    # Replace 0s with NaN to let colormap skip empty cells
    hm_data = retention_pct.replace(0, np.nan)
    # Cap at 100 for colour scaling; Month-0 is always 100%
    vmax = 100
    im = ax.imshow(hm_data.values, aspect="auto",
                   cmap="YlOrRd", vmin=0, vmax=vmax, interpolation="nearest")
    # Annotate cells
    for i in range(hm_data.shape[0]):
        for j in range(hm_data.shape[1]):
            val = hm_data.iloc[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                        fontsize=6.5, color="black" if val > 50 else "white")
    ax.set_xticks(range(len(hm_data.columns)))
    ax.set_xticklabels([f"M+{c}" for c in hm_data.columns], fontsize=8)
    ax.set_yticks(range(len(hm_data.index)))
    ax.set_yticklabels(hm_data.index.tolist(), fontsize=7)
    ax.set_xlabel("Month Since Acquisition (Offset)")
    ax.set_ylabel("Acquisition Cohort")
    cbar = fig.colorbar(im, ax=ax, shrink=0.5, pad=0.01)
    cbar.set_label("Retention %", color=PAL["text"])
    cbar.ax.yaxis.set_tick_params(color=PAL["sub"])
    ax.set_title("Customer Retention Matrix (%)", fontweight="bold")
    titlebar(fig, "Cohort Retention Heatmap",
             "Each cell = % of cohort still booking in that month offset")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "66_cohort_retention_heatmap.png")

    # ── CHART 67: Retention Curves by Cohort ─────────────────────
    fig, ax = plt.subplots(figsize=(18, 9))
    cohorts_to_plot = retention_pct.index.tolist()
    n = len(cohorts_to_plot)
    # Sample up to 12 cohorts for readability
    step = max(1, n // 12)
    sampled = cohorts_to_plot[::step]
    for i, cohort in enumerate(sampled):
        row = retention_pct.loc[cohort].values
        color = MC[i % len(MC)]
        ax.plot(range(len(row)), row, marker="o", ms=4, lw=2,
                color=color, alpha=0.85, label=str(cohort))
    ax.set_xlabel("Month Offset Since Acquisition")
    ax.set_ylabel("Retention Rate (%)")
    ax.set_title("Retention Curves by Acquisition Cohort", fontweight="bold")
    ax.legend(fontsize=8, loc="upper right", ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)
    titlebar(fig, "Customer Retention Curves",
             "How each acquisition cohort retains over its lifetime")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "67_retention_curves.png")

    # ── CHART 68: Cohort Revenue Heatmap ─────────────────────────
    fig, ax = plt.subplots(figsize=(22, max(7, len(rev_matrix) * 0.55 + 3)))
    im2 = ax.imshow(rev_matrix.values / 1e3, aspect="auto",
                    cmap="Blues", interpolation="nearest")
    ax.set_xticks(range(len(rev_matrix.columns)))
    ax.set_xticklabels([f"M+{c}" for c in rev_matrix.columns], fontsize=8)
    ax.set_yticks(range(len(rev_matrix.index)))
    ax.set_yticklabels(rev_matrix.index.tolist(), fontsize=7)
    ax.set_xlabel("Month Offset")
    ax.set_ylabel("Acquisition Cohort")
    cbar2 = fig.colorbar(im2, ax=ax, shrink=0.5, pad=0.01)
    cbar2.set_label("Revenue ($K)", color=PAL["text"])
    cbar2.ax.yaxis.set_tick_params(color=PAL["sub"])
    ax.set_title("Cohort Revenue Heatmap (USD Thousands)", fontweight="bold")
    titlebar(fig, "Cohort Revenue Contribution Heatmap",
             "Revenue generated by each cohort at each month offset (darker = more revenue)")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "68_cohort_revenue_heatmap.png")

    # ── CHART 69: Repeat Booking Frequency Distribution ──────────
    freq_seg = clv["Frequency_Segment"].value_counts().sort_index()
    rev_seg = clv.groupby("Frequency_Segment")["Total_Revenue"].sum().sort_index()

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    colors69 = [MC[i % len(MC)] for i in range(len(freq_seg))]

    axes[0].bar(freq_seg.index.astype(str), freq_seg.values,
                color=colors69, edgecolor=PAL["bg"])
    axes[0].set_ylabel("Number of Customers")
    axes[0].set_title("Customer Frequency Segments", fontweight="bold")
    axes[0].grid(axis="y", alpha=0.3)
    for i, v in enumerate(freq_seg.values):
        axes[0].text(i, v + max(freq_seg.values)*0.01, f"{v:,}",
                     ha="center", va="bottom", fontsize=9, color=PAL["text"])

    axes[1].bar(rev_seg.index.astype(str), rev_seg.values / 1e3,
                color=colors69, edgecolor=PAL["bg"], alpha=0.85)
    axes[1].set_ylabel("Total Revenue (USD Thousands)")
    axes[1].set_title("Revenue by Frequency Segment", fontweight="bold")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    axes[1].grid(axis="y", alpha=0.3)

    # Stats box
    stats_text = (
        f"Total Customers: {repeat_stats['Total_Customers']:,}\n"
        f"Repeat Rate: {repeat_stats['Repeat_Rate_Pct']:.1f}%\n"
        f"Avg Bookings/Customer: {repeat_stats['Avg_Bookings_per_Customer']:.1f}"
    )
    axes[0].text(0.98, 0.97, stats_text, transform=axes[0].transAxes,
                 va="top", ha="right", fontsize=9, color=PAL["sub"],
                 bbox=dict(facecolor=PAL["card"], edgecolor=PAL["grid"], boxstyle="round,pad=0.4"))

    titlebar(fig, "Repeat Booking Analysis",
             "LEFT: customer count per segment | RIGHT: revenue contribution")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "69_repeat_booking_analysis.png")

    # ── CHART 70: CLV Distribution by Frequency Segment ──────────
    fig, ax = plt.subplots(figsize=(16, 8))
    freq_labels = ["One-Time","Occasional","Regular","VIP"]
    clv_vals = [clv[clv["Frequency_Segment"]==seg]["Total_Revenue"].values
                for seg in freq_labels if (clv["Frequency_Segment"]==seg).any()]
    valid_labels = [seg for seg in freq_labels if (clv["Frequency_Segment"]==seg).any()]

    bplot = ax.violinplot(clv_vals, showmedians=True, showextrema=True)
    for i, pc in enumerate(bplot["bodies"]):
        pc.set_facecolor(MC[i % len(MC)])
        pc.set_alpha(0.75)
    bplot["cmedians"].set_color(PAL["text"])
    bplot["cbars"].set_color(PAL["sub"])
    bplot["cmaxes"].set_color(PAL["sub"])
    bplot["cmins"].set_color(PAL["sub"])

    ax.set_xticks(range(1, len(valid_labels) + 1))
    ax.set_xticklabels(valid_labels, fontsize=11)
    ax.set_ylabel("Customer Lifetime Revenue (USD)")
    ax.set_title("CLV Distribution by Frequency Segment", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
    ax.grid(axis="y", alpha=0.3)
    titlebar(fig, "Customer Lifetime Value (CLV) Distribution",
             "Violin plot of total revenue per customer, grouped by booking frequency")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "70_clv_distribution.png")

    # ── CHART 71: Cohort Size + Avg Retention (M3, M6) ───────────
    cohort_size_df = cohort_size.reset_index()
    cohort_size_df.columns = ["Cohort_Month","Cohort_Size"]
    cohort_size_df["Cohort_Month"] = cohort_size_df["Cohort_Month"].astype(str)

    # M3 and M6 retention rates
    m3_col = 3 if 3 in retention_pct.columns else None
    m6_col = 6 if 6 in retention_pct.columns else None
    cohort_size_df["M3_Retention"] = retention_pct[m3_col].values if m3_col else np.nan
    cohort_size_df["M6_Retention"] = retention_pct[m6_col].values if m6_col else np.nan

    fig, axes = plt.subplots(2, 1, figsize=(22, 12), sharex=True)
    x = range(len(cohort_size_df))

    axes[0].bar(x, cohort_size_df["Cohort_Size"], color=PAL["accent1"],
                edgecolor=PAL["bg"], alpha=0.85, label="Cohort Size")
    axes[0].set_ylabel("Number of New Customers")
    axes[0].set_title("Acquisition Cohort Size Over Time", fontweight="bold")
    axes[0].grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=9)

    if m3_col:
        axes[1].plot(x, cohort_size_df["M3_Retention"], color=PAL["accent3"],
                     lw=2.5, marker="o", ms=5, label="M+3 Retention %")
    if m6_col:
        axes[1].plot(x, cohort_size_df["M6_Retention"], color=PAL["accent4"],
                     lw=2.5, marker="s", ms=5, linestyle="--", label="M+6 Retention %")
    axes[1].set_xticks(list(x)[::2])
    axes[1].set_xticklabels(cohort_size_df["Cohort_Month"].tolist()[::2],
                             rotation=40, ha="right", fontsize=8)
    axes[1].set_ylabel("Retention Rate (%)")
    axes[1].set_title("M+3 and M+6 Retention Rates by Cohort", fontweight="bold")
    axes[1].set_ylim(0, 105)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=9)

    titlebar(fig, "Cohort Size & Retention KPIs",
             "TOP: new customers acquired per cohort | BOTTOM: 3-month and 6-month retention")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "71_cohort_size_retention_kpi.png")

    log.info("  Total charts generated: 6 (Images/66 through 71)")


# ─────────────────────────────────────────────
# 5. MARKDOWN REPORT
# ─────────────────────────────────────────────
def generate_report(retention_pct, clv, repeat_stats, cohort_size):
    os.makedirs("Reports", exist_ok=True)

    avg_m1 = retention_pct[1].mean() if 1 in retention_pct.columns else None
    avg_m3 = retention_pct[3].mean() if 3 in retention_pct.columns else None
    avg_m6 = retention_pct[6].mean() if 6 in retention_pct.columns else None

    avg_clv = clv["Total_Revenue"].mean()
    top_clv  = clv["Total_Revenue"].quantile(0.9)

    lines = [
        "# Phase 9 — Cohort & Retention Analysis Report",
        "",
        "**Project**: OTA Performance & Channel Management",
        "**Phase**: 9 — Cohort & Retention Analysis",
        "**Script**: `Python/cohort_analysis.py`",
        "",
        "---",
        "",
        "## Retention Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Cohorts Analysed | {len(retention_pct)} |",
        f"| Avg M+1 Retention Rate | {avg_m1:.1f}% |" if avg_m1 else "| Avg M+1 Retention Rate | N/A |",
        f"| Avg M+3 Retention Rate | {avg_m3:.1f}% |" if avg_m3 else "| Avg M+3 Retention Rate | N/A |",
        f"| Avg M+6 Retention Rate | {avg_m6:.1f}% |" if avg_m6 else "| Avg M+6 Retention Rate | N/A |",
        "",
        "---",
        "",
        "## Repeat Booking Statistics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Unique Customers | {repeat_stats['Total_Customers']:,} |",
        f"| One-Time Customers | {repeat_stats['One_Time_Customers']:,} |",
        f"| Repeat Customers | {repeat_stats['Repeat_Customers']:,} |",
        f"| Repeat Rate | {repeat_stats['Repeat_Rate_Pct']:.2f}% |",
        f"| Avg Bookings per Customer | {repeat_stats['Avg_Bookings_per_Customer']:.2f} |",
        f"| Max Bookings (single customer) | {repeat_stats['Max_Bookings_by_One_Customer']:,} |",
        "",
        "---",
        "",
        "## Customer Lifetime Value (CLV)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Average CLV | ${avg_clv:,.2f} |",
        f"| Top 10% CLV (P90) | ${top_clv:,.2f} |",
        "",
        "---",
        "",
        "## Output Files",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `Dataset/cohort_retention.csv` | Retention matrix (% by cohort × month offset) |",
        "| `Dataset/cohort_clv.csv` | Customer-level CLV and frequency segment |",
        "| `Images/66_cohort_retention_heatmap.png` | Cohort retention % heatmap |",
        "| `Images/67_retention_curves.png` | Retention curves per cohort |",
        "| `Images/68_cohort_revenue_heatmap.png` | Revenue contribution heatmap |",
        "| `Images/69_repeat_booking_analysis.png` | Repeat booking frequency analysis |",
        "| `Images/70_clv_distribution.png` | CLV violin plot by frequency segment |",
        "| `Images/71_cohort_size_retention_kpi.png` | Cohort size + M3/M6 retention KPIs |",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Improve M+1 Retention**: Send personalised re-engagement emails within 30 days of first booking.",
        "2. **VIP Loyalty Program**: Customers with 4+ bookings are top CLV contributors — offer exclusive perks.",
        "3. **Reactivate Dormant Cohorts**: Cohorts with <10% M+6 retention need win-back campaigns.",
        "4. **Acquisition Quality**: Prioritise OTA channels that produce cohorts with higher long-term retention.",
        "5. **CLV-Based Segmentation**: Use frequency segments for differential marketing spend allocation.",
    ]

    path = os.path.join("Reports", "Phase_9_Cohort_Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"Report saved -> {path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  PHASE 9: COHORT & RETENTION ANALYSIS")
    print("=" * 65)

    try:
        df = load_data()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    log.info("\nBuilding cohort data...")
    df_cohort = build_cohort_data(df)

    log.info("Building retention matrix...")
    ret_matrix, ret_pct, cohort_size = build_retention_matrix(df_cohort)
    log.info(f"  Cohorts: {len(ret_matrix)} | Max offset tracked: {max(ret_matrix.columns)} months")

    log.info("Building cohort revenue matrix...")
    rev_matrix = build_cohort_revenue(df_cohort)

    log.info("Computing CLV...")
    clv = build_customer_clv(df_cohort)

    log.info("Computing repeat booking stats...")
    repeat_stats = repeat_booking_stats(df_cohort)
    for k, v in repeat_stats.items():
        log.info(f"  {k}: {v}")

    log.info("\nExporting CSVs...")
    export_cohort(ret_pct, clv)

    generate_cohort_charts(ret_matrix, ret_pct, rev_matrix, clv,
                           cohort_size, repeat_stats, df_cohort)
    generate_report(ret_pct, clv, repeat_stats, cohort_size)

    print("\n" + "=" * 65)
    print("  PHASE 9 COMPLETE")
    print(f"  Cohorts: {len(ret_matrix)} | Repeat Rate: {repeat_stats['Repeat_Rate_Pct']:.1f}%")
    print("  Dataset: Dataset/cohort_retention.csv, cohort_clv.csv")
    print("  Charts:  Images/66 through 71")
    print("  Report:  Reports/Phase_9_Cohort_Report.md")
    print("=" * 65)


if __name__ == "__main__":
    main()
