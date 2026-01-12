/**
 * Validate that the API response has the expected structure
 */
export function validateResponse(response, expectedType = 'object') {
  if (!response || !response.data) {
    throw new Error('Invalid API response: missing data');
  }

  const data = response.data;

  if (expectedType === 'array' && !Array.isArray(data)) {
    console.error('Expected array but got:', typeof data, data);
    throw new Error('Invalid API response: expected array');
  }

  if (expectedType === 'object' && (typeof data !== 'object' || Array.isArray(data))) {
    console.error('Expected object but got:', typeof data, data);
    throw new Error('Invalid API response: expected object');
  }

  return data;
}

/**
 * Validate device object structure
 */
export function validateDevice(device) {
  if (!device || typeof device !== 'object') {
    return false;
  }

  // Required fields
  if (!device.id || !device.name || !device.type || !device.status) {
    console.warn('Device missing required fields:', device);
    return false;
  }

  return true;
}

/**
 * Safely get devices array from response, filtering out invalid ones
 */
export function safeGetDevices(response) {
  try {
    const data = validateResponse(response, 'array');
    return data.filter(validateDevice);
  } catch (error) {
    console.error('Failed to parse devices response:', error);
    return [];
  }
}

/**
 * Safely get single device from response
 */
export function safeGetDevice(response) {
  try {
    const data = validateResponse(response, 'object');
    if (!validateDevice(data)) {
      throw new Error('Invalid device data');
    }
    return data;
  } catch (error) {
    console.error('Failed to parse device response:', error);
    return null;
  }
}

/**
 * Safely get array data with fallback to empty array
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
