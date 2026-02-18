/**
 * Shared formatting utilities used across components.
 */

/**
 * Format a distance in meters into a human-readable string.
 * < 100m  → "52m away"
 * ≥ 100m  → "0.3mi away"
 */
export function formatDistance(meters?: number | null): string {
  if (meters == null) return '';
  if (meters < 100) return `${Math.round(meters)}m away`;
  const miles = meters / 1609.34;
  if (miles < 0.1) return `${Math.round(meters)}m away`;
  return `${miles.toFixed(1)}mi away`;
}
