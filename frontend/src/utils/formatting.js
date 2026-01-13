/**
 * Shared formatting utilities for the Homelab Manager application
 */

/**
 * Formats a timestamp into a human-readable string
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted timestamp or 'N/A' if invalid
 */
export function formatTimestamp(timestamp) {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * Formats a short timestamp for tables and compact displays
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted timestamp or 'N/A' if invalid
 */
export function formatShortTimestamp(timestamp) {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Formats a date only (no time)
 * @param {string|Date} date - The date to format
 * @returns {string} Formatted date or 'N/A' if invalid
 */
export function formatDate(date) {
  if (!date) return 'N/A';
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}
