export interface Geo {
  available: boolean;
  lat: number;
  lon: number;
  bounds: [[number, number], [number, number]];
}

export interface Summary {
  healthy: number;
  moderate: number;
  severe: number;
  total_zones: number;
}

export interface Zone {
  zone_id: number;
  severity: "HIGH" | "MODERATE" | "LOW";
  health_score: number;
  area: number;
  issue: string;
  recommendation: string;
  geo_coordinates?: [number, number][];
}

export interface AnalyzeResponse {
  status: "success";
  scan_id?: string;
  map: string;
  geo: Geo;
  summary: Summary;
  zones: Zone[];
}
