# VRR EFA API Data Fetcher for Dashy Dashboard

A Python script that fetches real-time public transport departure data from VRR (Verkehrsverbund Rhein-Ruhr) stops and provides it as JSON for dashboard consumption. Includes a beautiful Dashy widget for displaying the departure information.

![VRR Dashboard Widget](https://img.shields.io/badge/Dashy-Widget-blue) ![Python](https://img.shields.io/badge/Python-3.7+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🚌 **Real-time departure data** from VRR EFA API
- 🔍 **Automatic stop ID resolution** from city/stop name combinations
- 🎯 **Platform filtering** support (optional)
- 🎨 **Beautiful Dashy widget** that adapts to your theme
- 📱 **Mobile responsive** design
- ⚡ **Auto-refresh** capabilities
- 🌐 **UTF-8 support** for German umlauts (ÖÄÜß)
- 🔧 **Configurable** via JSON configuration file
- 📊 **Comprehensive logging** and error handling

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vrr-efa-fetcher.git
cd vrr-efa-fetcher

# Install dependencies
pip install -r requirements.txt

# Run the script to create sample configuration
python vrr_fetcher.py
```

### 2. Configuration

Edit the generated `vrr_config.json` file:

```json
{
  "output_file": "./vrr-efa-feed.json",
  "max_departures_per_stop": 10,
  "timeout": 30,
  "stops": [
    {
      "name": "Hauptbahnhof",
      "city": "Düsseldorf",
      "enabled": true,
      "max_departures": 8,
      "platforms": []
    },
    {
      "name": "Bismarckplatz",
      "city": "Düsseldorf", 
      "enabled": true,
      "max_departures": 6,
      "platforms": ["1", "2"]
    }
  ]
}
```

### 3. Run the Fetcher

```bash
# Single run
python vrr_fetcher.py

# With verbose logging
python vrr_fetcher.py -v

# Custom config file
python vrr_fetcher.py -c /path/to/your/config.json
```

### 4. Add Dashy Widget

Add this to your Dashy `conf.yml`:

```yaml
widgets:
  - type: embed
    options:
      html: |
        <div id="vrr-widget-container">
          <p>Lade Abfahrten...</p>
        </div>
      css: |
        # ... (see full widget code in repository PART_conf.yml)
      script: |
        # ... (see full widget code in repository PART_conf.yml)
```

## Configuration Options

### Global Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_file` | string | `"."` | Path where JSON output will be saved |
| `max_departures_per_stop` | number | `10` | Default maximum departures per stop |
| `timeout` | number | `30` | API request timeout in seconds |

### Stop Configuration

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `name` | string | ✅ | Stop name (e.g., "Hauptbahnhof") |
| `city` | string | ✅ | City name (e.g., "Düsseldorf") |
| `enabled` | boolean | ❌ | Whether to fetch this stop (default: true) |
| `max_departures` | number | ❌ | Max departures for this stop |
| `platforms` | array | ❌ | Platform filter (empty = all platforms) |
| `stop_id` | string | ❌ | VRR stop ID (auto-resolved if not provided) |

### Platform Filtering

```json
{
  "platforms": []           // All platforms (default)
  "platforms": ["1", "2"]   // Only platforms 1 and 2
  "platforms": ["A", "B"]   // Only platforms A and B
}
```

## Command Line Options

```bash
python vrr_fetcher.py [OPTIONS]

Options:
  -c, --config PATH     Configuration file path (default: vrr_config.json)
  -v, --verbose         Enable verbose logging
  --debug-api          Save raw API responses to debug files
  --resolve-ids        Force re-resolution of stop IDs
  -h, --help           Show help message
```

## Automation with Cron

For automatic updates, add a cron job:

```bash
# Edit crontab
crontab -e

# Add this line for updates every 10 minutes
*/10 * * * * cd /path/to/vrr-fetcher && /usr/bin/python3 vrr_fetcher.py

# Or every 15 minutes during operating hours (5 AM - 1 AM)
*/15 5-23 * * * cd /path/to/vrr-fetcher && /usr/bin/python3 vrr_fetcher.py
0-45/15 0 * * * cd /path/to/vrr-fetcher && /usr/bin/python3 vrr_fetcher.py
```

## Output Format  

The script generates a JSON file with this structure:

```json
{
  "last_updated": "2025-07-28T10:30:00.123456",
  "update_interval_minutes": 10,
  "stops": {
    "Düsseldorf Hauptbahnhof": {
      "city": "Düsseldorf",
      "name": "Hauptbahnhof", 
      "stop_id": "20009289",
      "platforms": [],
      "departures": [
        {
          "line": "U79",
          "destination": "Düsseldorf Universität Ost",
          "platform": "1",
          "departure_time": "10:35",
          "departure_date": "28.07.2025",
          "countdown_minutes": "5",
          "display_time": "5 Min",
          "delay": 2,
          "delay_text": "+2",
          "vehicle_type": "U-Bahn",
          "is_realtime": true,
          "cancelled": false,
          "operator": "Rheinbahn AG"
        }
      ],
      "last_updated": "2025-07-28T10:30:00.123456",
      "count": 8
    }
  }
}
```

## Dashy Widget Features

- 🎨 **Theme Integration**: Automatically adapts to your Dashy theme
- 📱 **Responsive Design**: Works on desktop and mobile
- ⏱️ **Real-time Updates**: Refreshes every 30 seconds
- 🚦 **Color Coding**: 
  - Green: Normal departures
  - Orange: Departures leaving soon (≤15 min)
  - Red: Immediate departures (≤5 min, with pulse animation)
- 🚏 **Platform Display**: Shows platform information when available
- ⏰ **Smart Time Display**: Shows countdown in minutes or exact time
- 🔄 **Auto-refresh**: Keeps data current without page reload

## Supported Cities/Regions

This tool works with all public transport stops covered by the VRR (Verkehrsverbund Rhein-Ruhr) network, including:

- Düsseldorf
- Essen  
- Dortmund
- Bochum
- Duisburg
- Wuppertal
- Mönchengladbach
- Krefeld
- And many more cities in North Rhine-Westphalia

## API Information

This tool uses the official VRR EFA (Electronic Fare Collection) API:
- **Base URL**: `https://efa.vrr.de/vrr`
- **Documentation**: [VRR Open Data](https://www.vrr.de/de/mobilitaet/open-data/)
- **Rate Limits**: Be respectful with API calls (recommended: max 1 request per minute per stop)

## Troubleshooting

### Common Issues

**Stop ID not found:**
```bash
# Force re-resolution of stop IDs
python vrr_fetcher.py --resolve-ids

# Check if city/stop name combination is correct
# Try variations like "Hbf" instead of "Hauptbahnhof"
```

**UTF-8 encoding errors:**
- Make sure your system supports UTF-8
- The script handles German umlauts automatically

**API timeout errors:**
- Increase timeout in configuration
- Check your internet connection
- VRR API might be temporarily unavailable

**Empty departures:**
- Check if the stop is served at the current time
- Verify platform filtering settings
- Some stops might have no service on weekends/holidays

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Save raw API responses
python vrr_fetcher.py --debug-api -v

# This creates debug files: debug_api_dm_[stop_id]_[timestamp].json
```

## Development

### Project Structure

```
vrr-efa-fetcher/
├── vrr_fetcher.py          # Main fetcher script
├── vrr_config.json         # Configuration file (auto-generated)
├── requirements.txt        # Python dependencies  
├── README.md              # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

### Testing

```bash
# Test with sample configuration
python vrr_fetcher.py -v

# Test specific stop
python -c "
from vrr_fetcher import VRRFetcher
fetcher = VRRFetcher()
print(fetcher.find_stop_id('Düsseldorf', 'Hauptbahnhof'))
"
```

## Requirements

- Python 3.7+
- `requests` library
- UTF-8 system encoding
- Internet connection for API access

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [VRR](https://www.vrr.de/) for providing the public transport API
- [Dashy](https://github.com/Lissy93/dashy) for the excellent dashboard framework
- Contributors and users who help improve this tool