#!/usr/bin/env python3
"""
Google Analytics 4 Android Version Distribution Fetcher
Pulls active users by Android version for Android devices in the last 30 days
"""

import csv
import os
from datetime import datetime
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    Filter,
)
from google.oauth2 import service_account
from google.auth import default

# Configuration
USE_SERVICE_ACCOUNT = False  # Set to True to use service account, False to use personal account
SERVICE_ACCOUNT_FILE = "../send-push-notificatation/cmd/service-account.json"
PROPERTY_ID = "1234567890"  # GA4 Property ID
OUTPUT_CSV = "android_versions_report.csv"

def fetch_android_versions(property_id: str, credentials_path: str = None, use_service_account: bool = False):
    """
    Fetch active users by Android version for Android devices from Google Analytics 4
    
    Args:
        property_id: GA4 Property ID (numeric)
        credentials_path: Path to service account JSON file (only needed if use_service_account=True)
        use_service_account: If True, use service account. If False, use personal account (ADC)
    
    Returns:
        List of dictionaries containing the report data
    """
    # Initialize credentials
    if use_service_account:
        print(f"🔑 Using service account: {credentials_path}")
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
    else:
        print("🔑 Using personal account (Application Default Credentials)")
        credentials, project = default(scopes=["https://www.googleapis.com/auth/analytics.readonly"])
    
    # Initialize the client
    client = BetaAnalyticsDataClient(credentials=credentials)
    
    # Build filter for Android devices
    android_filter = FilterExpression(
        filter=Filter(
            field_name="operatingSystem",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.CONTAINS,
                value="Android"
            )
        )
    )
    
    # Build the request
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="operatingSystemVersion"),
            Dimension(name="operatingSystem"),
            Dimension(name="deviceCategory"),
        ],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
        ],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        dimension_filter=android_filter,
    )
    
    # Run the report
    print(f"Fetching Android version data from GA4 Property: {property_id}")
    response = client.run_report(request)
    
    # Parse the response
    results = []
    for row in response.rows:
        os_version = row.dimension_values[0].value
        operating_system = row.dimension_values[1].value
        device_category = row.dimension_values[2].value
        active_users = row.metric_values[0].value
        new_users = row.metric_values[1].value
        sessions = row.metric_values[2].value
        
        results.append({
            'os_version': os_version,
            'operating_system': operating_system,
            'device_category': device_category,
            'active_users': active_users,
            'new_users': new_users,
            'sessions': sessions
        })
    
    # Sort by active users (descending)
    results.sort(key=lambda x: int(x['active_users']), reverse=True)
    
    return results

def save_to_csv(data: list, output_file: str, property_id: str):
    """
    Save the report data to a CSV file in simplified format
    
    Args:
        data: List of dictionaries with report data
        output_file: Output CSV file path
        property_id: GA4 Property ID for header
    """
    if not data:
        print("No data to save!")
        return
    
    # Calculate grand total
    grand_total = sum(int(row['active_users']) for row in data)
    
    # Get date range for header
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
    
    # Write to CSV with header
    with open(output_file, 'w', newline='') as csvfile:
        # Write header comments
        csvfile.write("# ----------------------------------------\n")
        csvfile.write(f"# Property ID: {property_id}\n")
        csvfile.write("# Active OS Versions - Android Devices\n")
        csvfile.write(f"# {date_range}\n")
        csvfile.write("# ----------------------------------------\n")
        csvfile.write("\n")
        
        # Write CSV header
        writer = csv.writer(csvfile)
        writer.writerow(['OS version', 'Active users'])
        
        # Write grand total
        writer.writerow(['', grand_total, 'Grand total'])
        
        # Write data rows (only version and active users)
        for row in data:
            writer.writerow([row['os_version'], row['active_users']])
        
        # Write empty lines at the end
        writer.writerow([])
        writer.writerow([])
    
    print(f"✅ Data saved to {output_file}")
    print(f"   Total rows: {len(data)}")
    print(f"   Grand total: {grand_total:,} active users")

def print_summary(data: list):
    """Print a summary of the data"""
    if not data:
        return
    
    # Calculate totals
    total_active_users = sum(int(row['active_users']) for row in data)
    total_new_users = sum(int(row['new_users']) for row in data)
    total_sessions = sum(int(row['sessions']) for row in data)
    
    print("\n📊 Summary (Last 30 Days - Android Devices Only):")
    print("=" * 70)
    print(f"Total Active Users: {total_active_users:,}")
    print(f"Total New Users:    {total_new_users:,}")
    print(f"Total Sessions:     {total_sessions:,}")
    print("=" * 70)
    
    # Show top 10 Android versions
    print("\n🔝 Top 10 Android Versions by Active Users:")
    print("-" * 70)
    print(f"{'OS Version':<20} {'OS':<15} {'Active Users':<15} {'% Share':<10}")
    print("-" * 70)
    
    for i, row in enumerate(data[:10], 1):
        active_users = int(row['active_users'])
        percentage = (active_users / total_active_users * 100) if total_active_users > 0 else 0
        print(f"{row['os_version']:<20} {row['operating_system']:<15} {active_users:<15,} {percentage:>6.2f}%")
    
    print("-" * 70)
    
    # Group by major version (Android 14.x, 13.x, etc.)
    major_versions = {}
    for row in data:
        os_name = row['operating_system']
        os_version = row['os_version']
        
        # Extract major version (e.g., "14" from "14.0")
        if os_version and os_version != "(not set)":
            major = os_version.split('.')[0]
            # Handle special case where version might be just a number
            if major.isdigit():
                key = f"{os_name} {major}.x"
            else:
                key = f"{os_name} {os_version}"
        else:
            key = f"{os_name} (unknown)"
        
        if key not in major_versions:
            major_versions[key] = 0
        major_versions[key] += int(row['active_users'])
    
    # Sort by users
    sorted_major = sorted(major_versions.items(), key=lambda x: x[1], reverse=True)
    
    print("\n📈 Distribution by Major Version:")
    print("-" * 70)
    print(f"{'Version':<30} {'Active Users':<15} {'% Share':<10}")
    print("-" * 70)
    
    for version, users in sorted_major[:10]:
        percentage = (users / total_active_users * 100) if total_active_users > 0 else 0
        print(f"{version:<30} {users:<15,} {percentage:>6.2f}%")
    
    print("-" * 70)

def main():
    """Main execution function"""
    print("=" * 70)
    print("Google Analytics 4 - Android Version Distribution Report")
    print("Platform: Android | Period: Last 30 Days")
    print("=" * 70)
    print()
    
    # Check authentication setup
    if USE_SERVICE_ACCOUNT:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"❌ Error: Service account file not found: {SERVICE_ACCOUNT_FILE}")
            print("   Please ensure the service account JSON file exists.")
            return
    else:
        print("💡 Using personal account authentication")
        print("   Make sure you've run: gcloud auth application-default login")
        print()
    
    # Check if property ID is configured
    if PROPERTY_ID == "YOUR_GA4_PROPERTY_ID":
        print("❌ Error: Please configure your GA4 Property ID")
        print("   Edit this script and replace PROPERTY_ID with your numeric GA4 Property ID")
        return
    
    try:
        # Fetch data
        data = fetch_android_versions(PROPERTY_ID, SERVICE_ACCOUNT_FILE, USE_SERVICE_ACCOUNT)
        
        if not data:
            print("⚠️  No data found for Android devices in the last 30 days.")
            print("   This could mean:")
            print("   - No Android device traffic in this period")
            print("   - Property ID is incorrect")
            print("   - Your account doesn't have access to this property")
            return
        
        # Save to CSV
        save_to_csv(data, OUTPUT_CSV, PROPERTY_ID)
        
        # Print summary
        print_summary(data)
        
        print(f"\n✨ Complete! Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        if USE_SERVICE_ACCOUNT:
            print("Common issues:")
            print("  - Service account doesn't have access to GA4 property")
            print("  - Wrong Property ID")
            print("  - Google Analytics Data API not enabled in Google Cloud Console")
        else:
            print("Common issues:")
            print("  - Run: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform")
            print("  - Wrong Property ID")
            print("  - Your account doesn't have access to the GA4 property")
            print("  - Google Analytics Data API not enabled in Google Cloud Console")

if __name__ == "__main__":
    main()

