# Dashy Calendar Feed Generator

A Python script that fetches Google Calendar events and creates a JSON feed for Dashy's data-feed widget, providing seamless theme integration.

## Features

- 🔐 Secure credential management with `.env` files
- 📅 Multiple Google Calendar support
- 🎨 Theme-matching colors for different calendars
- ⚡ Automatic authentication and token refresh
- 📱 Perfect integration with Dashy's material-dark theme

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

### Step 4: First Run

```bash
python3 calendar_feed.py
```

On first run:
- Browser will open for Google authentication
- Grant calendar read permissions
- Token will be saved for future runs

### Step 5: Add to Dashy

Add this to your `conf.yml`:

```yaml
- name: Today's Schedule
  icon: fas fa-calendar-check
  widgets:
    - type: data-feed
      url: ./calendar-feed.json
      title: Family Calendar
      refreshInterval: 900  # 15 minutes
```

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

This displays in Dashy as a native widget matching your theme perfectly!