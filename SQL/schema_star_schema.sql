-- SQL Schema Definition for Online Travel Agency (OTA) Star Schema
-- Compatible with PostgreSQL / MySQL / SQL Server

-- -------------------------------------------------------------
-- 1. Create Dimension Tables
-- -------------------------------------------------------------

-- Dimension: Customers
CREATE TABLE dim_customers (
    Customer_ID VARCHAR(50) PRIMARY KEY,
    Customer_Name VARCHAR(150) NOT NULL,
    Age INT NOT NULL,
    Gender VARCHAR(50) NOT NULL,
    Country VARCHAR(100) NOT NULL,
    State VARCHAR(100) NOT NULL,
    City VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NOT NULL,
    Phone VARCHAR(50) NOT NULL,
    Loyalty_Status VARCHAR(50) NOT NULL
);

-- Dimension: Hotels
CREATE TABLE dim_hotels (
    Hotel_ID VARCHAR(50) PRIMARY KEY,
    Hotel_Name VARCHAR(150) NOT NULL,
    Hotel_City VARCHAR(100) NOT NULL,
    Hotel_Rating DECIMAL(3, 2) NOT NULL
);

-- Dimension: OTAs
CREATE TABLE dim_otas (
    OTA_Name VARCHAR(100) PRIMARY KEY,
    Booking_Channel VARCHAR(100) NOT NULL
);

-- Dimension: Dates
CREATE TABLE dim_dates (
    Date VARCHAR(10) PRIMARY KEY, -- Formatted as YYYY-MM-DD
    Year INT NOT NULL,
    Month INT NOT NULL,
    Month_Name VARCHAR(20) NOT NULL,
    Quarter VARCHAR(2) NOT NULL,
    Day INT NOT NULL,
    Weekday_Weekend VARCHAR(10) NOT NULL,
    Season VARCHAR(20) NOT NULL
);

-- -------------------------------------------------------------
-- 2. Create Fact Table
-- -------------------------------------------------------------

-- Fact: Bookings
CREATE TABLE fact_bookings (
    Booking_ID VARCHAR(50) PRIMARY KEY,
    Booking_Date VARCHAR(10) NOT NULL,
    Checkin_Date VARCHAR(10) NOT NULL,
    Checkout_Date VARCHAR(10) NOT NULL,
    Customer_ID VARCHAR(50) NOT NULL,
    Hotel_ID VARCHAR(50) NOT NULL,
    OTA_Name VARCHAR(100) NOT NULL,
    Device_Type VARCHAR(50) NOT NULL,
    Room_Type VARCHAR(50) NOT NULL,
    Room_Price DECIMAL(10, 2) NOT NULL,
    Number_of_Rooms INT NOT NULL,
    Guests INT NOT NULL,
    Adults INT NOT NULL,
    Children INT NOT NULL,
    Nights INT NOT NULL,
    Booking_Status VARCHAR(50) NOT NULL,
    Cancellation_Date VARCHAR(10),
    Lead_Time INT NOT NULL,
    Commission_Rate DECIMAL(5, 4) NOT NULL,
    Commission_Amount DECIMAL(10, 2) NOT NULL,
    Discount DECIMAL(5, 4) NOT NULL,
    Taxes DECIMAL(10, 2) NOT NULL,
    Gross_Revenue DECIMAL(10, 2) NOT NULL,
    Net_Revenue DECIMAL(10, 2) NOT NULL,
    Payment_Method VARCHAR(50) NOT NULL,
    Coupon_Code VARCHAR(50) NOT NULL,
    Review_Score DECIMAL(3, 1) NOT NULL,
    Special_Request VARCHAR(100) NOT NULL,
    
    -- Foreign Key Constraints to Dimensions
    CONSTRAINT fk_booking_date FOREIGN KEY (Booking_Date) REFERENCES dim_dates (Date),
    CONSTRAINT fk_checkin_date FOREIGN KEY (Checkin_Date) REFERENCES dim_dates (Date),
    CONSTRAINT fk_checkout_date FOREIGN KEY (Checkout_Date) REFERENCES dim_dates (Date),
    CONSTRAINT fk_customer FOREIGN KEY (Customer_ID) REFERENCES dim_customers (Customer_ID),
    CONSTRAINT fk_hotel FOREIGN KEY (Hotel_ID) REFERENCES dim_hotels (Hotel_ID),
    CONSTRAINT fk_ota FOREIGN KEY (OTA_Name) REFERENCES dim_otas (OTA_Name)
);

-- Create Indexes for Performance Optimization
CREATE INDEX idx_fact_bookings_customer ON fact_bookings (Customer_ID);
CREATE INDEX idx_fact_bookings_hotel ON fact_bookings (Hotel_ID);
CREATE INDEX idx_fact_bookings_ota ON fact_bookings (OTA_Name);
CREATE INDEX idx_fact_bookings_booking_date ON fact_bookings (Booking_Date);
