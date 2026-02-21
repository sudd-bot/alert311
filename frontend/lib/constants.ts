/**
 * Shared constants used across the Alert311 frontend.
 */

/**
 * San Francisco geographic bounds for map and geocoding.
 * Used to:
 * - Limit map interactions to SF area
 * - Validate geolocation results
 * - Bias address search to SF
 */
export const SF_BOUNDS = {
  minLng: -122.52,
  maxLng: -122.35,
  minLat: 37.70,
  maxLat: 37.83,
};

/**
 * San Francisco center coordinates for initial map view.
 */
export const SF_CENTER = {
  lat: 37.7749,
  lng: -122.4194,
};
