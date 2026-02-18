/**
 * Shared formatting utilities used across components.
 */

/**
 * Format an SF311 address for display.
 * "Intersection Annie St, Stevenson St" → "Annie St & Stevenson St"
 * "123 Main St" → "123 Main St" (unchanged)
 */
export function formatAddress(addr: string): string {
  if (!addr) return addr;
  // "Intersection X, Y" → "X & Y" (SF311 intersection format)
  const match = addr.match(/^Intersection\s+(.+?),\s*(.+)$/i);
  if (match) {
    return `${match[1].trim()} & ${match[2].trim()}`;
  }
  return addr;
}

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

/**
 * Format a report date into a human-readable relative-time string.
 * Prefers an ISO 8601 rawDate for accurate sub-day resolution.
 * Falls back to the pre-formatted dateStr when rawDate is unavailable.
 *
 * Examples: "Just now", "5m ago", "3h ago", "Yesterday", "3 days ago", "2 weeks ago", "Jan 15, 2026"
 */
export function formatDate(dateStr: string, rawDate?: string | null): string {
  try {
    // Prefer raw ISO date for reliable parsing (avoids locale/implementation quirks of "Feb 15, 2026")
    const parseable = rawDate || dateStr;
    const date = new Date(parseable);
    if (isNaN(date.getTime())) return dateStr;

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    // For older dates: "Feb 9" (current year) or "Feb 9, 2025" (past year) — consistent across locales
    const month = date.toLocaleString('en-US', { month: 'short' });
    const day = date.getDate();
    const year = date.getFullYear();
    return year === now.getFullYear() ? `${month} ${day}` : `${month} ${day}, ${year}`;
  } catch {
    return dateStr;
  }
}
