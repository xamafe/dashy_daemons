#!/usr/bin/env python3
"""
VRR EFA API Data Fetcher for Dashy Dashboard
Fetches departure times from configured stops and saves to JSON file
Automatically resolves stop IDs from city/stop name combinations
"""

import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional, Tuple
import argparse
import time


class VRRFetcher:
    def __init__(self, config_file: str = "vrr_config.json", debug_api: bool = False):
        self.config_file = config_file
        self.debug_api = debug_api
        self.config = self.load_config()
        self.base_url = "https://efa.vrr.de/vrr"
        self.dm_endpoint = f"{self.base_url}/XML_DM_REQUEST"
        self.stopfinder_endpoint = f"{self.base_url}/XML_STOPFINDER_REQUEST"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VRR-Dashy-Fetcher/1.0',
            'Accept-Charset': 'utf-8'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Using configuration file: {self.config_file}")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file {self.config_file} not found")
            self.create_sample_config()
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def save_config(self):
        """Save current configuration back to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.debug("Configuration file updated")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    def create_sample_config(self):
        """Create a sample configuration file"""
        sample_config = {
            "output_file": ".",
            "max_departures_per_stop": 10,
            "timeout": 30,
            "stops": [
                {
                    "name": "Hauptbahnhof",
                    "city": "Düsseldorf",
                    "enabled": True,
                    "max_departures": 8,
                    "platforms": []  # Empty list = all platforms, or specify like ["1", "2", "3"]
                },
                {
                    "name": "Hauptbahnhof", 
                    "city": "Essen",
                    "enabled": True,
                    "max_departures": 5,
                    "platforms": ["1", "2"]  # Only platforms 1 and 2
                },
                {
                    "name": "Bismarckplatz",
                    "city": "Düsseldorf",
                    "enabled": False,
                    "max_departures": 6
                }
            ]
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Created sample configuration file: {self.config_file}")
        self.logger.info("Please edit the configuration file with your stops and run again")

    def find_stop_id(self, city: str, name: str) -> Optional[str]:
        """Find stop ID using the VRR EFA stopfinder API"""
        params = {
            'outputFormat': 'JSON',
            'language': 'de',
            'stateless': '1',
            'locationServerActive': '1',
            'type_sf': 'stop',
            'name_sf': f"{city}:{name}",
        }
        
        try:
            response = self.session.get(
                self.stopfinder_endpoint, 
                params=params, 
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            data = response.json()
            
            # Parse the stopfinder response
            if 'stopFinder' in data and 'points' in data['stopFinder']:
                points = data['stopFinder']['points']
                if isinstance(points, dict) and 'point' in points:
                    # Single result
                    if isinstance(points['point'], dict):
                        point = points['point']
                        if 'ref' in point:
                            return point['ref']['id']
                    # Multiple results - take the first exact match
                    elif isinstance(points['point'], list):
                        for point in points['point']:
                            if isinstance(point, dict) and 'ref' in point:
                                # Check if this is an exact match
                                point_name = point.get('name', '').lower()
                                search_name = name.lower()
                                if search_name in point_name or point_name.startswith(search_name):
                                    return point['ref']['id']
                        # If no exact match, take the first one
                        if points['point'] and 'ref' in points['point'][0]:
                            return points['point'][0]['ref']['id']
            
            self.logger.warning(f"No stop ID found for {city}:{name}")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching for stop {city}:{name}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing stopfinder response for {city}:{name}: {e}")
            return None

    def resolve_stop_id(self, stop_config: Dict[str, Any]) -> Optional[str]:
        """Resolve stop ID from configuration, fetching if necessary"""
        # Check if we already have a stop_id
        if 'stop_id' in stop_config and stop_config['stop_id']:
            return stop_config['stop_id']
        
        # We need city and name to search
        city = stop_config.get('city')
        name = stop_config.get('name')
        
        if not city or not name:
            self.logger.error(f"Missing city or name in stop configuration: {stop_config}")
            return None
        
        self.logger.info(f"Searching for stop ID: {city}:{name}")
        stop_id = self.find_stop_id(city, name)
        
        if stop_id:
            # Save the found ID back to configuration
            stop_config['stop_id'] = stop_id
            self.save_config()
            self.logger.info(f"Found and saved stop ID {stop_id} for {city}:{name}")
        
        return stop_id

    def should_include_departure(self, departure: Dict[str, Any], platform_filter: List[str]) -> bool:
        """Check if departure should be included based on platform filter"""
        if not platform_filter:  # Empty list means include all platforms
            return True
        
        departure_platform = departure.get('platform', '')
        return departure_platform in platform_filter

    def fetch_departures(self, stop_id: str, max_departures: int = 10, platform_filter: List[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Fetch departure data for a specific stop"""
        if platform_filter is None:
            platform_filter = []
            
        params = {
            'outputFormat': 'JSON',
            'language': 'de',
            'stateless': '1',
            'coordOutputFormat': 'WGS84[DD.DDDDD]',
            'type_dm': 'stopID',
            'name_dm': stop_id,
            'mode': 'direct',
            'dmLineSelectionAll': '1',
            'useAllStops': '1',
            'useRealtime': '1',
            'limit': str(max_departures * 2)  # Fetch more to account for platform filtering
        }
        
        try:
            response = self.session.get(
                self.dm_endpoint, 
                params=params, 
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            data = response.json()
            
            # Debug: Save raw API response if requested
            if self.debug_api:
                debug_file = f"debug_api_dm_{stop_id}_{int(time.time())}.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Saved raw API response to {debug_file}")
            
            # Debug: Log the raw response structure for troubleshooting
            self.logger.debug(f"API Response keys: {list(data.keys()) if data else 'None'}")
            if 'departureList' in data:
                self.logger.debug(f"Found {len(data['departureList'])} departures")
                if data['departureList']:
                    self.logger.debug(f"First departure keys: {list(data['departureList'][0].keys())}")
            
            # Parse the EFA response
            departures = []
            if 'departureList' in data and data['departureList']:
                for departure in data['departureList']:
                    serving_line = departure.get('servingLine', {})
                    date_time = departure.get('dateTime', {})
                    real_date_time = departure.get('realDateTime', {})
                    
                    # Extract time information from the API structure
                    departure_time = ''
                    departure_date = ''
                    real_time = ''
                    real_date = ''
                    
                    # Build time from individual components
                    if date_time:
                        hour = str(date_time.get('hour', 0)).zfill(2)
                        minute = str(date_time.get('minute', 0)).zfill(2)
                        departure_time = f"{hour}:{minute}"
                        
                        day = str(date_time.get('day', 1)).zfill(2)
                        month = str(date_time.get('month', 1)).zfill(2)
                        year = str(date_time.get('year', 2025))
                        departure_date = f"{day}.{month}.{year}"
                    
                    if real_date_time:
                        hour = str(real_date_time.get('hour', 0)).zfill(2)
                        minute = str(real_date_time.get('minute', 0)).zfill(2)
                        real_time = f"{hour}:{minute}"
                        
                        day = str(real_date_time.get('day', 1)).zfill(2)
                        month = str(real_date_time.get('month', 1)).zfill(2)
                        year = str(real_date_time.get('year', 2025))
                        real_date = f"{day}.{month}.{year}"
                    
                    # Use countdown as fallback for time calculation
                    countdown_minutes = departure.get('countdown')
                    if countdown_minutes and not departure_time:
                        try:
                            countdown_int = int(countdown_minutes)
                            future_time = datetime.now() + timedelta(minutes=countdown_int)
                            departure_time = future_time.strftime('%H:%M')
                            departure_date = future_time.strftime('%d.%m.%Y')
                        except (ValueError, TypeError):
                            pass
                    
                    # Extract delay from serving line
                    delay = 0
                    if serving_line.get('delay'):
                        try:
                            delay = int(serving_line['delay'])
                        except (ValueError, TypeError):
                            delay = 0
                    
                    # Extract vehicle type - VRR uses 'name' field in servingLine
                    vehicle_type = 'Bus'  # Default for VRR bus services
                    if serving_line.get('name'):
                        vehicle_type = serving_line['name']
                    
                    # Map motType to more readable vehicle types
                    mot_type = serving_line.get('motType', '5')
                    vehicle_type_map = {
                        '0': 'Zug', '1': 'S-Bahn', '2': 'U-Bahn', '3': 'Straßenbahn',
                        '4': 'Stadtbus', '5': 'Regionalbus', '6': 'Schnellbus',
                        '7': 'Bus', '8': 'Sonstige', '9': 'Fähre', '10': 'AST'
                    }
                    
                    if mot_type in vehicle_type_map:
                        vehicle_type = vehicle_type_map[mot_type]
                    
                    # Check if this is real-time data
                    is_realtime = serving_line.get('realtime') == '1'
                    
                    # Create formatted time display using countdown if available
                    display_time = departure_time
                    if countdown_minutes:
                        try:
                            countdown_int = int(countdown_minutes)
                            if countdown_int <= 0:
                                display_time = "sofort"
                            elif countdown_int < 60:
                                display_time = f"{countdown_int} Min"
                            else:
                                display_time = departure_time
                        except (ValueError, TypeError):
                            pass
                    
                    dep_info = {
                        'line': serving_line.get('number', 'Unknown'),
                        'destination': serving_line.get('direction', 'Unknown'),
                        'platform': departure.get('platform', ''),
                        'departure_time': departure_time,
                        'departure_date': departure_date,
                        'real_time': real_time,
                        'real_date': real_date,
                        'countdown_minutes': countdown_minutes,
                        'display_time': display_time,
                        'delay': delay,
                        'delay_text': f"+{delay}" if delay > 0 else ("pünktlich" if delay == 0 else f"{delay}"),
                        'vehicle_type': vehicle_type,
                        'route_type': mot_type,
                        'is_realtime': is_realtime,
                        'cancelled': departure.get('cancelled', False),
                        'operator': departure.get('operator', {}).get('name', ''),
                        'accessibility': {
                            'wheelchair': False,  # Not clearly available in this API version
                            'low_floor': vehicle_type.lower().find('niederflur') >= 0  # Check if "Niederflur" in name
                        }
                    }
                    
                    # Add stop sequence if available
                    if 'prevStopSeq' in departure:
                        dep_info['previous_stops'] = [
                            stop.get('name', '') for stop in departure['prevStopSeq']
                        ]
                    
                    # Apply platform filter
                    if self.should_include_departure(dep_info, platform_filter):
                        departures.append(dep_info)
                        
                        # Stop when we have enough departures after filtering
                        if len(departures) >= max_departures:
                            break
            
            return departures
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data for stop {stop_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response for stop {stop_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching data for stop {stop_id}: {e}")
            return None

    def fetch_all_stops(self) -> Dict[str, Any]:
        """Fetch departure data for all configured stops"""
        result = {
            'last_updated': datetime.now().isoformat(),
            'update_interval_minutes': 10,  # Default update interval
            'stops': {}
        }
        
        config_changed = False
        
        for stop_config in self.config.get('stops', []):
            if not stop_config.get('enabled', True):
                stop_display_name = f"{stop_config.get('city', 'Unknown')} {stop_config.get('name', 'Unknown')}"
                self.logger.info(f"Skipping disabled stop: {stop_display_name}")
                continue
                
            # Resolve stop ID
            stop_id = self.resolve_stop_id(stop_config)
            if not stop_id:
                continue
                
            # If we added a stop_id, mark config as changed
            if 'stop_id' not in stop_config:
                config_changed = True
            
            city = stop_config.get('city', 'Unknown')
            name = stop_config.get('name', 'Unknown')
            stop_display_name = f"{city} {name}"
            max_deps = stop_config.get('max_departures', self.config.get('max_departures_per_stop', 10))
            platform_filter = stop_config.get('platforms', [])
            
            # Log platform filtering info
            if platform_filter:
                self.logger.info(f"Fetching departures for {stop_display_name} (ID: {stop_id}) - Platforms: {', '.join(platform_filter)}")
            else:
                self.logger.info(f"Fetching departures for {stop_display_name} (ID: {stop_id}) - All platforms")
                
            departures = self.fetch_departures(stop_id, max_deps, platform_filter)
            
            if departures is not None:
                result['stops'][stop_display_name] = {
                    'city': city,
                    'name': name,
                    'stop_id': stop_id,
                    'platforms': platform_filter,
                    'departures': departures,
                    'last_updated': datetime.now().isoformat(),
                    'count': len(departures)
                }
                platform_info = f" (platforms: {', '.join(platform_filter)})" if platform_filter else " (all platforms)"
                self.logger.info(f"Successfully fetched {len(departures)} departures for {stop_display_name}{platform_info}")
            else:
                result['stops'][stop_display_name] = {
                    'city': city,
                    'name': name,
                    'stop_id': stop_id,
                    'platforms': platform_filter,
                    'departures': [],
                    'last_updated': datetime.now().isoformat(),
                    'count': 0,
                    'error': 'Failed to fetch data'
                }
                self.logger.warning(f"Failed to fetch departures for {stop_display_name}")
        
        # Save config if we added any stop IDs
        if config_changed:
            self.save_config()
        
        return result

    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to JSON file"""
        output_file = self.config.get('output_file', '.')
        
        # If output_file is a directory, create the filename
        if output_file == '.' or Path(output_file).is_dir():
            output_path = Path(output_file) / 'vrr_data.json'
        else:
            output_path = Path(output_file)
        
        try:
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {output_path}: {e}")
            return False

    def run(self):
        """Main execution method"""
        self.logger.info("Starting VRR data fetch")
        
        # Fetch data from all stops
        data = self.fetch_all_stops()
        
        # Save to file
        if self.save_data(data):
            total_departures = sum(stop.get('count', 0) for stop in data['stops'].values())
            self.logger.info(f"Successfully processed {len(data['stops'])} stops with {total_departures} total departures")
        else:
            self.logger.error("Failed to save data")
            sys.exit(1)


def main():
    
    SCRIPT_DIR = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description='Fetch VRR departure data for Dashy dashboard')
    parser.add_argument('-c', '--config', default= SCRIPT_DIR / 'vrr_config.json', 
                       help='Configuration file path (default: vrr_config.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--debug-api', action='store_true',
                       help='Save raw API responses to debug files')
    parser.add_argument('--resolve-ids', action='store_true',
                       help='Force re-resolution of stop IDs even if they exist')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    fetcher = VRRFetcher(args.config, args.debug_api)
    
    # Force re-resolution of stop IDs if requested
    if args.resolve_ids:
        for stop in fetcher.config.get('stops', []):
            if 'stop_id' in stop:
                del stop['stop_id']
        fetcher.logger.info("Forcing re-resolution of all stop IDs")
    
    fetcher.run()


if __name__ == "__main__":
    main()