import pandas as pd
import datetime
import os

def build_dynamic_schedule():
    print("🚀 INITIALIZING DYNAMIC AI SCHEDULING ENGINE...")
    
    # Configuration
    MAX_DRIVERS = 80
    SHIFT_HOURS = 8
    
    # 1. Load Data
    try:
        trips_df = pd.read_csv('daily_manifests/manifest_tomorrow.csv')
    except Exception as e:
        print(f"❌ ERROR: Missing manifest_tomorrow.csv in daily_manifests/ folder - {e}")
        return

    # 2. Clean Manifest Data
    active_status = ['Assigned', 'VendorAccepted']
    if 'Leg Status' in trips_df.columns:
        trips_df = trips_df[trips_df['Leg Status'].isin(active_status)].copy()
    
    # Extract Zip
    if 'Start Zip' in trips_df.columns:
        trips_df['CleanZip'] = trips_df['Start Zip'].astype(str).str[:5]
    else:
        trips_df['CleanZip'] = "00000"

    # Extract Times
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    date_series = trips_df['Appt Date'] if 'Appt Date' in trips_df.columns else today_str
        
    trips_df['TBR_Str'] = trips_df['TBR time'].astype(str).str.strip()
    trips_df = trips_df[~trips_df['TBR_Str'].str.contains('nan|24:')]
    trips_df['PickupTime'] = pd.to_datetime(date_series + ' ' + trips_df['TBR_Str'], errors='coerce')
    trips_df = trips_df.dropna(subset=['PickupTime']).sort_values('PickupTime')

    assigned_trips = set()
    shifts = []

    # 3. Dynamic Shift Generation (Bin Packing)
    for index, base_trip in trips_df.iterrows():
        base_trip_id = base_trip['tripid w Leg']
        
        # If trip is already assigned or we hit the 80 driver cap, skip
        if base_trip_id in assigned_trips:
            continue
        if len(shifts) >= MAX_DRIVERS:
            break

        # Create a new driver shift anchored to this unassigned trip
        shift_start = base_trip['PickupTime'] - pd.Timedelta(minutes=15)
        shift_end = shift_start + pd.Timedelta(hours=SHIFT_HOURS)
        is_wc = int(base_trip['Showwheelchair']) if pd.notna(base_trip['Showwheelchair']) else 0
        territory = base_trip['Territory']
        
        driver_name = f"Driver {len(shifts) + 1} ({'WC' if is_wc else 'AMB'} | {territory})"
        
        current_shift = {
            "Driver": driver_name,
            "StartTime": shift_start,
            "EndTime": shift_end,
            "WC": is_wc,
            "Territory": territory,
            "CurrentTime": shift_start,
            "CurrentZip": base_trip['CleanZip'],
            "Trips": []
        }

        # Fill this 8-hour shift greedily
        terr_mask = trips_df['Territory'] == territory
        
        while current_shift['CurrentTime'] < current_shift['EndTime']:
            valid_mask = (~trips_df['tripid w Leg'].isin(assigned_trips)) & \
                         (trips_df['PickupTime'] <= current_shift['CurrentTime'] + pd.Timedelta(minutes=45)) & \
                         (trips_df['PickupTime'] >= current_shift['CurrentTime'] - pd.Timedelta(minutes=60)) & \
                         (trips_df['Showwheelchair'] <= current_shift['WC']) & terr_mask
            
            valid_trips = trips_df[valid_mask]
            
            if valid_trips.empty:
                current_shift['CurrentTime'] += pd.Timedelta(minutes=15)
                continue
                
            best_trip = None
            best_score = -9999
            
            for _, trip in valid_trips.iterrows():
                deadhead = 5 if trip['CleanZip'] == current_shift['CurrentZip'] else 20
                arrival_time = current_shift['CurrentTime'] + pd.Timedelta(minutes=deadhead)
                
                # Compliance Constraints
                if str(trip['Leg']) == '1' and arrival_time > trip['PickupTime'] + pd.Timedelta(minutes=10):
                    continue
                if str(trip['Leg']) == '2' and arrival_time > trip['PickupTime'] + pd.Timedelta(minutes=55):
                    continue
                    
                # Score Logic
                score = 0
                if trip['CleanZip'] == current_shift['CurrentZip']: score += 50
                if str(trip['Leg']) == '2': score += 20
                
                wait_time = (trip['PickupTime'] - arrival_time).total_seconds() / 60
                if wait_time > 0: score -= wait_time
                
                if score > best_score:
                    best_score = score
                    best_trip = trip
                    best_arrival = arrival_time
                    
            if best_trip is None:
                current_shift['CurrentTime'] += pd.Timedelta(minutes=15)
                continue
                
            # Assign Trip
            trip_id = best_trip['tripid w Leg']
            actual_pickup = max(best_arrival, best_trip['PickupTime'])
            dist = float(best_trip['Distance Estimate']) if pd.notna(best_trip['Distance Estimate']) else 5.0
            trip_duration = (dist / 20.0) * 60
            dropoff_time = actual_pickup + pd.Timedelta(minutes=trip_duration)
            
            current_shift['Trips'].append({
                'TripID': trip_id,
                'Leg': best_trip['Leg'],
                'Pickup': actual_pickup.strftime('%H:%M'),
                'Dropoff': dropoff_time.strftime('%H:%M'),
                'Zip': best_trip['CleanZip'],
                'Distance': dist,
                'Purpose': str(best_trip['Purpose Description'])[:25]
            })
            
            assigned_trips.add(trip_id)
            current_shift['CurrentTime'] = dropoff_time
            current_shift['CurrentZip'] = best_trip['CleanZip']
            
        # Only add the shift if it actually got assigned trips
        if len(current_shift['Trips']) > 0:
            shifts.append(current_shift)

    # 4. Output Results
    os.makedirs('reports', exist_ok=True)
    
    unassigned_count = len(trips_df) - len(assigned_trips)
    
    with open('reports/dynamic_optimized_schedule.md', 'w') as f:
        f.write("# 🗺️ Dynamic AI Dispatch Manifest\n\n")
        f.write(f"**Total Trips on Manifest:** {len(trips_df)}\n")
        f.write(f"**Trips Successfully Assigned:** {len(assigned_trips)}\n")
        f.write(f"**Trips Unassigned (Need 3rd Party/Lyft):** {unassigned_count}\n")
        f.write(f"**Total Drivers Utilized:** {len(shifts)} / {MAX_DRIVERS}\n\n")
        
        for s in shifts:
            f.write(f"### 🚙 {s['Driver']} | {s['StartTime'].strftime('%H:%M')} - {s['EndTime'].strftime('%H:%M')}\n")
            f.write(f"*Total Trips: {len(s['Trips'])}*\n\n")
            f.write("| Time Window | Leg | Zip | Dist | Purpose |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for t in s['Trips']:
                f.write(f"| {t['Pickup']} -> {t['Dropoff']} | Leg {t['Leg']} | {t['Zip']} | {t['Distance']} mi | {t['Purpose']} |\n")
            f.write("\n---\n")
            
    print(f"✅ Schedule generated! Assigned {len(assigned_trips)} trips using {len(shifts)} drivers.")

if __name__ == "__main__":
    build_dynamic_schedule()
