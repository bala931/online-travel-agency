-- ============================================================
-- OTA Project — KPI & RFM SQL Queries
-- Compatible with PostgreSQL / MySQL / SQL Server
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- SECTION 1: RFM BASE METRICS
-- ─────────────────────────────────────────────────────────────

-- 1A. Compute raw Recency, Frequency, Monetary per customer
--     Using only Confirmed bookings (status = 'Confirmed')
WITH rfm_base AS (
    SELECT
        f.Customer_ID,
        c.Customer_Name,
        c.Country,
        c.Loyalty_Status,
        MAX(f.Booking_Date)                                             AS Last_Booking_Date,
        MIN(f.Booking_Date)                                             AS First_Booking_Date,
        COUNT(f.Booking_ID)                                             AS Frequency,
        SUM(f.Net_Revenue)                                              AS Monetary,
        DATEDIFF(DAY, MAX(f.Booking_Date), '2026-07-01')               AS Recency,
        AVG(f.Review_Score)                                             AS Avg_Review_Score,
        SUM(f.Nights)                                                   AS Total_Nights,
        AVG(f.Lead_Time)                                                AS Avg_Lead_Time
    FROM  fact_bookings  f
    JOIN  dim_customers  c ON f.Customer_ID = c.Customer_ID
    WHERE f.Booking_Status = 'Confirmed'
    GROUP BY f.Customer_ID, c.Customer_Name, c.Country, c.Loyalty_Status
),

-- 1B. Assign R, F, M quintile scores (1–5) using NTILE
rfm_scored AS (
    SELECT *,
        -- Recency: LOWER days = higher score (reversed)
        6 - NTILE(5) OVER (ORDER BY Recency ASC)   AS R_Score,
        NTILE(5) OVER (ORDER BY Frequency ASC)      AS F_Score,
        NTILE(5) OVER (ORDER BY Monetary ASC)       AS M_Score
    FROM rfm_base
),

-- 1C. Build composite RFM score string
rfm_final AS (
    SELECT *,
        CAST(R_Score AS VARCHAR) + CAST(F_Score AS VARCHAR) + CAST(M_Score AS VARCHAR)
                                                    AS RFM_Score,
        R_Score + F_Score + M_Score                 AS RFM_Total
    FROM rfm_scored
)

SELECT * FROM rfm_final
ORDER BY Monetary DESC;


-- ─────────────────────────────────────────────────────────────
-- SECTION 2: SEGMENT DISTRIBUTION
-- ─────────────────────────────────────────────────────────────

-- 2A. Count of customers and total revenue per segment
--     (After running segmentation, joined from rfm_segments table)
SELECT
    Segment,
    COUNT(Customer_ID)          AS Customers,
    ROUND(SUM(Monetary), 2)     AS Total_Revenue,
    ROUND(AVG(Monetary), 2)     AS Avg_CLV,
    ROUND(AVG(Recency), 1)      AS Avg_Recency_Days,
    ROUND(AVG(Frequency), 2)    AS Avg_Frequency,
    ROUND(SUM(Monetary) / (SELECT SUM(Monetary) FROM rfm_segments) * 100, 2)
                                AS Revenue_Share_Pct
FROM rfm_segments
GROUP BY Segment
ORDER BY Total_Revenue DESC;


-- ─────────────────────────────────────────────────────────────
-- SECTION 3: CHAMPION CUSTOMERS
-- ─────────────────────────────────────────────────────────────

-- 3A. Top 20 customers by total Net Revenue (Confirmed bookings)
SELECT TOP 20
    rs.Customer_ID,
    rs.Customer_Name,
    rs.Country,
    rs.Loyalty_Status,
    rs.Segment,
    rs.Frequency,
    ROUND(rs.Monetary, 2)              AS Total_Net_Revenue,
    rs.Recency                         AS Days_Since_Last_Booking,
    ROUND(rs.Avg_Revenue_Per_Booking, 2) AS Avg_Revenue_Per_Booking
FROM rfm_segments rs
ORDER BY rs.Monetary DESC;


-- ─────────────────────────────────────────────────────────────
-- SECTION 4: AT-RISK CUSTOMERS REQUIRING RETENTION ACTION
-- ─────────────────────────────────────────────────────────────

-- 4A. Customers in At Risk / Can't Lose Them / Hibernating segments
SELECT
    Customer_ID,
    Customer_Name,
    Country,
    Loyalty_Status,
    Segment,
    Recency            AS Days_Since_Last_Booking,
    Frequency          AS Total_Bookings,
    ROUND(Monetary, 2) AS Lifetime_Revenue,
    R_Score,
    F_Score,
    M_Score,
    RFM_Total
FROM rfm_segments
WHERE Segment IN ('At Risk', "Can't Lose Them", 'Hibernating')
ORDER BY Monetary DESC;


-- ─────────────────────────────────────────────────────────────
-- SECTION 5: LOYALTY STATUS vs. SEGMENT CROSS-TAB
-- ─────────────────────────────────────────────────────────────

SELECT
    Loyalty_Status,
    SUM(CASE WHEN Segment = 'Champions'          THEN 1 ELSE 0 END)  AS Champions,
    SUM(CASE WHEN Segment = 'Loyal Customers'    THEN 1 ELSE 0 END)  AS Loyal_Customers,
    SUM(CASE WHEN Segment = 'Potential Loyalists'THEN 1 ELSE 0 END)  AS Potential_Loyalists,
    SUM(CASE WHEN Segment = 'Promising'          THEN 1 ELSE 0 END)  AS Promising,
    SUM(CASE WHEN Segment = 'Recent Customers'   THEN 1 ELSE 0 END)  AS Recent_Customers,
    SUM(CASE WHEN Segment = 'Need Attention'     THEN 1 ELSE 0 END)  AS Need_Attention,
    SUM(CASE WHEN Segment = 'About to Sleep'     THEN 1 ELSE 0 END)  AS About_to_Sleep,
    SUM(CASE WHEN Segment = 'At Risk'            THEN 1 ELSE 0 END)  AS At_Risk,
    SUM(CASE WHEN Segment = 'Can''t Lose Them'   THEN 1 ELSE 0 END)  AS Cant_Lose_Them,
    SUM(CASE WHEN Segment = 'Hibernating'        THEN 1 ELSE 0 END)  AS Hibernating,
    SUM(CASE WHEN Segment = 'Lost'               THEN 1 ELSE 0 END)  AS Lost,
    COUNT(*)                                                          AS Total_Customers
FROM rfm_segments
GROUP BY Loyalty_Status
ORDER BY
    CASE Loyalty_Status
        WHEN 'Platinum' THEN 1
        WHEN 'Gold'     THEN 2
        WHEN 'Silver'   THEN 3
        ELSE 4
    END;


-- ─────────────────────────────────────────────────────────────
-- SECTION 6: AVERAGE CLV BY COUNTRY (TOP 10)
-- ─────────────────────────────────────────────────────────────

SELECT TOP 10
    Country,
    COUNT(Customer_ID)       AS Customers,
    ROUND(AVG(Monetary), 2)  AS Avg_CLV,
    ROUND(SUM(Monetary), 2)  AS Total_Revenue,
    ROUND(AVG(Frequency), 2) AS Avg_Bookings
FROM rfm_segments
GROUP BY Country
ORDER BY Avg_CLV DESC;


-- ─────────────────────────────────────────────────────────────
-- SECTION 7: RFM SCORE DISTRIBUTION
-- ─────────────────────────────────────────────────────────────

SELECT
    RFM_Total,
    COUNT(Customer_ID)       AS Customers,
    ROUND(AVG(Monetary), 2)  AS Avg_Monetary,
    ROUND(AVG(Recency), 1)   AS Avg_Recency,
    ROUND(AVG(Frequency), 2) AS Avg_Frequency
FROM rfm_segments
GROUP BY RFM_Total
ORDER BY RFM_Total DESC;
