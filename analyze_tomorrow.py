import pandas as pd
import datetime

def predict_tomorrow_surge():
    print("--- 🎯 TACTICAL WILL-CALL FORECAST FOR TOMORROW ---")

    # 1. Load Data
    try:
        history_df = pd.read_csv('brain/will_call_history.csv')
        tomorrow_df = pd.read_csv('daily_manifests/manifest_tomorrow.csv')
    except FileNotFoundError as e:
        print(f"❌ ERROR: Missing data file - {e}")
        return

    # 2. Clean Tomorrow's Manifest (Filter out cancellations)
    active_status = ['Assigned', 'VendorAccepted']
    tomorrow_df = tomorrow_df[tomorrow_df['Leg Status'].isin(active_status)]
    
    # Standardize the Route Genie address format to match the historical memory
    # Converts "2626 E 46th St , Indianapolis, In 46205" -> "2626 E 46th St"
    tomorrow_df['Clean_Address'] = tomorrow_df['Pickup Address'].astype(str).apply(lambda x: x.split(',')[0].strip())
    
    # Count total volume per facility tomorrow
    tomorrow_volume = tomorrow_df['Clean_Address'].value_counts()
    
    # 3. Clean Historical Data
    history_df['Request Time'] = pd.to_datetime(history_df['Return Ride Request Time'], format='%I:%M %p', errors='coerce').dt.time
    history_df = history_df.dropna(subset=['Request Time'])
    history_df['Call Hour'] = history_df['Request Time'].apply(lambda x: x.hour)

    # 4. Cross-Reference and Generate Tactical Insights
    print("\n🚨 CRITICAL SURGE WARNINGS (3+ Drop-offs) 🚨")
    found_surge = False
    
    for facility, count in tomorrow_volume.items():
        if count >= 3:
            # Look up this exact facility in the historical blueprint
            historical_data = history_df[history_df['Pickup_address'].str.lower() == facility.lower()]
            
            if not historical_data.empty:
                found_surge = True
                
                # Calculate Historical Peak
                busiest_hour = historical_data['Call Hour'].mode()[0]
                surge_start = datetime.time(busiest_hour, 0).strftime('%I:%M %p')
                surge_end = datetime.time((busiest_hour + 1) % 24, 0).strftime('%I:%M %p')
                
                # Calculate Wheelchair needs explicitly for TOMORROW
                wc_count = tomorrow_df[(tomorrow_df['Clean_Address'] == facility) & (tomorrow_df['Showwheelchair'] == 1)].shape[0]
                ambulatory_count = count - wc_count
                
                print(f"\n🏥 FACILITY: {facility}")
                print(f"   * Tomorrow's Volume: {count} patients scheduled for return.")
                print(f"   * Predicted Chaos Window: {surge_start} - {surge_end}")
                print(f"   * Asset Requirement: {wc_count} Wheelchair | {ambulatory_count} Ambulatory")
                print(f"   * ACTION: Pre-position assets by {surge_start} to secure the 1-hour contract window.")

    if not found_surge:
        print("\n✅ Coast is clear. No major multi-load surges detected for tomorrow.")

if __name__ == "__main__":
    predict_tomorrow_surge()
