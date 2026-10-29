import os
import json
import pandas as pd

# -----------------------------
# File Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "Dataset",
    "ota_master_dataset.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "Dashboard",
    "data"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "dashboard.json"
)

# -----------------------------
# Load Dataset
# -----------------------------
df = pd.read_csv(DATASET_PATH)

# -----------------------------
# Convert Date Column
# -----------------------------
if "Booking_Date" in df.columns:
    df["Booking_Date"] = pd.to_datetime(
        df["Booking_Date"],
        errors="coerce"
    )

# -----------------------------
# KPI Calculations
# -----------------------------
total_bookings = len(df)

confirmed = (
    df["Booking_Status"] == "Confirmed"
).sum() if "Booking_Status" in df.columns else 0

cancelled = (
    df["Booking_Status"] == "Cancelled"
).sum() if "Booking_Status" in df.columns else 0

cancellation_rate = (
    cancelled / total_bookings * 100
) if total_bookings else 0

gross_revenue = (
    df["Total_Amount"].sum()
    if "Total_Amount" in df.columns
    else 0
)

net_revenue = (
    df["Net_Revenue"].sum()
    if "Net_Revenue" in df.columns
    else gross_revenue
)

commission = (
    df["Commission_Amount"].sum()
    if "Commission_Amount" in df.columns
    else 0
)

adr = (
    df["ADR"].mean()
    if "ADR" in df.columns
    else 0
)

avg_review = (
    df["Review_Score"].mean()
    if "Review_Score" in df.columns
    else 0
)

unique_customers = (
    df["Customer_ID"].nunique()
    if "Customer_ID" in df.columns
    else 0
)

unique_hotels = (
    df["Hotel_Name"].nunique()
    if "Hotel_Name" in df.columns
    else 0
)

# -----------------------------
# Monthly Revenue
# -----------------------------
monthly_labels = []
monthly_values = []

if "Booking_Date" in df.columns:

    temp = df.copy()

    temp["Month"] = temp["Booking_Date"].dt.strftime("%b")

    monthly = (
        temp.groupby("Month")["Net_Revenue"]
        .sum()
        .reset_index()
    )

    monthly_labels = monthly["Month"].tolist()

    monthly_values = (
        monthly["Net_Revenue"]
        .round(2)
        .tolist()
    )

# -----------------------------
# Booking Status
# -----------------------------
status_labels = []
status_values = []

if "Booking_Status" in df.columns:

    status = (
        df["Booking_Status"]
        .value_counts()
    )

    status_labels = status.index.tolist()

    status_values = status.values.tolist()

# -----------------------------
# OTA Revenue
# -----------------------------
ota_labels = []
ota_values = []

if "OTA_Platform" in df.columns:

    ota = (
        df.groupby("OTA_Platform")["Net_Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    ota_labels = ota.index.tolist()

    ota_values = (
        ota.round(2).tolist()
    )

# -----------------------------
# Top Hotels
# -----------------------------
hotel_labels = []
hotel_values = []

if "Hotel_Name" in df.columns:

    hotels = (
        df.groupby("Hotel_Name")["Net_Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    hotel_labels = hotels.index.tolist()

    hotel_values = (
        hotels.round(2).tolist()
    )

# -----------------------------
# Customer Segments
# -----------------------------
segment_labels = []
segment_values = []

if "RFM_Segment" in df.columns:

    seg = (
        df["RFM_Segment"]
        .value_counts()
    )

    segment_labels = seg.index.tolist()

    segment_values = seg.values.tolist()

# -----------------------------
# Dashboard Dictionary
# -----------------------------
dashboard = {

    "kpis":{

        "total_bookings":int(total_bookings),

        "confirmed":int(confirmed),

        "cancelled":int(cancelled),

        "cancellation_rate":round(cancellation_rate,2),

        "gross_revenue":round(float(gross_revenue),2),

        "net_revenue":round(float(net_revenue),2),

        "commission":round(float(commission),2),

        "adr":round(float(adr),2),

        "review_score":round(float(avg_review),2),

        "customers":int(unique_customers),

        "hotels":int(unique_hotels)

    },

    "monthly_revenue":{

        "labels":monthly_labels,

        "values":monthly_values

    },

    "booking_status":{

        "labels":status_labels,

        "values":status_values

    },

    "ota_revenue":{

        "labels":ota_labels,

        "values":ota_values

    },

    "top_hotels":{

        "labels":hotel_labels,

        "values":hotel_values

    },

    "customer_segments":{

        "labels":segment_labels,

        "values":segment_values

    }

}

# -----------------------------
# Save JSON
# -----------------------------
with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        dashboard,
        f,
        indent=4
    )

print("="*50)
print("Dashboard JSON Created Successfully")
print(OUTPUT_FILE)
print("="*50)