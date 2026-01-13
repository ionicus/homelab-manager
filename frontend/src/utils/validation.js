/**
 * Validation and data extraction utilities for API responses
 */

/**
 * Safely get array data with fallback to empty array
 * Handles various API response structures
 *
 * @param {Object} response - API response object
 * @param {string} fieldName - Optional field name to extract from (default: 'data')
 * @returns {Array} Array of data or empty array if invalid
 */
export function safeGetArray(response, fieldName = 'data') {
  try {
    if (!response) return [];
    const data = response.data || response;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data[fieldName])) return data[fieldName];
    return [];
  } catch (error) {
    console.error('Failed to parse array response:', error);
    return [];
  }
}
