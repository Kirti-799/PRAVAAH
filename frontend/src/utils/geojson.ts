/**
 * frontend/src/utils/geojson.ts
 *
 * Robust GeoJSON validation guardrails.
 * Ensures any GeoJSON payload passed to Leaflet (<GeoJSON />) strictly conforms
 * to the GeoJSON specification (Feature, FeatureCollection, or Geometry), preventing
 * unhandled "Invalid GeoJSON object" exceptions that can unmount the React component tree.
 */

export function isValidGeoJSON(data: unknown): boolean {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const obj = data as Record<string, unknown>;

  // Check if it's an API error or status stub
  if ('status' in obj && !('type' in obj)) {
    return false;
  }

  const validTypes = [
    'Feature',
    'FeatureCollection',
    'Point',
    'MultiPoint',
    'LineString',
    'MultiLineString',
    'Polygon',
    'MultiPolygon',
    'GeometryCollection',
  ];

  if (typeof obj.type !== 'string' || !validTypes.includes(obj.type)) {
    return false;
  }

  // FeatureCollection must have an array of features
  if (obj.type === 'FeatureCollection') {
    return Array.isArray(obj.features);
  }

  // Feature must have geometry or properties
  if (obj.type === 'Feature') {
    return obj.geometry !== undefined || obj.properties !== undefined;
  }

  return true;
}
