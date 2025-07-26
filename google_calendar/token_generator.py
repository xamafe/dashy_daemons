#!/usr/bin/env python3
"""
Desktop Authentication Helper for Dashy Calendar Feed
Run this on your LOCAL machine (with browser) to generate token.json
Then copy token.json to your server.

Usage:
1. Run this script on your desktop/laptop
2. Complete browser authentication 
3. Copy the generated token.json to your server
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_desktop():
    """Authenticate using desktop browser"""
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("Please download it from Google Cloud Console first.")
        return False
    
    print("🖥️  Desktop Authentication Helper")
    print("=" * 40)
    
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    
    try:
        print("🌐 Opening browser for authentication...")
        creds = flow.run_local_server(port=8080)
        
        # Save token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Authentication successful!")
        print("📁 Token saved to: token.json")
        print("\n📋 Next steps:")
        print("1. Copy token.json to your server")
        print("2. Place it in the same directory as your calendar script")
        print("3. Run the calendar script on your server")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == '__main__':
    authenticate_desktop()