"""
Geocoding service using Nominatim (OpenStreetMap).
Free, no API key required.

Caches geocoding results in memory to avoid repeated API calls for the same address.
"""
import logging
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="alert311/1.0")
        # Simple in-memory cache: address -> (lat, lng)
        self._cache: dict[str, Tuple[float, float]] = {}

    def geocode(self, address: str, *, use_cache: bool = True) -> Optional[Tuple[float, float]]:
        """
        Convert address to (latitude, longitude).
        Returns None if geocoding fails.

        Args:
            address: The address string to geocode
            use_cache: Whether to check/use the in-memory cache (default: True)
        """
        # Normalize address for cache key (strip, case-insensitive)
        normalized = address.strip().lower()
        if not normalized:
            return None

        # Check cache first
        if use_cache and normalized in self._cache:
            return self._cache[normalized]

        try:
            # Add "San Francisco, CA" to improve accuracy
            full_address = f"{address}, San Francisco, CA, USA"
            location = self.geolocator.geocode(full_address, timeout=10)

            if location:
                coords = (location.latitude, location.longitude)
                # Cache the successful result
                self._cache[normalized] = coords
                return coords
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            return None


geocoding_service = GeocodingService()
