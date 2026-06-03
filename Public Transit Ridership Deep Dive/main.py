import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta

# --- Configuration ---
DATA_DIR = 'data'
REPORTS_DIR = 'reports'
DATA_FILE = os.path.join(DATA_DIR, 'transit_ridership_data.csv')

# --- 1. Synthetic Data Generation ---
def generate_synthetic_data(num_records=10000, start_date='2023-01-01', end_date='2023-12-31'):
    print("Generating synthetic public transit ridership data...")

    # Generate hourly timestamps for a year, filtered to common operational hours
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    dates = dates[(dates.hour >= 5) | (dates.hour <= 1)] # 5 AM to 1 AM next day

    num_rows = len(dates)

    data = {
        'timestamp': dates,
        'date': dates.date,
        'time': dates.time,
        'hour_of_day': dates.hour,
        'day_of_week': dates.day_name(),
        'weekday': dates.weekday < 5, # True for Mon-Fri
        'month': dates.month_name(),
        'route_id': np.random.choice([f'RT{i:02d}' for i in range(1, 21)], size=num_rows), # 20 routes
        'stop_id': np.random.choice([f'STOP{i:03d}' for i in range(1, 51)], size=num_rows), # 50 stops
        'weather_condition': np.random.choice(['Clear', 'Cloudy', 'Rain', 'Snow', 'Fog'], size=num_rows, p=[0.5, 0.25, 0.15, 0.05, 0.05]),
        'event_nearby': np.random.choice(['None', 'Concert', 'Sport Event', 'Holiday', 'Local Festival'], size=num_rows, p=[0.75, 0.08, 0.08, 0.05, 0.04])
    }

    df = pd.DataFrame(data)

    # Simulate base ridership
    base_riders = np.random.randint(5, 50, size=num_rows)

    # Adjust for hour of day (peak hours)
    peak_hours_morning = (df['hour_of_day'] >= 7) & (df['hour_of_day'] <= 9)
    peak_hours_evening = (df['hour_of_day'] >= 16) & (df['hour_of_day'] <= 19)
    df.loc[peak_hours_morning | peak_hours_evening, 'riders_multiplier'] = 2.5 # Peak ridership
    df.loc[~(peak_hours_morning | peak_hours_evening), 'riders_multiplier'] = 1.0 # Off-peak

    # Adjust for weekday vs. weekend
    df.loc[df['weekday'] == True, 'weekday_multiplier'] = 1.2 # Weekdays generally higher
    df.loc[df['weekday'] == False, 'weekday_multiplier'] = 0.8 # Weekends lower

    # Adjust for weather
    weather_multiplier = {
        'Clear': 1.1, 'Cloudy': 1.0, 'Rain': 0.8, 'Snow': 0.6, 'Fog': 0.9
    }
    df['weather_multiplier'] = df['weather_condition'].map(weather_multiplier)

    # Adjust for events
    event_multiplier = {
        'None': 1.0, 'Concert': 1.8, 'Sport Event': 2.0, 'Holiday': 0.7, 'Local Festival': 1.5
    }
    df['event_multiplier'] = df['event_nearby'].map(event_multiplier)

    # Calculate riders_on with multipliers and some noise
    df['riders_on'] = (base_riders * df['riders_multiplier'] * df['weekday_multiplier'] * df['weather_multiplier'] * df['event_multiplier'] + np.random.randint(-10, 10, size=num_rows)).astype(int)
    df['riders_on'] = df['riders_on'].apply(lambda x: max(1, x)) # Ensure at least 1 rider

    # Riders off are slightly correlated with riders on, but with variance
    df['riders_off'] = (df['riders_on'] * np.random.uniform(0.8, 1.2, size=num_rows)).astype(int)
    df['riders_off'] = df['riders_off'].apply(lambda x: max(0, x)) # Ensure non-negative

    df['total_riders'] = df['riders_on'] + df['riders_off']

    # Clean up temporary columns
    df = df.drop(columns=['riders_multiplier', 'weekday_multiplier', 'weather_multiplier', 'event_multiplier'])

    print(f"Generated {len(df)} records.")
    return df

# --- 2. Data Loading and Preprocessing ---
def load_data(file_path):
    if not os.path.exists(file_path):
        print(f"Data file not found at {file_path}. Generating new data...")
        df = generate_synthetic_data()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False)
        print(f"Synthetic data saved to {file_path}")
    else:
        print(f"Loading data from {file_path}...")
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = pd.to_datetime(df['date'])
        print(f"Loaded {len(df)} records.")
    return df

# --- 3. Deep Dive Analysis and Visualization ---
def perform_analysis(df):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    print("\nStarting deep dive analysis and visualization...")

    # Set style for plots
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 7)
    plt.rcParams['font.size'] = 10

    # Overall Ridership Trends (Daily)
    print("1. Analyzing overall daily ridership trends...")
    daily_ridership = df.groupby(df['date'].dt.date)['total_riders'].sum().reset_index()
    daily_ridership['date'] = pd.to_datetime(daily_ridership['date'])
    plt.figure(figsize=(15, 6))
    sns.lineplot(x='date', y='total_riders', data=daily_ridership)
    plt.title('Daily Total Transit Ridership Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Ridership')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'daily_ridership_trend.png'))
    plt.close()

    # Ridership by Day of Week
    print("2. Analyzing ridership by day of week...")
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ridership_by_day = df.groupby('day_of_week')['total_riders'].sum().reindex(day_order).reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='day_of_week', y='total_riders', data=ridership_by_day, palette='viridis')
    plt.title('Total Ridership by Day of Week')
    plt.xlabel('Day of Week')
    plt.ylabel('Total Ridership')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'ridership_by_day_of_week.png'))
    plt.close()

    # Ridership by Hour of Day
    print("3. Analyzing ridership by hour of day...")
    ridership_by_hour = df.groupby('hour_of_day')['total_riders'].sum().reset_index()
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='hour_of_day', y='total_riders', data=ridership_by_hour, marker='o', color='purple')
    plt.title('Total Ridership by Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Total Ridership')
    plt.xticks(range(0, 24)) # Ensure all hours are displayed
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'ridership_by_hour_of_day.png'))
    plt.close()

    # Ridership by Day of Week & Hour (Heatmap)
    print("4. Analyzing ridership by day of week and hour (heatmap)...")
    ridership_heatmap = df.groupby(['day_of_week', 'hour_of_day'])['total_riders'].sum().unstack()
    ridership_heatmap = ridership_heatmap.reindex(day_order) # Ensure correct day order
    plt.figure(figsize=(14, 8))
    sns.heatmap(ridership_heatmap, cmap='YlGnBu', fmt=".0f", linewidths=.5, linecolor='lightgray')
    plt.title('Ridership Heatmap: Day of Week vs. Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Day of Week')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'ridership_heatmap_day_hour.png'))
    plt.close()

    # Top N Routes by Ridership
    N_routes = 10
    print(f"5. Analyzing top {N_routes} routes by ridership...")
    ridership_by_route = df.groupby('route_id')['total_riders'].sum().nlargest(N_routes).reset_index()
    plt.figure(figsize=(12, 6))
    sns.barplot(x='route_id', y='total_riders', data=ridership_by_route, palette='plasma')
    plt.title(f'Top {N_routes} Transit Routes by Total Ridership')
    plt.xlabel('Route ID')
    plt.ylabel('Total Ridership')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, f'top_{N_routes}_routes_ridership.png'))
    plt.close()

    # Ridership by Weather Condition
    print("6. Analyzing ridership by weather condition...")
    ridership_by_weather = df.groupby('weather_condition')['total_riders'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='weather_condition', y='total_riders', data=ridership_by_weather.sort_values(by='total_riders', ascending=False), palette='coolwarm')
    plt.title('Average Ridership by Weather Condition')
    plt.xlabel('Weather Condition')
    plt.ylabel('Average Total Ridership')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'ridership_by_weather_condition.png'))
    plt.close()

    # Ridership by Event Nearby
    print("7. Analyzing ridership by nearby events...")
    ridership_by_event = df.groupby('event_nearby')['total_riders'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='event_nearby', y='total_riders', data=ridership_by_event.sort_values(by='total_riders', ascending=False), palette='rocket')
    plt.title('Average Ridership by Nearby Event')
    plt.xlabel('Event Nearby')
    plt.ylabel('Average Total Ridership')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'ridership_by_event_nearby.png'))
    plt.close()

    # Correlation Matrix (example, limited numerical features)
    print("8. Displaying a simple correlation matrix...")
    numeric_df = df[['riders_on', 'riders_off', 'total_riders', 'hour_of_day']].copy()
    # Add a numerical representation for day of week for correlation
    numeric_df['day_of_week_num'] = df['timestamp'].dt.dayofweek
    plt.figure(figsize=(8, 6))
    sns.heatmap(numeric_df.corr(numeric_only=True), annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Matrix of Ridership Metrics and Time Features')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, 'correlation_matrix.png'))
    plt.close()

    print(f"\nAnalysis complete. Reports saved to '{REPORTS_DIR}' directory.")

# --- Main Execution ---
def main():
    print("--- Public Transit Ridership Deep Dive ---")

    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    df = load_data(DATA_FILE)

    if df is not None and not df.empty:
        perform_analysis(df)
    else:
        print("No data available for analysis.")

if __name__ == "__main__":
    main()
