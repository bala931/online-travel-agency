# Power Query M Steps - ETL & Schema Setup

This document outlines the Power Query (M Formula Language) steps required to import, clean, and structure the raw OTA dataset (`ota_raw_dataset.csv`) directly in Power BI, maintaining the exact schema and data types.

---

## 1. Importing and Cleaning the Master Dataset

Here is the complete M script to transform `ota_raw_dataset.csv` into a cleaned table.

```powerquery
let
    // 1. Source definition (Change path to your local folder)
    Source = Csv.Document(File.Contents("C:\Users\balam\OneDrive\Desktop\OAT\Dataset\ota_raw_dataset.csv"), [Delimiter=",", Columns=43, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    
    // 2. Promote Headers
    PromoteHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    
    // 3. Remove Duplicates based on Booking_ID
    Deduplicate = Table.Distinct(PromoteHeaders, {"Booking_ID"}),
    
    // 4. Clean Room_Price currency formatting
    CleanRoomPrice = Table.ReplaceValue(Deduplicate, "$", "", Replacer.ReplaceText, {"Room_Price"}),
    CleanRoomPrice2 = Table.ReplaceValue(CleanRoomPrice, ",", "", Replacer.ReplaceText, {"Room_Price"}),
    
    // 5. Standardize Gender values
    StandardizeGender = Table.ReplaceValue(CleanRoomPrice2, "m", "Male", Replacer.ReplaceText, {"Gender"}),
    StandardizeGender2 = Table.ReplaceValue(StandardizeGender, "male", "Male", Replacer.ReplaceText, {"Gender"}),
    StandardizeGender3 = Table.ReplaceValue(StandardizeGender2, "f", "Female", Replacer.ReplaceText, {"Gender"}),
    StandardizeGender4 = Table.ReplaceValue(StandardizeGender3, "female", "Female", Replacer.ReplaceText, {"Gender"}),
    StandardizeGender5 = Table.ReplaceValue(StandardizeGender4, "nb", "Non-binary", Replacer.ReplaceText, {"Gender"}),
    StandardizeGender6 = Table.ReplaceValue(StandardizeGender5, "U", "Unknown", Replacer.ReplaceText, {"Gender"}),
    StandardizeGender7 = Table.ReplaceValue(StandardizeGender6, "unknown", "Unknown", Replacer.ReplaceText, {"Gender"}),

    // 6. Standardize Loyalty_Status values (Capitalize)
    CapitalizeLoyalty = Table.TransformColumns(StandardizeGender7, {{"Loyalty_Status", Text.TitleCase, type text}}),
    
    // 7. Parse and Standardize Dates (Support multiple date formats)
    ParseBookingDate = Table.TransformColumns(CapitalizeLoyalty, {{"Booking_Date", each try Date.FromText(_) otherwise null, type date}}),
    ParseCheckinDate = Table.TransformColumns(ParseBookingDate, {{"Checkin_Date", each try Date.FromText(_) otherwise null, type date}}),
    ParseCheckoutDate = Table.TransformColumns(ParseCheckinDate, {{"Checkout_Date", each try Date.FromText(_) otherwise null, type date}}),
    ParseCancelDate = Table.TransformColumns(ParseCheckoutDate, {{"Cancellation_Date", each try Date.FromText(_) otherwise null, type date}}),
    
    // 8. Change Data Types
    ChangeTypes = Table.TransformColumnTypes(ParseCancelDate, {
        {"Booking_ID", type text},
        {"Lead_Time", Int64.Type},
        {"Customer_ID", type text},
        {"Customer_Name", type text},
        {"Age", Int64.Type},
        {"Country", type text},
        {"State", type text},
        {"City", type text},
        {"Email", type text},
        {"Phone", type text},
        {"OTA_Name", type text},
        {"Booking_Channel", type text},
        {"Device_Type", type text},
        {"Hotel_ID", type text},
        {"Hotel_Name", type text},
        {"Hotel_City", type text},
        {"Hotel_Rating", type number},
        {"Room_Type", type text},
        {"Room_Price", type number},
        {"Number_of_Rooms", Int64.Type},
        {"Guests", Int64.Type},
        {"Adults", Int64.Type},
        {"Children", Int64.Type},
        {"Nights", Int64.Type},
        {"Booking_Status", type text},
        {"Commission_Rate", type number},
        {"Commission_Amount", type number},
        {"Discount", type number},
        {"Taxes", type number},
        {"Gross_Revenue", type number},
        {"Net_Revenue", type number},
        {"Payment_Method", type text},
        {"Coupon_Code", type text},
        {"Review_Score", type number},
        {"Season", type text},
        {"Weekday_Weekend", type text},
        {"Special_Request", type text}
    }),

    // 9. Clean Age Outliers (Replace < 18 or > 85 with Median e.g. 45)
    CleanAges = Table.ReplaceValue(ChangeTypes, each [Age], each if [Age] < 18 or [Age] > 85 then 45 else [Age], Replacer.ReplaceValue, {"Age"}),
    
    // 10. Recalculate Financial Columns for exact alignment
    RecalculateGross = Table.AddColumn(CleanAges, "New_Gross", each ([Room_Price] * [Nights] * [Number_of_Rooms] * (1 - [Discount])) * 1.12, type number),
    RecalculateNet = Table.AddColumn(RecalculateGross, "New_Net", each [New_Gross] - ([Room_Price] * [Nights] * [Number_of_Rooms] * (1 - [Discount]) * [Commission_Rate]), type number)
in
    RecalculateNet
```

---

## 2. Setting Up the Star Schema Queries

To implement the Star Schema directly in Power BI Desktop, you should reference the cleaned master query above (let's assume it is named `CleanedMaster`) and split it into normalized dimension and fact tables using the **Reference** feature in Power Query.

### Query 1: `dim_customers`
1. Right-click `CleanedMaster` -> **Reference**.
2. Select columns: `Customer_ID`, `Customer_Name`, `Age`, `Gender`, `Country`, `State`, `City`, `Email`, `Phone`, `Loyalty_Status`.
3. Right-click `Customer_ID` -> **Remove Duplicates** (to ensure 1:Many relationships).
4. Rename query to `dim_customers`.

### Query 2: `dim_hotels`
1. Right-click `CleanedMaster` -> **Reference**.
2. Select columns: `Hotel_ID`, `Hotel_Name`, `Hotel_City`, `Hotel_Rating`.
3. Right-click `Hotel_ID` -> **Remove Duplicates**.
4. Rename query to `dim_hotels`.

### Query 3: `dim_otas`
1. Right-click `CleanedMaster` -> **Reference**.
2. Select columns: `OTA_Name`, `Booking_Channel`.
3. Right-click `OTA_Name` -> **Remove Duplicates**.
4. Rename query to `dim_otas`.

### Query 4: `dim_dates` (Generated dynamically in Power Query)
Create a new Blank Query and enter the following M code to generate a continuous Date table:
```powerquery
let
    StartDate = #date(2024, 1, 1),
    EndDate = #date(2026, 12, 31),
    NumberOfDays = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, NumberOfDays, #duration(1, 0, 0, 0)),
    TableFromList = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    ChangedType = Table.TransformColumnTypes(TableFromList, {{"Date", type date}}),
    AddYear = Table.AddColumn(ChangedType, "Year", each Date.Year([Date]), Int64.Type),
    AddMonth = Table.AddColumn(AddYear, "Month", each Date.Month([Date]), Int64.Type),
    AddMonthName = Table.AddColumn(AddMonth, "Month_Name", each Date.MonthName([Date]), type text),
    AddQuarter = Table.AddColumn(AddMonthName, "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    AddDay = Table.AddColumn(AddQuarter, "Day", each Date.Day([Date]), Int64.Type),
    AddWeekdayWeekend = Table.AddColumn(AddDay, "Weekday_Weekend", each if Date.DayOfWeek([Date]) >= 5 then "Weekend" else "Weekday", type text),
    AddSeason = Table.AddColumn(AddWeekdayWeekend, "Season", each 
        let m = Date.Month([Date]) in
        if m >= 3 and m <= 5 then "Spring"
        else if m >= 6 and m <= 8 then "Summer"
        else if m >= 9 and m <= 11 then "Autumn"
        else "Winter", type text)
in
    AddSeason
```

### Query 5: `fact_bookings`
1. Right-click `CleanedMaster` -> **Reference**.
2. Select all factual columns and keys:
   - `Booking_ID`, `Booking_Date`, `Checkin_Date`, `Checkout_Date`, `Customer_ID`, `Hotel_ID`, `OTA_Name`, `Device_Type`, `Room_Type`, `Room_Price`, `Number_of_Rooms`, `Guests`, `Adults`, `Children`, `Nights`, `Booking_Status`, `Cancellation_Date`, `Lead_Time`, `Commission_Rate`, `Commission_Amount`, `Discount`, `Taxes`, `Gross_Revenue`, `Net_Revenue`, `Payment_Method`, `Coupon_Code`, `Review_Score`, `Special_Request`.
3. Keep the columns, and ensure `Booking_ID` is unique.
4. Rename query to `fact_bookings`.
