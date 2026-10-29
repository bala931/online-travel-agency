import os
import pandas as pd
import numpy as np

def validate():
    raw_path = os.path.join("Dataset", "ota_raw_dataset.csv")
    master_path = os.path.join("Dataset", "ota_master_dataset.csv")
    
    errors = []
    # Check file existence
    if not os.path.exists(raw_path):
        errors.append("Raw dataset file does not exist.")
        return errors
    if not os.path.exists(master_path):
        errors.append("Master dataset file does not exist.")
        return errors

    # Load datasets
    df_raw = pd.read_csv(raw_path)
    df_master = pd.read_csv(master_path)
    
    print("--- VALIDATION METRICS ---")
    print(f"Raw shape: {df_raw.shape}")
    print(f"Master shape: {df_master.shape}")
    
    # 1. Shape validations
    if len(df_raw) != 6000:
        errors.append(f"Raw dataset has {len(df_raw)} rows instead of 6000.")
    if len(df_master) != 5900:
        errors.append(f"Master dataset has {len(df_master)} rows instead of 5900.")
        
    if len(df_raw.columns) != 43:
        errors.append(f"Raw dataset has {len(df_raw.columns)} columns instead of 43.")
    if len(df_master.columns) != 43:
        errors.append(f"Master dataset has {len(df_master.columns)} columns instead of 43.")

    # 2. Duplicate validation
    raw_duplicates = df_raw["Booking_ID"].duplicated().sum()
    master_duplicates = df_master["Booking_ID"].duplicated().sum()
    print(f"Raw duplicates by Booking_ID: {raw_duplicates}")
    print(f"Master duplicates by Booking_ID: {master_duplicates}")
    
    if raw_duplicates != 100:
        errors.append(f"Raw dataset has {raw_duplicates} duplicates instead of 100.")
    if master_duplicates != 0:
        errors.append(f"Master dataset has {master_duplicates} duplicates instead of 0.")

    # 3. Column names and order consistency
    raw_cols = list(df_raw.columns)
    master_cols = list(df_master.columns)
    if raw_cols != master_cols:
        errors.append("Column name order does not match between Raw and Master.")
        
    # 4. Age boundaries in Master
    invalid_ages = df_master[(df_master["Age"] < 18) | (df_master["Age"] > 85)]
    if len(invalid_ages) > 0:
        errors.append(f"Master dataset has {len(invalid_ages)} records with ages outside [18, 85].")

    # 5. Room Price cleaning
    price_nulls = df_master["Room_Price"].isna().sum()
    if price_nulls > 0:
        errors.append(f"Master dataset has {price_nulls} null room prices.")
    negative_prices = (df_master["Room_Price"] <= 0).sum()
    if negative_prices > 0:
        errors.append(f"Master dataset has {negative_prices} negative or zero room prices.")

    # 6. Date format validation (YYYY-MM-DD)
    date_cols = ["Booking_Date", "Checkin_Date", "Checkout_Date"]
    for col in date_cols:
        invalid_format_count = 0
        for val in df_master[col].dropna():
            try:
                pd.to_datetime(val, format="%Y-%m-%d")
            except ValueError:
                invalid_format_count += 1
        if invalid_format_count > 0:
            errors.append(f"Master dataset column '{col}' has {invalid_format_count} values that do not match YYYY-MM-DD.")

    # 7. Logical date checks
    invalid_checkin = (pd.to_datetime(df_master["Checkin_Date"]) < pd.to_datetime(df_master["Booking_Date"])).sum()
    invalid_checkout = (pd.to_datetime(df_master["Checkout_Date"]) <= pd.to_datetime(df_master["Checkin_Date"])).sum()
    if invalid_checkin > 0:
        errors.append(f"Master dataset has {invalid_checkin} rows where Checkin_Date < Booking_Date.")
    if invalid_checkout > 0:
        errors.append(f"Master dataset has {invalid_checkout} rows where Checkout_Date <= Checkin_Date.")

    # 8. Financial calculations verification
    # Allow small rounding discrepancies up to $0.05 due to roundings in sub-steps
    mismatched_revenue = 0
    for idx, row in df_master.iterrows():
        subtotal = row["Room_Price"] * row["Nights"] * row["Number_of_Rooms"]
        discounted_sub = subtotal * (1.0 - row["Discount"])
        expected_taxes = round(discounted_sub * 0.12, 2)
        expected_gross = round(discounted_sub + expected_taxes, 2)
        expected_commission = round(discounted_sub * row["Commission_Rate"], 2)
        expected_net = round(expected_gross - expected_commission, 2)
        
        gross_diff = abs(row["Gross_Revenue"] - expected_gross)
        net_diff = abs(row["Net_Revenue"] - expected_net)
        
        if gross_diff > 0.02 or net_diff > 0.02:
            mismatched_revenue += 1
            
    print(f"Financial calculation mismatches in Master: {mismatched_revenue}")
    if mismatched_revenue > 0:
        errors.append(f"Master dataset has {mismatched_revenue} records with inconsistent financial columns.")

    # 9. Star Schema files existence
    schema_files = ["dim_customers.csv", "dim_hotels.csv", "dim_otas.csv", "dim_dates.csv", "fact_bookings.csv"]
    for file in schema_files:
        fpath = os.path.join("Dataset", file)
        if not os.path.exists(fpath):
            errors.append(f"Star schema file {file} is missing.")
        else:
            df_temp = pd.read_csv(fpath)
            print(f"Star Schema File: {file} shape: {df_temp.shape}")

    # Final summary
    if len(errors) == 0:
        print("\nAll validations passed successfully! The ETL output is clean and consistent.")
    else:
        print(f"\nValidation failed with {len(errors)} errors:")
        for err in errors:
            print(f" - {err}")
            
    return errors

if __name__ == "__main__":
    validate()
