import os
import random
import datetime
import pandas as pd
import numpy as np

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)
# Create Dataset and Python directories if they don't exist
os.makedirs("Dataset", exist_ok=True)
os.makedirs("Python", exist_ok=True)
# Define lookup data
otas = [
    "Booking.com", "Expedia", "Agoda", "MakeMyTrip", "Goibibo",
    "Airbnb", "Hotels.com", "Trip.com", "Traveloka", "Cleartrip",
    "Yatra", "EaseMyTrip", "Priceline", "Orbitz", "Trivago"
]
ota_channels = {
    "Booking.com": "Online",
    "Expedia": "Online",
    "Agoda": "Online",
    "MakeMyTrip": "Online",
    "Goibibo": "Online",
    "Airbnb": "Online",
    "Hotels.com": "Online",
    "Trip.com": "Online",
    "Traveloka": "Mobile App",
    "Cleartrip": "Online",
    "Yatra": "Online",
    "EaseMyTrip": "Online",
    "Priceline": "Online",
    "Orbitz": "Online",
    "Trivago": "Metasearch"
}

hotels_db = [
    {"Hotel_ID": "HTL-101", "Hotel_Name": "The Plaza Hotel", "Hotel_City": "New York", "Country": "USA", "Hotel_Rating": 4.8},
    {"Hotel_ID": "HTL-102", "Hotel_Name": "Ritz-Carlton", "Hotel_City": "Los Angeles", "Country": "USA", "Hotel_Rating": 4.7},
    {"Hotel_ID": "HTL-103", "Hotel_Name": "Mandarin Oriental", "Hotel_City": "London", "Country": "UK", "Hotel_Rating": 4.9},
    {"Hotel_ID": "HTL-104", "Hotel_Name": "Taj Mahal Palace", "Hotel_City": "Mumbai", "Country": "India", "Hotel_Rating": 4.9},
    {"Hotel_ID": "HTL-105", "Hotel_Name": "Burj Al Arab", "Hotel_City": "Dubai", "Country": "UAE", "Hotel_Rating": 5.0},
    {"Hotel_ID": "HTL-106", "Hotel_Name": "Park Hyatt", "Hotel_City": "Tokyo", "Country": "Japan", "Hotel_Rating": 4.8},
    {"Hotel_ID": "HTL-107", "Hotel_Name": "Shangri-La", "Hotel_City": "Toronto", "Country": "Canada", "Hotel_Rating": 4.6},
    {"Hotel_ID": "HTL-108", "Hotel_Name": "Sydney Harbour Marriott", "Hotel_City": "Sydney", "Country": "Australia", "Hotel_Rating": 4.5},
    {"Hotel_ID": "HTL-109", "Hotel_Name": "Hotel Ritz", "Hotel_City": "Paris", "Country": "France", "Hotel_Rating": 4.9},
    {"Hotel_ID": "HTL-110", "Hotel_Name": "Grand Hotel", "Hotel_City": "Stockholm", "Country": "Sweden", "Hotel_Rating": 4.4},
    {"Hotel_ID": "HTL-111", "Hotel_Name": "Marina Bay Sands", "Hotel_City": "Singapore", "Country": "Singapore", "Hotel_Rating": 4.8},
    {"Hotel_ID": "HTL-112", "Hotel_Name": "Hotel Adlon Kempinski", "Hotel_City": "Berlin", "Country": "Germany", "Hotel_Rating": 4.7},
    {"Hotel_ID": "HTL-113", "Hotel_Name": "Rome Cavalieri", "Hotel_City": "Rome", "Country": "Italy", "Hotel_Rating": 4.6},
    {"Hotel_ID": "HTL-114", "Hotel_Name": "Copacabana Palace", "Hotel_City": "Rio de Janeiro", "Country": "Brazil", "Hotel_Rating": 4.7},
    {"Hotel_ID": "HTL-115", "Hotel_Name": "Table Mountain Inn", "Hotel_City": "Cape Town", "Country": "South Africa", "Hotel_Rating": 4.3},
    {"Hotel_ID": "HTL-116", "Hotel_Name": "The Peninsula", "Hotel_City": "Hong Kong", "Country": "Hong Kong", "Hotel_Rating": 4.8},
    {"Hotel_ID": "HTL-117", "Hotel_Name": "W Barcelona", "Hotel_City": "Barcelona", "Country": "Spain", "Hotel_Rating": 4.5},
    {"Hotel_ID": "HTL-118", "Hotel_Name": "Fairmont Chateau", "Hotel_City": "Vancouver", "Country": "Canada", "Hotel_Rating": 4.6},
    {"Hotel_ID": "HTL-119", "Hotel_Name": "Oberoi Grand", "Hotel_City": "Kolkata", "Country": "India", "Hotel_Rating": 4.5},
    {"Hotel_ID": "HTL-120", "Hotel_Name": "InterContinental", "Hotel_City": "Geneva", "Country": "Switzerland", "Hotel_Rating": 4.4},
    {"Hotel_ID": "HTL-121", "Hotel_Name": "Sofitel Legend", "Hotel_City": "Amsterdam", "Country": "Netherlands", "Hotel_Rating": 4.7},
    {"Hotel_ID": "HTL-122", "Hotel_Name": "Four Seasons", "Hotel_City": "Bangkok", "Country": "Thailand", "Hotel_Rating": 4.8},
    {"Hotel_ID": "HTL-123", "Hotel_Name": "Atlantis The Palm", "Hotel_City": "Dubai", "Country": "UAE", "Hotel_Rating": 4.7},
    {"Hotel_ID": "HTL-124", "Hotel_Name": "The Savoy", "Hotel_City": "London", "Country": "UK", "Hotel_Rating": 4.8},
    {"Hotel_ID": "HTL-125", "Hotel_Name": "ITC Maurya", "Hotel_City": "New Delhi", "Country": "India", "Hotel_Rating": 4.6}
]

customer_origins = [
    {"Country": "USA", "State": "New York", "City": "New York"},
    {"Country": "USA", "State": "California", "City": "Los Angeles"},
    {"Country": "USA", "State": "Florida", "City": "Miami"},
    {"Country": "UK", "State": "England", "City": "London"},
    {"Country": "UK", "State": "Scotland", "City": "Edinburgh"},
    {"Country": "India", "State": "Maharashtra", "City": "Mumbai"},
    {"Country": "India", "State": "Delhi", "City": "New Delhi"},
    {"Country": "India", "State": "Karnataka", "City": "Bangalore"},
    {"Country": "France", "State": "Île-de-France", "City": "Paris"},
    {"Country": "France", "State": "Provence-Alpes-Côte d'Azur", "City": "Nice"},
    {"Country": "Japan", "State": "Tokyo", "City": "Tokyo"},
    {"Country": "Japan", "State": "Kyoto", "City": "Kyoto"},
    {"Country": "Canada", "State": "Ontario", "City": "Toronto"},
    {"Country": "Canada", "State": "British Columbia", "City": "Vancouver"},
    {"Country": "UAE", "State": "Dubai", "City": "Dubai"},
    {"Country": "Australia", "State": "New South Wales", "City": "Sydney"},
    {"Country": "Australia", "State": "Victoria", "City": "Melbourne"},
    {"Country": "Germany", "State": "Berlin", "City": "Berlin"},
    {"Country": "Germany", "State": "Bavaria", "City": "Munich"},
    {"Country": "Singapore", "State": "Central", "City": "Singapore"}
]

first_names = [
    "John", "Jane", "Michael", "Emily", "David", "Sarah", "James", "Jessica", "Robert", "Ashley",
    "William", "Amanda", "Joseph", "Melissa", "Christopher", "Stephanie", "Matthew", "Elizabeth",
    "Andrew", "Jennifer", "Ryan", "Nicole", "Nicholas", "Christine", "Jonathan", "Laura", "Daniel",
    "Rebecca", "Kevin", "Michelle", "Brian", "Kimberly", "George", "Cynthia", "Edward", "Angela"
]
last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
    "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
    "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez",
    "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott"
]

# Generate Customer Pool (1,500 customers to allow repeat bookings)
customer_pool = []
for i in range(1500):
    cust_id = f"CUST-{1000 + i + 1}"
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    name = f"{fn} {ln}"
    age = random.randint(18, 78)
    
    # Introduce messy ages in customer pool
    if random.random() < 0.005:  # 0.5% outliers
        age = random.choice([-5, 120, 150])
        
    gender = random.choice(["Male", "Female", "Non-binary"])
    # Introduce gender inconsistency
    if random.random() < 0.05:
        gender = random.choice(["M", "F", "male", "FEMALE", "U"])
        
    origin = random.choice(customer_origins)
    country = origin["Country"]
    state = origin["State"]
    city = origin["City"]
    
    email = f"{fn.lower()}.{ln.lower()}{random.randint(10,99)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])}"
    # Introduce messy email
    if random.random() < 0.01:
        email = f"{fn.lower()}{ln.lower()}gmail.com"  # missing @
        
    phone = f"+{random.randint(1,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
    # Introduce messy phone
    if random.random() < 0.01:
        phone = f"abc-{random.randint(100,999)}"
        
    loyalty = random.choices(["Standard", "Silver", "Gold", "Platinum"], weights=[0.55, 0.25, 0.12, 0.08])[0]
    # Introduce messy loyalty
    if random.random() < 0.03:
        loyalty = loyalty.lower()
        
    customer_pool.append({
        "Customer_ID": cust_id,
        "Customer_Name": name,
        "Age": age,
        "Gender": gender,
        "Country": country,
        "State": state,
        "City": city,
        "Email": email,
        "Phone": phone,
        "Loyalty_Status": loyalty
    })

# Now generate exactly 5900 unique bookings
bookings = []
start_date = datetime.date(2024, 1, 1)
end_date = datetime.date(2026, 6, 30)
date_range = (end_date - start_date).days

# Build a list of booking dates with seasonality (peaks in summer and winter)
booking_dates = []
for i in range(5900):
    # Seasonality weights based on month
    while True:
        r_days = random.randint(0, date_range)
        b_date = start_date + datetime.timedelta(days=r_days)
        m = b_date.month
        # Peak booking months: June(6), July(7), August(8), December(12)
        # Give higher probability to these months
        weight = 1.0
        if m in [6, 7, 8]:
            weight = 1.6
        elif m in [12]:
            weight = 1.5
        elif m in [1, 2]:
            weight = 0.8  # low season
            
        if random.random() < (weight / 1.6):
            booking_dates.append(b_date)
            break

booking_dates.sort()

# Pre-generate bookings
for idx, b_date in enumerate(booking_dates):
    booking_id = f"BKN-{10000 + idx + 1}"
    
    # Customer selection (skewed to allow frequent buyers)
    cust_idx = int(np.random.exponential(scale=300)) % len(customer_pool)
    cust = customer_pool[cust_idx]
    
    # Lead time (lognormal distribution)
    lead_time = int(np.random.lognormal(mean=2.8, sigma=1.0))
    lead_time = min(lead_time, 180) # Cap at 180 days
    
    # Outliers in lead time
    if random.random() < 0.003:
        lead_time = random.choice([-8, 999])
        
    checkin = b_date + datetime.timedelta(days=lead_time)
    
    # Room nights
    nights = int(random.choices([1, 2, 3, 4, 5, 6, 7, 10, 14], weights=[0.25, 0.35, 0.20, 0.10, 0.05, 0.02, 0.01, 0.01, 0.01])[0])
    checkout = checkin + datetime.timedelta(days=nights)
    
    # Hotel details
    hotel = random.choice(hotels_db)
    hotel_id = hotel["Hotel_ID"]
    hotel_name = hotel["Hotel_Name"]
    hotel_city = hotel["Hotel_City"]
    hotel_rating = hotel["Hotel_Rating"]
    
    # Room Type & Base Price
    room_type = random.choices(["Single", "Double", "Deluxe", "Suite", "Family"], weights=[0.25, 0.35, 0.20, 0.10, 0.10])[0]
    base_prices = {"Single": 75, "Double": 120, "Deluxe": 180, "Suite": 350, "Family": 200}
    hotel_multipliers = {
        "Burj Al Arab": 2.6, "The Plaza Hotel": 1.8, "Mandarin Oriental": 1.7, "Taj Mahal Palace": 1.5,
        "Marina Bay Sands": 1.6, "Hotel Ritz": 1.9, "The Savoy": 1.7, "Table Mountain Inn": 0.8
    }
    multiplier = hotel_multipliers.get(hotel_name, 1.0)
    room_price = float(np.round(base_prices[room_type] * multiplier * random.uniform(0.9, 1.1), 2))
    
    # Outliers in Room Price
    if random.random() < 0.003:
        room_price = random.choice([-150.00, 18500.00])
        
    num_rooms = random.choices([1, 2, 3, 4], weights=[0.85, 0.10, 0.04, 0.01])[0]
    
    # Occupancy
    adults = random.choices([1, 2, 3, 4], weights=[0.30, 0.55, 0.10, 0.05])[0]
    children = random.choices([0, 1, 2, 3], weights=[0.75, 0.15, 0.08, 0.02])[0]
    guests = adults + children
    
    # Booking Status (15% cancellations, 3% No-show, 82% Confirmed)
    booking_status = random.choices(["Confirmed", "Cancelled", "No-Show"], weights=[0.82, 0.15, 0.03])[0]
    
    cancellation_date = np.nan
    if booking_status == "Cancelled":
        # Cancel date must be between booking and checkin
        days_to_cancel = random.randint(0, max(0, lead_time - 1))
        cancellation_date = b_date + datetime.timedelta(days=days_to_cancel)
        
    # OTA Name & Details
    ota = random.choice(otas)
    booking_channel = ota_channels[ota]
    device_type = random.choices(["Desktop", "Mobile", "Tablet", "Smart TV"], weights=[0.40, 0.48, 0.10, 0.02])[0]
    
    # Financial details
    commission_rates = {
        "Booking.com": 0.15, "Expedia": 0.18, "Agoda": 0.12, "Airbnb": 0.10, "MakeMyTrip": 0.15,
        "Goibibo": 0.14, "Hotels.com": 0.16, "Trip.com": 0.15, "Traveloka": 0.12, "Cleartrip": 0.13,
        "Yatra": 0.15, "EaseMyTrip": 0.11, "Priceline": 0.15, "Orbitz": 0.16, "Trivago": 0.10
    }
    comm_rate = commission_rates[ota]
    
    discount_pct = random.choices([0.0, 0.05, 0.10, 0.15, 0.20, 0.25], weights=[0.50, 0.20, 0.15, 0.08, 0.05, 0.02])[0]
    
    # Calculate Gross and Net Revenue
    # Gross Revenue = (Room Price * Nights * Number of Rooms) * (1 - Discount)
    subtotal = float(room_price * nights * num_rooms)
    discount_amount = float(np.round(subtotal * discount_pct, 2))
    discounted_subtotal = subtotal - discount_amount
    taxes = float(np.round(discounted_subtotal * 0.12, 2)) # 12% tax rate
    
    gross_revenue = float(np.round(discounted_subtotal + taxes, 2))
    comm_amount = float(np.round(discounted_subtotal * comm_rate, 2))
    net_revenue = float(np.round(gross_revenue - comm_amount, 2))
    
    # In some records, introduce calculation errors
    if random.random() < 0.005:
        gross_revenue = gross_revenue - 50.0  # Incorrect math
        
    payment_method = random.choices(["Credit Card", "Debit Card", "PayPal", "Net Banking", "Cash", "Crypto"], weights=[0.45, 0.25, 0.15, 0.10, 0.04, 0.01])[0]
    coupon_code = "None"
    if discount_pct > 0:
        coupon_code = f"SAVE{int(discount_pct * 100)}"
        
    review_score = float(random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.08, 0.15, 0.32, 0.40])[0])
    # Introduce messy review scores
    if random.random() < 0.01:
        review_score = random.choice([0, 11, np.nan])
        
    # Season & weekday classification
    season = "Winter"
    if b_date.month in [3, 4, 5]:
        season = "Spring"
    elif b_date.month in [6, 7, 8]:
        season = "Summer"
    elif b_date.month in [9, 10, 11]:
        season = "Autumn"
        
    weekday_weekend = "Weekday" if b_date.weekday() < 5 else "Weekend"
    
    special_request = random.choices(["None", "Late Checkout", "Extra Bed", "Quiet Room", "High Floor", "Near Elevator"], weights=[0.60, 0.15, 0.10, 0.08, 0.05, 0.02])[0]
    
    # String format variations for dates in raw dataset (to make ETL interesting)
    b_date_str = b_date.strftime("%Y-%m-%d")
    c_date_str = checkin.strftime("%Y-%m-%d")
    co_date_str = checkout.strftime("%Y-%m-%d")
    
    date_format_choice = random.random()
    if date_format_choice < 0.15:
        b_date_str = b_date.strftime("%d/%m/%Y")
    elif date_format_choice < 0.30:
        b_date_str = b_date.strftime("%m-%d-%Y")
        
    date_format_choice_c = random.random()
    if date_format_choice_c < 0.15:
        c_date_str = checkin.strftime("%d/%m/%Y")
    elif date_format_choice_c < 0.30:
        c_date_str = checkin.strftime("%m-%d-%Y")
        
    cancel_date_str = ""
    if pd.notna(cancellation_date):
        cancel_date_str = cancellation_date.strftime("%Y-%m-%d")
        if random.random() < 0.15:
            cancel_date_str = cancellation_date.strftime("%d/%m/%Y")
            
    # String format for price
    room_price_str = str(room_price)
    if random.random() < 0.05:
        room_price_str = f"${room_price:,.2f}"
        
    # Introduce logical violations (Checkout_Date <= Checkin_Date)
    if random.random() < 0.002:
        co_date_str = c_date_str # Zero-night or negative checkout error
        
    bookings.append({
        "Booking_ID": booking_id,
        "Booking_Date": b_date_str,
        "Checkin_Date": c_date_str,
        "Checkout_Date": co_date_str,
        "Lead_Time": lead_time,
        "Customer_ID": cust["Customer_ID"],
        "Customer_Name": cust["Customer_Name"],
        "Age": cust["Age"],
        "Gender": cust["Gender"],
        "Country": cust["Country"],
        "State": cust["State"],
        "City": cust["City"],
        "Email": cust["Email"],
        "Phone": cust["Phone"],
        "OTA_Name": ota,
        "Booking_Channel": booking_channel,
        "Device_Type": device_type,
        "Hotel_ID": hotel_id,
        "Hotel_Name": hotel_name,
        "Hotel_City": hotel_city,
        "Hotel_Rating": hotel_rating,
        "Room_Type": room_type,
        "Room_Price": room_price_str,
        "Number_of_Rooms": num_rooms,
        "Guests": guests,
        "Adults": adults,
        "Children": children,
        "Nights": nights,
        "Booking_Status": booking_status,
        "Cancellation_Date": cancel_date_str,
        "Commission_Rate": comm_rate,
        "Commission_Amount": comm_amount,
        "Discount": discount_pct,
        "Taxes": taxes,
        "Gross_Revenue": gross_revenue,
        "Net_Revenue": net_revenue,
        "Payment_Method": payment_method,
        "Coupon_Code": coupon_code,
        "Loyalty_Status": cust["Loyalty_Status"],
        "Review_Score": review_score,
        "Season": season,
        "Weekday_Weekend": weekday_weekend,
        "Special_Request": special_request
    })

# Convert to DataFrame
df = pd.DataFrame(bookings)

# Duplicate exactly 100 random bookings to reach exactly 6,000 rows
# Pick 100 random indices from the 5900 bookings
duplicate_indices = random.sample(range(5900), 100)
duplicate_rows = df.iloc[duplicate_indices].copy()

# Concatenate to get exactly 6000 rows
df_raw = pd.concat([df, duplicate_rows], ignore_index=True)

# Randomize row order so duplicates are not stacked next to each other
df_raw = df_raw.sample(frac=1, random_state=42).reset_index(drop=True)

# Double check that we have exactly 6000 rows and 43 columns
assert len(df_raw) == 6000, f"Expected 6000 rows, got {len(df_raw)}"
assert len(df_raw.columns) == 43, f"Expected 43 columns, got {len(df_raw.columns)}"

# Save raw dataset
raw_path = os.path.join("Dataset", "ota_raw_dataset.csv")
df_raw.to_csv(raw_path, index=False)
print(f"Generated raw dataset: {raw_path} with shape {df_raw.shape}")
print(f"Number of columns: {len(df_raw.columns)}")
print(f"Unique Booking_IDs: {df_raw['Booking_ID'].nunique()}")
print(f"Duplicated Booking_IDs count: {df_raw['Booking_ID'].duplicated().sum()}")
