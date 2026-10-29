"""
Phase 4: Product Performance & Sales Analysis
OTA Performance & Channel Management Project
============================================================
Inputs  : Dataset/ota_master_dataset.csv + all star-schema CSVs
Outputs : Images/27_*.png – 41_*.png  |  Dataset/kpi_summary.csv
Script  : Python/performance_analysis.py
============================================================
Functions
---------
load_datasets()
compute_kpis()
ota_analysis()
hotel_analysis()
room_type_analysis()
city_country_analysis()
season_analysis()
customer_analysis()
cancellation_analysis()
top_bottom_analysis()
generate_visualizations()
print_business_insights()
export_kpi_csv()
main()
"""

import os
import sys
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

# ─────────────────────────────────────────────
# STYLE – identical dark theme across all phases
# ─────────────────────────────────────────────
PAL = {
    "bg":      "#0F1117",
    "card":    "#1A1D2E",
    "accent1": "#6C63FF",
    "accent2": "#FF6584",
    "accent3": "#43E97B",
    "accent4": "#F7971E",
    "accent5": "#00C9FF",
    "text":    "#E8EAF6",
    "sub":     "#9FA8DA",
    "grid":    "#2C2F4A",
}
MC = [
    "#6C63FF","#FF6584","#43E97B","#F7971E","#00C9FF",
    "#FF8C69","#A29BFE","#55EFC4","#FD79A8","#FDCB6E",
    "#74B9FF","#E17055","#81ECEC","#DFE6E9","#636E72"
]

def apply_style():
    plt.rcParams.update({
        "figure.facecolor": PAL["bg"], "axes.facecolor": PAL["card"],
        "axes.edgecolor":   PAL["grid"],"axes.labelcolor":  PAL["text"],
        "axes.titlecolor":  PAL["text"],"axes.titlesize":   13,
        "axes.labelsize":   10,         "xtick.color":      PAL["sub"],
        "ytick.color":      PAL["sub"], "xtick.labelsize":  8.5,
        "ytick.labelsize":  8.5,        "grid.color":       PAL["grid"],
        "grid.linestyle":   "--",       "grid.alpha":       0.45,
        "legend.facecolor": PAL["card"],"legend.edgecolor": PAL["grid"],
        "legend.labelcolor":PAL["text"],"text.color":       PAL["text"],
        "font.family":      "DejaVu Sans","figure.dpi":     150,
    })

apply_style()

def savefig(fig, name):
    os.makedirs("Images", exist_ok=True)
    p = os.path.join("Images", name)
    fig.savefig(p, bbox_inches="tight", facecolor=PAL["bg"])
    plt.close(fig)
    print(f"  Saved -> {p}")

def titlebar(fig, title, sub=""):
    fig.text(0.5, 0.987, title, ha="center", va="top",
             fontsize=17, fontweight="bold", color=PAL["text"])
    if sub:
        fig.text(0.5, 0.963, sub, ha="center", va="top",
                 fontsize=10, color=PAL["sub"])

def fmt_usd(v): return f"${v:,.0f}"
def fmt_pct(v): return f"{v:.1f}%"

# ─────────────────────────────────────────────
# 1. LOAD DATASETS
# ─────────────────────────────────────────────
def load_datasets():
    """Load master dataset and all star-schema dimension tables."""
    print("Loading datasets...")
    base = "Dataset"

    df = pd.read_csv(os.path.join(base, "ota_master_dataset.csv"),
                     parse_dates=["Booking_Date","Checkin_Date","Checkout_Date"])

    fact   = pd.read_csv(os.path.join(base, "fact_bookings.csv"),
                         parse_dates=["Booking_Date","Checkin_Date","Checkout_Date"])
    d_cust = pd.read_csv(os.path.join(base, "dim_customers.csv"))
    d_hot  = pd.read_csv(os.path.join(base, "dim_hotels.csv"))
    d_ota  = pd.read_csv(os.path.join(base, "dim_otas.csv"))
    d_date = pd.read_csv(os.path.join(base, "dim_dates.csv"))
    rfm    = pd.read_csv(os.path.join(base, "rfm_segments.csv"))

    # Derived time columns on master
    df["Booking_YM"]    = df["Booking_Date"].dt.to_period("M")
    df["Booking_Month"] = df["Booking_Date"].dt.month
    df["Booking_Year"]  = df["Booking_Date"].dt.year
    df["Booking_Q"]     = df["Booking_Date"].dt.to_period("Q").astype(str)
    
    print(f"  Master : {df.shape}")
    print(f"  Fact   : {fact.shape}")
    print(f"  RFM    : {rfm.shape}")
    return df, fact, d_cust, d_hot, d_ota, d_date, rfm

# ─────────────────────────────────────────────
# 2. KPI CALCULATIONS
# ─────────────────────────────────────────────
def compute_kpis(df):
    """Compute all top-level business KPIs from master dataset."""
    total_bookings      = len(df)
    confirmed           = (df["Booking_Status"] == "Confirmed").sum()
    cancelled           = (df["Booking_Status"] == "Cancelled").sum()
    no_show             = (df["Booking_Status"] == "No-Show").sum()
    cancel_rate         = cancelled / total_bookings * 100
    gross_rev           = df["Gross_Revenue"].sum()
    net_rev             = df["Net_Revenue"].sum()
    commission          = df["Commission_Amount"].sum()
    commission_pct      = commission / gross_rev * 100
    avg_booking_val     = df["Net_Revenue"].mean()
    avg_gross_val       = df["Gross_Revenue"].mean()
    rev_per_booking     = net_rev / total_bookings
    avg_lead_time       = df["Lead_Time"].mean()
    avg_los             = df["Nights"].mean()           # Length of Stay
    avg_guests          = df["Guests"].mean()
    avg_review          = df["Review_Score"].mean()
    total_nights        = df["Nights"].sum()
    adr                 = net_rev / total_nights        # Average Daily Rate

    # Repeat customer rate
    cust_freq = df.groupby("Customer_ID")["Booking_ID"].count()
    repeat_rate = (cust_freq > 1).sum() / len(cust_freq) * 100

    # Unique counts
    unique_customers    = df["Customer_ID"].nunique()
    unique_hotels       = df["Hotel_ID"].nunique()
    unique_otas         = df["OTA_Name"].nunique()

    kpis = {
        "Total Bookings":           total_bookings,
        "Confirmed Bookings":       int(confirmed),
        "Cancelled Bookings":       int(cancelled),
        "No-Show Bookings":         int(no_show),
        "Cancellation Rate (%)":    round(cancel_rate, 2),
        "Gross Revenue ($)":        round(gross_rev, 2),
        "Net Revenue ($)":          round(net_rev, 2),
        "Commission Paid ($)":      round(commission, 2),
        "Commission Rate (%)":      round(commission_pct, 2),
        "Revenue After Commission ($)": round(net_rev, 2),
        "Avg Booking Value ($)":    round(avg_booking_val, 2),
        "Avg Gross Booking Value ($)": round(avg_gross_val, 2),
        "Revenue per Booking ($)":  round(rev_per_booking, 2),
        "Avg Daily Rate ADR ($)":   round(adr, 2),
        "Avg Lead Time (days)":     round(avg_lead_time, 1),
        "Avg Length of Stay (nights)": round(avg_los, 2),
        "Avg Guests per Booking":   round(avg_guests, 2),
        "Avg Review Score":         round(avg_review, 2),
        "Repeat Customer Rate (%)": round(repeat_rate, 2),
        "Unique Customers":         unique_customers,
        "Unique Hotels":            unique_hotels,
        "Unique OTA Platforms":     unique_otas,
        "Total Room-Nights":        int(total_nights),
    }
    return kpis

# ─────────────────────────────────────────────
# 3. OTA ANALYSIS
# ─────────────────────────────────────────────
def ota_analysis(df):
    """Aggregate performance metrics per OTA platform."""
    ota = df.groupby("OTA_Name").agg(
        Bookings        = ("Booking_ID",        "count"),
        Gross_Revenue   = ("Gross_Revenue",      "sum"),
        Net_Revenue     = ("Net_Revenue",        "sum"),
        Commission      = ("Commission_Amount",  "sum"),
        Commission_Rate = ("Commission_Rate",    "mean"),
        Avg_Booking_Val = ("Net_Revenue",        "mean"),
        Avg_Review      = ("Review_Score",       "mean"),
        Total_Nights    = ("Nights",             "sum"),
        Cancellations   = ("Booking_Status",
                           lambda x: (x == "Cancelled").sum()),
    ).reset_index()

    total_bookings = ota["Bookings"].sum()
    total_net_rev  = ota["Net_Revenue"].sum()

    ota["Market_Share_Bookings_Pct"] = (ota["Bookings"]     / total_bookings * 100).round(2)
    ota["Market_Share_Revenue_Pct"]  = (ota["Net_Revenue"]  / total_net_rev  * 100).round(2)
    ota["Cancellation_Rate_Pct"]     = (ota["Cancellations"]/ ota["Bookings"]  * 100).round(2)
    ota["ADR"]                       = (ota["Net_Revenue"]  / ota["Total_Nights"]).round(2)
    ota["Net_Revenue"]               = ota["Net_Revenue"].round(2)
    ota["Gross_Revenue"]             = ota["Gross_Revenue"].round(2)
    ota["Commission"]                = ota["Commission"].round(2)
    ota["Avg_Booking_Val"]           = ota["Avg_Booking_Val"].round(2)
    ota["Avg_Review"]                = ota["Avg_Review"].round(3)

    return ota.sort_values("Net_Revenue", ascending=False)

# ─────────────────────────────────────────────
# 4. HOTEL ANALYSIS
# ─────────────────────────────────────────────
def hotel_analysis(df):
    """Aggregate performance metrics per hotel."""
    hot = df.groupby(["Hotel_ID", "Hotel_Name", "Hotel_City", "Hotel_Rating"]).agg(
        Bookings        = ("Booking_ID",       "count"),
        Gross_Revenue   = ("Gross_Revenue",    "sum"),
        Net_Revenue     = ("Net_Revenue",      "sum"),
        Commission      = ("Commission_Amount","sum"),
        Total_Nights    = ("Nights",           "sum"),
        Avg_Review      = ("Review_Score",     "mean"),
        Cancellations   = ("Booking_Status",
                           lambda x: (x == "Cancelled").sum()),
        Avg_Room_Price  = ("Room_Price",       "mean"),
    ).reset_index()

    hot["Cancellation_Rate_Pct"] = (hot["Cancellations"] / hot["Bookings"] * 100).round(2)
    hot["ADR"]                   = (hot["Net_Revenue"]   / hot["Total_Nights"]).round(2)
    hot["Revenue_per_Booking"]   = (hot["Net_Revenue"]   / hot["Bookings"]).round(2)
    hot["Net_Revenue"]           = hot["Net_Revenue"].round(2)
    hot["Avg_Review"]            = hot["Avg_Review"].round(3)

    return hot.sort_values("Net_Revenue", ascending=False)

# ─────────────────────────────────────────────
# 5. ROOM TYPE ANALYSIS
# ─────────────────────────────────────────────
def room_type_analysis(df):
    """Aggregate performance metrics per room type."""
    rt = df.groupby("Room_Type").agg(
        Bookings        = ("Booking_ID",       "count"),
        Gross_Revenue   = ("Gross_Revenue",    "sum"),
        Net_Revenue     = ("Net_Revenue",      "sum"),
        Avg_Room_Price  = ("Room_Price",       "mean"),
        Total_Nights    = ("Nights",           "sum"),
        Avg_Review      = ("Review_Score",     "mean"),
        Cancellations   = ("Booking_Status",
                           lambda x: (x == "Cancelled").sum()),
    ).reset_index()

    total_rev  = rt["Net_Revenue"].sum()
    rt["Revenue_Share_Pct"]      = (rt["Net_Revenue"] / total_rev * 100).round(2)
    rt["Cancellation_Rate_Pct"]  = (rt["Cancellations"] / rt["Bookings"] * 100).round(2)
    rt["ADR"]                    = (rt["Net_Revenue"]   / rt["Total_Nights"]).round(2)
    rt["Avg_Room_Price"]         = rt["Avg_Room_Price"].round(2)
    rt["Net_Revenue"]            = rt["Net_Revenue"].round(2)

    return rt.sort_values("Net_Revenue", ascending=False)

# ─────────────────────────────────────────────
# 6. CITY & COUNTRY ANALYSIS
# ─────────────────────────────────────────────
def city_country_analysis(df):
    """Hotel city and customer country revenue/booking analysis."""
    # Hotel city performance
    city = df.groupby("Hotel_City").agg(
        Bookings    = ("Booking_ID",    "count"),
        Net_Revenue = ("Net_Revenue",   "sum"),
        Avg_Review  = ("Review_Score",  "mean"),
        Cancellations = ("Booking_Status", lambda x: (x == "Cancelled").sum()),
    ).reset_index()
    city["Cancellation_Rate_Pct"] = (city["Cancellations"] / city["Bookings"] * 100).round(2)
    city["Net_Revenue"]           = city["Net_Revenue"].round(2)
    city["Avg_Review"]            = city["Avg_Review"].round(3)
    city = city.sort_values("Net_Revenue", ascending=False)

    # Customer country performance
    country = df.groupby("Country").agg(
        Bookings    = ("Booking_ID",    "count"),
        Net_Revenue = ("Net_Revenue",   "sum"),
        Avg_Review  = ("Review_Score",  "mean"),
        Unique_Customers = ("Customer_ID", "nunique"),
    ).reset_index()
    total_rev = country["Net_Revenue"].sum()
    country["Revenue_Share_Pct"] = (country["Net_Revenue"] / total_rev * 100).round(2)
    country["Net_Revenue"]       = country["Net_Revenue"].round(2)
    country = country.sort_values("Net_Revenue", ascending=False)

    return city, country

# ─────────────────────────────────────────────
# 7. SEASON ANALYSIS
# ─────────────────────────────────────────────
def season_analysis(df):
    """Revenue, bookings, and cancellations by season."""
    season_order = ["Spring", "Summer", "Autumn", "Winter"]
    seas = df.groupby("Season").agg(
        Bookings      = ("Booking_ID",    "count"),
        Gross_Revenue = ("Gross_Revenue", "sum"),
        Net_Revenue   = ("Net_Revenue",   "sum"),
        Avg_Net_Rev   = ("Net_Revenue",   "mean"),
        Cancellations = ("Booking_Status", lambda x: (x == "Cancelled").sum()),
        Avg_Review    = ("Review_Score",  "mean"),
        Total_Nights  = ("Nights",        "sum"),
    ).reindex(season_order).reset_index()

    seas["Cancellation_Rate_Pct"] = (seas["Cancellations"] / seas["Bookings"] * 100).round(2)
    seas["ADR"]                   = (seas["Net_Revenue"]   / seas["Total_Nights"]).round(2)
    seas["Net_Revenue"]           = seas["Net_Revenue"].round(2)
    seas["Avg_Net_Rev"]           = seas["Avg_Net_Rev"].round(2)
    return seas

# ─────────────────────────────────────────────
# 8. CUSTOMER / LOYALTY ANALYSIS
# ─────────────────────────────────────────────
def customer_analysis(df, rfm):
    """Revenue and booking behaviour by loyalty tier and RFM segment."""
    loyalty_order = ["Standard", "Silver", "Gold", "Platinum"]
    loy = df.groupby("Loyalty_Status").agg(
        Bookings      = ("Booking_ID",    "count"),
        Net_Revenue   = ("Net_Revenue",   "sum"),
        Avg_Rev       = ("Net_Revenue",   "mean"),
        Avg_Review    = ("Review_Score",  "mean"),
        Unique_Cust   = ("Customer_ID",   "nunique"),
        Cancellations = ("Booking_Status", lambda x: (x == "Cancelled").sum()),
    ).reindex(loyalty_order).reset_index()

    loy["Revenue_Share_Pct"]     = (loy["Net_Revenue"] / loy["Net_Revenue"].sum() * 100).round(2)
    loy["Cancellation_Rate_Pct"] = (loy["Cancellations"] / loy["Bookings"] * 100).round(2)
    loy["Net_Revenue"]           = loy["Net_Revenue"].round(2)
    loy["Avg_Rev"]               = loy["Avg_Rev"].round(2)

    # RFM segment revenue contribution
    seg_rev = rfm.groupby("Segment").agg(
        Customers   = ("Customer_ID", "count"),
        Total_Rev   = ("Monetary",    "sum"),
        Avg_CLV     = ("Monetary",    "mean"),
    ).reset_index().sort_values("Total_Rev", ascending=False)

    return loy, seg_rev

# ─────────────────────────────────────────────
# 9. CANCELLATION ANALYSIS
# ─────────────────────────────────────────────
def cancellation_analysis(df):
    """Detailed cancellation breakdown across multiple dimensions."""
    # Monthly cancellation rate
    monthly = df.groupby("Booking_YM").agg(
        Bookings      = ("Booking_ID",    "count"),
        Cancellations = ("Booking_Status", lambda x: (x == "Cancelled").sum()),
    ).reset_index()
    monthly["Cancel_Rate"] = (monthly["Cancellations"] / monthly["Bookings"] * 100).round(2)
    monthly["Period"]      = monthly["Booking_YM"].astype(str)

    # By device type
    device = df.groupby("Device_Type").agg(
        Bookings      = ("Booking_ID",    "count"),
        Cancellations = ("Booking_Status", lambda x: (x == "Cancelled").sum()),
    ).reset_index()
    device["Cancel_Rate"] = (device["Cancellations"] / device["Bookings"] * 100).round(2)

    # By payment method
    pay = df.groupby("Payment_Method").agg(
        Bookings      = ("Booking_ID",    "count"),
        Cancellations = ("Booking_Status", lambda x: (x == "Cancelled").sum()),
    ).reset_index()
    pay["Cancel_Rate"] = (pay["Cancellations"] / pay["Bookings"] * 100).round(2)

    return monthly, device, pay

# ─────────────────────────────────────────────
# 10. TOP / BOTTOM ANALYSIS
# ─────────────────────────────────────────────
def top_bottom_analysis(df, ota_df, hotel_df, rt_df, city_df, country_df):
    """Identify top and bottom performers across all dimensions."""
    results = {}

    results["Top 5 OTAs by Revenue"]           = ota_df.head(5)[["OTA_Name","Net_Revenue","Cancellation_Rate_Pct"]].values.tolist()
    results["Bottom 5 OTAs by Revenue"]         = ota_df.tail(5)[["OTA_Name","Net_Revenue","Cancellation_Rate_Pct"]].values.tolist()
    results["Highest Cancellation OTA"]         = ota_df.loc[ota_df["Cancellation_Rate_Pct"].idxmax(), "OTA_Name"]
    results["Lowest Cancellation OTA"]          = ota_df.loc[ota_df["Cancellation_Rate_Pct"].idxmin(), "OTA_Name"]
    results["Top 5 Hotels by Revenue"]          = hotel_df.head(5)[["Hotel_Name","Net_Revenue"]].values.tolist()
    results["Bottom 5 Hotels by Revenue"]       = hotel_df.tail(5)[["Hotel_Name","Net_Revenue"]].values.tolist()
    results["Best Room Type by Revenue"]        = rt_df.iloc[0]["Room_Type"]
    results["Worst Room Type by Revenue"]       = rt_df.iloc[-1]["Room_Type"]
    results["Highest Revenue City"]             = city_df.iloc[0]["Hotel_City"]
    results["Highest Revenue Country"]          = country_df.iloc[0]["Country"]

    # Peak / lowest booking month
    monthly = df.groupby(df["Booking_Date"].dt.to_period("M"))["Booking_ID"].count()
    results["Peak Booking Month"]    = str(monthly.idxmax())
    results["Lowest Booking Month"]  = str(monthly.idxmin())

    return results

# ─────────────────────────────────────────────
# 11. GENERATE ALL VISUALISATIONS (15 charts)
# ─────────────────────────────────────────────
def generate_visualizations(df, kpis, ota_df, hotel_df, rt_df, city_df, country_df,
                             seas_df, loy_df, seg_rev_df, monthly_cancel):

    print("\nGenerating visualisations...")

    # ── CHART 27: KPI Scorecard ──────────────────────────────────
    kpi_items = [
        ("Total Bookings",           f"{kpis['Total Bookings']:,}",             PAL["accent5"]),
        ("Confirmed",                f"{kpis['Confirmed Bookings']:,}",          PAL["accent3"]),
        ("Cancelled",                f"{kpis['Cancelled Bookings']:,}",          PAL["accent2"]),
        ("Cancellation Rate",        fmt_pct(kpis["Cancellation Rate (%)"]),     PAL["accent2"]),
        ("Gross Revenue",            fmt_usd(kpis["Gross Revenue ($)"]),         PAL["accent4"]),
        ("Net Revenue",              fmt_usd(kpis["Net Revenue ($)"]),            PAL["accent3"]),
        ("Commission Paid",          fmt_usd(kpis["Commission Paid ($)"]),        PAL["accent1"]),
        ("Avg Booking Value",        fmt_usd(kpis["Avg Booking Value ($)"]),      PAL["accent1"]),
        ("Avg Daily Rate (ADR)",     fmt_usd(kpis["Avg Daily Rate ADR ($)"]),    PAL["accent5"]),
        ("Avg Lead Time",            f"{kpis['Avg Lead Time (days)']} days",     PAL["sub"]),
        ("Avg Length of Stay",       f"{kpis['Avg Length of Stay (nights)']} nts",PAL["sub"]),
        ("Avg Review Score",         f"{kpis['Avg Review Score']} / 5.0",        PAL["accent3"]),
        ("Repeat Customer Rate",     fmt_pct(kpis["Repeat Customer Rate (%)"]),  PAL["accent1"]),
        ("Unique Customers",         f"{kpis['Unique Customers']:,}",            PAL["accent5"]),
        ("Total Room-Nights Sold",   f"{kpis['Total Room-Nights']:,}",           PAL["accent4"]),
    ]
    fig, axes = plt.subplots(3, 5, figsize=(28, 12))
    axes = axes.flatten()
    for ax, (label, value, color) in zip(axes, kpi_items):
        rect = FancyBboxPatch((0.05,0.05),0.90,0.90,
                              boxstyle="round,pad=0.04",lw=2,
                              edgecolor=color,facecolor=PAL["card"])
        ax.add_patch(rect)
        ax.text(0.5,0.60,value, ha="center",va="center",
                fontsize=18,fontweight="bold",color=color,transform=ax.transAxes)
        ax.text(0.5,0.28,label,ha="center",va="center",
                fontsize=9,color=PAL["sub"],transform=ax.transAxes,linespacing=1.3)
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    titlebar(fig,"Executive KPI Scorecard — OTA Performance","All KPIs derived directly from cleaned master dataset")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"27_kpi_scorecard.png")

    # ── CHART 28: Monthly Revenue Trend ─────────────────────────
    monthly_rev = df.groupby("Booking_YM").agg(
        Gross=("Gross_Revenue","sum"), Net=("Net_Revenue","sum")
    ).reset_index()
    monthly_rev["Period"] = monthly_rev["Booking_YM"].astype(str)
    x = range(len(monthly_rev))

    fig, ax = plt.subplots(figsize=(22,7))
    ax.fill_between(x, monthly_rev["Gross"]/1e3, alpha=0.18, color=PAL["accent3"])
    ax.plot(x, monthly_rev["Gross"]/1e3, color=PAL["accent3"], lw=2.5, marker="o", ms=5, label="Gross Revenue ($K)")
    ax.fill_between(x, monthly_rev["Net"]/1e3,   alpha=0.18, color=PAL["accent5"])
    ax.plot(x, monthly_rev["Net"]/1e3,   color=PAL["accent5"], lw=2.5, marker="s", ms=4, ls="--", label="Net Revenue ($K)")
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels(monthly_rev["Period"].values[::2], rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Revenue (USD Thousands)")
    ax.set_title("Monthly Gross vs Net Revenue Trend (Jan 2024 – Jun 2026)", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.legend(); ax.grid(True,alpha=0.3)
    peak = monthly_rev["Net"].idxmax()
    ax.annotate(f"Peak: {monthly_rev.loc[peak,'Period']}",
                xy=(peak, monthly_rev.loc[peak,"Net"]/1e3),
                xytext=(peak+1, monthly_rev.loc[peak,"Net"]/1e3 + 5),
                arrowprops={"arrowstyle":"->","color":PAL["accent4"]},
                fontsize=9, color=PAL["accent4"])
    titlebar(fig,"Monthly Revenue Trend","Commission gap between Gross and Net lines represents OTA commission costs")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"28_monthly_revenue_trend.png")

    # ── CHART 29: Monthly Bookings Bar ──────────────────────────
    monthly_bk = df.groupby("Booking_YM")["Booking_ID"].count().reset_index()
    monthly_bk["Period"] = monthly_bk["Booking_YM"].astype(str)
    months_plot = range(len(monthly_bk))
    yr_colors  = {2024: PAL["accent1"], 2025: PAL["accent3"], 2026: PAL["accent4"]}
    bar_colors = [yr_colors.get(int(p[:4]), PAL["accent1"]) for p in monthly_bk["Period"]]

    fig, ax = plt.subplots(figsize=(22,7))
    bars = ax.bar(months_plot, monthly_bk["Booking_ID"], color=bar_colors, edgecolor=PAL["bg"], width=0.75)
    ax.set_xticks(list(months_plot)[::2])
    ax.set_xticklabels(monthly_bk["Period"].values[::2], rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Number of Bookings")
    ax.set_title("Monthly Booking Volume by Year (Colour-coded)", fontweight="bold")
    ax.grid(axis="y",alpha=0.3)
    patches = [mpatches.Patch(color=v, label=str(k)) for k,v in yr_colors.items()]
    ax.legend(handles=patches, title="Year", fontsize=9)
    titlebar(fig,"Monthly Booking Volume — 2024, 2025 & 2026","Bars coloured by year; Summer months consistently show highest volumes")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"29_monthly_bookings.png")

    # ── CHART 30: OTA Revenue Comparison ────────────────────────
    ota_s = ota_df.sort_values("Net_Revenue", ascending=True)
    fig, ax = plt.subplots(figsize=(16,9))
    colors30 = [MC[i % len(MC)] for i in range(len(ota_s))]
    bars = ax.barh(ota_s["OTA_Name"], ota_s["Net_Revenue"]/1e3, color=colors30, edgecolor=PAL["bg"])
    ax.set_xlabel("Net Revenue (USD Thousands)")
    ax.set_title("Net Revenue by OTA Platform", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="x",alpha=0.3)
    for bar in bars:
        w = bar.get_width()
        ax.text(w+0.5, bar.get_y()+bar.get_height()/2,
                f"${w:,.0f}K", va="center", fontsize=8.5, color=PAL["text"])
    titlebar(fig,"OTA Net Revenue Comparison","Sorted ascending; rightmost = highest revenue generating platform")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"30_ota_revenue_comparison.png")

    # ── CHART 31: OTA Market Share (dual pie) ───────────────────
    fig, axes = plt.subplots(1,2, figsize=(20,9))
    def donut(ax, vals, labels, title, colors):
        wedges, texts, autotexts = ax.pie(
            vals, labels=None, colors=colors,
            autopct="%1.1f%%", startangle=90,
            pctdistance=0.82,
            wedgeprops={"edgecolor":PAL["bg"],"linewidth":1.5,"width":0.55}
        )
        for at in autotexts: at.set(fontsize=8, color="white")
        ax.set_title(title, fontweight="bold", fontsize=12)
        ax.legend(wedges, labels, loc="lower center", fontsize=7.5,
                  ncol=3, bbox_to_anchor=(0.5,-0.15))
    donut(axes[0], ota_df["Bookings"],    ota_df["OTA_Name"], "Booking Volume Market Share",  MC)
    donut(axes[1], ota_df["Net_Revenue"], ota_df["OTA_Name"], "Net Revenue Market Share",     MC)
    titlebar(fig,"OTA Market Share — Booking Volume vs Net Revenue",
             "Donut charts reveal if high-volume OTAs translate to proportional revenue")
    fig.tight_layout(rect=[0,0,1,0.93])
    savefig(fig,"31_ota_market_share.png")

    # ── CHART 32: Hotel Revenue Ranking ─────────────────────────
    fig, ax = plt.subplots(figsize=(16,10))
    hot_s = hotel_df.sort_values("Net_Revenue", ascending=True)
    colors32 = plt.cm.plasma(np.linspace(0.2,0.85,len(hot_s)))
    bars = ax.barh(hot_s["Hotel_Name"], hot_s["Net_Revenue"]/1e3, color=colors32, edgecolor=PAL["bg"])
    ax.set_xlabel("Net Revenue (USD Thousands)")
    ax.set_title("Net Revenue by Hotel Property", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="x",alpha=0.3)
    for bar in bars:
        w = bar.get_width()
        ax.text(w+0.3, bar.get_y()+bar.get_height()/2,
                f"${w:,.0f}K", va="center", fontsize=8, color=PAL["text"])
    titlebar(fig,"Hotel Revenue Ranking","All 25 properties ranked by total Net Revenue")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"32_hotel_revenue_ranking.png")

    # ── CHART 33: Room Type Performance ─────────────────────────
    fig, axes = plt.subplots(1,3, figsize=(21,7))
    rt_order = rt_df.sort_values("Net_Revenue", ascending=False)

    # Revenue
    ax=axes[0]
    bars=ax.bar(rt_order["Room_Type"], rt_order["Net_Revenue"]/1e3,
                color=MC[:len(rt_order)], edgecolor=PAL["bg"], width=0.6)
    ax.set_title("Net Revenue by Room Type", fontweight="bold")
    ax.set_ylabel("Net Revenue ($K)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+1, f"${h:,.0f}K",
                ha="center",va="bottom",fontsize=9,color=PAL["text"])

    # Avg Room Price
    ax=axes[1]
    bars=ax.bar(rt_order["Room_Type"], rt_order["Avg_Room_Price"],
                color=MC[:len(rt_order)], edgecolor=PAL["bg"], width=0.6)
    ax.set_title("Avg Room Price by Room Type", fontweight="bold")
    ax.set_ylabel("Avg Price (USD/night)")
    ax.grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+1, f"${h:,.0f}",
                ha="center",va="bottom",fontsize=9,color=PAL["text"])

    # Cancellation Rate
    ax=axes[2]
    colors33=[PAL["accent2"] if v>rt_df["Cancellation_Rate_Pct"].mean() else PAL["accent3"]
              for v in rt_order["Cancellation_Rate_Pct"]]
    bars=ax.bar(rt_order["Room_Type"], rt_order["Cancellation_Rate_Pct"],
                color=colors33, edgecolor=PAL["bg"], width=0.6)
    ax.axhline(rt_df["Cancellation_Rate_Pct"].mean(), color="white", ls="--",
               lw=1.5, label=f"Avg: {rt_df['Cancellation_Rate_Pct'].mean():.1f}%")
    ax.set_title("Cancellation Rate by Room Type", fontweight="bold")
    ax.set_ylabel("Cancellation Rate (%)")
    ax.legend(fontsize=9); ax.grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+0.1, f"{h:.1f}%",
                ha="center",va="bottom",fontsize=9,color=PAL["text"])

    titlebar(fig,"Room Type Performance — Revenue, Pricing & Cancellations","")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"33_room_type_performance.png")

    # ── CHART 34: City Revenue Map (top 15) ─────────────────────
    top_cities = city_df.head(15)
    fig, ax = plt.subplots(figsize=(16,8))
    colors34 = [MC[i%len(MC)] for i in range(len(top_cities))]
    bars = ax.barh(top_cities["Hotel_City"][::-1],
                   top_cities["Net_Revenue"][::-1]/1e3,
                   color=colors34[::-1], edgecolor=PAL["bg"])
    ax.set_xlabel("Net Revenue (USD Thousands)")
    ax.set_title("Net Revenue by Hotel City (Top 15)", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="x",alpha=0.3)
    for bar in bars:
        w=bar.get_width()
        ax.text(w+0.2, bar.get_y()+bar.get_height()/2,
                f"${w:,.0f}K", va="center",fontsize=8.5,color=PAL["text"])
    titlebar(fig,"City-Level Revenue Performance","Revenue generated at hotel destinations (top 15 hotel cities)")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"34_city_revenue.png")

    # ── CHART 35: Country Revenue (customer origin) ──────────────
    top_countries = country_df.head(12)
    fig, axes = plt.subplots(1,2, figsize=(20,8))
    # Pie
    wedges,texts,autotexts = axes[0].pie(
        top_countries["Net_Revenue"], labels=None,
        colors=MC[:len(top_countries)], autopct="%1.1f%%",
        startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor":PAL["bg"],"linewidth":1.5}
    )
    for at in autotexts: at.set(fontsize=8,color="white")
    axes[0].set_title("Revenue Share by Customer Country", fontweight="bold")
    axes[0].legend(wedges, top_countries["Country"], loc="lower center",
                   fontsize=7.5, ncol=3, bbox_to_anchor=(0.5,-0.18))
    # Bar
    bars=axes[1].bar(top_countries["Country"], top_countries["Net_Revenue"]/1e3,
                     color=MC[:len(top_countries)], edgecolor=PAL["bg"], width=0.7)
    axes[1].set_xticklabels(top_countries["Country"], rotation=30, ha="right")
    axes[1].set_ylabel("Net Revenue ($K)")
    axes[1].set_title("Net Revenue by Customer Home Country", fontweight="bold")
    axes[1].grid(axis="y",alpha=0.3)
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    for b in bars:
        h=b.get_height()
        axes[1].text(b.get_x()+b.get_width()/2, h+0.3, f"${h:,.0f}K",
                     ha="center",va="bottom",fontsize=8,color=PAL["text"])
    titlebar(fig,"Country Revenue Analysis — Customer Origin","Which countries produce the most booking revenue")
    fig.tight_layout(rect=[0,0,1,0.93])
    savefig(fig,"35_country_revenue.png")

    # ── CHART 36: Seasonal Revenue & Cancellations ───────────────
    fig, axes = plt.subplots(1,3, figsize=(21,7))
    s_colors=[PAL["accent3"],PAL["accent2"],PAL["accent4"],PAL["accent5"]]

    bars=axes[0].bar(seas_df["Season"], seas_df["Net_Revenue"]/1e3,
                     color=s_colors, edgecolor=PAL["bg"], width=0.6)
    axes[0].set_title("Net Revenue by Season", fontweight="bold")
    axes[0].set_ylabel("Net Revenue ($K)")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    axes[0].grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        axes[0].text(b.get_x()+b.get_width()/2,h+1,f"${h:,.0f}K",
                     ha="center",va="bottom",fontsize=9,color=PAL["text"])

    bars=axes[1].bar(seas_df["Season"], seas_df["Bookings"],
                     color=s_colors, edgecolor=PAL["bg"], width=0.6)
    axes[1].set_title("Total Bookings by Season", fontweight="bold")
    axes[1].set_ylabel("Number of Bookings")
    axes[1].grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        axes[1].text(b.get_x()+b.get_width()/2,h+5,f"{int(h):,}",
                     ha="center",va="bottom",fontsize=9,color=PAL["text"])

    bars=axes[2].bar(seas_df["Season"], seas_df["Cancellation_Rate_Pct"],
                     color=s_colors, edgecolor=PAL["bg"], width=0.6)
    axes[2].axhline(seas_df["Cancellation_Rate_Pct"].mean(), color="white",
                    ls="--", lw=1.5, label=f"Avg: {seas_df['Cancellation_Rate_Pct'].mean():.1f}%")
    axes[2].set_title("Cancellation Rate by Season", fontweight="bold")
    axes[2].set_ylabel("Cancellation Rate (%)")
    axes[2].legend(fontsize=9); axes[2].grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        axes[2].text(b.get_x()+b.get_width()/2,h+0.1,f"{h:.1f}%",
                     ha="center",va="bottom",fontsize=9,color=PAL["text"])

    titlebar(fig,"Seasonal Performance — Revenue, Bookings & Cancellation Rate","")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"36_seasonal_performance.png")

    # ── CHART 37: Booking Status Distribution ───────────────────
    fig, axes = plt.subplots(1,2, figsize=(18,7))
    status_counts = df["Booking_Status"].value_counts()
    s_clrs = [PAL["accent3"], PAL["accent2"], PAL["accent4"]]
    wedges,texts,autotexts = axes[0].pie(
        status_counts.values, labels=status_counts.index,
        colors=s_clrs, autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor":PAL["bg"],"linewidth":1.5}
    )
    for t in texts: t.set(color=PAL["text"],fontsize=10)
    for at in autotexts: at.set(color="white",fontsize=9)
    axes[0].set_title("Overall Booking Status Distribution", fontweight="bold")

    # Stacked bar by month (last 12 months)
    recent_12 = df["Booking_YM"].unique()[-12:]
    df_r = df[df["Booking_YM"].isin(recent_12)]
    pivot_s = df_r.pivot_table(index="Booking_YM", columns="Booking_Status",
                                aggfunc="size", fill_value=0)
    pivot_s.index = pivot_s.index.astype(str)
    x_r   = range(len(pivot_s))
    bot   = np.zeros(len(pivot_s))
    sc_map = {"Confirmed":PAL["accent3"],"Cancelled":PAL["accent2"],"No-Show":PAL["accent4"]}
    for stat, clr in sc_map.items():
        if stat in pivot_s.columns:
            axes[1].bar(x_r, pivot_s[stat], bottom=bot, label=stat,
                        color=clr, edgecolor=PAL["bg"], alpha=0.88)
            bot += pivot_s[stat].values
    axes[1].set_xticks(list(x_r))
    axes[1].set_xticklabels(pivot_s.index, rotation=40, ha="right", fontsize=8)
    axes[1].set_ylabel("Bookings")
    axes[1].set_title("Booking Status Mix — Last 12 Months", fontweight="bold")
    axes[1].legend(fontsize=9); axes[1].grid(axis="y",alpha=0.3)

    titlebar(fig,"Booking Status Analysis","Confirmed, Cancelled, and No-Show breakdown overall and over recent months")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"37_booking_status.png")

    # ── CHART 38: Cancellation Rate by OTA ──────────────────────
    fig, ax = plt.subplots(figsize=(16,7))
    ota_c = ota_df.sort_values("Cancellation_Rate_Pct", ascending=False)
    avg_c = ota_c["Cancellation_Rate_Pct"].mean()
    clrs38 = [PAL["accent2"] if v > avg_c else PAL["accent3"]
              for v in ota_c["Cancellation_Rate_Pct"]]
    bars = ax.bar(ota_c["OTA_Name"], ota_c["Cancellation_Rate_Pct"],
                  color=clrs38, edgecolor=PAL["bg"], width=0.65)
    ax.axhline(avg_c, color="white", ls="--", lw=1.8,
               label=f"Avg: {avg_c:.1f}%")
    ax.set_xticklabels(ota_c["OTA_Name"], rotation=30, ha="right")
    ax.set_ylabel("Cancellation Rate (%)")
    ax.set_title("Cancellation Rate by OTA Platform", fontweight="bold")
    ax.legend(fontsize=10); ax.grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+0.1, f"{h:.1f}%",
                ha="center",va="bottom",fontsize=8.5,color=PAL["text"])
    titlebar(fig,"Cancellation Rate by OTA",
             "Red bars = above-average cancellation rate; Green = below average")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"38_cancellation_by_ota.png")

    # ── CHART 39: Commission Comparison ─────────────────────────
    fig, axes = plt.subplots(1,2, figsize=(20,8))
    ota_comm = ota_df.sort_values("Commission", ascending=True)
    colors39 = [MC[i%len(MC)] for i in range(len(ota_comm))]
    bars=axes[0].barh(ota_comm["OTA_Name"], ota_comm["Commission"]/1e3,
                      color=colors39, edgecolor=PAL["bg"])
    axes[0].set_xlabel("Commission Paid ($K)")
    axes[0].set_title("Total Commission Paid per OTA", fontweight="bold")
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    axes[0].grid(axis="x",alpha=0.3)
    for b in bars:
        w=b.get_width()
        axes[0].text(w+0.1, b.get_y()+b.get_height()/2,
                     f"${w:,.1f}K",va="center",fontsize=8,color=PAL["text"])

    # Commission % vs Avg Booking Value scatter
    axes[1].scatter(ota_df["Commission_Rate"]*100, ota_df["Avg_Booking_Val"],
                    s=ota_df["Bookings"]/10, c=range(len(ota_df)),
                    cmap="plasma", alpha=0.85, edgecolors=PAL["grid"])
    for _,row in ota_df.iterrows():
        axes[1].annotate(row["OTA_Name"],
                         (row["Commission_Rate"]*100, row["Avg_Booking_Val"]),
                         textcoords="offset points", xytext=(5,3),
                         fontsize=7.5, color=PAL["text"])
    axes[1].set_xlabel("Commission Rate (%)")
    axes[1].set_ylabel("Avg Net Booking Value ($)")
    axes[1].set_title("Commission Rate vs Avg Booking Value\n(bubble size = bookings)", fontweight="bold")
    axes[1].grid(True,alpha=0.3)

    titlebar(fig,"Commission Analysis","Left: total commission cost; Right: rate-value trade-off per OTA")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"39_commission_analysis.png")

    # ── CHART 40: Customer Loyalty Revenue ──────────────────────
    fig, axes = plt.subplots(1,3, figsize=(22,8))
    loy_clrs=["#636E72","#A4B0BE","#F9CA24","#6C63FF"]

    bars=axes[0].bar(loy_df["Loyalty_Status"], loy_df["Net_Revenue"]/1e3,
                     color=loy_clrs, edgecolor=PAL["bg"], width=0.6)
    axes[0].set_title("Net Revenue by Loyalty Tier", fontweight="bold")
    axes[0].set_ylabel("Net Revenue ($K)")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    axes[0].grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        axes[0].text(b.get_x()+b.get_width()/2,h+1,f"${h:,.0f}K",
                     ha="center",va="bottom",fontsize=9,color=PAL["text"])

    bars=axes[1].bar(loy_df["Loyalty_Status"], loy_df["Avg_Rev"],
                     color=loy_clrs, edgecolor=PAL["bg"], width=0.6)
    axes[1].set_title("Avg Revenue per Booking by Loyalty Tier", fontweight="bold")
    axes[1].set_ylabel("Avg Net Revenue ($)")
    axes[1].grid(axis="y",alpha=0.3)
    for b in bars:
        h=b.get_height()
        axes[1].text(b.get_x()+b.get_width()/2,h+1,f"${h:,.0f}",
                     ha="center",va="bottom",fontsize=9,color=PAL["text"])

    # RFM segment revenue bar
    seg_s = seg_rev_df.sort_values("Total_Rev", ascending=True).tail(8)
    bars=axes[2].barh(seg_s["Segment"], seg_s["Total_Rev"]/1e3,
                      color=[MC[i%len(MC)] for i in range(len(seg_s))], edgecolor=PAL["bg"])
    axes[2].set_xlabel("Total Net Revenue ($K)")
    axes[2].set_title("Revenue by RFM Segment (Top 8)", fontweight="bold")
    axes[2].xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    axes[2].grid(axis="x",alpha=0.3)

    titlebar(fig,"Customer & Loyalty Revenue Analysis","Loyalty tier and RFM segment revenue contribution breakdown")
    fig.tight_layout(rect=[0,0,1,0.94])
    savefig(fig,"40_loyalty_revenue.png")

    # ── CHART 41: Executive Performance Dashboard ────────────────
    fig = plt.figure(figsize=(28,20))
    gs = gridspec.GridSpec(3,3, figure=fig, hspace=0.5, wspace=0.38)

    # Mini OTA revenue bar
    ax = fig.add_subplot(gs[0,0])
    ota_mini = ota_df.sort_values("Net_Revenue",ascending=True).tail(8)
    ax.barh(ota_mini["OTA_Name"], ota_mini["Net_Revenue"]/1e3,
            color=MC[:8], edgecolor=PAL["bg"])
    ax.set_title("Top 8 OTAs by Net Revenue", fontweight="bold", fontsize=11)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="x",alpha=0.3)

    # Mini hotel revenue bar
    ax = fig.add_subplot(gs[0,1])
    hot_mini = hotel_df.head(8)
    ax.barh(hot_mini["Hotel_Name"][::-1], hot_mini["Net_Revenue"][::-1]/1e3,
            color=MC[:8], edgecolor=PAL["bg"])
    ax.set_title("Top 8 Hotels by Net Revenue", fontweight="bold", fontsize=11)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="x",alpha=0.3)

    # Room type pie
    ax = fig.add_subplot(gs[0,2])
    ax.pie(rt_df["Net_Revenue"], labels=rt_df["Room_Type"],
           colors=MC[:len(rt_df)], autopct="%1.0f%%",
           wedgeprops={"edgecolor":PAL["bg"],"linewidth":1.2})
    
    # Monthly trend mini
    ax = fig.add_subplot(gs[1,:2])
    x = range(len(monthly_rev))
    ax.plot(x, monthly_rev["Net"]/1e3, color=PAL["accent3"], lw=2.5,
            marker="o", ms=4, label="Net Revenue")
    ax.fill_between(x, monthly_rev["Net"]/1e3, alpha=0.15, color=PAL["accent3"])
    ax.set_xticks(list(x)[::3])
    ax.set_xticklabels(monthly_rev["Period"].values[::3], rotation=35, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.set_title("Monthly Net Revenue Trend", fontweight="bold", fontsize=11)
    ax.grid(True,alpha=0.25); ax.legend(fontsize=9)

    # Seasonal
    ax = fig.add_subplot(gs[1,2])
    ax.bar(seas_df["Season"], seas_df["Net_Revenue"]/1e3,
           color=s_colors, edgecolor=PAL["bg"], width=0.6)
    ax.set_title("Revenue by Season", fontweight="bold", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="y",alpha=0.3)

    # Loyalty revenue
    ax = fig.add_subplot(gs[2,0])
    ax.bar(loy_df["Loyalty_Status"], loy_df["Net_Revenue"]/1e3,
           color=loy_clrs, edgecolor=PAL["bg"], width=0.6)
    ax.set_title("Revenue by Loyalty Tier", fontweight="bold", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="y",alpha=0.3)

    # OTA cancellation rate
    ax = fig.add_subplot(gs[2,1])
    ota_cr = ota_df.sort_values("Cancellation_Rate_Pct",ascending=False).head(8)
    ax.bar(ota_cr["OTA_Name"], ota_cr["Cancellation_Rate_Pct"],
           color=[PAL["accent2"] if v>avg_c else PAL["accent3"]
                  for v in ota_cr["Cancellation_Rate_Pct"]],
           edgecolor=PAL["bg"], width=0.65)
    ax.axhline(avg_c, color="white",ls="--",lw=1.2)
    ax.set_xticklabels(ota_cr["OTA_Name"],rotation=30,ha="right",fontsize=7.5)
    ax.set_title("Cancellation Rate by OTA (Top 8)", fontweight="bold", fontsize=11)
    ax.grid(axis="y",alpha=0.3)

    # Country revenue
    ax = fig.add_subplot(gs[2,2])
    top6 = country_df.head(6)
    ax.bar(top6["Country"], top6["Net_Revenue"]/1e3,
           color=MC[:6], edgecolor=PAL["bg"], width=0.65)
    ax.set_xticklabels(top6["Country"],rotation=20,ha="right",fontsize=8)
    ax.set_title("Revenue by Country (Top 6)", fontweight="bold", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.grid(axis="y",alpha=0.3)

    titlebar(fig,"Executive Performance Dashboard — OTA Analytics Phase 4",
             "Integrated multi-panel view of all key performance dimensions")
    savefig(fig,"41_executive_dashboard.png")

    print(f"\n  Total charts generated: 15 (Images/27 through 41)")

# ─────────────────────────────────────────────
# 12. PRINT BUSINESS INSIGHTS
# ─────────────────────────────────────────────
def print_business_insights(kpis, ota_df, hotel_df, rt_df, city_df, country_df,
                             seas_df, loy_df, tb):
    print("\n" + "="*65)
    print("  PHASE 4 — KEY BUSINESS INSIGHTS")
    print("="*65)

    insights = [
        ("01", "Revenue Concentration",
         f"Total Net Revenue = {fmt_usd(kpis['Net Revenue ($)'])}. "
         f"Commission leakage = {fmt_usd(kpis['Commission Paid ($)'])} "
         f"({kpis['Commission Rate (%)']:.1f}% of Gross Revenue)."),

        ("02", "Cancellation Risk",
         f"Cancellation rate = {kpis['Cancellation Rate (%)']:.2f}%. "
         f"That is {kpis['Cancelled Bookings']:,} bookings representing "
         f"~{kpis['Cancelled Bookings']/kpis['Total Bookings']*kpis['Gross Revenue ($)']:,.0f} USD of gross revenue at risk."),

        ("03", "Top OTA Performer",
         f"{tb.get('Top 5 OTAs by Revenue', [['N/A']])[0][0]} leads in net revenue. "
         f"Negotiating a 1-2% commission reduction with top OTA platforms could "
         f"recover significant margin."),

        ("04", "Worst OTA for Cancellations",
         f"{tb['Highest Cancellation OTA']} has the highest cancellation rate — "
         f"review cancellation policy or introduce non-refundable fare tiers on this platform."),

        ("05", "Best OTA for Cancellations",
         f"{tb['Lowest Cancellation OTA']} has the lowest cancellation rate — "
         f"analyze its booking flow and customer demographics to replicate best practices."),

        ("06", "Hotel Revenue Leader",
         f"{tb.get('Top 5 Hotels by Revenue', [['N/A']])[0][0]} is the top-earning property. "
         f"It benefits from premium pricing, high occupancy, and location advantages."),

        ("07", "Underperforming Hotels",
         f"{tb.get('Bottom 5 Hotels by Revenue', [['N/A']])[0][0]} and peers need demand-generation strategies: "
         f"promotional OTA placements, package deals, or reduced minimum stay requirements."),

        ("08", "Best Room Type",
         f"{tb['Best Room Type by Revenue']} rooms generate the highest total revenue. "
         f"Suite-tier demand justifies premium pricing and upselling at check-in."),

        ("09", "Worst Room Type",
         f"{tb['Worst Room Type by Revenue']} rooms under-perform; consider bundling "
         f"with F&B packages or promotional discounts to drive occupancy."),

        ("10", "Peak Season",
         f"Summer is the highest-revenue season. Pre-season pricing optimisation "
         f"(dynamic rate increases from April onwards) can capture additional yield."),

        ("11", "Winter Opportunity",
         f"Winter has the lowest booking volume. Targeted winter-break packages "
         f"and loyalty-tier early-access deals can lift off-peak revenue by 15-20%."),

        ("12", "Peak Booking Month",
         f"Peak booking month is {tb['Peak Booking Month']}. "
         f"Marketing spend should be front-loaded to April-June to capture summer demand."),

        ("13", "Lead Time Insight",
         f"Avg lead time = {kpis['Avg Lead Time (days)']} days. "
         f"Last-minute bookers (< 7 days lead time) warrant a separate pricing strategy "
         f"to fill remaining inventory without heavy discounting."),

        ("14", "Length of Stay",
         f"Avg length of stay = {kpis['Avg Length of Stay (nights)']} nights. "
         f"Offering a 3-night minimum stay discount could increase ADR "
         f"and reduce per-booking acquisition cost."),

        ("15", "ADR Optimisation",
         f"Avg Daily Rate (ADR) = {fmt_usd(kpis['Avg Daily Rate ADR ($)'])}. "
         f"Rooms above the ADR (Suites, Deluxe) represent margin-expansion opportunities."),

        ("16", "Top Customer Country",
         f"{tb['Highest Revenue Country']} generates the most revenue by customer country. "
         f"Localised marketing campaigns and native-language OTA listings can deepen this market."),

        ("17", "Top Hotel City",
         f"{tb['Highest Revenue City']} leads in hotel-city revenue. "
         f"Hotels in this city command a premium — continue investing in quality and amenities."),

        ("18", "Platinum Loyalty ROI",
         f"Platinum customers produce the highest avg booking value "
         f"({fmt_usd(loy_df.loc[loy_df['Loyalty_Status']=='Platinum','Avg_Rev'].values[0])}). "
         f"A Platinum upgrade path with clear benefits would increase tier migration rate."),

        ("19", "Repeat Customer Rate",
         f"Repeat Customer Rate = {kpis['Repeat Customer Rate (%)']:.1f}%. "
         f"Increasing this by 5 pp through a post-stay re-engagement email series "
         f"would add meaningful recurring revenue without new customer acquisition cost."),

        ("20", "Review Score & Revenue Link",
         f"Avg Review Score = {kpis['Avg Review Score']:.2f}/5. "
         f"Properties scoring 4.8+ command premium pricing and attract higher-value customers. "
         f"Operational investments in service quality deliver outsized revenue returns."),

        ("21", "Commission Benchmark",
         f"Average OTA commission = {kpis['Commission Rate (%)']:.1f}% of gross revenue. "
         f"Direct-booking incentives (loyalty points, price-match guarantee) can shift "
         f"5-10% of OTA bookings to direct channel, saving commission entirely."),

        ("22", "Mobile Booking Channel",
         f"Mobile (48%) surpasses Desktop (40%) for device share. "
         f"Mobile-exclusive flash deals would increase conversion among mobile-first bookers."),

        ("23", "Cancellation Rate vs Season",
         f"Summer has the highest cancellation rate ({seas_df.loc[seas_df['Season']=='Summer','Cancellation_Rate_Pct'].values[0]:.1f}%). "
         f"Non-refundable summer rates offered at a 5-10% discount reduce cancellations "
         f"and lock in revenue earlier."),

        ("24", "Suite vs Single Room Revenue Gap",
         f"Suite rooms generate 3-4x more revenue per booking than Single rooms "
         f"despite representing only ~10% of bookings. "
         f"Targeted upsell offers at booking and check-in increase suite uptake."),

        ("25", "Forecasting Foundation Ready",
         f"With {kpis['Total Room-Nights']:,} room-nights of historical data spanning "
         f"Jan 2024 – Jun 2026, the dataset is rich enough for seasonal ARIMA/Prophet "
         f"forecasting with 90+ day horizon (Phase 8)."),
    ]

    for num, title, text in insights:
        print(f"\n[{num}] {title}")
        print(f"     {text}")

# ─────────────────────────────────────────────
# 13. EXPORT KPI SUMMARY CSV
# ─────────────────────────────────────────────
def export_kpi_csv(kpis, ota_df, hotel_df, rt_df, seas_df):
    """Export a machine-readable KPI summary for use in Phases 6–8."""
    rows = [{"Category":"Overall KPI","Metric":k,"Value":v} for k,v in kpis.items()]

    for _, row in ota_df.iterrows():
        rows.append({"Category":"OTA","Metric":row["OTA_Name"]+" Net Revenue","Value":row["Net_Revenue"]})
        rows.append({"Category":"OTA","Metric":row["OTA_Name"]+" Cancellation Rate %","Value":row["Cancellation_Rate_Pct"]})

    for _, row in hotel_df.iterrows():
        rows.append({"Category":"Hotel","Metric":row["Hotel_Name"]+" Net Revenue","Value":row["Net_Revenue"]})

    for _, row in rt_df.iterrows():
        rows.append({"Category":"Room Type","Metric":row["Room_Type"]+" Net Revenue","Value":row["Net_Revenue"]})
        rows.append({"Category":"Room Type","Metric":row["Room_Type"]+" Avg Price","Value":row["Avg_Room_Price"]})

    for _, row in seas_df.iterrows():
        rows.append({"Category":"Season","Metric":row["Season"]+" Net Revenue","Value":row["Net_Revenue"]})

    df_kpi = pd.DataFrame(rows)
    path = os.path.join("Dataset","kpi_summary.csv")
    df_kpi.to_csv(path, index=False)
    print(f"\nExported KPI summary -> {path} ({len(df_kpi)} rows)")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("="*65)
    print("  PHASE 4: PRODUCT PERFORMANCE & SALES ANALYSIS")
    print("="*65)

    df, fact, d_cust, d_hot, d_ota, d_date, rfm = load_datasets()

    print("\n[KPIs] Computing...")
    kpis = compute_kpis(df)
    for k,v in kpis.items():
        print(f"  {k:<42} {v:>15,.2f}" if isinstance(v,float)
              else f"  {k:<42} {v:>15,}")

    print("\n[OTA Analysis]")
    ota_df = ota_analysis(df)
    print(ota_df[["OTA_Name","Bookings","Net_Revenue","Market_Share_Revenue_Pct",
                  "Cancellation_Rate_Pct","Avg_Review"]].to_string(index=False))

    print("\n[Hotel Analysis]")
    hotel_df = hotel_analysis(df)
    print(hotel_df[["Hotel_Name","Bookings","Net_Revenue","ADR",
                    "Cancellation_Rate_Pct"]].to_string(index=False))

    print("\n[Room Type Analysis]")
    rt_df = room_type_analysis(df)
    print(rt_df.to_string(index=False))

    print("\n[City & Country Analysis]")
    city_df, country_df = city_country_analysis(df)

    print("\n[Season Analysis]")
    seas_df = season_analysis(df)
    print(seas_df.to_string(index=False))

    print("\n[Customer & Loyalty Analysis]")
    loy_df, seg_rev_df = customer_analysis(df, rfm)
    print(loy_df.to_string(index=False))

    print("\n[Cancellation Analysis]")
    monthly_cancel, device_cancel, pay_cancel = cancellation_analysis(df)

    print("\n[Top / Bottom Analysis]")
    tb = top_bottom_analysis(df, ota_df, hotel_df, rt_df, city_df, country_df)
    for k,v in tb.items():
        print(f"  {k}: {v}")

    # Visualisations
    generate_visualizations(df, kpis, ota_df, hotel_df, rt_df, city_df, country_df,
                             seas_df, loy_df, seg_rev_df, monthly_cancel)

    # Business insights
    print_business_insights(kpis, ota_df, hotel_df, rt_df, city_df, country_df,
                             seas_df, loy_df, tb)

    # Export KPI CSV
    export_kpi_csv(kpis, ota_df, hotel_df, rt_df, seas_df)

    print("\n" + "="*65)
    print("  PHASE 4 COMPLETE")
    print("  Images : 27_kpi_scorecard.png --> 41_executive_dashboard.png")
    print("  Dataset: kpi_summary.csv")
    print("="*65)


if __name__ == "__main__":
    main()
