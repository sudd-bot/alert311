"""
Geocoding service using Nominatim (OpenStreetMap).
Free, no API key required.
"""
import logging
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="alert311/1.0")
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to (latitude, longitude).
        Returns None if geocoding fails.
        """
        try:
            # Add "San Francisco, CA" to improve accuracy
            full_address = f"{address}, San Francisco, CA, USA"
            location = self.geolocator.geocode(full_address, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            return None


geocoding_service = GeocodingService()
