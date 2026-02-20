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
    # Cache size limit to prevent memory issues in long-running processes
    # 1000 addresses is plenty for typical usage (each entry ~100 bytes)
    MAX_CACHE_SIZE = 1000

    def __init__(self):
        self.geolocator = Nominatim(user_agent="alert311/1.0")
        # Simple in-memory cache: address -> (lat, lng)
        self._cache: dict[str, Tuple[float, float]] = {}
        self._access_order: list[str] = []  # Track access order for LRU eviction

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

        # Check cache first (LRU: update access order)
        if use_cache and normalized in self._cache:
            # Update access order for LRU tracking
            self._access_order.remove(normalized)
            self._access_order.append(normalized)
            return self._cache[normalized]

        try:
            # Add "San Francisco, CA" to improve accuracy
            full_address = f"{address}, San Francisco, CA, USA"
            location = self.geolocator.geocode(full_address, timeout=10)

            if location:
                coords = (location.latitude, location.longitude)
                # Cache the successful result
                self._cache[normalized] = coords
                self._access_order.append(normalized)

                # Evict oldest entry if cache exceeds limit
                if len(self._cache) > self.MAX_CACHE_SIZE:
                    oldest_key = self._access_order.pop(0)
                    self._cache.pop(oldest_key, None)

                return coords
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            return None


geocoding_service = GeocodingService()
