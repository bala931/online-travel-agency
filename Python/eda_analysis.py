"""
Phase 2: Exploratory Data Analysis (EDA)
OTA Performance & Channel Management Project
============================================================
Covers:
  - Summary Statistics
  - Missing Value Analysis
  - Data Distribution & KDE
  - Univariate Analysis
  - Bivariate Analysis
  - Correlation Heatmap
  - Outlier Detection (Box Plots + IQR)
  - Multivariate Analysis
  - Trend Analysis
All charts are saved to the Images/ folder.
"""
import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file saving
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from scipy import stats

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# GLOBAL STYLE CONFIGURATION
# ─────────────────────────────────────────────
PALETTE = {
    "bg": "#0F1117",
    "card": "#1A1D2E",
    "accent1": "#6C63FF",
    "accent2": "#FF6584",
    "accent3": "#43E97B",
    "accent4": "#F7971E",
    "accent5": "#00C9FF",
    "text": "#E8EAF6",
    "subtext": "#9FA8DA",
    "grid": "#2C2F4A",
}

MULTI_COLORS = [
    "#6C63FF", "#FF6584", "#43E97B", "#F7971E", "#00C9FF",
    "#FF8C69", "#A29BFE", "#55EFC4", "#FD79A8", "#FDCB6E",
    "#74B9FF", "#E17055", "#81ECEC", "#DFE6E9", "#636E72"
]

def apply_dark_style():
    """Apply consistent dark theme to all matplotlib figures."""
    plt.rcParams.update({
        "figure.facecolor": PALETTE["bg"],
        "axes.facecolor": PALETTE["card"],
        "axes.edgecolor": PALETTE["grid"],
        "axes.labelcolor": PALETTE["text"],
        "axes.titlecolor": PALETTE["text"],
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.color": PALETTE["subtext"],
        "ytick.color": PALETTE["subtext"],
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "grid.color": PALETTE["grid"],
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
        "legend.facecolor": PALETTE["card"],
        "legend.edgecolor": PALETTE["grid"],
        "legend.labelcolor": PALETTE["text"],
        "text.color": PALETTE["text"],
        "font.family": "DejaVu Sans",
        "figure.dpi": 150,
    })

apply_dark_style()

def save_fig(fig, filename):
    """Save figure to Images/ directory."""
    os.makedirs("Images", exist_ok=True)
    path = os.path.join("Images", filename)
    fig.savefig(path, bbox_inches="tight", facecolor=PALETTE["bg"])
    plt.close(fig)
    print(f"  Saved: {path}")

def add_title_bar(fig, title, subtitle=""):
    """Add a styled title bar at the top of a figure."""
    fig.text(0.5, 0.98, title, ha="center", va="top",
             fontsize=18, fontweight="bold", color=PALETTE["text"])
    if subtitle:
        fig.text(0.5, 0.955, subtitle, ha="center", va="top",
                 fontsize=11, color=PALETTE["subtext"])

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
def load_data():
    path = os.path.join("Dataset", "ota_master_dataset.csv")
    df = pd.read_csv(path, parse_dates=["Booking_Date", "Checkin_Date", "Checkout_Date"])
    df["Booking_YM"] = df["Booking_Date"].dt.to_period("M")
    df["Booking_Month"] = df["Booking_Date"].dt.month
    df["Booking_Year"] = df["Booking_Date"].dt.year
    df["Booking_MonthName"] = df["Booking_Date"].dt.strftime("%b %Y")
    return df

# ─────────────────────────────────────────────
# 1. SUMMARY STATISTICS
# ─────────────────────────────────────────────
def summary_statistics(df):
    print("\n[1] Summary Statistics")

    numeric_cols = [
        "Age", "Lead_Time", "Room_Price", "Number_of_Rooms", "Guests",
        "Adults", "Children", "Nights", "Commission_Rate", "Commission_Amount",
        "Discount", "Taxes", "Gross_Revenue", "Net_Revenue", "Review_Score"
    ]

    stats_df = df[numeric_cols].describe().T.round(2)
    stats_df["skewness"] = df[numeric_cols].skew().round(3)
    stats_df["kurtosis"] = df[numeric_cols].kurt().round(3)
    stats_df["median"] = df[numeric_cols].median().round(2)

    print(stats_df.to_string())

    # ── Visualise as a styled heatmap table ──
    fig, ax = plt.subplots(figsize=(20, 8))
    ax.set_visible(False)

    table_cols = ["count", "mean", "std", "min", "25%", "50%", "75%", "max", "median", "skewness"]
    data_vals = stats_df[table_cols].values

    col_labels = ["Count", "Mean", "Std Dev", "Min", "Q1", "Median\n(50%)", "Q3", "Max", "Median", "Skewness"]
    row_labels = stats_df.index.tolist()

    ax2 = fig.add_axes([0.02, 0.05, 0.96, 0.82])
    ax2.set_facecolor(PALETTE["bg"])
    ax2.set_visible(True)
    ax2.axis("off")

    tbl = ax2.table(
        cellText=data_vals,
        rowLabels=row_labels,
        colLabels=col_labels,
        cellLoc="center",
        loc="center"
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.6)

    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor(PALETTE["grid"])
        if row == 0:
            cell.set_facecolor(PALETTE["accent1"])
            cell.set_text_props(color="white", fontweight="bold")
        elif col == -1:
            cell.set_facecolor(PALETTE["card"])
            cell.set_text_props(color=PALETTE["accent5"], fontweight="bold")
        else:
            cell.set_facecolor(PALETTE["card"])
            cell.set_text_props(color=PALETTE["text"])

    add_title_bar(fig, "Summary Statistics — Numeric Columns",
                  "Descriptive statistics including mean, std, quartiles, skewness")
    save_fig(fig, "01_summary_statistics.png")
    return stats_df

# ─────────────────────────────────────────────
# 2. MISSING VALUE ANALYSIS
# ─────────────────────────────────────────────
def missing_value_analysis(df):
    print("\n[2] Missing Value Analysis")
    miss = df.isnull().sum()
    miss_pct = (miss / len(df) * 100).round(2)
    miss_df = pd.DataFrame({"Missing Count": miss, "Missing %": miss_pct})
    miss_df = miss_df[miss_df["Missing Count"] > 0].sort_values("Missing %", ascending=False)

    if miss_df.empty:
        print("  No missing values found in master dataset (ETL cleaned them).")
        # Create an info chart
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "✓  No Missing Values Detected\n\nAll columns are fully populated\nafter ETL cleaning.",
                ha="center", va="center", fontsize=20,
                color=PALETTE["accent3"], fontweight="bold",
                transform=ax.transAxes)
        ax.set_axis_off()
        add_title_bar(fig, "Missing Value Analysis", "Post-ETL master dataset — all nulls resolved")
        save_fig(fig, "02_missing_values.png")
    else:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        # Bar chart
        axes[0].barh(miss_df.index, miss_df["Missing %"],
                     color=PALETTE["accent2"], edgecolor=PALETTE["grid"])
        axes[0].set_xlabel("Missing %")
        axes[0].set_title("Columns with Missing Values (%)")
        axes[0].grid(axis="x", alpha=0.4)

        # Heatmap style
        presence = df[miss_df.index].isnull().astype(int)
        axes[1].imshow(presence.T, aspect="auto", cmap="RdYlGn_r", interpolation="nearest")
        axes[1].set_yticks(range(len(miss_df.index)))
        axes[1].set_yticklabels(miss_df.index, fontsize=8)
        axes[1].set_title("Missing Value Heatmap (Row-Level)")
        axes[1].set_xlabel("Row Index")

        add_title_bar(fig, "Missing Value Analysis")
        save_fig(fig, "02_missing_values.png")

# ─────────────────────────────────────────────
# 3. UNIVARIATE — NUMERIC DISTRIBUTIONS
# ─────────────────────────────────────────────
def univariate_numeric(df):
    print("\n[3] Univariate — Numeric Distributions")
    cols = ["Age", "Lead_Time", "Room_Price", "Nights",
            "Gross_Revenue", "Net_Revenue", "Commission_Amount", "Review_Score"]

    fig, axes = plt.subplots(2, 4, figsize=(22, 10))
    axes = axes.flatten()

    for i, col in enumerate(cols):
        ax = axes[i]
        data = df[col].dropna()
        n, bins, patches = ax.hist(data, bins=40, color=MULTI_COLORS[i],
                                   edgecolor=PALETTE["bg"], alpha=0.85, density=True)
        # KDE overlay
        kde_x = np.linspace(data.min(), data.max(), 300)
        kde = stats.gaussian_kde(data)
        ax.plot(kde_x, kde(kde_x), color="white", lw=2, linestyle="--")

        # Mean & Median lines
        ax.axvline(data.mean(), color=PALETTE["accent2"], lw=1.5, linestyle="-", label=f"Mean: {data.mean():.1f}")
        ax.axvline(data.median(), color=PALETTE["accent3"], lw=1.5, linestyle=":", label=f"Median: {data.median():.1f}")

        ax.set_title(col.replace("_", " "), fontweight="bold", pad=8)
        ax.set_xlabel("Value")
        ax.set_ylabel("Density")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    add_title_bar(fig, "Univariate Analysis — Numeric Distributions",
                  "Histogram + KDE overlays with Mean (red) and Median (green) markers")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "03_univariate_numeric.png")

# ─────────────────────────────────────────────
# 4. UNIVARIATE — CATEGORICAL DISTRIBUTIONS
# ─────────────────────────────────────────────
def univariate_categorical(df):
    print("\n[4] Univariate — Categorical Distributions")
    cat_cols = ["OTA_Name", "Booking_Status", "Room_Type", "Season",
                "Weekday_Weekend", "Payment_Method", "Loyalty_Status", "Gender", "Device_Type"]

    fig = plt.figure(figsize=(26, 20))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.4)

    for i, col in enumerate(cat_cols):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        counts = df[col].value_counts()
        colors = [MULTI_COLORS[j % len(MULTI_COLORS)] for j in range(len(counts))]
        bars = ax.bar(range(len(counts)), counts.values, color=colors,
                      edgecolor=PALETTE["bg"], width=0.7)
        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels(counts.index, rotation=35, ha="right", fontsize=8)
        ax.set_title(col.replace("_", " "), fontweight="bold", pad=6)
        ax.set_ylabel("Count")
        ax.grid(axis="y", alpha=0.35)
        # Value labels on bars
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + counts.max() * 0.01,
                    f"{int(h):,}", ha="center", va="bottom", fontsize=7,
                    color=PALETTE["subtext"])

    add_title_bar(fig, "Univariate Analysis — Categorical Variables",
                  "Distribution of bookings across key categorical dimensions")
    save_fig(fig, "04_univariate_categorical.png")

# ─────────────────────────────────────────────
# 5. BIVARIATE — REVENUE BY KEY DIMENSIONS
# ─────────────────────────────────────────────
def bivariate_revenue(df):
    print("\n[5] Bivariate — Revenue Analysis")
    fig = plt.figure(figsize=(24, 20))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.55, wspace=0.35)

    # 5a: Net Revenue by OTA
    ax1 = fig.add_subplot(gs[0, :])
    ota_rev = df.groupby("OTA_Name")["Net_Revenue"].sum().sort_values(ascending=True)
    colors_h = [MULTI_COLORS[i % len(MULTI_COLORS)] for i in range(len(ota_rev))]
    bars = ax1.barh(ota_rev.index, ota_rev.values / 1e6, color=colors_h, edgecolor=PALETTE["bg"])
    ax1.set_xlabel("Net Revenue (USD Million)")
    ax1.set_title("Total Net Revenue by OTA Platform", fontweight="bold", fontsize=13)
    ax1.grid(axis="x", alpha=0.35)
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 0.01, bar.get_y() + bar.get_height() / 2,
                 f"${w:.2f}M", va="center", fontsize=8.5, color=PALETTE["text"])

    # 5b: Net Revenue by Room Type
    ax2 = fig.add_subplot(gs[1, 0])
    room_rev = df.groupby("Room_Type")["Net_Revenue"].sum().sort_values(ascending=False)
    wedge_colors = MULTI_COLORS[:len(room_rev)]
    wedges, texts, autotexts = ax2.pie(
        room_rev.values, labels=room_rev.index,
        colors=wedge_colors, autopct="%1.1f%%", startangle=140,
        wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 1.5}
    )
    for t in texts:
        t.set_color(PALETTE["text"])
        t.set_fontsize(9)
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(8)
    ax2.set_title("Net Revenue Share by Room Type", fontweight="bold")

    # 5c: Net Revenue by Season
    ax3 = fig.add_subplot(gs[1, 1])
    season_order = ["Spring", "Summer", "Autumn", "Winter"]
    season_rev = df.groupby("Season")["Net_Revenue"].sum().reindex(season_order)
    s_colors = [PALETTE["accent3"], PALETTE["accent2"], PALETTE["accent4"], PALETTE["accent5"]]
    bars3 = ax3.bar(season_rev.index, season_rev.values / 1e6, color=s_colors,
                    edgecolor=PALETTE["bg"], width=0.6)
    ax3.set_title("Net Revenue by Season", fontweight="bold")
    ax3.set_ylabel("Net Revenue (USD Million)")
    ax3.grid(axis="y", alpha=0.35)
    for bar in bars3:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                 f"${h:.2f}M", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    # 5d: Avg Net Revenue by Loyalty Status
    ax4 = fig.add_subplot(gs[2, 0])
    loyalty_order = ["Standard", "Silver", "Gold", "Platinum"]
    loy_avg = df.groupby("Loyalty_Status")["Net_Revenue"].mean().reindex(loyalty_order)
    loy_colors = ["#636E72", "#A4B0BE", "#F9CA24", "#6C63FF"]
    bars4 = ax4.bar(loy_avg.index, loy_avg.values, color=loy_colors,
                    edgecolor=PALETTE["bg"], width=0.6)
    ax4.set_title("Avg Net Revenue by Loyalty Status", fontweight="bold")
    ax4.set_ylabel("Avg Net Revenue (USD)")
    ax4.grid(axis="y", alpha=0.35)
    for bar in bars4:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width() / 2, h + 2,
                 f"${h:,.0f}", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    # 5e: Avg Net Revenue by Device Type
    ax5 = fig.add_subplot(gs[2, 1])
    dev_avg = df.groupby("Device_Type")["Net_Revenue"].mean().sort_values(ascending=False)
    d_colors = MULTI_COLORS[:len(dev_avg)]
    bars5 = ax5.bar(dev_avg.index, dev_avg.values, color=d_colors,
                    edgecolor=PALETTE["bg"], width=0.6)
    ax5.set_title("Avg Net Revenue by Device Type", fontweight="bold")
    ax5.set_ylabel("Avg Net Revenue (USD)")
    ax5.grid(axis="y", alpha=0.35)
    for bar in bars5:
        h = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width() / 2, h + 2,
                 f"${h:,.0f}", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    add_title_bar(fig, "Bivariate Analysis — Revenue by Key Dimensions",
                  "OTA, Room Type, Season, Loyalty Status and Device Type revenue breakdown")
    save_fig(fig, "05_bivariate_revenue.png")

# ─────────────────────────────────────────────
# 6. BIVARIATE — BOOKINGS & CANCELLATIONS
# ─────────────────────────────────────────────
def bivariate_bookings_cancellations(df):
    print("\n[6] Bivariate — Bookings & Cancellations")
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))

    # 6a: Booking Status Distribution per OTA
    ax1 = axes[0, 0]
    pivot = df.groupby(["OTA_Name", "Booking_Status"]).size().unstack(fill_value=0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    bottom = np.zeros(len(pivot_pct))
    status_colors = {"Confirmed": PALETTE["accent3"], "Cancelled": PALETTE["accent2"], "No-Show": PALETTE["accent4"]}
    for status in pivot_pct.columns:
        ax1.barh(pivot_pct.index, pivot_pct[status], left=bottom,
                 label=status, color=status_colors.get(status, PALETTE["accent1"]),
                 edgecolor=PALETTE["bg"])
        bottom += pivot_pct[status].values
    ax1.set_xlabel("Percentage (%)")
    ax1.set_title("Booking Status Mix by OTA (%)", fontweight="bold")
    ax1.legend(loc="lower right", fontsize=9)
    ax1.grid(axis="x", alpha=0.35)

    # 6b: Cancellation Rate by Room Type
    ax2 = axes[0, 1]
    cancel_by_room = (
        df.groupby("Room_Type")["Booking_Status"]
        .apply(lambda x: (x == "Cancelled").sum() / len(x) * 100)
        .sort_values(ascending=False)
    )
    bars = ax2.bar(cancel_by_room.index, cancel_by_room.values,
                   color=MULTI_COLORS[:len(cancel_by_room)], edgecolor=PALETTE["bg"], width=0.6)
    ax2.set_ylabel("Cancellation Rate (%)")
    ax2.set_title("Cancellation Rate by Room Type", fontweight="bold")
    ax2.grid(axis="y", alpha=0.35)
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.1,
                 f"{h:.1f}%", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    # 6c: Lead Time vs Booking Status (Box Plot)
    ax3 = axes[1, 0]
    statuses = ["Confirmed", "Cancelled", "No-Show"]
    lead_data = [df[df["Booking_Status"] == s]["Lead_Time"].dropna().values for s in statuses]
    bp = ax3.boxplot(lead_data, labels=statuses, patch_artist=True, notch=False,
                     medianprops={"color": "white", "lw": 2})
    box_colors = [PALETTE["accent3"], PALETTE["accent2"], PALETTE["accent4"]]
    for patch, color in zip(bp["boxes"], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
    for element in ["whiskers", "caps", "fliers"]:
        for item in bp[element]:
            item.set_color(PALETTE["subtext"])
    ax3.set_ylabel("Lead Time (Days)")
    ax3.set_title("Lead Time Distribution by Booking Status", fontweight="bold")
    ax3.grid(axis="y", alpha=0.35)

    # 6d: Cancellation Rate by Season
    ax4 = axes[1, 1]
    season_order = ["Spring", "Summer", "Autumn", "Winter"]
    cancel_season = (
        df.groupby("Season")["Booking_Status"]
        .apply(lambda x: (x == "Cancelled").sum() / len(x) * 100)
        .reindex(season_order)
    )
    s_colors = [PALETTE["accent3"], PALETTE["accent2"], PALETTE["accent4"], PALETTE["accent5"]]
    bars4 = ax4.bar(cancel_season.index, cancel_season.values, color=s_colors,
                    edgecolor=PALETTE["bg"], width=0.6)
    ax4.set_ylabel("Cancellation Rate (%)")
    ax4.set_title("Cancellation Rate by Season", fontweight="bold")
    ax4.grid(axis="y", alpha=0.35)
    for bar in bars4:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                 f"{h:.1f}%", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    add_title_bar(fig, "Bivariate Analysis — Bookings & Cancellations",
                  "Booking status patterns across OTA, room type, lead time, and season")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "06_bivariate_bookings.png")

# ─────────────────────────────────────────────
# 7. CORRELATION HEATMAP
# ─────────────────────────────────────────────
def correlation_heatmap(df):
    print("\n[7] Correlation Heatmap")
    numeric_cols = [
        "Age", "Lead_Time", "Room_Price", "Number_of_Rooms", "Guests",
        "Nights", "Commission_Amount", "Discount", "Taxes",
        "Gross_Revenue", "Net_Revenue", "Review_Score"
    ]
    corr = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(14, 11))
    n = len(numeric_cols)
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    labels = [c.replace("_", "\n") for c in numeric_cols]
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = corr.values[i, j]
            color = "white" if abs(val) > 0.5 else PALETTE["text"]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8.5, color=color, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Pearson Correlation", color=PALETTE["text"])
    cbar.ax.yaxis.set_tick_params(color=PALETTE["text"])
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE["text"])

    add_title_bar(fig, "Correlation Heatmap — Numeric Variables",
                  "Pearson correlation between all key numeric columns")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "07_correlation_heatmap.png")

# ─────────────────────────────────────────────
# 8. OUTLIER DETECTION (BOX PLOTS + IQR)
# ─────────────────────────────────────────────
def outlier_detection(df):
    print("\n[8] Outlier Detection — Box Plots + IQR")
    cols = ["Room_Price", "Lead_Time", "Net_Revenue", "Gross_Revenue",
            "Commission_Amount", "Nights", "Taxes", "Age"]

    fig, axes = plt.subplots(2, 4, figsize=(22, 10))
    axes = axes.flatten()

    outlier_summary = {}
    for i, col in enumerate(cols):
        ax = axes[i]
        data = df[col].dropna()

        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        n_outliers = ((data < lower) | (data > upper)).sum()
        outlier_summary[col] = {"Q1": Q1, "Q3": Q3, "IQR": IQR,
                                 "Lower Fence": lower, "Upper Fence": upper,
                                 "Outliers": n_outliers}

        bp = ax.boxplot(data, patch_artist=True, vert=True, notch=False,
                        medianprops={"color": "white", "lw": 2.5})
        bp["boxes"][0].set_facecolor(MULTI_COLORS[i])
        bp["boxes"][0].set_alpha(0.8)
        for item in bp["whiskers"] + bp["caps"]:
            item.set_color(PALETTE["subtext"])
        for flier in bp["fliers"]:
            flier.set(marker="o", color=PALETTE["accent2"], alpha=0.5, markersize=3)

        ax.set_title(col.replace("_", " "), fontweight="bold", pad=8)
        ax.set_ylabel("Value")
        ax.set_xticks([])
        ax.grid(axis="y", alpha=0.35)
        ax.text(0.97, 0.97, f"Outliers: {n_outliers}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=9, color=PALETTE["accent2"],
                bbox={"facecolor": PALETTE["card"], "alpha": 0.7, "edgecolor": PALETTE["accent2"], "boxstyle": "round,pad=0.3"})

    add_title_bar(fig, "Outlier Detection — Box Plots (IQR Method)",
                  "Each box shows Q1–Q3 range; dots beyond fences are outliers")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "08_outlier_boxplots.png")

    # Print IQR table
    out_df = pd.DataFrame(outlier_summary).T
    print(out_df.to_string())
    return outlier_summary

# ─────────────────────────────────────────────
# 9. MULTIVARIATE — GROUPED ANALYSIS
# ─────────────────────────────────────────────
def multivariate_analysis(df):
    print("\n[9] Multivariate Analysis")
    fig = plt.figure(figsize=(24, 18))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    # 9a: Net Revenue by OTA x Room Type (Heatmap)
    ax1 = fig.add_subplot(gs[0, :])
    pivot = df.pivot_table(values="Net_Revenue", index="OTA_Name",
                           columns="Room_Type", aggfunc="sum", fill_value=0)
    pivot_m = pivot / 1e3  # in thousands
    im = ax1.imshow(pivot_m.values, cmap="YlOrRd", aspect="auto")
    ax1.set_xticks(range(len(pivot_m.columns)))
    ax1.set_yticks(range(len(pivot_m.index)))
    ax1.set_xticklabels(pivot_m.columns, fontsize=10, fontweight="bold")
    ax1.set_yticklabels(pivot_m.index, fontsize=9)
    ax1.set_title("Net Revenue (in $000s) — OTA vs Room Type Heatmap", fontweight="bold", fontsize=12)
    for i in range(pivot_m.shape[0]):
        for j in range(pivot_m.shape[1]):
            ax1.text(j, i, f"${pivot_m.values[i, j]:,.0f}K",
                     ha="center", va="center", fontsize=8,
                     color="black" if pivot_m.values[i, j] > pivot_m.values.max() * 0.6 else "white")
    fig.colorbar(im, ax=ax1, fraction=0.015, pad=0.02).set_label("Revenue ($000s)", color=PALETTE["text"])

    # 9b: Avg Review Score by OTA x Loyalty Status (Heatmap)
    ax2 = fig.add_subplot(gs[1, 0])
    loyalty_order = ["Standard", "Silver", "Gold", "Platinum"]
    pivot2 = df.pivot_table(values="Review_Score", index="OTA_Name",
                            columns="Loyalty_Status", aggfunc="mean")[loyalty_order]
    im2 = ax2.imshow(pivot2.values, cmap="RdYlGn", aspect="auto", vmin=1, vmax=5)
    ax2.set_xticks(range(len(pivot2.columns)))
    ax2.set_yticks(range(len(pivot2.index)))
    ax2.set_xticklabels(pivot2.columns, fontsize=9)
    ax2.set_yticklabels(pivot2.index, fontsize=8)
    ax2.set_title("Avg Review Score by OTA × Loyalty Status", fontweight="bold")
    for i in range(pivot2.shape[0]):
        for j in range(pivot2.shape[1]):
            ax2.text(j, i, f"{pivot2.values[i, j]:.2f}",
                     ha="center", va="center", fontsize=8.5,
                     color="black" if pivot2.values[i, j] > 3.5 else "white")
    fig.colorbar(im2, ax=ax2, fraction=0.04, pad=0.02)

    # 9c: Gross Revenue vs Room Price (Scatter coloured by Season)
    ax3 = fig.add_subplot(gs[1, 1])
    season_colors_map = {"Spring": PALETTE["accent3"], "Summer": PALETTE["accent2"],
                         "Autumn": PALETTE["accent4"], "Winter": PALETTE["accent5"]}
    for season, grp in df.groupby("Season"):
        ax3.scatter(grp["Room_Price"], grp["Gross_Revenue"],
                    c=season_colors_map.get(season, PALETTE["accent1"]),
                    alpha=0.35, s=12, label=season, rasterized=True)
    ax3.set_xlabel("Room Price (USD)")
    ax3.set_ylabel("Gross Revenue (USD)")
    ax3.set_title("Room Price vs Gross Revenue (by Season)", fontweight="bold")
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    add_title_bar(fig, "Multivariate Analysis",
                  "Revenue heatmaps and cross-dimensional relationships")
    save_fig(fig, "09_multivariate.png")

# ─────────────────────────────────────────────
# 10. TREND ANALYSIS — MONTHLY BOOKINGS & REVENUE
# ─────────────────────────────────────────────
def trend_analysis(df):
    print("\n[10] Trend Analysis — Monthly Bookings & Revenue")
    # Monthly aggregation
    monthly = df.groupby("Booking_YM").agg(
        Bookings=("Booking_ID", "count"),
        Gross_Revenue=("Gross_Revenue", "sum"),
        Net_Revenue=("Net_Revenue", "sum"),
        Cancellations=("Booking_Status", lambda x: (x == "Cancelled").sum())
    ).reset_index()
    monthly["Cancellation_Rate"] = (monthly["Cancellations"] / monthly["Bookings"] * 100).round(2)
    monthly["Period"] = monthly["Booking_YM"].astype(str)

    fig, axes = plt.subplots(3, 1, figsize=(22, 18))

    # 10a: Monthly Bookings with Cancellations overlay
    ax1 = axes[0]
    x = range(len(monthly))
    ax1.fill_between(x, monthly["Bookings"], alpha=0.25, color=PALETTE["accent1"])
    ax1.plot(x, monthly["Bookings"], color=PALETTE["accent1"], lw=2.5,
             marker="o", markersize=5, label="Total Bookings")
    ax1.fill_between(x, monthly["Cancellations"], alpha=0.3, color=PALETTE["accent2"])
    ax1.plot(x, monthly["Cancellations"], color=PALETTE["accent2"], lw=2,
             marker="s", markersize=4, linestyle="--", label="Cancellations")

    ax1.set_xticks(x[::2])
    ax1.set_xticklabels(monthly["Period"].values[::2], rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("Number of Bookings")
    ax1.set_title("Monthly Booking Volume vs Cancellations", fontweight="bold", fontsize=13)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Annotate peak months
    peak_idx = monthly["Bookings"].idxmax()
    ax1.annotate(f"Peak: {monthly.loc[peak_idx, 'Period']}",
                 xy=(peak_idx, monthly.loc[peak_idx, "Bookings"]),
                 xytext=(peak_idx + 1, monthly.loc[peak_idx, "Bookings"] + 5),
                 arrowprops={"arrowstyle": "->", "color": PALETTE["accent3"]},
                 fontsize=9, color=PALETTE["accent3"])

    # 10b: Monthly Gross & Net Revenue
    ax2 = axes[1]
    ax2.fill_between(x, monthly["Gross_Revenue"] / 1e3, alpha=0.2, color=PALETTE["accent3"])
    ax2.plot(x, monthly["Gross_Revenue"] / 1e3, color=PALETTE["accent3"], lw=2.5,
             marker="o", markersize=5, label="Gross Revenue ($K)")
    ax2.fill_between(x, monthly["Net_Revenue"] / 1e3, alpha=0.2, color=PALETTE["accent5"])
    ax2.plot(x, monthly["Net_Revenue"] / 1e3, color=PALETTE["accent5"], lw=2.5,
             marker="s", markersize=4, linestyle="--", label="Net Revenue ($K)")

    ax2.set_xticks(x[::2])
    ax2.set_xticklabels(monthly["Period"].values[::2], rotation=45, ha="right", fontsize=8)
    ax2.set_ylabel("Revenue (USD Thousands)")
    ax2.set_title("Monthly Gross vs Net Revenue Trend", fontweight="bold", fontsize=13)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}K"))

    # 10c: Monthly Cancellation Rate (%)
    ax3 = axes[2]
    ax3.fill_between(x, monthly["Cancellation_Rate"], alpha=0.25, color=PALETTE["accent4"])
    ax3.plot(x, monthly["Cancellation_Rate"], color=PALETTE["accent4"], lw=2.5,
             marker="D", markersize=5, label="Cancellation Rate %")
    # Rolling 3-month average
    rolling_avg = monthly["Cancellation_Rate"].rolling(3, center=True).mean()
    ax3.plot(x, rolling_avg, color="white", lw=1.5, linestyle=":", label="3-Month Rolling Avg")

    ax3.axhline(monthly["Cancellation_Rate"].mean(), color=PALETTE["accent2"],
                linestyle="--", lw=1.5, alpha=0.8,
                label=f"Overall Avg: {monthly['Cancellation_Rate'].mean():.1f}%")
    ax3.set_xticks(x[::2])
    ax3.set_xticklabels(monthly["Period"].values[::2], rotation=45, ha="right", fontsize=8)
    ax3.set_ylabel("Cancellation Rate (%)")
    ax3.set_title("Monthly Cancellation Rate with 3-Month Rolling Average", fontweight="bold", fontsize=13)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    add_title_bar(fig, "Trend Analysis — Monthly Booking, Revenue & Cancellation",
                  "Time-series patterns from January 2024 to June 2026")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save_fig(fig, "10_trend_analysis.png")

    return monthly

# ─────────────────────────────────────────────
# 11. TREND — TOP HOTELS & COUNTRIES
# ─────────────────────────────────────────────
def hotel_country_analysis(df):
    print("\n[11] Hotel & Country Analysis")
    fig, axes = plt.subplots(1, 2, figsize=(22, 9))

    # Top 10 Hotels by Total Net Revenue
    ax1 = axes[0]
    hotel_rev = df.groupby("Hotel_Name")["Net_Revenue"].sum().sort_values(ascending=True).tail(10)
    bars = ax1.barh(hotel_rev.index, hotel_rev.values / 1e6,
                    color=MULTI_COLORS[:10], edgecolor=PALETTE["bg"])
    ax1.set_xlabel("Net Revenue (USD Million)")
    ax1.set_title("Top 10 Hotels by Net Revenue", fontweight="bold", fontsize=13)
    ax1.grid(axis="x", alpha=0.35)
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 0.005, bar.get_y() + bar.get_height() / 2,
                 f"${w:.2f}M", va="center", fontsize=9, color=PALETTE["text"])

    # Top Countries by Booking Volume
    ax2 = axes[1]
    country_count = df["Country"].value_counts().head(12)
    bars2 = ax2.bar(range(len(country_count)), country_count.values,
                    color=MULTI_COLORS[:12], edgecolor=PALETTE["bg"], width=0.7)
    ax2.set_xticks(range(len(country_count)))
    ax2.set_xticklabels(country_count.index, rotation=35, ha="right", fontsize=9)
    ax2.set_ylabel("Total Bookings")
    ax2.set_title("Top Countries by Booking Volume", fontweight="bold", fontsize=13)
    ax2.grid(axis="y", alpha=0.35)
    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 3,
                 f"{int(h):,}", ha="center", va="bottom", fontsize=8.5, color=PALETTE["text"])

    add_title_bar(fig, "Hotel & Country Performance Overview",
                  "Revenue leaders and booking origin distribution")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "11_hotel_country.png")

# ─────────────────────────────────────────────
# 12. PAYMENT & COUPON ANALYSIS
# ─────────────────────────────────────────────
def payment_coupon_analysis(df):
    print("\n[12] Payment & Coupon Analysis")
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    # Payment Method distribution (pie)
    ax1 = axes[0]
    pay = df["Payment_Method"].value_counts()
    wedges, texts, autotexts = ax1.pie(
        pay.values, labels=pay.index,
        colors=MULTI_COLORS[:len(pay)], autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 1.5}
    )
    for t in texts:
        t.set_color(PALETTE["text"])
        t.set_fontsize(9)
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(8)
    ax1.set_title("Payment Method Share", fontweight="bold")

    # Avg Net Revenue by Payment Method
    ax2 = axes[1]
    pay_rev = df.groupby("Payment_Method")["Net_Revenue"].mean().sort_values(ascending=False)
    bars = ax2.bar(pay_rev.index, pay_rev.values, color=MULTI_COLORS[:len(pay_rev)],
                   edgecolor=PALETTE["bg"], width=0.6)
    ax2.set_xticklabels(pay_rev.index, rotation=25, ha="right", fontsize=9)
    ax2.set_ylabel("Avg Net Revenue (USD)")
    ax2.set_title("Avg Net Revenue by Payment Method", fontweight="bold")
    ax2.grid(axis="y", alpha=0.35)
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 1,
                 f"${h:,.0f}", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    add_title_bar(fig, "Payment Method & Revenue Analysis",
                  "Booking share and revenue performance by payment channel")
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    save_fig(fig, "12_payment_coupon.png")

# ─────────────────────────────────────────────
# 13. YEAR-OVER-YEAR COMPARISON
# ─────────────────────────────────────────────
def yoy_comparison(df):
    print("\n[13] Year-over-Year Comparison")
    yoy = df.groupby(["Booking_Year", "Booking_Month"]).agg(
        Bookings=("Booking_ID", "count"),
        Net_Revenue=("Net_Revenue", "sum")
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(22, 8))
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    yr_colors = {2024: PALETTE["accent1"], 2025: PALETTE["accent3"], 2026: PALETTE["accent4"]}

    for ax, metric, label in zip(axes,
                                  ["Bookings", "Net_Revenue"],
                                  ["Bookings Volume", "Net Revenue (USD)"]):
        for yr, grp in yoy.groupby("Booking_Year"):
            grp = grp.sort_values("Booking_Month")
            ax.plot(grp["Booking_Month"], grp[metric] / (1000 if metric == "Net_Revenue" else 1),
                    color=yr_colors.get(yr, PALETTE["accent5"]),
                    marker="o", markersize=6, lw=2.5, label=str(yr))
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(month_names, fontsize=9)
        ax.set_ylabel(label)
        ax.set_title(f"Year-over-Year: Monthly {label}", fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)
        if metric == "Net_Revenue":
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}K"))

    add_title_bar(fig, "Year-over-Year Comparison — 2024, 2025 & 2026",
                  "Monthly bookings and revenue compared across years")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "13_yoy_comparison.png")

# ─────────────────────────────────────────────
# 14. REVIEW SCORE ANALYSIS
# ─────────────────────────────────────────────
def review_score_analysis(df):
    print("\n[14] Review Score Analysis")
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))

    # 14a: Distribution
    ax1 = axes[0]
    counts = df["Review_Score"].value_counts().sort_index()
    stars = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
    colors_r = ["#E17055", "#FDCB6E", "#F7971E", "#81ECEC", "#55EFC4"]
    bars = ax1.bar(counts.index, counts.values, color=colors_r,
                   edgecolor=PALETTE["bg"], width=0.7)
    ax1.set_xticks(counts.index)
    ax1.set_xticklabels([f"{int(s)} ★" for s in counts.index], fontsize=10)
    ax1.set_ylabel("Count")
    ax1.set_title("Review Score Distribution", fontweight="bold")
    ax1.grid(axis="y", alpha=0.35)
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, h + 5,
                 f"{int(h):,}", ha="center", va="bottom", fontsize=9, color=PALETTE["text"])

    # 14b: Avg Review Score by OTA
    ax2 = axes[1]
    ota_rev = df.groupby("OTA_Name")["Review_Score"].mean().sort_values(ascending=True)
    colors2 = [PALETTE["accent3"] if v >= ota_rev.mean() else PALETTE["accent2"] for v in ota_rev.values]
    bars2 = ax2.barh(ota_rev.index, ota_rev.values, color=colors2, edgecolor=PALETTE["bg"])
    ax2.axvline(ota_rev.mean(), color="white", lw=1.5, linestyle="--",
                label=f"Avg: {ota_rev.mean():.2f}")
    ax2.set_xlabel("Avg Review Score")
    ax2.set_title("Avg Review Score by OTA", fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.set_xlim(1, 5)
    ax2.grid(axis="x", alpha=0.35)

    # 14c: Avg Review Score by Hotel Rating band
    ax3 = axes[2]
    df["Hotel_Rating_Band"] = pd.cut(df["Hotel_Rating"],
                                      bins=[4.0, 4.4, 4.6, 4.8, 5.1],
                                      labels=["4.0–4.4", "4.4–4.6", "4.6–4.8", "4.8–5.0"])
    band_scores = df.groupby("Hotel_Rating_Band", observed=True)["Review_Score"].mean()
    bars3 = ax3.bar(band_scores.index.astype(str), band_scores.values,
                    color=MULTI_COLORS[:4], edgecolor=PALETTE["bg"], width=0.6)
    ax3.set_xlabel("Hotel Rating Band")
    ax3.set_ylabel("Avg Review Score")
    ax3.set_title("Review Score by Hotel Rating Band", fontweight="bold")
    ax3.grid(axis="y", alpha=0.35)
    for bar in bars3:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                 f"{h:.2f}", ha="center", va="bottom", fontsize=10, color=PALETTE["text"])

    add_title_bar(fig, "Review Score Analysis",
                  "Distribution and cross-dimensional review performance")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, "14_review_score_analysis.png")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  PHASE 2: EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 60)

    df = load_data()
    print(f"Master dataset loaded: {df.shape[0]} rows x {df.shape[1]} columns")

    stats_df = summary_statistics(df)
    missing_value_analysis(df)
    univariate_numeric(df)
    univariate_categorical(df)
    bivariate_revenue(df)
    bivariate_bookings_cancellations(df)
    correlation_heatmap(df)
    outlier_summary = outlier_detection(df)
    multivariate_analysis(df)
    monthly_trends = trend_analysis(df)
    hotel_country_analysis(df)
    payment_coupon_analysis(df)
    yoy_comparison(df)
    review_score_analysis(df)

    print("\n" + "=" * 60)
    print("  EDA COMPLETE — All charts saved to Images/")
    print("=" * 60)

    # Print key business metrics summary
    print("\n--- KEY METRICS SUMMARY ---")
    print(f"Total Bookings         : {len(df):,}")
    print(f"Unique Customers       : {df['Customer_ID'].nunique():,}")
    print(f"Confirmed Bookings     : {(df['Booking_Status']=='Confirmed').sum():,}")
    print(f"Cancelled Bookings     : {(df['Booking_Status']=='Cancelled').sum():,}")
    print(f"Cancellation Rate      : {(df['Booking_Status']=='Cancelled').mean()*100:.2f}%")
    print(f"Total Gross Revenue    : ${df['Gross_Revenue'].sum():,.2f}")
    print(f"Total Net Revenue      : ${df['Net_Revenue'].sum():,.2f}")
    print(f"Total Commission Paid  : ${df['Commission_Amount'].sum():,.2f}")
    print(f"Avg Booking Value (Net): ${df['Net_Revenue'].mean():,.2f}")
    print(f"Avg Room Price         : ${df['Room_Price'].mean():,.2f}")
    print(f"Avg Lead Time (days)   : {df['Lead_Time'].mean():.1f}")
    print(f"Avg Stay Duration      : {df['Nights'].mean():.2f} nights")
    print(f"Avg Review Score       : {df['Review_Score'].mean():.2f} / 5.0")
    print(f"Top OTA (by Revenue)   : {df.groupby('OTA_Name')['Net_Revenue'].sum().idxmax()}")
    print(f"Top Hotel (by Revenue) : {df.groupby('Hotel_Name')['Net_Revenue'].sum().idxmax()}")
    print(f"Best Season (Revenue)  : {df.groupby('Season')['Net_Revenue'].sum().idxmax()}")
    print(f"Peak Booking Month     : {monthly_trends.loc[monthly_trends['Bookings'].idxmax(), 'Period']}")


if __name__ == "__main__":
    main()
