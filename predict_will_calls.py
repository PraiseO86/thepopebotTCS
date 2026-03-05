import pandas as pd
import datetime

def analyze_statewide_capacity():
    print("--- 🧠 STATEWIDE NEMT WILL-CALL PREDICTOR ---")
    
    # 1. Load the Historical Memory
    try:
        df = pd.read_csv('will_call_history.csv')
    except FileNotFoundError:
        print("❌ ERROR: Could not find will_call_history.csv")
        return

    # 2. Clean the Timestamp
    df['Request Time'] = pd.to_datetime(df['Return Ride Request Time'], format='%I:%M %p', errors='coerce').dt.time
    df = df.dropna(subset=['Request Time', 'Territory'])
    df['Call Hour'] = df['Request Time'].apply(lambda x: x.hour)

    # 3. Identify the Top 5 Busiest Territories in the State
    top_territories = df['Territory'].value_counts().head(5).index

    for territory in top_territories:
        print(f"\n========================================")
        print(f"📍 REGION: {territory.strip()}")
        print(f"========================================")
        
        terr_df = df[df['Territory'] == territory]
        
        # Find the top 3 busiest facilities in THIS specific territory
        top_facilities = terr_df['Pickup_address'].value_counts().head(3)
        
        for facility, count in top_facilities.items():
            # Skip random residential addresses or one-off trips (e.g., less than 20 historical trips)
            if count < 20: 
                continue
                
            print(f"\n🏥 Facility: {facility} (Historical Returns: {count})")
            
            fac_df = terr_df[terr_df['Pickup_address'] == facility]
            
            # Calculate the busiest hour of the day
            busiest_hour = fac_df['Call Hour'].mode()[0]
            
            # Format the hour nicely (e.g., 14 -> 2:00 PM)
            surge_time_start = datetime.time(busiest_hour, 0).strftime('%I:%M %p')
            surge_time_end = datetime.time((busiest_hour + 1) % 24, 0).strftime('%I:%M %p')
            
            # Check Wheelchair vs Ambulatory Demand
            wc_demand = fac_df['WheelChairYN'].value_counts(normalize=True).get('Y', 0) * 100
            
            print(f"   ⚠️ SURGE WINDOW: {surge_time_start} - {surge_time_end}")
            print(f"   ♿ WC Capacity Needed: {wc_demand:.1f}%")
            print(f"   📋 ACTION: Protect the 1-hour window for {facility} starting at {surge_time_start}.")

if __name__ == "__main__":
    analyze_statewide_capacity()
