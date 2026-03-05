import pandas as pd
import datetime

def analyze_will_call_capacity():
    print("--- 🧠 INITIALIZING NEMT WILL-CALL PREDICTOR ---")
    
    # 1. Load the Historical Memory
    try:
        df = pd.read_csv('brain/will_call_history.csv')
        print(f"✅ Loaded {len(df)} historical dispatch records.")
    except FileNotFoundError:
        print("❌ ERROR: Could not find brain/will_call_history.csv")
        return

    # 2. Clean the Timestamp (Convert "2:52 PM" to standard Time)
    df['Request Time'] = pd.to_datetime(df['Return Ride Request Time'], format='%I:%M %p', errors='coerce').dt.time
    
    # 3. Filter out bad time data
    df = df.dropna(subset=['Request Time'])
    
    # Extract the "Hour" of the day the call came in
    df['Call Hour'] = df['Request Time'].apply(lambda x: x.hour)

    # 4. Filter for Indianapolis / Pike Township (Marion County)
    # Using the Territory or County name provided in the dataset
    indy_df = df[df['Territory'].str.contains("INDIANAPOLIS", na=False, case=False)]
    
    print("\n--- 📍 INDIANAPOLIS METRO SURGE ANALYSIS ---")
    
    # Find the top 3 busiest facilities for Will-Calls
    top_facilities = indy_df['Pickup_address'].value_counts().head(3)
    
    for facility, count in top_facilities.items():
        print(f"\n🏥 Facility: {facility} (Total Historical Returns: {count})")
        
        fac_df = indy_df[indy_df['Pickup_address'] == facility]
        
        # Calculate the busiest hour of the day
        busiest_hour = fac_df['Call Hour'].mode()[0]
        
        # Format the hour nicely (e.g., 14 -> 2:00 PM)
        surge_time_start = datetime.time(busiest_hour, 0).strftime('%I:%M %p')
        surge_time_end = datetime.time((busiest_hour + 1) % 24, 0).strftime('%I:%M %p')
        
        # Check Wheelchair vs Ambulatory Demand at this facility
        wc_demand = fac_df['WheelChairYN'].value_counts(normalize=True).get('Y', 0) * 100
        
        print(f"   ⚠️ PEAK SURGE WINDOW: {surge_time_start} - {surge_time_end}")
        print(f"   ♿ Wheelchair Capacity Needed: {wc_demand:.1f}% of all trips.")
        print(f"   📋 ACTION: Pre-position assets near {facility} by {surge_time_start} to protect the 1-hour contractual obligation.")

if __name__ == "__main__":
    analyze_will_call_capacity()
