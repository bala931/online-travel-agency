"""
Phase 8: Sales Forecasting
OTA Performance & Channel Management Project
============================================================
Inputs  : Dataset/ota_master_dataset.csv
Outputs : Dataset/forecast_results.csv
          Images/60_*.png – 65_*.png
          Reports/Phase_8_Forecast_Report.md
============================================================
Forecast chain (auto-detect & fallback):
  1. Prophet (if installed)
  2. ARIMA via statsmodels
  3. Holt-Winters Exponential Smoothing (always available)
Forecast horizon: 90 days
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
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
FORECAST_DAYS = 90
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
# 1. LOAD & PREPARE TIME SERIES
# ─────────────────────────────────────────────
def load_data():
    path = os.path.join("Dataset", "ota_master_dataset.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Master dataset not found: {path}")
    df = pd.read_csv(path, parse_dates=["Booking_Date"])
    df["Net_Revenue"] = pd.to_numeric(df["Net_Revenue"], errors="coerce")
    log.info(f"Master dataset loaded: {df.shape}")
    return df


def prepare_daily_series(df):
    """Aggregate to daily net revenue, fill missing dates."""
    daily = df.groupby("Booking_Date")["Net_Revenue"].sum().reset_index()
    daily = daily.rename(columns={"Booking_Date": "ds", "Net_Revenue": "y"})
    daily["ds"] = pd.to_datetime(daily["ds"])
    daily = daily.sort_values("ds")

    # Fill any missing dates
    full_idx = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    daily = daily.set_index("ds").reindex(full_idx).fillna(0).reset_index()
    daily.columns = ["ds", "y"]
    log.info(f"Daily series: {len(daily)} days | "
             f"{daily['ds'].min().date()} → {daily['ds'].max().date()}")
    return daily


# ─────────────────────────────────────────────
# 2. FORECASTING MODELS (with fallback chain)
# ─────────────────────────────────────────────
def forecast_prophet(daily, horizon=FORECAST_DAYS):
    try:
        from prophet import Prophet
        log.info("  Using Prophet for forecasting...")
        m = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            interval_width=0.95,
            changepoint_prior_scale=0.05,
        )
        m.fit(daily.rename(columns={"ds":"ds","y":"y"}))
        future = m.make_future_dataframe(periods=horizon, freq="D")
        fc = m.predict(future)
        fc = fc[["ds","yhat","yhat_lower","yhat_upper"]].copy()
        fc.columns = ["ds","forecast","lower_ci","upper_ci"]
        fc["model"] = "Prophet"
        return fc, m, "Prophet"
    except ImportError:
        log.warning("  Prophet not installed — trying ARIMA...")
        return None, None, None


def forecast_arima(daily, horizon=FORECAST_DAYS):
    try:
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        log.info("  Using ARIMA for forecasting...")
        y = daily["y"].values
        # Use a simple auto-fit: try ARIMA(2,1,2)
        model = ARIMA(y, order=(2, 1, 2))
        result = model.fit()
        fc_vals = result.forecast(steps=horizon)
        conf = result.get_forecast(steps=horizon).conf_int(alpha=0.05)

        last_date = daily["ds"].max()
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        all_dates = pd.concat([daily["ds"], pd.Series(future_dates)], ignore_index=True)
        all_fitted = np.concatenate([result.fittedvalues, fc_vals])
        lower = np.concatenate([result.fittedvalues, conf.iloc[:,0].values])
        upper = np.concatenate([result.fittedvalues, conf.iloc[:,1].values])

        fc = pd.DataFrame({
            "ds": all_dates,
            "forecast": all_fitted,
            "lower_ci": lower,
            "upper_ci": upper,
            "model": "ARIMA",
        })
        return fc, result, "ARIMA"
    except Exception as e:
        log.warning(f"  ARIMA failed ({e}) — using Exponential Smoothing...")
        return None, None, None


def forecast_ets(daily, horizon=FORECAST_DAYS):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    log.info("  Using Holt-Winters Exponential Smoothing...")
    y = daily["y"].values
    # Seasonal period = 7 days
    seasonal_periods = 7 if len(y) >= 2 * 7 else None
    model = ExponentialSmoothing(
        y,
        trend="add",
        seasonal="add" if seasonal_periods else None,
        seasonal_periods=seasonal_periods,
        initialization_method="estimated",
    )
    result = model.fit(optimized=True)
    fc_vals = result.forecast(horizon)

    # Approximate CI with ±1.96 * residual std
    resid_std = np.std(result.resid)
    last_date = daily["ds"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
    all_dates = pd.concat([daily["ds"], pd.Series(future_dates)], ignore_index=True)
    all_fitted = np.concatenate([result.fittedvalues, fc_vals])

    lower = all_fitted - 1.96 * resid_std
    upper = all_fitted + 1.96 * resid_std

    fc = pd.DataFrame({
        "ds": all_dates,
        "forecast": all_fitted,
        "lower_ci": lower,
        "upper_ci": upper,
        "model": "ETS",
    })
    return fc, result, "Holt-Winters ETS"


def run_forecast(daily):
    """Try Prophet → ARIMA → ETS."""
    fc, model, name = forecast_prophet(daily)
    if fc is None:
        fc, model, name = forecast_arima(daily)
    if fc is None:
        fc, model, name = forecast_ets(daily)
    log.info(f"  Forecast model used: {name}")
    return fc, model, name


# ─────────────────────────────────────────────
# 3. EVALUATION METRICS
# ─────────────────────────────────────────────
def compute_metrics(daily, fc):
    actual = daily["y"].values
    # Align fitted (in-sample portion of fc)
    fc_in = fc[fc["ds"].isin(daily["ds"])].copy()
    fc_in = fc_in.sort_values("ds")
    min_len = min(len(actual), len(fc_in))
    y_true = actual[:min_len]
    y_pred = fc_in["forecast"].values[:min_len]

    mae  = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.any() else np.nan
    r2   = 1 - np.sum((y_true - y_pred)**2) / np.sum((y_true - np.mean(y_true))**2)

    metrics = {"MAE": round(mae, 2), "RMSE": round(rmse, 2),
               "MAPE_Pct": round(mape, 2) if not np.isnan(mape) else None,
               "R2_Score": round(r2, 4)}
    log.info(f"  Metrics: MAE={metrics['MAE']:.2f}, RMSE={metrics['RMSE']:.2f}, "
             f"MAPE={metrics['MAPE_Pct']}%, R²={metrics['R2_Score']}")
    return metrics


# ─────────────────────────────────────────────
# 4. EXPORT CSV
# ─────────────────────────────────────────────
def export_forecast(daily, fc):
    os.makedirs("Dataset", exist_ok=True)
    # Mark which rows are historical vs forecast
    fc2 = fc.copy()
    fc2["is_forecast"] = ~fc2["ds"].isin(daily["ds"])
    fc2["ds"] = fc2["ds"].astype(str)
    path = os.path.join("Dataset", "forecast_results.csv")
    fc2.to_csv(path, index=False)
    log.info(f"  Exported -> {path} ({len(fc2)} rows)")


# ─────────────────────────────────────────────
# 5. VISUALISATIONS (Charts 60–65)
# ─────────────────────────────────────────────
def generate_forecast_charts(daily, fc, metrics, model_name):
    log.info("\nGenerating forecast charts...")

    # Split: historical vs forecast
    fc["ds"] = pd.to_datetime(fc["ds"])
    daily_cutoff = daily["ds"].max()
    fc_hist = fc[fc["ds"] <= daily_cutoff]
    fc_future = fc[fc["ds"] > daily_cutoff]

    # ── CHART 60: Main Forecast Plot ─────────────────────────────
    fig, ax = plt.subplots(figsize=(22, 8))
    ax.plot(daily["ds"], daily["y"] / 1e3, color=PAL["sub"], lw=1.5,
            alpha=0.7, label="Actual Daily Revenue")
    # 7-day rolling for clarity
    daily_roll = daily["y"].rolling(7, min_periods=1).mean()
    ax.plot(daily["ds"], daily_roll / 1e3, color=PAL["accent1"], lw=2.5,
            label="7-day Rolling Avg")
    ax.plot(fc_future["ds"], fc_future["forecast"] / 1e3, color=PAL["accent3"],
            lw=2.5, linestyle="--", marker="o", ms=3, label=f"{model_name} Forecast")
    ax.fill_between(fc_future["ds"],
                    fc_future["lower_ci"] / 1e3,
                    fc_future["upper_ci"] / 1e3,
                    alpha=0.25, color=PAL["accent3"], label="95% CI")
    ax.axvline(daily_cutoff, color=PAL["accent2"], lw=1.5, linestyle=":",
               label="Forecast Start")
    ax.set_ylabel("Daily Net Revenue (USD Thousands)")
    ax.set_title(f"90-Day Revenue Forecast — {model_name}", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    titlebar(fig, f"Sales Forecast: {FORECAST_DAYS}-Day Revenue Outlook",
             f"Model: {model_name} | Shaded region = 95% confidence interval")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "60_forecast_main.png")

    # ── CHART 61: Residuals Plot ──────────────────────────────────
    fc_in = fc[fc["ds"].isin(daily["ds"])].copy().sort_values("ds")
    min_len = min(len(daily), len(fc_in))
    residuals = daily["y"].values[:min_len] - fc_in["forecast"].values[:min_len]

    fig, axes = plt.subplots(2, 1, figsize=(22, 10), sharex=False)
    axes[0].plot(daily["ds"][:min_len], residuals / 1e3, color=PAL["accent2"],
                 lw=1.2, alpha=0.8)
    axes[0].axhline(0, color=PAL["sub"], lw=1.5, linestyle="--")
    axes[0].fill_between(daily["ds"][:min_len], residuals / 1e3, 0,
                         alpha=0.2, color=PAL["accent2"])
    axes[0].set_ylabel("Residual (USD Thousands)")
    axes[0].set_title("Residuals Over Time (Actual − Fitted)", fontweight="bold")
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(residuals / 1e3, bins=40, color=PAL["accent1"],
                 edgecolor=PAL["bg"], alpha=0.85)
    axes[1].axvline(0, color=PAL["accent2"], lw=2, linestyle="--", label="Zero")
    mu, sigma = residuals.mean() / 1e3, residuals.std() / 1e3
    axes[1].set_xlabel("Residual (USD Thousands)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title(f"Residual Distribution  (μ={mu:.1f}K, σ={sigma:.1f}K)",
                      fontweight="bold")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)

    titlebar(fig, "Forecast Residual Analysis",
             "TOP: residuals over time | BOTTOM: residual distribution")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "61_forecast_residuals.png")

    # ── CHART 62: Error Metrics Bar ───────────────────────────────
    m_labels = [k for k in metrics if metrics[k] is not None]
    m_vals   = [metrics[k] for k in m_labels]
    fig, ax = plt.subplots(figsize=(12, 6))
    colors62 = [MC[i % len(MC)] for i in range(len(m_labels))]
    bars = ax.bar(m_labels, m_vals, color=colors62, edgecolor=PAL["bg"], width=0.5)
    ax.set_title("Model Error Metrics", fontweight="bold")
    ax.set_ylabel("Metric Value")
    ax.grid(axis="y", alpha=0.3)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + max(m_vals)*0.01,
                f"{h:,.2f}", ha="center", va="bottom", fontsize=10,
                fontweight="bold", color=PAL["text"])
    titlebar(fig, "Forecast Model Evaluation Metrics",
             f"Model: {model_name} | MAE · RMSE · MAPE · R²")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "62_forecast_metrics.png")

    # ── CHART 63: Weekly Revenue Pattern (seasonality) ───────────
    df_dow = daily.copy()
    df_dow["DOW"] = df_dow["ds"].dt.day_name()
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow_avg = df_dow.groupby("DOW")["y"].mean().reindex(day_order)

    fig, ax = plt.subplots(figsize=(14, 6))
    colors63 = [MC[i % len(MC)] for i in range(7)]
    bars = ax.bar(dow_avg.index, dow_avg.values / 1e3, color=colors63, edgecolor=PAL["bg"])
    ax.set_ylabel("Avg Daily Revenue (USD Thousands)")
    ax.set_title("Weekly Seasonality Pattern", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.1f}K"))
    ax.grid(axis="y", alpha=0.3)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + max(dow_avg.values/1e3)*0.01,
                f"${h:.1f}K", ha="center", va="bottom", fontsize=9, color=PAL["text"])
    titlebar(fig, "Weekly Booking Revenue Seasonality",
             "Average daily net revenue by day of week")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "63_weekly_seasonality.png")

    # ── CHART 64: Monthly Revenue with Forecast Extension ────────
    # Aggregate actual monthly + forecast monthly
    fc_fut_m = fc_future.copy()
    fc_fut_m["Month"] = fc_fut_m["ds"].dt.to_period("M").astype(str)
    fc_monthly = fc_fut_m.groupby("Month")["forecast"].sum().reset_index()
    fc_monthly.columns = ["Month","Revenue"]
    fc_monthly["Type"] = "Forecast"

    hist_m = daily.copy()
    hist_m["Month"] = hist_m["ds"].dt.to_period("M").astype(str)
    hist_monthly = hist_m.groupby("Month")["y"].sum().reset_index()
    hist_monthly.columns = ["Month","Revenue"]
    hist_monthly["Type"] = "Actual"

    combined_m = pd.concat([hist_monthly, fc_monthly], ignore_index=True).sort_values("Month")
    fig, ax = plt.subplots(figsize=(22, 7))
    colors64 = [PAL["accent1"] if t=="Actual" else PAL["accent3"] for t in combined_m["Type"]]
    bars = ax.bar(combined_m["Month"], combined_m["Revenue"]/1e3,
                  color=colors64, edgecolor=PAL["bg"], alpha=0.85)
    ax.set_ylabel("Net Revenue (USD Thousands)")
    ax.set_title("Monthly Revenue — Actual + Forecast Extension", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.tick_params(axis="x", rotation=40)
    ax.grid(axis="y", alpha=0.3)
    legend_patches = [
        mpatches.Patch(color=PAL["accent1"], label="Actual"),
        mpatches.Patch(color=PAL["accent3"], label="Forecasted"),
    ]
    ax.legend(handles=legend_patches, fontsize=10)
    titlebar(fig, "Monthly Revenue — Actual vs Forecasted",
             "Blue = historical bookings | Green = 90-day model forecast")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "64_monthly_actual_vs_forecast.png")

    # ── CHART 65: Actual vs Fitted (scatter) ─────────────────────
    fig, ax = plt.subplots(figsize=(12, 10))
    y_true = daily["y"].values[:min_len]
    y_pred = fc_in["forecast"].values[:min_len]
    ax.scatter(y_true/1e3, y_pred/1e3, alpha=0.35, color=PAL["accent1"],
               edgecolors=PAL["bg"], s=30)
    lim = max(y_true.max(), y_pred.max()) / 1e3
    ax.plot([0, lim], [0, lim], color=PAL["accent2"], lw=2, linestyle="--",
            label="Perfect Fit (y = x)")
    ax.set_xlabel("Actual Daily Revenue (USD Thousands)")
    ax.set_ylabel("Fitted/Forecast Daily Revenue (USD Thousands)")
    ax.set_title("Actual vs Fitted Revenue", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v:,.0f}K"))
    titlebar(fig, "Actual vs Fitted Revenue (In-Sample)",
             f"R² = {metrics['R2_Score']} | Points on diagonal = perfect prediction")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savefig(fig, "65_actual_vs_fitted.png")

    log.info("  Total charts generated: 6 (Images/60 through 65)")


# ─────────────────────────────────────────────
# 6. MARKDOWN REPORT
# ─────────────────────────────────────────────
def generate_report(daily, fc, metrics, model_name):
    os.makedirs("Reports", exist_ok=True)
    future_fc = fc[fc["ds"] > daily["ds"].max()].copy()
    fc_revenue = future_fc["forecast"].clip(lower=0).sum()
    fc_avg_daily = future_fc["forecast"].clip(lower=0).mean()

    lines = [
        "# Phase 8 — Sales Forecasting Report",
        "",
        "**Project**: OTA Performance & Channel Management",
        "**Phase**: 8 — Sales Forecasting",
        "**Script**: `Python/sales_forecast.py`",
        "",
        "---",
        "",
        "## Model Summary",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Forecasting Model | {model_name} |",
        f"| Forecast Horizon | {FORECAST_DAYS} days |",
        f"| Training Period Start | {daily['ds'].min().date()} |",
        f"| Training Period End | {daily['ds'].max().date()} |",
        f"| Forecast Start | {(daily['ds'].max() + pd.Timedelta(days=1)).date()} |",
        f"| Forecast End | {(daily['ds'].max() + pd.Timedelta(days=FORECAST_DAYS)).date()} |",
        "",
        "---",
        "",
        "## Forecast Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Forecasted Total Revenue (90 days) | ${fc_revenue:,.2f} |",
        f"| Forecasted Avg Daily Revenue | ${fc_avg_daily:,.2f} |",
        f"| Historical Avg Daily Revenue | ${daily['y'].mean():,.2f} |",
        "",
        "---",
        "",
        "## Model Evaluation Metrics (In-Sample)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| MAE (Mean Absolute Error) | ${metrics['MAE']:,.2f} |",
        f"| RMSE (Root Mean Squared Error) | ${metrics['RMSE']:,.2f} |",
        f"| MAPE (Mean Absolute % Error) | {metrics['MAPE_Pct']}% |",
        f"| R² Score | {metrics['R2_Score']} |",
        "",
        "---",
        "",
        "## Output Files",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `Dataset/forecast_results.csv` | Daily forecast + CI + is_forecast flag |",
        "| `Images/60_forecast_main.png` | Main 90-day forecast chart with CI band |",
        "| `Images/61_forecast_residuals.png` | Residuals over time + distribution |",
        "| `Images/62_forecast_metrics.png` | Error metric comparison bar chart |",
        "| `Images/63_weekly_seasonality.png` | Weekly day-of-week revenue pattern |",
        "| `Images/64_monthly_actual_vs_forecast.png` | Monthly actual + forecast bar |",
        "| `Images/65_actual_vs_fitted.png` | Actual vs fitted scatter plot |",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Seasonal Peaks**: Align staffing and inventory with forecasted high-demand periods.",
        "2. **Dynamic Pricing**: Use forecast confidence intervals to set dynamic pricing floors/ceilings.",
        "3. **Marketing Spend**: Increase digital marketing during predicted revenue troughs.",
        "4. **Model Refresh**: Retrain the forecast model monthly as new booking data arrives.",
        "5. **OTA Allocation**: Shift inventory toward higher-converting OTAs during peak forecast windows.",
    ]

    path = os.path.join("Reports", "Phase_8_Forecast_Report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"Report saved -> {path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  PHASE 8: SALES FORECASTING")
    print("=" * 65)

    try:
        df = load_data()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    log.info("\nPreparing daily time series...")
    daily = prepare_daily_series(df)

    log.info("\nRunning forecast model chain...")
    fc, model, model_name = run_forecast(daily)

    log.info("\nComputing evaluation metrics...")
    metrics = compute_metrics(daily, fc)

    log.info("\nExporting forecast CSV...")
    export_forecast(daily, fc)

    generate_forecast_charts(daily, fc, metrics, model_name)
    generate_report(daily, fc, metrics, model_name)

    print("\n" + "=" * 65)
    print("  PHASE 8 COMPLETE")
    print(f"  Model:   {model_name}")
    print(f"  MAE: ${metrics['MAE']:,.2f} | RMSE: ${metrics['RMSE']:,.2f} | R²: {metrics['R2_Score']}")
    print("  Dataset: Dataset/forecast_results.csv")
    print("  Charts:  Images/60 through 65")
    print("  Report:  Reports/Phase_8_Forecast_Report.md")
    print("=" * 65)


if __name__ == "__main__":
    main()
