# Online Travel Agency (OTA) Performance and Channel Management

An industry-level end-to-end data analytics and business intelligence project. This project implements a comprehensive analytics workflow—spanning data generation, ETL, SQL database schema design, exploratory data analysis, customer segmentation, performance analysis, fraud detection, forecasting, and cohort analysis.

---

## Project Structure

```
OAT/
├── Dataset/                      # Raw, Master, and Dimension/Fact CSVs
│   ├── ota_raw_dataset.csv       # Raw messy transaction data (6000 rows, 43 cols)
│   ├── ota_master_dataset.csv    # Cleaned master dataset (5900 rows, 43 cols)
│   ├── dim_customers.csv         # Customer dimension table
│   ├── dim_hotels.csv            # Hotel dimension table
│   ├── dim_otas.csv              # OTA platform dimension table
│   ├── dim_dates.csv             # Date dimension table (2024-2026)
│   └── fact_bookings.csv         # Booking transactions fact table
├── Python/                       # Scripts for ETL, EDA, Modeling, and Forecasting
│   ├── data_generator.py         # Simulates raw messy travel data
│   ├── etl_pipeline.py           # Cleans data and exports star schema
│   └── validate_etl.py           # Runs automated sanity checks
├── SQL/                          # Star schema DDL and performance analysis queries
│   └── schema_star_schema.sql    # DDL for database table creation
├── PowerBI/                      # DAX measures and Power Query ETL steps
│   └── power_query_m_steps.md    # Guide to Power Query transformations
├── Reports/                      # Detailed phase-by-phase reports
│   └── Phase_1_ETL_Report.md     # ETL and Integration Report
├── Documentation/                # Data Dictionary and setup guidelines
│   └── data_dictionary.md        # Comprehensive 43-column data dictionary
└── README.md                     # Project overview and roadmap
```

---

## How to Run the ETL Pipeline

### Prerequisites
Make sure you have Python 3 installed, along with the `pandas` and `numpy` packages.
```bash
pip install pandas numpy
```

### Step 1: Generate Raw Data
Run the generator script to create the raw dataset:
```bash
C:\Users\balam\AppData\Local\Programs\Python\Python310\python.exe Python/data_generator.py
```
This writes `Dataset/ota_raw_dataset.csv` (exactly 6000 rows, 43 columns).

### Step 2: Clean and Structure the Data
Run the ETL pipeline script:
```bash
C:\Users\balam\AppData\Local\Programs\Python\Python310\python.exe Python/etl_pipeline.py
```
This cleans the data, enforces constraints, recalculates financials, and exports the master dataset (`Dataset/ota_master_dataset.csv`) and the 5 relational star schema files.

### Step 3: Validate Outputs
Verify that all outputs are mathematically aligned and structurally clean:
```bash
C:\Users\balam\AppData\Local\Programs\Python\Python310\python.exe Python/validate_etl.py
```

### Step 4: Run EDA
```bash
C:\Users\balam\AppData\Local\Programs\Python\Python310\python.exe Python/eda_analysis.py
```
All charts are saved to the `Images/` folder.

> **Note**: Use the explicit Python 3.10 path above, as this system has multiple Python environments and `matplotlib`/`scipy` are installed in Python 3.10.

---

## Roadmap & Status

- [x] **Phase 1: Data Integration & Preprocessing (ETL)** - *Completed*
- [x] **Phase 2: Exploratory Data Analysis (EDA)** - *Completed*
- [x] **Phase 3: Customer Segmentation (RFM)** - *Completed*
- [ ] **Phase 4: Product Performance & Sales Analysis**
- [ ] **Phase 5: Fraud Detection**
- [ ] **Phase 6: KPI Dashboard**
- [ ] **Phase 7: Interactive Dashboard**
- [ ] **Phase 8: Sales Forecasting**
- [ ] **Phase 9: Cohort & Retention Analysis**
