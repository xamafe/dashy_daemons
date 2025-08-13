# Dashy Calendar Feed Generator

A Python script that fetches Google Calendar events and creates a JSON feed for Dashy's data-feed widget, providing seamless theme integration.

## Features

- 🔐 Secure credential management with `.env` files
- 📅 Multiple Google Calendar support
- 🎨 Theme-matching colors for different calendars
- ⚡ Automatic authentication and token refresh
- 📱 Perfect integration with Dashy's material-dark theme

## Example

<img width="546" height="510" alt="demo" src="https://github.com/user-attachments/assets/c5babe68-dea3-4b32-aa89-802ecd848b99" />

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Clone or download the script
cd /opt/dashy/

# Install Python requirements
pip install -r requirements.txt
```

### Step 2: Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Calendar API**
4. Create credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Desktop application"
   - Download the JSON file and save as `credentials.json`

### Step 3: Configuration

1. Copy the template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` with your calendar information:
   ```bash
   nano .env
   ```

3. Get your Calendar IDs:
   - Go to [Google Calendar](https://calendar.google.com)
   - Settings → Select your calendar → "Calendar ID"
   - Copy the ID (looks like `abc123@gmail.com`)
   - Add it to `.env`

4. Add ouput file:
   The output file has to be saved into the "user-data" directory. Otherwise the webserver will not recognize if it changes.

### Step 4: First Run

```bash
python3 calendar_feed.py
```

On first run:
- Browser will open for Google authentication (If you ran it on a server you have to copy some data...)
- Grant calendar read permissions 
- Token will be saved for future runs 

### Step 5: Add to Dashy

Add the PART_conf.yml to your `conf.yml`

### Step 6: Automation

Add a cron job to update every 15 minutes:

```bash
crontab -e

# Add this line:
*/15 * * * * cd /opt/dashy && python3 calendar_feed.py
```

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CALENDAR_1_ID` | First calendar ID | `you@gmail.com` |
| `CALENDAR_1_NAME` | Display name | `My Calendar` |
| `OUTPUT_FILE` | JSON output path | `/opt/dashy/public/calendar-feed.json` |

### Custom Colors

Override default colors by setting:
```bash
MY_CALENDAR_COLOR=#4299e1
WIFES_CALENDAR_COLOR=#ed8936
```

## Troubleshooting

### Debians python packeges are too old
- install python3-venv
- create a virtual environment
- add it to the cronjob

### Authentication Issues
- Delete `token.json` and run again
- Check `credentials.json` is valid
- Verify Calendar API is enabled

### No Events Showing
- Check calendar IDs in `.env`
- Verify calendar sharing permissions
- Check date/timezone settings

### Permission Errors
- Ensure output directory exists: `mkdir -p /opt/dashy/public`
- Check file permissions: `chmod +w /opt/dashy/public`

## Security Notes

- ✅ All sensitive data in `.env` (not committed to git)
- ✅ OAuth tokens stored locally
- ✅ Read-only calendar access
- ❌ Never commit `credentials.json` or `token.json`

## Example Output

The script generates JSON like this:

```json
{
  "title": "Today's Schedule",
  "subtitle": "Saturday, July 26, 2025",
  "items": [
    {
      "label": "Team Meeting",
      "value": "09:00",
      "unit": "My Calendar",
      "color": "#4299e1"
    }
  ],
  "total": 4
}
```
