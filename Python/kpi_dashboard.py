"""
Phase 6: KPI Monitoring Dashboard Datasets
OTA Performance & Channel Management Project
============================================================
Inputs  : Dataset/ota_master_dataset.csv
          Dataset/dim_hotels.csv, dim_otas.csv, dim_customers.csv
Outputs : Dataset/kpi_monthly.csv
          Dataset/kpi_by_ota.csv
          Dataset/kpi_by_property.csv
          Dataset/kpi_by_customer_segment.csv
          Images/48_*.png – 53_*.png
          Reports/Phase_6_KPI_Report.md
============================================================
KPIs computed:
  - Total Revenue, Net Revenue, Gross Revenue
  - ADR (Average Daily Rate), RevPAR, Occupancy Rate
  - Cancellation Rate, Commission Rate, Commission Amount
  - Booking Count, Room Nights
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
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# STYLE — consistent dark theme
# ─────────────────────────────────────────────
PAL = {
    "bg": "#0F1117", "card": "#1A1D2E",
    "accent1": "#6C63FF", "accent2": "#FF6584",
    "accent3": "#43E97B", "accent4": "#F7971E",
    "accent5": "#00C9FF", "accent6": "#A29BFE",
    "text": "#E8EAF6", "sub": "#9FA8DA", "grid": "#2C2F4A",
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
    for col in ["Net_Revenue", "Gross_Revenue", "Commission_Amount",
                "Commission_Rate", "Lead_Time", "Nights"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    log.info(f"Master dataset loaded: {df.shape}")
    return df


# ─────────────────────────────────────────────
# 2. COMPUTE KPIs
# ─────────────────────────────────────────────
def portfolio_kpis(df):
    total_bookings = len(df)
    confirmed = df[df["Booking_Status"] == "Confirmed"] if "Booking_Status" in df.columns else df
    cancelled = df[df["Booking_Status"] == "Cancelled"] if "Booking_Status" in df.columns else pd.DataFrame()

    total_revenue   = df["Net_Revenue"].sum()
    gross_revenue   = df["Gross_Revenue"].sum() if "Gross_Revenue" in df.columns else np.nan
    commission_amt  = df["Commission_Amount"].sum() if "Commission_Amount" in df.columns else np.nan
    avg_commission  = df["Commission_Rate"].mean() * 100 if "Commission_Rate" in df.columns else np.nan
    cancel_rate     = len(cancelled) / total_bookings * 100 if total_bookings > 0 else 0

    nights = df["Nights"].fillna(1)
    total_room_nights = nights.sum()
    adr = total_revenue / total_room_nights if total_room_nights > 0 else 0

    # Occupancy: assume 100 rooms across portfolio, 365 days -> available = hotels*365*rooms_per_hotel
    n_hotels = df["Hotel_ID"].nunique() if "Hotel_ID" in df.columns else 1
    available_room_nights = n_hotels * 365 * 50  # assume 50-room avg hotel
    occupancy = total_room_nights / available_room_nights * 100
    revpar = adr * (occupancy / 100)

    kpis = {
        "Total_Bookings": total_bookings,
        "Net_Revenue": round(total_revenue, 2),
        "Gross_Revenue": round(gross_revenue, 2),
        "Commission_Amount": round(commission_amt, 2),
        "Avg_Commission_Rate_Pct": round(avg_commission, 2),
        "Cancel_Rate_Pct": round(cancel_rate, 2),
        "Total_Room_Nights": int(total_room_nights),
        "ADR": round(adr, 2),
        "Occupancy_Rate_Pct": round(occupancy, 2),
        "RevPAR": round(revpar, 2),
    }
    return kpis


def monthly_kpis(df):
    df2 = df.copy()
    df2["Month"] = df2["Booking_Date"].dt.to_period("M")
    nights = df2["Nights"].fillna(1)

    monthly = df2.groupby("Month").agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Commission_Amount=("Commission_Amount", "sum"),
        Avg_Commission_Rate=("Commission_Rate", "mean"),
        Room_Nights=("Nights", "sum"),
    ).reset_index()

    # Cancel rate
    monthly_cancel = df2[df2["Booking_Status"] == "Cancelled"].groupby("Month").size().reset_index(name="Cancelled")
    monthly = monthly.merge(monthly_cancel, on="Month", how="left")
    monthly["Cancelled"] = monthly["Cancelled"].fillna(0)
    monthly["Cancel_Rate_Pct"] = monthly["Cancelled"] / monthly["Bookings"] * 100

    monthly["ADR"] = monthly["Net_Revenue"] / monthly["Room_Nights"].replace(0, np.nan)
    monthly["Avg_Commission_Rate_Pct"] = monthly["Avg_Commission_Rate"] * 100
    monthly["Month"] = monthly["Month"].astype(str)

    cols = ["Month","Bookings","Net_Revenue","Gross_Revenue","Commission_Amount",
            "Avg_Commission_Rate_Pct","Room_Nights","Cancel_Rate_Pct","ADR"]
    return monthly[[c for c in cols if c in monthly.columns]].round(2)


def ota_kpis(df):
    if "OTA_Name" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby("OTA_Name").agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Commission_Amount=("Commission_Amount", "sum"),
        Avg_Commission_Rate=("Commission_Rate", "mean"),
        Avg_Lead_Time=("Lead_Time", "mean"),
        Room_Nights=("Nights", "sum"),
    ).reset_index()

    cancel_grp = df[df["Booking_Status"]=="Cancelled"].groupby("OTA_Name").size().reset_index(name="Cancelled")
    grp = grp.merge(cancel_grp, on="OTA_Name", how="left")
    grp["Cancelled"] = grp["Cancelled"].fillna(0)
    grp["Cancel_Rate_Pct"] = grp["Cancelled"] / grp["Bookings"] * 100
    grp["ADR"] = grp["Net_Revenue"] / grp["Room_Nights"].replace(0, np.nan)
    grp["Avg_Commission_Rate_Pct"] = grp["Avg_Commission_Rate"] * 100

    cols = ["OTA_Name","Bookings","Net_Revenue","Gross_Revenue","Commission_Amount",
            "Avg_Commission_Rate_Pct","Cancel_Rate_Pct","ADR","Avg_Lead_Time"]
    return grp[[c for c in cols if c in grp.columns]].sort_values("Net_Revenue", ascending=False).round(2)


def property_kpis(df):
    if "Hotel_Name" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby(["Hotel_ID","Hotel_Name"]).agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Commission_Amount=("Commission_Amount", "sum"),
        Avg_Commission_Rate=("Commission_Rate", "mean"),
        Room_Nights=("Nights", "sum"),
    ).reset_index()

    cancel_grp = df[df["Booking_Status"]=="Cancelled"].groupby("Hotel_ID").size().reset_index(name="Cancelled")
    grp = grp.merge(cancel_grp, on="Hotel_ID", how="left")
    grp["Cancelled"] = grp["Cancelled"].fillna(0)
    grp["Cancel_Rate_Pct"] = grp["Cancelled"] / grp["Bookings"] * 100
    grp["ADR"] = grp["Net_Revenue"] / grp["Room_Nights"].replace(0, np.nan)
    grp["Avg_Commission_Rate_Pct"] = grp["Avg_Commission_Rate"] * 100

    cols = ["Hotel_ID","Hotel_Name","Bookings","Net_Revenue","Gross_Revenue",
            "Commission_Amount","Avg_Commission_Rate_Pct","Cancel_Rate_Pct","ADR","Room_Nights"]
    return grp[[c for c in cols if c in grp.columns]].sort_values("Net_Revenue", ascending=False).round(2)


def customer_segment_kpis(df):
    seg_col = None
    for c in ["Customer_Segment", "Segment", "RFM_Segment"]:
        if c in df.columns:
            seg_col = c
            break
    if seg_col is None:
        # Try joining rfm_segments
        rfm_path = os.path.join("Dataset", "rfm_segments.csv")
        if os.path.exists(rfm_path):
            rfm = pd.read_csv(rfm_path)
            for c in ["Customer_Segment", "Segment", "RFM_Segment"]:
                if c in rfm.columns:
                    seg_col = c
                    break
            if seg_col and "Customer_ID" in rfm.columns:
                df = df.merge(rfm[["Customer_ID", seg_col]], on="Customer_ID", how="left")

    if seg_col is None or seg_col not in df.columns:
        # Fallback: create segment from booking count
        cust_cnt = df.groupby("Customer_ID")["Booking_ID"].count()
        df = df.copy()
        df["_seg_cnt"] = df["Customer_ID"].map(cust_cnt)
        df[seg_col] = pd.cut(df["_seg_cnt"], bins=[0,1,3,7,9999],
                              labels=["One-Time","Occasional","Regular","VIP"])
        seg_col = seg_col

    grp = df.groupby(seg_col).agg(
        Customers=("Customer_ID", "nunique"),
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Avg_Revenue_per_Booking=("Net_Revenue", "mean"),
        Avg_Lead_Time=("Lead_Time", "mean"),
    ).reset_index()

    cancel_grp = df[df["Booking_Status"]=="Cancelled"].groupby(seg_col).size().reset_index(name="Cancelled")
    grp = grp.merge(cancel_grp, on=seg_col, how="left")
    grp["Cancelled"] = grp["Cancelled"].fillna(0)
    grp["Cancel_Rate_Pct"] = grp["Cancelled"] / grp["Bookings"] * 100

    return grp.sort_values("Net_Revenue", ascending=False).round(2)


# ─────────────────────────────────────────────
# 3. EXPORT CSVs
# ─────────────────────────────────────────────
def export_kpi_tables(monthly, ota, property_, customer_seg, portfolio_kpis_dict):
    os.makedirs("Dataset", exist_ok=True)

    monthly.to_csv(os.path.join("Dataset", "kpi_monthly.csv"), index=False)
    log.info("  Exported -> Dataset/kpi_monthly.csv")

    ota.to_csv(os.path.join("Dataset", "kpi_by_ota.csv"), index=False)
    log.info("  Exported -> Dataset/kpi_by_ota.csv")

    property_.to_csv(os.path.join("Dataset", "kpi_by_property.csv"), index=False)
    log.info("  Exported -> Dataset/kpi_by_property.csv")

    customer_seg.to_csv(os.path.join("Dataset", "kpi_by_customer_segment.csv"), index=False)
    log.info("  Exported -> Dataset/kpi_by_customer_segment.csv")

    # Portfolio summary row
    pd.DataFrame([portfolio_kpis_dict]).to_csv(
        os.path.join("Dataset", "kpi_summary.csv"), index=False)
    log.info("  Exported -> Dataset/kpi_summary.csv")


# ─────────────────────────────────────────────
# 4. VISUALISATIONS (Charts 48–53)
# ─────────────────────────────────────────────
def generate_kpi_charts(df, monthly, ota, property_, customer_seg, portfolio):
    log.info("\nGenerating KPI charts...")

    # ── CHART 48: Portfolio KPI Scorecard Tiles ─────────────────
    kpi_items = [
        ("Total Revenue",    f"${portfolio['Net_Revenue']:,.0f}",    PAL["accent1"]),
        ("Total Bookings",   f"{portfolio['Total_Bookings']:,}",      PAL["accent2"]),
        ("ADR",              f"${portfolio['ADR']:,.2f}",             PAL["accent3"]),
        ("RevPAR",           f"${portfolio['RevPAR']:,.2f}",          PAL["accent4"]),
        ("Occupancy Rate",   f"{portfolio['Occupancy_Rate_Pct']:.1f}%", PAL["accent5"]),
        ("Cancel Rate",      f"{portfolio['Cancel_Rate_Pct']:.1f}%",  PAL["accent6"]),
        ("Commission Total", f"${portfolio['Commission_Amount']:,.0f}", "#FDCB6E"),
        ("Avg Commission",   f"{portfolio['Avg_Commission_Rate_Pct']:.1f}%", "#FD79A8"),
        ("Room Nights",      f"{portfolio['Total_Room_Nights']:,}",   "#55EFC4"),
    ]
    n = len(kpi_items)
    cols = 3
    rows = (n + cols - 1) // cols
    fig = plt.figure(figsize=(18, rows * 3.5 + 1.5))
    titlebar(fig, "Phase 6 — Portfolio KPI Scorecard",
             "Key performance indicators across the entire OTA portfolio")
    gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=0.55, wspace=0.35,
                           top=0.88, bottom=0.05, left=0.04, right=0.96)
    for i, (label, value, color) in enumerate(kpi_items):
        r, c = divmod(i, cols)
        ax = fig.add_subplot(gs[r, c])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.axis("off")
        box = FancyBboxPatch((0.05, 0.08), 0.90, 0.84,
                              boxstyle="round,pad=0.03",
                              linewidth=2, edgecolor=color,
                              facecolor=PAL["card"])
        ax.add_patch(box)
        ax.text(0.5, 0.62, value, ha="center", va="center",
                fontsize=22, fontweight="bold", color=color)
        ax.text(0.5, 0.25, label, ha="center", va="center",
                fontsize=10, color=PAL["sub"])
    savefig(fig, "48_kpi_scorecard.png")

    # ── CHART 49: Monthly Revenue + ADR Trend ───────────────────
    if not monthly.empty and "Month" in monthly.columns:
        fig, axes = plt.subplots(2, 1, figsize=(22, 12), sharex=True)
        x = range(len(monthly))
        axes[0].fill_between(x, monthly["Net_Revenue"] / 1e3, alpha=0.25, color=PAL["accent1"])
        axes[0].plot(x, monthly["Net_Revenue"] / 1e3, color=PAL["accent1"],
                     lw=2.5, marker="o", ms=5, label="Net Revenue")
        axes[0].set_ylabel("Net Revenue (USD Thousands)")
        axes[0].set_title("Monthly Net Revenue", fontweight="bold")
        axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(fontsize=9)

        axes[1].plot(x, monthly["ADR"], color=PAL["accent3"],
                     lw=2.5, marker="s", ms=5, label="ADR")
        axes[1].fill_between(x, monthly["ADR"], alpha=0.20, color=PAL["accent3"])
        axes[1].set_ylabel("ADR (USD)")
        axes[1].set_title("Monthly Average Daily Rate (ADR)", fontweight="bold")
        axes[1].set_xticks(list(x)[::2])
        axes[1].set_xticklabels(monthly["Month"].tolist()[::2], rotation=40, ha="right", fontsize=8)
        axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(fontsize=9)

        titlebar(fig, "Monthly Revenue & ADR Trends",
                 "Net Revenue and ADR over the booking horizon")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "49_monthly_revenue_adr.png")

    # ── CHART 50: OTA Revenue & Commission Comparison ───────────
    if not ota.empty:
        fig, axes = plt.subplots(1, 2, figsize=(20, 8))
        colors50 = [MC[i % len(MC)] for i in range(len(ota))]

        bars = axes[0].barh(ota["OTA_Name"], ota["Net_Revenue"] / 1e3,
                            color=colors50, edgecolor=PAL["bg"])
        axes[0].set_xlabel("Net Revenue (USD Thousands)")
        axes[0].set_title("Net Revenue by OTA", fontweight="bold")
        axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
        axes[0].grid(axis="x", alpha=0.3)
        for b in bars:
            w = b.get_width()
            axes[0].text(w + 0.5, b.get_y() + b.get_height()/2,
                         f"${w:,.0f}K", va="center", fontsize=8, color=PAL["text"])

        axes[1].barh(ota["OTA_Name"], ota["Avg_Commission_Rate_Pct"],
                     color=colors50, edgecolor=PAL["bg"], alpha=0.85)
        axes[1].axvline(30, color=PAL["accent2"], lw=2, linestyle="--", label="30% threshold")
        axes[1].set_xlabel("Avg Commission Rate (%)")
        axes[1].set_title("Avg Commission Rate by OTA", fontweight="bold")
        axes[1].legend(fontsize=9)
        axes[1].grid(axis="x", alpha=0.3)

        titlebar(fig, "OTA Revenue & Commission Analysis",
                 "LEFT: Net Revenue | RIGHT: Average Commission Rate per OTA")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "50_ota_revenue_commission.png")

    # ── CHART 51: Occupancy Heatmap (Month × Property) ──────────
    if "Hotel_Name" in df.columns and "Booking_Date" in df.columns:
        df2 = df.copy()
        df2["Month"] = df2["Booking_Date"].dt.to_period("M").astype(str)
        occ_pivot = df2.groupby(["Hotel_Name","Month"])["Nights"].sum().unstack(fill_value=0)
        occ_pivot = occ_pivot.iloc[:, -24:]  # last 24 months max

        fig, ax = plt.subplots(figsize=(22, max(6, len(occ_pivot)*0.55 + 2)))
        im = ax.imshow(occ_pivot.values, aspect="auto",
                       cmap="RdYlGn", interpolation="nearest")
        ax.set_xticks(range(len(occ_pivot.columns)))
        ax.set_xticklabels(occ_pivot.columns.tolist(), rotation=45, ha="right", fontsize=7)
        ax.set_yticks(range(len(occ_pivot.index)))
        ax.set_yticklabels(occ_pivot.index.tolist(), fontsize=8)
        cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.01)
        cbar.set_label("Room Nights", color=PAL["text"])
        cbar.ax.yaxis.set_tick_params(color=PAL["sub"])
        ax.set_title("Room Nights Heatmap: Month × Property", fontweight="bold")
        titlebar(fig, "Occupancy Heatmap — Room Nights by Month & Property",
                 "Green = high occupancy | Red = low occupancy")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "51_occupancy_heatmap.png")

    # ── CHART 52: Cancellation Rate by OTA + Monthly Trend ──────
    if not ota.empty and not monthly.empty:
        fig, axes = plt.subplots(1, 2, figsize=(20, 8))
        colors52 = [PAL["accent2"] if r > 20 else PAL["accent3"]
                    for r in ota["Cancel_Rate_Pct"]]
        axes[0].barh(ota["OTA_Name"], ota["Cancel_Rate_Pct"],
                     color=colors52, edgecolor=PAL["bg"])
        axes[0].axvline(20, color=PAL["accent4"], lw=2, linestyle="--", label="20% benchmark")
        axes[0].set_xlabel("Cancellation Rate (%)")
        axes[0].set_title("Cancellation Rate by OTA", fontweight="bold")
        axes[0].legend(fontsize=9)
        axes[0].grid(axis="x", alpha=0.3)

        x = range(len(monthly))
        axes[1].plot(x, monthly["Cancel_Rate_Pct"], color=PAL["accent2"],
                     lw=2.5, marker="o", ms=5, label="Cancel Rate")
        axes[1].fill_between(x, monthly["Cancel_Rate_Pct"], alpha=0.20, color=PAL["accent2"])
        axes[1].set_xticks(list(x)[::2])
        axes[1].set_xticklabels(monthly["Month"].tolist()[::2], rotation=40, ha="right", fontsize=8)
        axes[1].set_ylabel("Cancellation Rate (%)")
        axes[1].set_title("Monthly Cancellation Rate Trend", fontweight="bold")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(fontsize=9)

        titlebar(fig, "Cancellation Rate Analysis",
                 "LEFT: by OTA (red = >20%) | RIGHT: monthly trend")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "52_cancellation_analysis.png")

    # ── CHART 53: Customer Segment Revenue + Bookings ────────────
    if not customer_seg.empty:
        seg_col = customer_seg.columns[0]
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        colors53 = [MC[i % len(MC)] for i in range(len(customer_seg))]

        axes[0].bar(customer_seg[seg_col], customer_seg["Net_Revenue"] / 1e3,
                    color=colors53, edgecolor=PAL["bg"])
        axes[0].set_ylabel("Net Revenue (USD Thousands)")
        axes[0].set_title("Revenue by Customer Segment", fontweight="bold")
        axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
        axes[0].tick_params(axis="x", rotation=30)
        axes[0].grid(axis="y", alpha=0.3)

        axes[1].bar(customer_seg[seg_col], customer_seg["Bookings"],
                    color=colors53, edgecolor=PAL["bg"], alpha=0.85)
        axes[1].set_ylabel("Number of Bookings")
        axes[1].set_title("Bookings by Customer Segment", fontweight="bold")
        axes[1].tick_params(axis="x", rotation=30)
        axes[1].grid(axis="y", alpha=0.3)

        titlebar(fig, "Customer Segment KPI Analysis",
                 "LEFT: Revenue contribution | RIGHT: Booking volume per segment")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "53_customer_segment_kpi.png")

    log.info("  Total charts generated: 6 (Images/48 through 53)")


# ─────────────────────────────────────────────
# 5. GENERATE MARKDOWN REPORT
# ─────────────────────────────────────────────
def generate_report(portfolio, monthly, ota, property_, customer_seg):
    os.makedirs("Reports", exist_ok=True)

    top5_ota = ota.head(5) if not ota.empty else pd.DataFrame()
    top5_prop = property_.head(5) if not property_.empty else pd.DataFrame()

    lines = [
        "# Phase 6 — KPI Monitoring Dashboard Report",
        "",
        "**Project**: OTA Performance & Channel Management",
        "**Phase**: 6 — KPI Monitoring Dashboard Datasets",
        "**Script**: `Python/kpi_dashboard.py`",
        "",
        "---",
        "",
        "## Portfolio KPI Summary",
        "",
        "| KPI | Value |",
        "|-----|-------|",
        f"| Total Bookings | {portfolio['Total_Bookings']:,} |",
        f"| Net Revenue | ${portfolio['Net_Revenue']:,.2f} |",
        f"| Gross Revenue | ${portfolio['Gross_Revenue']:,.2f} |",
        f"| Commission Amount | ${portfolio['Commission_Amount']:,.2f} |",
        f"| Avg Commission Rate | {portfolio['Avg_Commission_Rate_Pct']:.2f}% |",
        f"| Cancellation Rate | {portfolio['Cancel_Rate_Pct']:.2f}% |",
        f"| Total Room Nights | {portfolio['Total_Room_Nights']:,} |",
        f"| ADR (Avg Daily Rate) | ${portfolio['ADR']:.2f} |",
        f"| RevPAR | ${portfolio['RevPAR']:.2f} |",
        f"| Estimated Occupancy Rate | {portfolio['Occupancy_Rate_Pct']:.2f}% |",
        "",
        "---",
        "",
        "## Top OTAs by Net Revenue",
        "",
    ]

    if not top5_ota.empty:
        lines.append("| OTA | Bookings | Net Revenue | Cancel Rate | Avg Commission |")
        lines.append("|-----|----------|------------|------------|----------------|")
        for _, row in top5_ota.iterrows():
            lines.append(
                f"| {row['OTA_Name']} | {int(row['Bookings']):,} | "
                f"${row['Net_Revenue']:,.0f} | {row['Cancel_Rate_Pct']:.1f}% | "
                f"{row['Avg_Commission_Rate_Pct']:.1f}% |"
            )
    lines += ["", "---", "", "## Top Properties by Net Revenue", ""]
    if not top5_prop.empty:
        lines.append("| Hotel | Bookings | Net Revenue | Cancel Rate | ADR |")
        lines.append("|-------|----------|------------|------------|-----|")
        for _, row in top5_prop.iterrows():
            lines.append(
                f"| {row['Hotel_Name']} | {int(row['Bookings']):,} | "
                f"${row['Net_Revenue']:,.0f} | {row['Cancel_Rate_Pct']:.1f}% | "
                f"${row['ADR']:.2f} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Output Files",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `Dataset/kpi_monthly.csv` | Monthly KPI metrics |",
        "| `Dataset/kpi_by_ota.csv` | OTA-level KPI summary |",
        "| `Dataset/kpi_by_property.csv` | Property-level KPI summary |",
        "| `Dataset/kpi_by_customer_segment.csv` | Customer segment KPIs |",
        "| `Dataset/kpi_summary.csv` | Single-row portfolio snapshot |",
        "| `Images/48_kpi_scorecard.png` | Portfolio KPI tile scorecard |",
        "| `Images/49_monthly_revenue_adr.png` | Monthly Revenue and ADR trends |",
        "| `Images/50_ota_revenue_commission.png` | OTA revenue and commission comparison |",
        "| `Images/51_occupancy_heatmap.png` | Room nights heatmap by month × property |",
        "| `Images/52_cancellation_analysis.png` | Cancellation rate by OTA and monthly |",
        "| `Images/53_customer_segment_kpi.png` | Customer segment revenue and bookings |",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **RevPAR Improvement**: Focus upselling strategies on low-ADR periods to lift RevPAR.",
        "2. **OTA Commission Renegotiation**: Platforms exceeding 25% commission deserve contract review.",
        "3. **Cancellation Reduction**: OTAs with >20% cancel rate should offer incentive-based retention.",
        "4. **Segment Focus**: Direct investment in top-revenue segments to maximise lifetime value.",
        "5. **Occupancy Efficiency**: Identify low-occupancy months for dynamic pricing campaigns.",
    ]

    path = os.path.join("Reports", "Phase_6_KPI_Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"Report saved -> {path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  PHASE 6: KPI MONITORING DASHBOARD DATASETS")
    print("=" * 65)

    try:
        df = load_data()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    log.info("\nComputing portfolio KPIs...")
    portfolio = portfolio_kpis(df)
    for k, v in portfolio.items():
        log.info(f"  {k}: {v}")

    log.info("\nBuilding KPI tables...")
    monthly   = monthly_kpis(df)
    ota       = ota_kpis(df)
    property_ = property_kpis(df)
    cust_seg  = customer_segment_kpis(df)

    log.info("\nExporting CSVs...")
    export_kpi_tables(monthly, ota, property_, cust_seg, portfolio)

    generate_kpi_charts(df, monthly, ota, property_, cust_seg, portfolio)
    generate_report(portfolio, monthly, ota, property_, cust_seg)

    print("\n" + "=" * 65)
    print("  PHASE 6 COMPLETE")
    print("  CSVs:   Dataset/kpi_monthly.csv, kpi_by_ota.csv,")
    print("           kpi_by_property.csv, kpi_by_customer_segment.csv")
    print("  Charts: Images/48 through 53")
    print("  Report: Reports/Phase_6_KPI_Report.md")
    print("=" * 65)


if __name__ == "__main__":
    main()
