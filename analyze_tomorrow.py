import pandas as pd
import datetime

def predict_tomorrow_surge():
    print("--- 🎯 TACTICAL WILL-CALL FORECAST FOR TOMORROW ---")

    # 1. Load Data
    try:
        history_df = pd.read_csv('brain/will_call_history.csv')
        tomorrow_df = pd.read_csv('daily_manifests/manifest_tomorrow.csv')
    except Exception as e:
        print(f"❌ ERROR: Missing data file - {e}")
        return

    # 2. Clean Tomorrow's Manifest
    active_status = ['Assigned', 'VendorAccepted']
    tomorrow_df = tomorrow_df[tomorrow_df['Leg Status'].isin(active_status)]
    tomorrow_df['Clean_Address'] = tomorrow_df['Pickup Address'].astype(str).apply(lambda x: x.split(',')[0].strip())

    # 3. Clean Historical Data
    history_df['Request Time'] = pd.to_datetime(history_df['Return Ride Request Time'], format='%I:%M %p', errors='coerce').dt.time
    history_df = history_df.dropna(subset=['Request Time'])
    history_df['Call Hour'] = history_df['Request Time'].apply(lambda x: x.hour)

    # 4. Group by Territory and Generate Insights
    territories = tomorrow_df['Territory'].dropna().unique()
    found_any_surge = False

    for territory in sorted(territories):
        terr_df = tomorrow_df[tomorrow_df['Territory'] == territory]
        tomorrow_volume = terr_df['Clean_Address'].value_counts()
        
        # Only print the territory if it has facilities with 3+ drop-offs
        if not tomorrow_volume.empty and tomorrow_volume.max() >= 3:
            print(f"\n{'='*60}")
            print(f"📍 REGION: {territory.strip()}")
            print(f"{'='*60}")
            
            for facility, count in tomorrow_volume.items():
                if count >= 3:
                    historical_data = history_df[history_df['Pickup_address'].str.lower().str.strip() == facility.lower()]
                    
                    if not historical_data.empty:
                        found_any_surge = True
                        
                        # Find the 1-hour windows that capture ~70% of historical volume
                        hour_counts = historical_data['Call Hour'].value_counts(normalize=True).sort_values(ascending=False)
                        
                        cumulative_pct = 0
                        top_hours = []
                        for hr, pct in hour_counts.items():
                            top_hours.append((hr, pct))
                            cumulative_pct += pct
                            if cumulative_pct >= 0.70:
                                break
                                
                        # Format the hours for readability
                        surge_windows = []
                        for hr, pct in top_hours:
                            s_start = datetime.time(hr, 0).strftime('%I:%M %p')
                            s_end = datetime.time((hr + 1) % 24, 0).strftime('%I:%M %p')
                            surge_windows.append(f"{s_start}-{s_end} ({pct*100:.1f}%)")
                            
                        # Asset Breakdown
                        wc_count = terr_df[(terr_df['Clean_Address'] == facility) & (terr_df['Showwheelchair'] == 1)].shape[0]
                        amb_count = count - wc_count
                        
                        print(f"\n🏥 FACILITY: {facility}")
                        print(f"   * Tomorrow's Volume: {count} patients (WC: {wc_count} | AMB: {amb_count})")
                        print(f"   * Historical 70%+ Surge Windows: {', '.join(surge_windows)}")
                        print(f"   * Tomorrow's Scheduled Drop-offs (Use this to plan the sweeps):")
                        
                        # Detail the actual trips
                        fac_trips = terr_df[terr_df['Clean_Address'] == facility].sort_values('Appt Time')
                        for _, row in fac_trips.iterrows():
                            appt_time = row['Appt Time']
                            purpose = row['Purpose Description']
                            mco = row['MCO Name']
                            req_wc = "♿ WC" if row['Showwheelchair'] == 1 else "🚶 AMB"
                            
                            # Clean up the output string
                            print(f"      - Appt: {appt_time} | Type: {req_wc} | MCO: {mco} | Purpose: {purpose}")

    if not found_any_surge:
        print("\n✅ Coast is clear. No major multi-load surges detected for tomorrow.")

if __name__ == "__main__":
    predict_tomorrow_surge()
