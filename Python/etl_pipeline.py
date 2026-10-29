import os
import pandas as pd
import numpy as np
import datetime
# Define helper functions for date parsing
def parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "" or str(date_str).lower() == "nan":
        return pd.NaT
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return pd.to_datetime(date_str, format=fmt).date()
        except (ValueError, TypeError):
            continue
    try:
        # Fallback to pandas auto-parsing
        return pd.to_datetime(date_str).date()
    except Exception:
        return pd.NaT
def clean_room_price(price_val):
    if pd.isna(price_val):
        return np.nan
    price_str = str(price_val).replace("$", "").replace(",", "").strip()
    try:
        return float(price_str)
    except ValueError:
        return np.nan

def clean_gender(gender_val):
    if pd.isna(gender_val):
        return "Unknown"
    val = str(gender_val).strip().lower()
    if val in ["m", "male"]:
        return "Male"
    elif val in ["f", "female"]:
        return "Female"
    elif val in ["non-binary", "nb"]:
        return "Non-binary"
    else:
        return "Unknown"

def clean_loyalty(loy_val):
    if pd.isna(loy_val):
        return "Standard"
    val = str(loy_val).strip().capitalize()
    if val in ["Standard", "Silver", "Gold", "Platinum"]:
        return val
    return "Standard"

def main():
    raw_file = os.path.join("Dataset", "ota_raw_dataset.csv")
    if not os.path.exists(raw_file):
        print(f"Error: Raw dataset file {raw_file} not found!")
        return

    print("Loading raw dataset...")
    df = pd.read_csv(raw_file)
    print(f"Initial shape: {df.shape}")

    # 1. Deduplicate by Booking_ID (keeping the first occurrence)
    df.drop_duplicates(subset=["Booking_ID"], keep="first", inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"After deduplication shape: {df.shape} (Expected: 5900)")

    # 2. Clean Room_Price format (string to float)
    df["Room_Price"] = df["Room_Price"].apply(clean_room_price)

    # 3. Parse and standardize dates
    for date_col in ["Booking_Date", "Checkin_Date", "Checkout_Date", "Cancellation_Date"]:
        df[date_col] = df[date_col].apply(parse_date)

    # 4. Standardize text and categorical fields
    df["Gender"] = df["Gender"].apply(clean_gender)
    df["Loyalty_Status"] = df["Loyalty_Status"].apply(clean_loyalty)
    
    # Impute missing Ages
    median_age = df.loc[(df["Age"] >= 18) & (df["Age"] <= 85), "Age"].median()
    if pd.isna(median_age):
        median_age = 45
    df["Age"] = df["Age"].fillna(median_age).astype(int)
    # Fix outlier Ages
    df.loc[(df["Age"] < 18) | (df["Age"] > 85), "Age"] = int(median_age)

    # Impute missing and outlier review scores
    # Outlier review scores are outside [1, 5]
    df.loc[(df["Review_Score"] < 1) | (df["Review_Score"] > 5), "Review_Score"] = np.nan
    # Impute with hotel median rating or overall median
    overall_median_review = df["Review_Score"].median()
    if pd.isna(overall_median_review):
        overall_median_review = 4.0
    
    hotel_review_medians = df.groupby("Hotel_ID")["Review_Score"].transform("median")
    df["Review_Score"] = df["Review_Score"].fillna(hotel_review_medians).fillna(overall_median_review)
    df["Review_Score"] = df["Review_Score"].round(1)

    # Clean outlier lead times (replace negative or > 365 with checkin_date - booking_date)
    # If both dates are clean, compute difference. If not, impute.
    median_lead = df.loc[(df["Lead_Time"] >= 0) & (df["Lead_Time"] <= 365), "Lead_Time"].median()
    if pd.isna(median_lead):
        median_lead = 30
    df.loc[(df["Lead_Time"] < 0) | (df["Lead_Time"] > 365), "Lead_Time"] = np.nan
    
    # Fix logical violations between Booking_Date and Checkin_Date
    # If Checkin_Date < Booking_Date, reset Checkin_Date
    for i, row in df.iterrows():
        b_dt = row["Booking_Date"]
        c_dt = row["Checkin_Date"]
        co_dt = row["Checkout_Date"]
        
        # Ensure booking date is valid
        if pd.isna(b_dt):
            df.at[i, "Booking_Date"] = datetime.date(2024, 1, 1)
            b_dt = datetime.date(2024, 1, 1)
            
        # Standardize check-in date
        if pd.isna(c_dt) or c_dt < b_dt:
            lead = row["Lead_Time"]
            if pd.isna(lead) or lead < 0:
                lead = median_lead
            c_dt = b_dt + datetime.timedelta(days=int(lead))
            df.at[i, "Checkin_Date"] = c_dt
            
        # Standardize check-out date
        if pd.isna(co_dt) or co_dt <= c_dt:
            nights = row["Nights"]
            if pd.isna(nights) or nights <= 0:
                nights = 1
            co_dt = c_dt + datetime.timedelta(days=int(nights))
            df.at[i, "Checkout_Date"] = co_dt
            
        # Update lead time and nights based on dates
        df.at[i, "Lead_Time"] = int((c_dt - b_dt).days)
        df.at[i, "Nights"] = int((co_dt - c_dt).days)

    df["Lead_Time"] = df["Lead_Time"].astype(int)
    df["Nights"] = df["Nights"].astype(int)

    # Impute and clean Room_Price outliers
    # For room prices <= 0 or > 5000, impute based on Hotel and Room Type
    df.loc[(df["Room_Price"] <= 0) | (df["Room_Price"] > 5000), "Room_Price"] = np.nan
    hotel_type_price = df.groupby(["Hotel_ID", "Room_Type"])["Room_Price"].transform("median")
    type_price = df.groupby("Room_Type")["Room_Price"].transform("median")
    df["Room_Price"] = df["Room_Price"].fillna(hotel_type_price).fillna(type_price).fillna(100.0)
    df["Room_Price"] = df["Room_Price"].round(2)

    # Clean other numeric columns
    df["Number_of_Rooms"] = df["Number_of_Rooms"].fillna(1).astype(int)
    df["Adults"] = df["Adults"].fillna(1).astype(int)
    df["Children"] = df["Children"].fillna(0).astype(int)
    df["Guests"] = (df["Adults"] + df["Children"]).astype(int)

    # Clean cancellation date: if Confirmed or No-Show, must be empty
    # If Cancelled and Cancellation_Date is empty, impute (Booking_Date + half lead time)
    for i, row in df.iterrows():
        status = row["Booking_Status"]
        c_date = row["Cancellation_Date"]
        b_date = row["Booking_Date"]
        ch_date = row["Checkin_Date"]
        
        if status in ["Confirmed", "No-Show"]:
            df.at[i, "Cancellation_Date"] = pd.NaT
        else: # Cancelled
            if pd.isna(c_date) or c_date < b_date or c_date >= ch_date:
                # Cancelled date must be between Booking_Date and Checkin_Date
                lead_days = (ch_date - b_date).days
                cancel_offset = max(0, lead_days // 2)
                df.at[i, "Cancellation_Date"] = b_date + datetime.timedelta(days=cancel_offset)

    # Recalculate financials to enforce absolute consistency
    # subtotal = Room_Price * Nights * Number_of_Rooms
    # discount_amount = subtotal * Discount
    # discounted_subtotal = subtotal - discount_amount
    # Taxes = discounted_subtotal * 0.12
    # Gross_Revenue = discounted_subtotal + Taxes
    # Commission_Amount = discounted_subtotal * Commission_Rate
    # Net_Revenue = Gross_Revenue - Commission_Amount
    
    subtotal = df["Room_Price"] * df["Nights"] * df["Number_of_Rooms"]
    discounted_subtotal = subtotal * (1.0 - df["Discount"].fillna(0.0))
    df["Taxes"] = (discounted_subtotal * 0.12).round(2)
    df["Gross_Revenue"] = (discounted_subtotal + df["Taxes"]).round(2)
    df["Commission_Amount"] = (discounted_subtotal * df["Commission_Rate"].fillna(0.15)).round(2)
    df["Net_Revenue"] = (df["Gross_Revenue"] - df["Commission_Amount"]).round(2)

    # Clean emails & phones
    df["Email"] = df["Email"].astype(str).str.lower().str.strip()
    df["Phone"] = df["Phone"].astype(str).str.strip()
    # Simple email check: if doesn't contain '@', fix it
    df.loc[~df["Email"].str.contains("@"), "Email"] = df["Customer_Name"].str.lower().str.replace(" ", "") + "@example.com"
    # Simple phone cleanup: replace alphabetic characters
    df["Phone"] = df["Phone"].str.replace(r"[a-zA-Z]", "", regex=True)
    df.loc[df["Phone"].str.len() < 5, "Phone"] = "+1-555-0199"

    # Enforce loyalty status capitalization and valid values
    df["Loyalty_Status"] = df["Loyalty_Status"].str.capitalize()

    # Recalculate Season and Weekday_Weekend based on Booking_Date
    df["Season"] = df["Booking_Date"].apply(lambda d: 
        "Spring" if d.month in [3, 4, 5] else
        "Summer" if d.month in [6, 7, 8] else
        "Autumn" if d.month in [9, 10, 11] else "Winter"
    )
    df["Weekday_Weekend"] = df["Booking_Date"].apply(lambda d: 
        "Weekend" if d.weekday() >= 5 else "Weekday"
    )

    # Reorder columns to match the exact 43 requested columns
    expected_columns = [
        "Booking_ID", "Booking_Date", "Checkin_Date", "Checkout_Date", "Lead_Time",
        "Customer_ID", "Customer_Name", "Age", "Gender", "Country", "State", "City",
        "Email", "Phone", "OTA_Name", "Booking_Channel", "Device_Type", "Hotel_ID",
        "Hotel_Name", "Hotel_City", "Hotel_Rating", "Room_Type", "Room_Price",
        "Number_of_Rooms", "Guests", "Adults", "Children", "Nights", "Booking_Status",
        "Cancellation_Date", "Commission_Rate", "Commission_Amount", "Discount", "Taxes",
        "Gross_Revenue", "Net_Revenue", "Payment_Method", "Coupon_Code", "Loyalty_Status",
        "Review_Score", "Season", "Weekday_Weekend", "Special_Request"
    ]
    
    # Fill in any missing columns just in case
    for col in expected_columns:
        if col not in df.columns:
            df[col] = "None"
            
    df_master = df[expected_columns].copy()
    # Convert all date types to YYYY-MM-DD string format for final CSV export
    for col in ["Booking_Date", "Checkin_Date", "Checkout_Date", "Cancellation_Date"]:
        df_master[col] = df_master[col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "")
    # Save Cleaned Master Dataset
    master_path = os.path.join("Dataset", "ota_master_dataset.csv")
    df_master.to_csv(master_path, index=False)
    print(f"Exported master dataset: {master_path} with shape {df_master.shape}")
    # Generate Star Schema Tables (Deduplicated dimensions and fact table)
    print("Generating Star Schema tables...")
    # 1. dim_customers
    # Aggregate customer demographics to resolve inconsistencies if a customer had multiple bookings
    # We will choose the latest booking's demographics for that customer
    df_sorted = df.sort_values("Booking_Date", ascending=True)
    customer_cols = ["Customer_ID", "Customer_Name", "Age", "Gender", "Country", "State", "City", "Email", "Phone", "Loyalty_Status"]
    dim_customers = df_sorted.groupby("Customer_ID")[customer_cols[1:]].last().reset_index()
    dim_customers.to_csv(os.path.join("Dataset", "dim_customers.csv"), index=False)
    print(f"dim_customers shape: {dim_customers.shape} (Unique customer count: {dim_customers['Customer_ID'].nunique()})")

    # 2. dim_hotels
    hotel_cols = ["Hotel_ID", "Hotel_Name", "Hotel_City", "Hotel_Rating"]
    dim_hotels = df.groupby("Hotel_ID")[hotel_cols[1:]].first().reset_index()
    dim_hotels.to_csv(os.path.join("Dataset", "dim_hotels.csv"), index=False)
    print(f"dim_hotels shape: {dim_hotels.shape} (25 hotels expected)")

    # 3. dim_otas
    ota_cols = ["OTA_Name", "Booking_Channel"]
    dim_otas = df.groupby("OTA_Name")[ota_cols[1:]].first().reset_index()
    dim_otas.to_csv(os.path.join("Dataset", "dim_otas.csv"), index=False)
    print(f"dim_otas shape: {dim_otas.shape} (15 OTAs expected)")

    # 4. dim_dates
    # Create a full date list spanning Jan 1, 2024 to Dec 31, 2026
    start_d = datetime.date(2024, 1, 1)
    end_d = datetime.date(2026, 12, 31)
    date_list = [start_d + datetime.timedelta(days=x) for x in range((end_d - start_d).days + 1)]
    
    dates_df = pd.DataFrame({"Date": date_list})
    dates_df["Date"] = dates_df["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    dates_df["Date_Obj"] = pd.to_datetime(dates_df["Date"]).dt.date
    dates_df["Year"] = dates_df["Date_Obj"].apply(lambda d: d.year)
    dates_df["Month"] = dates_df["Date_Obj"].apply(lambda d: d.month)
    dates_df["Month_Name"] = dates_df["Date_Obj"].apply(lambda d: d.strftime("%B"))
    dates_df["Quarter"] = dates_df["Date_Obj"].apply(lambda d: f"Q{(d.month - 1) // 3 + 1}")
    dates_df["Day"] = dates_df["Date_Obj"].apply(lambda d: d.day)
    dates_df["Weekday_Weekend"] = dates_df["Date_Obj"].apply(lambda d: "Weekend" if d.weekday() >= 5 else "Weekday")
    dates_df["Season"] = dates_df["Date_Obj"].apply(lambda d: 
        "Spring" if d.month in [3, 4, 5] else
        "Summer" if d.month in [6, 7, 8] else
        "Autumn" if d.month in [9, 10, 11] else "Winter"
    )
    dates_df.drop(columns=["Date_Obj"], inplace=True)
    dates_df.to_csv(os.path.join("Dataset", "dim_dates.csv"), index=False)
    print(f"dim_dates shape: {dates_df.shape}")

    # 5. fact_bookings
    # Keep FKs and key measures. Refer to expected columns minus full customer/hotel/ota text details if we want
    # but the instructions state: "maintain referential integrity between fact and dimension tables and export a clean star schema"
    # To maintain referential integrity, fact_bookings contains foreign keys linking to dimensions.
    # We will export the full fact table.
    fact_cols = [
        "Booking_ID", "Booking_Date", "Checkin_Date", "Checkout_Date", "Customer_ID", 
        "Hotel_ID", "OTA_Name", "Device_Type", "Room_Type", "Room_Price", "Number_of_Rooms",
        "Guests", "Adults", "Children", "Nights", "Booking_Status", "Cancellation_Date",
        "Lead_Time", "Commission_Rate", "Commission_Amount", "Discount", "Taxes", 
        "Gross_Revenue", "Net_Revenue", "Payment_Method", "Coupon_Code", "Review_Score",
        "Special_Request"
    ]
    fact_bookings = df_master[fact_cols].copy()
    fact_bookings.to_csv(os.path.join("Dataset", "fact_bookings.csv"), index=False)
    print(f"fact_bookings shape: {fact_bookings.shape}")
    print("ETL and Star Schema Generation Completed Successfully!")

if __name__ == "__main__":
    main()
