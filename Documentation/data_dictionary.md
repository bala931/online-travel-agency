# Data Dictionary - OTA Performance & Channel ManagementThis dictionary documents all 43 columns maintained throughout the Online Travel Agency (OTA) Performance and Channel Management project.
---
| # | Column Name | Data Type | Constraints | Description | Dimension/Fact Association |
|---|-------------|-----------|-------------|-------------|----------------------------|
| 1 | **Booking_ID** | String | Primary Key (PK) | Unique booking identifier (e.g., `BKN-10001`). Duplicate bookings are deduplicated in ETL. | Fact |
| 2 | **Booking_Date** | Date | Non-Null | Date when the booking was made. Format: `YYYY-MM-DD`. | Fact (FK to `dim_dates`) |
| 3 | **Checkin_Date** | Date | Non-Null, >= Booking_Date | Date when customer is scheduled to check in. Format: `YYYY-MM-DD`. | Fact (FK to `dim_dates`) |
| 4 | **Checkout_Date** | Date | Non-Null, > Checkin_Date | Date when customer is scheduled to check out. Format: `YYYY-MM-DD`. | Fact (FK to `dim_dates`) |
| 5 | **Lead_Time** | Integer | Non-Null, >= 0 | Number of days between Booking_Date and Checkin_Date. | Fact |
| 6 | **Customer_ID** | String | Foreign Key (FK) | Unique customer identifier (e.g., `CUST-1001`). | Fact / Dimension (`dim_customers`) |
| 7 | **Customer_Name** | String | Non-Null | Full name of the customer. | Dimension (`dim_customers`) |
| 8 | **Age** | Integer | Non-Null, 18 to 85 | Customer's age in years. Imputed with median age during ETL. | Dimension (`dim_customers`) |
| 9 | **Gender** | String | Non-Null | Customer's gender. Values: `Male`, `Female`, `Non-binary`, `Unknown`. | Dimension (`dim_customers`) |
| 10 | **Country** | String | Non-Null | Customer's home country. | Dimension (`dim_customers`) |
| 11 | **State** | String | Non-Null | Customer's home state or province. | Dimension (`dim_customers`) |
| 12 | **City** | String | Non-Null | Customer's home city. | Dimension (`dim_customers`) |
| 13 | **Email** | String | Non-Null | Customer's email address. Format validated in ETL. | Dimension (`dim_customers`) |
| 14 | **Phone** | String | Non-Null | Customer's phone number. Standardized in ETL. | Dimension (`dim_customers`) |
| 15 | **OTA_Name** | String | Foreign Key (FK) | Name of the Online Travel Agency platform. | Fact / Dimension (`dim_otas`) |
| 16 | **Booking_Channel** | String | Non-Null | Channel type. Values: `Online`, `Mobile App`, `Metasearch`. | Dimension (`dim_otas`) |
| 17 | **Device_Type** | String | Non-Null | Device used. Values: `Desktop`, `Mobile`, `Tablet`, `Smart TV`. | Fact |
| 18 | **Hotel_ID** | String | Foreign Key (FK) | Unique hotel identifier (e.g., `HTL-101`). | Fact / Dimension (`dim_hotels`) |
| 19 | **Hotel_Name** | String | Non-Null | Name of the booked hotel. | Dimension (`dim_hotels`) |
| 20 | **Hotel_City** | String | Non-Null | City where the hotel is located. | Dimension (`dim_hotels`) |
| 21 | **Hotel_Rating** | Decimal | Non-Null, 1.0 to 5.0 | Average star rating of the hotel. | Dimension (`dim_hotels`) |
| 22 | **Room_Type** | String | Non-Null | Room tier booked. Values: `Single`, `Double`, `Deluxe`, `Suite`, `Family`. | Fact |
| 23 | **Room_Price** | Decimal | Non-Null, > 0 | Nightly price of the room. Outliers imputed during ETL. | Fact |
| 24 | **Number_of_Rooms** | Integer | Non-Null, >= 1 | Number of rooms booked in this transaction. | Fact |
| 25 | **Guests** | Integer | Non-Null, = Adults + Children | Total number of guests. | Fact |
| 26 | **Adults** | Integer | Non-Null, >= 1 | Number of adult guests. | Fact |
| 27 | **Children** | Integer | Non-Null, >= 0 | Number of child guests. | Fact |
| 28 | **Nights** | Integer | Non-Null, >= 1 | Length of stay in nights. Calculated as Checkout_Date - Checkin_Date. | Fact |
| 29 | **Booking_Status** | String | Non-Null | Status of reservation. Values: `Confirmed`, `Cancelled`, `No-Show`. | Fact |
| 30 | **Cancellation_Date** | Date | Nullable | Date when cancellation occurred. Only valid for `Cancelled` status. | Fact |
| 31 | **Commission_Rate** | Decimal | Non-Null, 0.0 to 1.0 | commission percentage charged by the OTA platform. | Fact |
| 32 | **Commission_Amount** | Decimal | Non-Null, >= 0 | Calculated as `Discounted_Subtotal * Commission_Rate`. | Fact |
| 33 | **Discount** | Decimal | Non-Null, 0.0 to 1.0 | Discount rate applied to the subtotal. | Fact |
| 34 | **Taxes** | Decimal | Non-Null, >= 0 | Tax amount, calculated as 12% of the discounted subtotal. | Fact |
| 35 | **Gross_Revenue** | Decimal | Non-Null, >= 0 | Revenue including taxes. Calculated as `Discounted_Subtotal + Taxes`. | Fact |
| 36 | **Net_Revenue** | Decimal | Non-Null | Revenue retained by hotel. Calculated as `Gross_Revenue - Commission_Amount`. | Fact |
| 37 | **Payment_Method** | String | Non-Null | Payment provider. Values: `Credit Card`, `Debit Card`, `PayPal`, `Net Banking`, `Cash`, `Crypto`. | Fact |
| 38 | **Coupon_Code** | String | Non-Null | Promo coupon used (e.g., `SAVE10`, `SAVE15`, `None`). | Fact |
| 39 | **Loyalty_Status** | String | Non-Null | Customer loyalty status. Values: `Standard`, `Silver`, `Gold`, `Platinum`. | Dimension (`dim_customers`) |
| 40 | **Review_Score** | Decimal | Non-Null, 1.0 to 5.0 | Customer review rating. Missing and outliers imputed in ETL. | Fact |
| 41 | **Season** | String | Non-Null | Booking season based on booking date. Values: `Spring`, `Summer`, `Autumn`, `Winter`. | Fact |
| 42 | **Weekday_Weekend** | String | Non-Null | Booking day type. Values: `Weekday`, `Weekend`. | Fact |
| 43 | **Special_Request** | String | Non-Null | Customer request preference. Values: `None`, `Late Checkout`, `Extra Bed`, `Quiet Room`, etc. | Fact |
