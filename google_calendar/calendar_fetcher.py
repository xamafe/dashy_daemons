#!/usr/bin/env python3
"""
Dashy Calendar Data Feed Generator
Fetches Google Calendar events and creates JSON feed for Dashy data-feed widget

Author: Markus
License: MIT
Repository: https://github.com/xamafe/dashy_deamons
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Check for required packages
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', '/opt/dashy/public/calendar-feed.json')

def load_calendar_config():
    """Load calendar configuration from environment variables"""
    calendars = {}
    
    # Load calendars from environment (CALENDAR_1, CALENDAR_2, etc.)
    i = 1
    while True:
        calendar_id = os.getenv(f'CALENDAR_{i}_ID')
        calendar_name = os.getenv(f'CALENDAR_{i}_NAME')
        
        if not calendar_id or not calendar_name:
            break
            
        calendars[calendar_id] = calendar_name
        i += 1
    
    if not calendars:
        print("❌ No calendars configured!")
        print("Please set CALENDAR_1_ID and CALENDAR_1_NAME in your .env file")
        sys.exit(1)
    
    return calendars

def authenticate():
    """Authenticate with Google Calendar API"""
    print("🔐 Authenticating with Google Calendar API...")
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("Please download your Google API credentials and save as credentials.json")
        print("Get them from: https://console.cloud.google.com/")
        sys.exit(1)
    
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("✅ Authentication successful!")
    
    return build('calendar', 'v3', credentials=creds)

def get_theme_color(calendar_name):
    """Return theme-matching colors for different calendars"""
    # You can customize these colors to match your Dashy theme
    default_colors = {
        'My Calendar': '#4299e1',      # Blue
        "Wife's Calendar": '#ed8936',   # Orange  
        'Our Calendar': '#38b2ac',      # Teal
        'Family Calendar': '#68d391',   # Green
        'Work Calendar': '#9f7aea',     # Purple
        'Kids Calendar': '#f56565'      # Red
    }
    
    # Allow color override from environment
    color_key = calendar_name.upper().replace(' ', '_').replace("'", '') + '_COLOR'
    env_color = os.getenv(color_key)
    
    return env_color or default_colors.get(calendar_name, '#a0aec0')

def format_event_time(event):
    """Format event time for display"""
    start = event['start']
    
    # Check if it's an all-day event
    if 'date' in start:
        return "All Day", True
    
    # Parse datetime
    try:
        dt_string = start['dateTime']
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime('%H:%M'), False
    except Exception as e:
        print(f"⚠️  Error parsing time for event '{event.get('summary', 'Unknown')}': {e}")
        return "Time TBD", False

def fetch_calendar_events(service, calendar_id, calendar_name):
    """Fetch today's events from a specific calendar"""
    print(f"📅 Fetching events from: {calendar_name}")
    
    # Get today's date range
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime',
            maxResults=50  # Limit to avoid too many events
        ).execute()
        
        events = events_result.get('items', [])
        print(f"   Found {len(events)} events")
        
        formatted_events = []
        for event in events:
            time_str, is_all_day = format_event_time(event)
            
            formatted_events.append({
                'label': event.get('summary', 'No Title'),
                'value': time_str,
                'unit': calendar_name,
                'color': get_theme_color(calendar_name),
                'is_all_day': is_all_day,
                'start_time': event['start'].get('dateTime', event['start'].get('date')),
                'location': event.get('location', ''),
                'description': event.get('description', '')[:100] + '...' if event.get('description', '') else ''
            })
        
        return formatted_events
        
    except Exception as e:
        print(f"❌ Error fetching calendar '{calendar_name}': {e}")
        return []

def generate_calendar_feed():
    """Main function to generate the calendar data feed"""
    print("🚀 Starting Dashy Calendar Feed Generator")
    print(f"📁 Output file: {OUTPUT_FILE}")
    
    # Load configuration
    calendars = load_calendar_config()
    print(f"📋 Configured calendars: {list(calendars.values())}")
    
    # Authenticate
    service = authenticate()
    
    # Fetch all events
    all_events = []
    for calendar_id, calendar_name in calendars.items():
        events = fetch_calendar_events(service, calendar_id, calendar_name)
        all_events.extend(events)
    
    # Sort events: all-day first, then by time
    all_events.sort(key=lambda x: (not x['is_all_day'], x['start_time']))
    
    # Create data feed structure for Dashy
    now = datetime.now()
    feed_data = {
        "title": "Heutige Termine",
        "subtitle": now.strftime("%A, %B %d, %Y"),
        "items": [
            {
                "label": event['label'],
                "value": event['value'],
                "unit": event['unit'],
                "color": event['color']
            }
            for event in all_events
        ],
        "total": len(all_events),
        "lastUpdated": now.isoformat() + 'Z'
    }
    
    # Ensure output directory exists
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(feed_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Successfully generated calendar feed with {len(all_events)} events")
        print(f"📄 Saved to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        generate_calendar_feed()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)