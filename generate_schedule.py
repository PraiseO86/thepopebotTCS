import pandas as pd
import datetime
import os

def build_schedule():
    print("🚀 INITIALIZING AI SCHEDULING ENGINE...")
    
    # 1. Load Data
    try:
        trips_df = pd.read_csv('daily_manifests/manifest_tomorrow.csv')
        roster_df = pd.read_csv('daily_manifests/driver_roster.csv')
    except Exception as e:
        print(f"❌ ERROR: Missing manifest or roster file - {e}")
        return

    # 2. Clean Manifest Data
    # Keep only active trips
    active_status = ['Assigned', 'VendorAccepted']
    trips_df = trips_df[trips_df['Leg Status'].isin(active_status)].copy()
    
    # Extract clean Zip Code from the Address or Start Zip column
    if 'Start Zip' in trips_df.columns:
        trips_df['CleanZip'] = trips_df['Start Zip'].astype(str).str[:5]
    else:
        trips_df['CleanZip'] = "00000"

    # Convert times
    today_str = datetime.date.today().strftime('%Y-%m-%d') # Default to today if date parsing fails
    if 'Appt Date' in trips_df.columns:
        date_series = trips_df['Appt Date']
    else:
        date_series = today_str
        
    trips_df['TBR_Str'] = trips_df['TBR time'].astype(str).str.strip()
    trips_df = trips_df[~trips_df['TBR_Str'].str.contains('nan|24:')]
    trips_df['PickupTime'] = pd.to_datetime(date_series + ' ' + trips_df['TBR_Str'], errors='coerce')
    trips_df = trips_df.dropna(subset=['PickupTime']).sort_values('PickupTime')

    # 3. Setup Shifts from Roster
    shifts = []
    base_date = trips_df['PickupTime'].dt.strftime('%Y-%m-%d').iloc[0] # Get the date of tomorrow's manifest
    
    for _, row in roster_df.iterrows():
        shifts.append({
            "Driver": row['DriverName'],
            "StartTime": pd.to_datetime(f"{base_date} {row['ShiftStart']}"),
            "EndTime": pd.to_datetime(f"{base_date} {row['ShiftEnd']}"),
            "WC": int(row['IsWheelchair']),
            "CurrentTime": pd.to_datetime(f"{base_date} {row['ShiftStart']}"),
            "CurrentZip": str(row['StartZip'])[:5],
            "Territory": row['Territory'],
            "Trips": []
        })

    assigned_trips = set()

    # 4. The Greedy Routing Algorithm
    for s in shifts:
        terr_mask = trips_df['Territory'] == s['Territory']
        
        while s['CurrentTime'] < s['EndTime']:
            # Look ahead 45 minutes for valid trips
            valid_mask = (~trips_df['tripid w Leg'].isin(assigned_trips)) & \
                         (trips_df['PickupTime'] <= s['CurrentTime'] + pd.Timedelta(minutes=45)) & \
                         (trips_df['PickupTime'] >= s['CurrentTime'] - pd.Timedelta(minutes=60)) & \
                         (trips_df['Showwheelchair'] <= s['WC']) & terr_mask
            
            valid_trips = trips_df[valid_mask]
            
            if valid_trips.empty:
                s['CurrentTime'] += pd.Timedelta(minutes=15)
                continue
                
            best_trip = None
            best_score = -9999
            
            for _, trip in valid_trips.iterrows():
                # Deadhead calculation
                deadhead = 5 if trip['CleanZip'] == s['CurrentZip'] else 20
                arrival_time = s['CurrentTime'] + pd.Timedelta(minutes=deadhead)
                
                # Compliance Constraints (1 Hour Rule)
                if str(trip['Leg']) == '1' and arrival_time > trip['PickupTime'] + pd.Timedelta(minutes=10):
                    continue
                if str(trip['Leg']) == '2' and arrival_time > trip['PickupTime'] + pd.Timedelta(minutes=55):
                    continue
                    
                # Scoring (Prioritize same zip, less wait time)
                score = 0
                if trip['CleanZip'] == s['CurrentZip']: score += 50
                if str(trip['Leg']) == '2': score += 20
                
                wait_time = (trip['PickupTime'] - arrival_time).total_seconds() / 60
                if wait_time > 0: score -= wait_time
                
                if score > best_score:
                    best_score = score
                    best_trip = trip
                    best_arrival = arrival_time
                    
            if best_trip is None:
                s['CurrentTime'] += pd.Timedelta(minutes=15)
                continue
                
            # Assign the trip
            trip_id = best_trip['tripid w Leg']
            actual_pickup = max(best_arrival, best_trip['PickupTime'])
            dist = float(best_trip['Distance Estimate']) if pd.notna(best_trip['Distance Estimate']) else 5.0
            trip_duration = (dist / 20.0) * 60 # Assume 20 mph urban average
            dropoff_time = actual_pickup + pd.Timedelta(minutes=trip_duration)
            
            s['Trips'].append({
                'TripID': trip_id,
                'Leg': best_trip['Leg'],
                'Pickup': actual_pickup.strftime('%H:%M'),
                'Dropoff': dropoff_time.strftime('%H:%M'),
                'Zip': best_trip['CleanZip'],
                'Distance': dist,
                'Purpose': str(best_trip['Purpose Description'])[:25]
            })
            
            assigned_trips.add(trip_id)
            s['CurrentTime'] = dropoff_time
            s['CurrentZip'] = best_trip['CleanZip']

    # 5. Output Results
    os.makedirs('reports', exist_ok=True)
    
    with open('reports/optimized_schedule.md', 'w') as f:
        f.write("# 🗺️ AI Optimized Dispatch Manifest\n\n")
        f.write(f"**Total Trips Assigned:** {len(assigned_trips)}\n\n")
        
        for s in shifts:
            f.write(f"### 🚙 {s['Driver']} | {s['StartTime'].strftime('%H:%M')} - {s['EndTime'].strftime('%H:%M')}\n")
            f.write(f"*Total Trips: {len(s['Trips'])}*\n\n")
            f.write("| Time Window | Leg | Zip | Dist | Purpose |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for t in s['Trips']:
                f.write(f"| {t['Pickup']} -> {t['Dropoff']} | Leg {t['Leg']} | {t['Zip']} | {t['Distance']} mi | {t['Purpose']} |\n")
            f.write("\n---\n")
            
    print(f"✅ Schedule generated! Assigned {len(assigned_trips)} trips.")
    print("📄 Saved to reports/optimized_schedule.md")

if __name__ == "__main__":
    build_schedule()
