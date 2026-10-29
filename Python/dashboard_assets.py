"""
Phase 7: Interactive Dashboard Assets
OTA Performance & Channel Management Project
============================================================
Inputs  : Dataset/ota_master_dataset.csv
          Dataset/kpi_monthly.csv (from Phase 6)
          Dataset/kpi_by_ota.csv
          Dataset/kpi_by_property.csv
Outputs : Dataset/dash_summary.csv
          Dataset/dash_monthly.csv
          Dataset/dash_ota_monthly.csv
          Dataset/dash_property_monthly.csv
          Dataset/dash_customer_kpis.csv
          Images/54_*.png – 59_*.png
============================================================
All tables are Power BI / Tableau ready (flat, numeric types clean).
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
# STYLE
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
# 2. BUILD DASHBOARD ASSET TABLES
# ─────────────────────────────────────────────
def build_summary(df):
    """Single-row portfolio snapshot for a dashboard header."""
    total = len(df)
    cancelled = (df["Booking_Status"] == "Cancelled").sum() if "Booking_Status" in df.columns else 0
    confirmed = total - cancelled
    room_nights = df["Nights"].fillna(1).sum()
    adr = df["Net_Revenue"].sum() / room_nights if room_nights > 0 else 0

    summary = pd.DataFrame([{
        "Report_Date": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "Total_Bookings": total,
        "Confirmed_Bookings": int(confirmed),
        "Cancelled_Bookings": int(cancelled),
        "Cancel_Rate_Pct": round(cancelled / total * 100, 2) if total > 0 else 0,
        "Net_Revenue": round(df["Net_Revenue"].sum(), 2),
        "Gross_Revenue": round(df["Gross_Revenue"].sum(), 2) if "Gross_Revenue" in df.columns else None,
        "Commission_Amount": round(df["Commission_Amount"].sum(), 2) if "Commission_Amount" in df.columns else None,
        "Avg_Commission_Rate_Pct": round(df["Commission_Rate"].mean() * 100, 2) if "Commission_Rate" in df.columns else None,
        "Total_Room_Nights": int(room_nights),
        "ADR": round(adr, 2),
        "Unique_Customers": df["Customer_ID"].nunique(),
        "Unique_Properties": df["Hotel_ID"].nunique() if "Hotel_ID" in df.columns else None,
        "Unique_OTAs": df["OTA_Name"].nunique() if "OTA_Name" in df.columns else None,
        "Avg_Lead_Time_Days": round(df["Lead_Time"].mean(), 1) if "Lead_Time" in df.columns else None,
    }])
    return summary


def build_monthly(df):
    """Month-level dashboard metrics."""
    df2 = df.copy()
    df2["Month"] = df2["Booking_Date"].dt.to_period("M").astype(str)
    df2["YearMonth_Num"] = df2["Booking_Date"].dt.year * 100 + df2["Booking_Date"].dt.month

    monthly = df2.groupby(["Month","YearMonth_Num"]).agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Commission_Amount=("Commission_Amount", "sum"),
        Avg_Commission_Rate=("Commission_Rate", "mean"),
        Room_Nights=("Nights", "sum"),
        Avg_Lead_Time=("Lead_Time", "mean"),
        Unique_Customers=("Customer_ID", "nunique"),
    ).reset_index()

    cancel_monthly = df2[df2["Booking_Status"]=="Cancelled"].groupby("Month").size().reset_index(name="Cancellations")
    monthly = monthly.merge(cancel_monthly, on="Month", how="left")
    monthly["Cancellations"] = monthly["Cancellations"].fillna(0)
    monthly["Cancel_Rate_Pct"] = (monthly["Cancellations"] / monthly["Bookings"] * 100).round(2)
    monthly["ADR"] = (monthly["Net_Revenue"] / monthly["Room_Nights"].replace(0, np.nan)).round(2)
    monthly["Avg_Commission_Rate_Pct"] = (monthly["Avg_Commission_Rate"] * 100).round(2)
    monthly = monthly.sort_values("YearMonth_Num")
    monthly["MoM_Revenue_Pct"] = monthly["Net_Revenue"].pct_change() * 100
    monthly["MoM_Bookings_Pct"] = monthly["Bookings"].pct_change() * 100

    cols = ["Month","Bookings","Net_Revenue","Gross_Revenue","Commission_Amount",
            "Avg_Commission_Rate_Pct","Room_Nights","Cancellations","Cancel_Rate_Pct",
            "ADR","Avg_Lead_Time","Unique_Customers","MoM_Revenue_Pct","MoM_Bookings_Pct"]
    return monthly[[c for c in cols if c in monthly.columns]].round(2)


def build_ota_monthly(df):
    """OTA × Month pivot — useful for slicer-based filtering in Power BI."""
    if "OTA_Name" not in df.columns:
        return pd.DataFrame()
    df2 = df.copy()
    df2["Month"] = df2["Booking_Date"].dt.to_period("M").astype(str)

    grp = df2.groupby(["OTA_Name","Month"]).agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Commission_Amount=("Commission_Amount", "sum"),
        Avg_Commission_Rate=("Commission_Rate", "mean"),
        Room_Nights=("Nights", "sum"),
    ).reset_index()

    cancel_grp = df2[df2["Booking_Status"]=="Cancelled"].groupby(
        ["OTA_Name","Month"]).size().reset_index(name="Cancellations")
    grp = grp.merge(cancel_grp, on=["OTA_Name","Month"], how="left")
    grp["Cancellations"] = grp["Cancellations"].fillna(0)
    grp["Cancel_Rate_Pct"] = (grp["Cancellations"] / grp["Bookings"] * 100).round(2)
    grp["ADR"] = (grp["Net_Revenue"] / grp["Room_Nights"].replace(0, np.nan)).round(2)
    grp["Avg_Commission_Rate_Pct"] = (grp["Avg_Commission_Rate"] * 100).round(2)

    cols = ["OTA_Name","Month","Bookings","Net_Revenue","Commission_Amount",
            "Avg_Commission_Rate_Pct","Room_Nights","Cancellations","Cancel_Rate_Pct","ADR"]
    return grp[[c for c in cols if c in grp.columns]].sort_values(["OTA_Name","Month"]).round(2)


def build_property_monthly(df):
    """Property × Month pivot."""
    if "Hotel_Name" not in df.columns:
        return pd.DataFrame()
    df2 = df.copy()
    df2["Month"] = df2["Booking_Date"].dt.to_period("M").astype(str)

    grp = df2.groupby(["Hotel_ID","Hotel_Name","Month"]).agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum"),
        Commission_Amount=("Commission_Amount", "sum"),
        Room_Nights=("Nights", "sum"),
    ).reset_index()

    cancel_grp = df2[df2["Booking_Status"]=="Cancelled"].groupby(
        ["Hotel_ID","Month"]).size().reset_index(name="Cancellations")
    grp = grp.merge(cancel_grp, on=["Hotel_ID","Month"], how="left")
    grp["Cancellations"] = grp["Cancellations"].fillna(0)
    grp["Cancel_Rate_Pct"] = (grp["Cancellations"] / grp["Bookings"] * 100).round(2)
    grp["ADR"] = (grp["Net_Revenue"] / grp["Room_Nights"].replace(0, np.nan)).round(2)

    cols = ["Hotel_ID","Hotel_Name","Month","Bookings","Net_Revenue",
            "Commission_Amount","Room_Nights","Cancellations","Cancel_Rate_Pct","ADR"]
    return grp[[c for c in cols if c in grp.columns]].sort_values(["Hotel_Name","Month"]).round(2)


def build_customer_kpis(df):
    """Customer-level CLV / frequency metrics."""
    cust = df.groupby("Customer_ID").agg(
        Total_Bookings=("Booking_ID", "count"),
        Total_Revenue=("Net_Revenue", "sum"),
        Avg_Revenue_per_Booking=("Net_Revenue", "mean"),
        Avg_Lead_Time=("Lead_Time", "mean"),
        First_Booking=("Booking_Date", "min"),
        Last_Booking=("Booking_Date", "max"),
    ).reset_index()

    cancel_cust = df[df["Booking_Status"]=="Cancelled"].groupby("Customer_ID").size() \
                    .reset_index(name="Cancellations")
    cust = cust.merge(cancel_cust, on="Customer_ID", how="left")
    cust["Cancellations"] = cust["Cancellations"].fillna(0)
    cust["Cancel_Rate_Pct"] = (cust["Cancellations"] / cust["Total_Bookings"] * 100).round(2)

    cust["First_Booking"] = cust["First_Booking"].astype(str)
    cust["Last_Booking"] = cust["Last_Booking"].astype(str)

    return cust.sort_values("Total_Revenue", ascending=False).round(2)


# ─────────────────────────────────────────────
# 3. EXPORT CSVs
# ─────────────────────────────────────────────
def export_assets(summary, monthly, ota_monthly, prop_monthly, customer_kpi):
    os.makedirs("Dataset", exist_ok=True)
    exports = {
        "dash_summary.csv": summary,
        "dash_monthly.csv": monthly,
        "dash_ota_monthly.csv": ota_monthly,
        "dash_property_monthly.csv": prop_monthly,
        "dash_customer_kpis.csv": customer_kpi,
    }
    for fname, df in exports.items():
        path = os.path.join("Dataset", fname)
        df.to_csv(path, index=False)
        log.info(f"  Exported -> {path} ({len(df)} rows)")


# ─────────────────────────────────────────────
# 4. VISUALISATIONS (Charts 54–59)
# ─────────────────────────────────────────────
def generate_dashboard_charts(df, monthly, ota_monthly, prop_monthly, customer_kpi):
    log.info("\nGenerating dashboard asset charts...")

    # ── CHART 54: Multi-KPI Monthly Overview Grid ────────────────
    if not monthly.empty:
        kpi_pairs = [
            ("Net_Revenue", "Net Revenue ($)", PAL["accent1"], "M"),
            ("Bookings",    "Bookings",         PAL["accent3"], ""),
            ("ADR",         "ADR ($)",           PAL["accent4"], ""),
            ("Cancel_Rate_Pct","Cancel Rate (%)", PAL["accent2"], ""),
        ]
        avail = [(k,l,c,f) for k,l,c,f in kpi_pairs if k in monthly.columns]
        fig, axes = plt.subplots(2, 2, figsize=(22, 12))
        axes_flat = axes.flatten()
        x = range(len(monthly))
        for idx, (key, label, color, fmt) in enumerate(avail[:4]):
            ax = axes_flat[idx]
            ax.fill_between(x, monthly[key], alpha=0.20, color=color)
            ax.plot(x, monthly[key], color=color, lw=2.5, marker="o", ms=4, label=label)
            ax.set_title(label, fontweight="bold")
            ax.set_xticks(list(x)[::3])
            ax.set_xticklabels(monthly["Month"].tolist()[::3], rotation=35, ha="right", fontsize=7)
            ax.grid(True, alpha=0.3)
            if fmt == "M":
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v/1e3:,.0f}K"))
            ax.legend(fontsize=9)
        titlebar(fig, "Dashboard: Multi-KPI Monthly Overview",
                 "Revenue · Bookings · ADR · cancellation rate across the full booking horizon")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "54_dashboard_multi_kpi.png")

    # ── CHART 55: ADR vs Occupancy Scatter ──────────────────────
    if "Hotel_Name" in df.columns:
        prop_grp = df.groupby("Hotel_Name").agg(
            Net_Revenue=("Net_Revenue", "sum"),
            Room_Nights=("Nights", "sum"),
            Bookings=("Booking_ID", "count"),
        ).reset_index()
        prop_grp["ADR"] = prop_grp["Net_Revenue"] / prop_grp["Room_Nights"].replace(0, np.nan)

        fig, ax = plt.subplots(figsize=(16, 9))
        colors55 = [MC[i % len(MC)] for i in range(len(prop_grp))]
        sc = ax.scatter(prop_grp["ADR"], prop_grp["Room_Nights"],
                        s=prop_grp["Bookings"] / prop_grp["Bookings"].max() * 800 + 60,
                        c=colors55, alpha=0.80, edgecolors=PAL["bg"], linewidths=1.5)
        for _, row in prop_grp.iterrows():
            ax.annotate(row["Hotel_Name"],
                        (row["ADR"], row["Room_Nights"]),
                        fontsize=7, color=PAL["sub"],
                        xytext=(4, 4), textcoords="offset points")
        ax.set_xlabel("ADR (USD)")
        ax.set_ylabel("Total Room Nights")
        ax.set_title("ADR vs Room Nights by Property (bubble = bookings)", fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
        titlebar(fig, "Property Performance: ADR vs Room Nights",
                 "Bubble size = total booking count")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "55_adr_vs_room_nights.png")

    # ── CHART 56: OTA Monthly Revenue Stacked Area ──────────────
    if not ota_monthly.empty and "OTA_Name" in ota_monthly.columns:
        pivot = ota_monthly.pivot_table(index="Month", columns="OTA_Name",
                                         values="Net_Revenue", aggfunc="sum", fill_value=0)
        pivot = pivot.sort_index()
        x = range(len(pivot))
        fig, ax = plt.subplots(figsize=(22, 8))
        bottom = np.zeros(len(pivot))
        for i, col in enumerate(pivot.columns):
            color = MC[i % len(MC)]
            ax.fill_between(x, bottom, bottom + pivot[col].values,
                            alpha=0.75, color=color, label=col)
            bottom += pivot[col].values
        ax.set_xticks(list(x)[::2])
        ax.set_xticklabels(pivot.index.tolist()[::2], rotation=40, ha="right", fontsize=8)
        ax.set_ylabel("Net Revenue (USD)")
        ax.set_title("Monthly Net Revenue by OTA (Stacked Area)", fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}"))
        ax.legend(fontsize=8, loc="upper left", ncol=2)
        ax.grid(True, alpha=0.25)
        titlebar(fig, "OTA Monthly Revenue Composition",
                 "Stacked area shows each OTA's revenue contribution over time")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "56_ota_monthly_stacked_area.png")

    # ── CHART 57: Lead Time Distribution ────────────────────────
    if "Lead_Time" in df.columns:
        fig, axes = plt.subplots(1, 2, figsize=(18, 7))
        lead = df["Lead_Time"].dropna()
        axes[0].hist(lead, bins=40, color=PAL["accent1"], edgecolor=PAL["bg"], alpha=0.85)
        axes[0].axvline(lead.mean(), color=PAL["accent2"], lw=2, linestyle="--",
                        label=f"Mean: {lead.mean():.1f} days")
        axes[0].axvline(lead.median(), color=PAL["accent3"], lw=2, linestyle=":",
                        label=f"Median: {lead.median():.1f} days")
        axes[0].set_xlabel("Lead Time (Days)")
        axes[0].set_ylabel("Frequency")
        axes[0].set_title("Booking Lead Time Distribution", fontweight="bold")
        axes[0].legend(fontsize=9)
        axes[0].grid(True, alpha=0.3)

        if "OTA_Name" in df.columns:
            lead_by_ota = df.groupby("OTA_Name")["Lead_Time"].mean().sort_values(ascending=True)
            colors57 = [MC[i % len(MC)] for i in range(len(lead_by_ota))]
            axes[1].barh(lead_by_ota.index, lead_by_ota.values, color=colors57, edgecolor=PAL["bg"])
            axes[1].set_xlabel("Avg Lead Time (Days)")
            axes[1].set_title("Average Lead Time by OTA", fontweight="bold")
            axes[1].grid(axis="x", alpha=0.3)
        else:
            axes[1].axis("off")

        titlebar(fig, "Booking Lead Time Analysis",
                 "LEFT: overall distribution | RIGHT: mean lead time per OTA")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "57_lead_time_analysis.png")

    # ── CHART 58: Booking Status Funnel ─────────────────────────
    if "Booking_Status" in df.columns:
        status_counts = df["Booking_Status"].value_counts()
        total = len(df)
        fig, ax = plt.subplots(figsize=(14, 7))
        colors58 = [MC[i % len(MC)] for i in range(len(status_counts))]
        bars = ax.barh(status_counts.index, status_counts.values,
                       color=colors58, edgecolor=PAL["bg"], height=0.55)
        ax.set_xlabel("Number of Bookings")
        ax.set_title("Booking Status Distribution", fontweight="bold")
        ax.grid(axis="x", alpha=0.3)
        for b in bars:
            w = b.get_width()
            pct = w / total * 100
            ax.text(w + 10, b.get_y() + b.get_height()/2,
                    f"{int(w):,} ({pct:.1f}%)", va="center", fontsize=9, color=PAL["text"])
        titlebar(fig, "Booking Status Breakdown",
                 "Distribution of Confirmed / Cancelled / other booking statuses")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "58_booking_status_funnel.png")

    # ── CHART 59: Revenue Blend — Room Type + OTA Stacked Bar ───
    if "Room_Type" in df.columns and "OTA_Name" in df.columns:
        rev_blend = df.groupby(["Room_Type","OTA_Name"])["Net_Revenue"].sum().unstack(fill_value=0)
        row_totals = rev_blend.sum(axis=1)
        rev_blend = rev_blend.loc[row_totals.sort_values(ascending=True).index]

        fig, ax = plt.subplots(figsize=(18, 8))
        bottom = np.zeros(len(rev_blend))
        for i, col in enumerate(rev_blend.columns):
            ax.bar(rev_blend.index, rev_blend[col].values / 1e3,
                   bottom=bottom / 1e3, label=col,
                   color=MC[i % len(MC)], edgecolor=PAL["bg"], alpha=0.85)
            bottom += rev_blend[col].values
        ax.set_ylabel("Net Revenue (USD Thousands)")
        ax.set_title("Revenue Blend: Room Type × OTA", fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
        ax.tick_params(axis="x", rotation=35)
        ax.legend(fontsize=8, loc="upper right", ncol=2)
        ax.grid(axis="y", alpha=0.3)
        titlebar(fig, "Revenue Blend: Room Type × OTA",
                 "Stacked bars show which OTA drives revenue for each room category")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        savefig(fig, "59_revenue_blend_room_ota.png")

    log.info("  Total charts generated: 6 (Images/54 through 59)")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  PHASE 7: INTERACTIVE DASHBOARD ASSETS")
    print("=" * 65)

    try:
        df = load_data()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    log.info("\nBuilding dashboard asset tables...")
    summary      = build_summary(df)
    monthly      = build_monthly(df)
    ota_monthly  = build_ota_monthly(df)
    prop_monthly = build_property_monthly(df)
    cust_kpi     = build_customer_kpis(df)

    log.info("\nExporting CSVs...")
    export_assets(summary, monthly, ota_monthly, prop_monthly, cust_kpi)

    generate_dashboard_charts(df, monthly, ota_monthly, prop_monthly, cust_kpi)

    print("\n" + "=" * 65)
    print("  PHASE 7 COMPLETE")
    print("  CSVs:   Dataset/dash_summary.csv, dash_monthly.csv,")
    print("           dash_ota_monthly.csv, dash_property_monthly.csv,")
    print("           dash_customer_kpis.csv")
    print("  Charts: Images/54 through 59")
    print("=" * 65)


if __name__ == "__main__":
    main()
